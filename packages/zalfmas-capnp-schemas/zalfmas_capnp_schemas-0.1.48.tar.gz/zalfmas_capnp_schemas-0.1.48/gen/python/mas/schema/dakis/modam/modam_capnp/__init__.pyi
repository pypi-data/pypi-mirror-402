"""This is an automatically generated stub for `modam.capnp`."""

from collections.abc import Awaitable
from typing import Any, NamedTuple, Protocol, override

from capnp.lib.capnp import (
    _DynamicCapabilityClient,
    _DynamicCapabilityServer,
    _DynamicStructBuilder,
    _InterfaceModule,
)

class _ModamWrapperServiceInterfaceModule(_InterfaceModule):
    class RunaemmodelRequest(Protocol):
        input: str
        def send(
            self,
        ) -> _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient.RunaemmodelResult: ...

    class RunfieldmodelRequest(Protocol):
        input: str
        def send(
            self,
        ) -> _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient.RunfieldmodelResult: ...

    @override
    def _new_client(
        self,
        server: _DynamicCapabilityServer,
    ) -> _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient: ...
    class Server(_DynamicCapabilityServer):
        class RunaemmodelResult(_DynamicStructBuilder):
            @property
            def output(self) -> str: ...
            @output.setter
            def output(self, value: str) -> None: ...

        class RunfieldmodelResult(_DynamicStructBuilder):
            @property
            def output(self) -> str: ...
            @output.setter
            def output(self, value: str) -> None: ...

        class RunaemmodelResultTuple(NamedTuple):
            output: str

        class RunfieldmodelResultTuple(NamedTuple):
            output: str

        class RunaemmodelParams(Protocol):
            input: str

        class RunaemmodelCallContext(Protocol):
            params: _ModamWrapperServiceInterfaceModule.Server.RunaemmodelParams
            @property
            def results(
                self,
            ) -> _ModamWrapperServiceInterfaceModule.Server.RunaemmodelResult: ...

        class RunfieldmodelParams(Protocol):
            input: str

        class RunfieldmodelCallContext(Protocol):
            params: _ModamWrapperServiceInterfaceModule.Server.RunfieldmodelParams
            @property
            def results(
                self,
            ) -> _ModamWrapperServiceInterfaceModule.Server.RunfieldmodelResult: ...

        def runAemModel(
            self,
            input: str,
            _context: _ModamWrapperServiceInterfaceModule.Server.RunaemmodelCallContext,
            **kwargs: Any,
        ) -> Awaitable[
            str
            | _ModamWrapperServiceInterfaceModule.Server.RunaemmodelResultTuple
            | None
        ]: ...
        def runAemModel_context(
            self,
            context: _ModamWrapperServiceInterfaceModule.Server.RunaemmodelCallContext,
        ) -> Awaitable[None]: ...
        def runFieldModel(
            self,
            input: str,
            _context: _ModamWrapperServiceInterfaceModule.Server.RunfieldmodelCallContext,
            **kwargs: Any,
        ) -> Awaitable[
            str
            | _ModamWrapperServiceInterfaceModule.Server.RunfieldmodelResultTuple
            | None
        ]: ...
        def runFieldModel_context(
            self,
            context: _ModamWrapperServiceInterfaceModule.Server.RunfieldmodelCallContext,
        ) -> Awaitable[None]: ...

    class ModamWrapperServiceClient(_DynamicCapabilityClient):
        class RunaemmodelResult(Awaitable[RunaemmodelResult], Protocol):
            output: str

        class RunfieldmodelResult(Awaitable[RunfieldmodelResult], Protocol):
            output: str

        def runAemModel(
            self,
            input: str | None = None,
        ) -> _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient.RunaemmodelResult: ...
        def runFieldModel(
            self,
            input: str | None = None,
        ) -> _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient.RunfieldmodelResult: ...
        def runAemModel_request(
            self,
            input: str | None = None,
        ) -> _ModamWrapperServiceInterfaceModule.RunaemmodelRequest: ...
        def runFieldModel_request(
            self,
            input: str | None = None,
        ) -> _ModamWrapperServiceInterfaceModule.RunfieldmodelRequest: ...

ModamWrapperService: _ModamWrapperServiceInterfaceModule

# Top-level type aliases for use in type annotations
type ModamWrapperServiceClient = (
    _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient
)
type ModamWrapperServiceServer = _ModamWrapperServiceInterfaceModule.Server
type RunaemmodelResult = (
    _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient.RunaemmodelResult
)
type RunfieldmodelResult = (
    _ModamWrapperServiceInterfaceModule.ModamWrapperServiceClient.RunfieldmodelResult
)
