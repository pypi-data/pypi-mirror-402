import pathlib
import typing

from finecode_extension_api import common_types


class IDevEnvInfoProvider(typing.Protocol):
    ...
    # methods related to file ownership
    # async def owned_files(self, dev_env: common_types.DevEnv) -> list[pathlib.Path]:
    #     ...

    # async def is_owner_of(self, dev_env: common_types.DevEnv, file_path: pathlib.Path) -> bool:
    #     ...

    # async def file_is_owned_by(self, file_path: pathlib.Path) -> list[common_types.DevEnv]:
    #     ...

    # async def files_owned_by_dev_envs(self) -> list[pathlib.Path]:
    #     ...

    # async def get_file_content(self, file_path: pathlib.Path) -> bytes:
    #     # supposed to be used only by `ifilemanager.IFileManager`, which provides
    #     # unified interface for file access independently of owner.
    #     ...
    
    # async def save_file_content(self, file_path: pathlib.Path, file_content: bytes) -> None:
    #     # supposed to be used only by `ifilemanager.IFileManager`, which provides
    #     # unified interface for file access independently of owner.
    #     ...
