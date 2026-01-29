import typing

from finecode_extension_api import service


class ILspClient(service.DisposableService, typing.Protocol):
    # TODO: init readable_id: str

    ...
