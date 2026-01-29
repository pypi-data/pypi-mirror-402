import typing

from finecode_extension_api import service



class IJsonRpcClient(service.DisposableService, typing.Protocol):
    ...
