"""
Utilities for integration of existing tools.

Scenarios:
1. The tool has API for processing file content ... the most optimal case.
2. The tool has LSP server.
    2.1 Either it supports unsaved files (pyrefly).
    2.2 Or it supports only saved files and reads them from the file system.
3. The tool has CLI for processing multiple files.
    3.1 Either CLI can process files from file system and file content(usually provided in stdin) (e.g. ruff).
    3.2 Or CLI can process files only from file system (e.g. pyrefly, mypy).

        In this case user sees updates only after saving the file.
"""

# TODO: integrate pyrefly with LSP client?
#       - https://github.com/facebook/pyrefly/blob/main/pyrefly/lib/lsp/non_wasm/server.rs
#       - LSP client as service (interface + impl)?
# TODO: analyze ruff as well, maybe the same approach can be applied
import abc
import asyncio
import pathlib

from finecode_extension_api.interfaces import (
    iprojectinfoprovider,
    icache,
    ifilemanager,
    ilogger,
)
from finecode_extension_api.actions import lint as lint_action
from finecode_extension_api import code_action


class ExternalLintHandlerBase(
    abc.ABC,
    code_action.ActionHandler[
        lint_action.LintAction, code_action.ActionHandlerConfigType
    ],
):
    CACHE_KEY: str

    def __init__(
        self,
        cache: icache.ICache,
        file_manager: ifilemanager.IFileManager,
        project_info_provider: iprojectinfoprovider.IProjectInfoProvider,
        lifecycle: code_action.ActionHandlerLifecycle,
        logger: ilogger.ILogger,
    ) -> None:
        self.cache = cache
        self.file_manager = file_manager
        self.project_info_provider = project_info_provider
        self.lifecycle = lifecycle
        self.logger = logger

        lifecycle.on_shutdown(self.shutdown)
        lifecycle.on_exit(self.exit)

        self._process_lock_by_cwd: dict[pathlib.Path, asyncio.Lock] = {}
        # projects that are being checked right now
        self._projects_being_checked_done_events: dict[pathlib.Path, asyncio.Event] = {}

    @abc.abstractmethod
    async def run_tool(
        self, file_paths: list[pathlib.Path], cwd: pathlib.Path
    ) -> str: ...

    @abc.abstractmethod
    def parse_tool_output(
        self, output: str
    ) -> dict[str, list[lint_action.LintMessage]]: ...

    @abc.abstractmethod
    def shutdown(self) -> None: ...

    @abc.abstractmethod
    def exit(self) -> None: ...

    async def run(
        self,
        payload: lint_action.LintRunPayload,
        run_context: code_action.RunActionWithPartialResultsContext,
        meta: code_action.RunActionMeta
    ) -> None:
        file_paths = [file_path async for file_path in payload]

        files_by_projects: dict[pathlib.Path, list[pathlib.Path]] = (
            group_files_by_projects(
                file_paths, self.project_info_provider.get_current_project_dir_path()
            )
        )

        for project_path, project_files in files_by_projects.items():
            for file_path in project_files:
                run_context.partial_result_scheduler.schedule(
                    file_path,
                    self.run_on_single_file(
                        file_path,
                        project_path,
                        project_files,
                        action_run_id=run_context.run_id,
                    ),
                )

    async def run_on_single_file(
        self,
        file_path: pathlib.Path,
        project_path: pathlib.Path,
        all_project_files: list[pathlib.Path],
        action_run_id: int,
    ) -> lint_action.LintRunResult:
        # if mypy was run on the file, the result will be found in cache. If result
        # is not in cache, we need additionally to check whether mypy is not running
        # on the file right now, because we run mypy on the whole packages.
        messages: dict[str, list[lint_action.LintMessage]] = {}
        # TODO: right cache with dependencies
        try:
            cached_lint_messages = await self.cache.get_file_cache(
                file_path, self.CACHE_KEY
            )
            messages[str(file_path)] = cached_lint_messages
            return lint_action.LintRunResult(messages=messages)
        except icache.CacheMissException:
            pass

        if project_path in self._projects_being_checked_done_events:
            # use events to know when checking of the project is done. Get results from
            # cache because saving them locally would require more complex data
            # structure and additional synchronization, because we need to to wait on
            # the result, provide it to all waiting tasks and remove after that.
            await self._projects_being_checked_done_events[project_path].wait()
            try:
                cached_lint_messages = await self.cache.get_file_cache(
                    file_path, self.CACHE_KEY
                )
            except icache.CacheMissException:
                # if checking failed, there are no results in cache
                cached_lint_messages = []

            messages[str(file_path)] = cached_lint_messages
            return lint_action.LintRunResult(messages=messages)
        else:
            # save file versions at the beginning because file can be changed during
            # checking and we want to cache result for current version, not for changed
            project_checked_event = asyncio.Event()
            self._projects_being_checked_done_events[project_path] = (
                project_checked_event
            )
            files_versions: dict[pathlib.Path, str] = {}
            # can we exclude cached files here? Using the right cache(one that handles
            # dependencies as well) should be possible
            for file_path in all_project_files:
                file_version = await self.file_manager.get_file_version(file_path)
                files_versions[file_path] = file_version

            try:
                all_processed_files_with_messages = await self.run_tool_on_project(
                    project_path, all_project_files
                )
                messages = {
                    str(file_path): lint_messages
                    for (
                        file_path,
                        lint_messages,
                    ) in all_processed_files_with_messages.items()
                }

                for (
                    file_path,
                    lint_messages,
                ) in all_processed_files_with_messages.items():
                    try:
                        file_version = files_versions[file_path]
                    except KeyError:
                        # mypy can resolve dependencies which are not in `files_to_lint`
                        # and as result also not in `files_versions`
                        file_version = await self.file_manager.get_file_version(
                            file_path
                        )

                    await self.cache.save_file_cache(
                        file_path, file_version, self.CACHE_KEY, lint_messages
                    )
            finally:
                project_checked_event.set()
                del self._projects_being_checked_done_events[project_path]

            return lint_action.LintRunResult(messages=messages)

    async def run_tool_on_project(
        self, project_dir_path: pathlib.Path, all_project_files: list[pathlib.Path]
    ) -> dict[pathlib.Path, list[lint_action.LintMessage]]:
        new_messages: dict[str, list[lint_action.LintMessage]] = {}
        if project_dir_path not in self._process_lock_by_cwd:
            self._process_lock_by_cwd[project_dir_path] = asyncio.Lock()

        project_lock = self._process_lock_by_cwd[project_dir_path]
        async with project_lock:
            try:
                tool_output = await self.run_tool(
                    file_paths=all_project_files, cwd=project_dir_path
                )
            except Exception as unexpected_exception:
                self.logger.error(str(unexpected_exception))
                return {}

        try:
            project_lint_messages = self.parse_tool_output(output=tool_output)
        except Exception as unexpected_exception:
            self.logger.error(str(unexpected_exception))
            project_lint_messages = {}

        new_messages.update(project_lint_messages)
        all_processed_files_with_messages: dict[
            pathlib.Path, list[lint_action.LintMessage]
        ] = {file_path: [] for file_path in all_project_files}
        all_processed_files_with_messages.update(
            {
                pathlib.Path(file_path_str): lint_messages
                for file_path_str, lint_messages in new_messages.items()
            }
        )
        return all_processed_files_with_messages


def group_files_by_projects(
    files: list[pathlib.Path], root_dir: pathlib.Path
) -> dict[pathlib.Path, list[pathlib.Path]]:
    files_by_projects_dirs: dict[pathlib.Path, list[pathlib.Path]] = {}

    projects_defs = list(root_dir.rglob("pyproject.toml"))
    projects_dirs = [project_def.parent for project_def in projects_defs]
    # sort by depth so that child items are first
    # default reverse path sorting works so, that child items are before their
    # parents
    projects_dirs.sort(reverse=True)

    for file_path in files:
        for project_dir in projects_dirs:
            if file_path.is_relative_to(project_dir):
                if project_dir not in files_by_projects_dirs:
                    files_by_projects_dirs[project_dir] = []
                files_by_projects_dirs[project_dir].append(file_path)
                break

    return files_by_projects_dirs
