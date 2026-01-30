"""This is an automatically generated stub for `a.capnp`."""

from collections.abc import Awaitable
from typing import Any, NamedTuple, Protocol, override

from capnp.lib.capnp import (
    _DynamicCapabilityClient,
    _DynamicCapabilityServer,
    _DynamicStructBuilder,
    _InterfaceModule,
)

class _AInterfaceModule(_InterfaceModule):
    class MethodRequest(Protocol):
        param: str
        def send(self) -> _AInterfaceModule.AClient.MethodResult: ...

    @override
    def _new_client(
        self,
        server: _DynamicCapabilityServer,
    ) -> _AInterfaceModule.AClient: ...
    class Server(_DynamicCapabilityServer):
        class MethodResult(_DynamicStructBuilder):
            @property
            def res(self) -> str: ...
            @res.setter
            def res(self, value: str) -> None: ...

        class MethodResultTuple(NamedTuple):
            res: str

        class MethodParams(Protocol):
            param: str

        class MethodCallContext(Protocol):
            params: _AInterfaceModule.Server.MethodParams
            @property
            def results(self) -> _AInterfaceModule.Server.MethodResult: ...

        def method(
            self,
            param: str,
            _context: _AInterfaceModule.Server.MethodCallContext,
            **kwargs: Any,
        ) -> Awaitable[str | _AInterfaceModule.Server.MethodResultTuple | None]: ...
        def method_context(
            self,
            context: _AInterfaceModule.Server.MethodCallContext,
        ) -> Awaitable[None]: ...

    class AClient(_DynamicCapabilityClient):
        class MethodResult(Awaitable[MethodResult], Protocol):
            res: str

        def method(
            self,
            param: str | None = None,
        ) -> _AInterfaceModule.AClient.MethodResult: ...
        def method_request(
            self,
            param: str | None = None,
        ) -> _AInterfaceModule.MethodRequest: ...

A: _AInterfaceModule

# Top-level type aliases for use in type annotations
type AClient = _AInterfaceModule.AClient
type AServer = _AInterfaceModule.Server
type MethodResult = _AInterfaceModule.AClient.MethodResult
