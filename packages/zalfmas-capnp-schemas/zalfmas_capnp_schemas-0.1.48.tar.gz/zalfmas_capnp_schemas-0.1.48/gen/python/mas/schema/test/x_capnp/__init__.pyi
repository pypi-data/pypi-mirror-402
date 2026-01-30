"""This is an automatically generated stub for `x.capnp`."""

from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from typing import IO, Any, Literal, NamedTuple, Protocol, overload, override

from capnp.lib.capnp import (
    _DynamicCapabilityClient,
    _DynamicCapabilityServer,
    _DynamicStructBuilder,
    _DynamicStructReader,
    _InterfaceModule,
    _StructModule,
)

class _XInterfaceModule(_InterfaceModule):
    class MRequest(Protocol):
        i: int
        def send(self) -> _XInterfaceModule.XClient.MResult: ...

    @override
    def _new_client(
        self,
        server: _DynamicCapabilityServer,
    ) -> _XInterfaceModule.XClient: ...
    class Server(_DynamicCapabilityServer):
        class MResult(_DynamicStructBuilder):
            @property
            def t(self) -> str: ...
            @t.setter
            def t(self, value: str) -> None: ...

        class MResultTuple(NamedTuple):
            t: str

        class MParams(Protocol):
            i: int

        class MCallContext(Protocol):
            params: _XInterfaceModule.Server.MParams
            @property
            def results(self) -> _XInterfaceModule.Server.MResult: ...

        def m(
            self,
            i: int,
            _context: _XInterfaceModule.Server.MCallContext,
            **kwargs: Any,
        ) -> Awaitable[str | _XInterfaceModule.Server.MResultTuple | None]: ...
        def m_context(
            self,
            context: _XInterfaceModule.Server.MCallContext,
        ) -> Awaitable[None]: ...

    class XClient(_DynamicCapabilityClient):
        class MResult(Awaitable[MResult], Protocol):
            t: str

        def m(self, i: int | None = None) -> _XInterfaceModule.XClient.MResult: ...
        def m_request(self, i: int | None = None) -> _XInterfaceModule.MRequest: ...

X: _XInterfaceModule

class _SStructModule(_StructModule):
    class Reader(_DynamicStructReader):
        @property
        def c(self) -> _XInterfaceModule.XClient: ...
        @override
        def as_builder(
            self,
            num_first_segment_words: int | None = None,
            allocate_seg_callable: Callable[[int], bytearray] | None = None,
        ) -> SBuilder: ...

    class Builder(_DynamicStructBuilder):
        @property
        def c(self) -> _XInterfaceModule.XClient: ...
        @c.setter
        def c(
            self,
            value: _XInterfaceModule.XClient | _XInterfaceModule.Server,
        ) -> None: ...
        @override
        def as_reader(self) -> SReader: ...

    @override
    def new_message(
        self,
        num_first_segment_words: int | None = None,
        allocate_seg_callable: Callable[[int], bytearray] | None = None,
        c: _XInterfaceModule.XClient | _XInterfaceModule.Server | None = None,
        **kwargs: Any,
    ) -> SBuilder: ...
    @override
    @overload
    def from_bytes(
        self,
        buf: bytes,
        traversal_limit_in_words: int | None = None,
        nesting_limit: int | None = None,
    ) -> AbstractContextManager[SReader]: ...
    @overload
    def from_bytes(
        self,
        buf: bytes,
        traversal_limit_in_words: int | None = None,
        nesting_limit: int | None = None,
        *,
        builder: Literal[False],
    ) -> AbstractContextManager[SReader]: ...
    @overload
    def from_bytes(
        self,
        buf: bytes,
        traversal_limit_in_words: int | None = None,
        nesting_limit: int | None = None,
        *,
        builder: Literal[True],
    ) -> AbstractContextManager[SBuilder]: ...
    @override
    def from_bytes_packed(
        self,
        buf: bytes,
        traversal_limit_in_words: int | None = None,
        nesting_limit: int | None = None,
    ) -> _DynamicStructReader: ...
    @override
    def read(
        self,
        file: IO[str] | IO[bytes],
        traversal_limit_in_words: int | None = None,
        nesting_limit: int | None = None,
    ) -> SReader: ...
    @override
    def read_packed(
        self,
        file: IO[str] | IO[bytes],
        traversal_limit_in_words: int | None = None,
        nesting_limit: int | None = None,
    ) -> SReader: ...

S: _SStructModule

class _YInterfaceModule(_InterfaceModule):
    class MRequest(Protocol):
        hello: str
        def send(self) -> _YInterfaceModule.YClient.MResult: ...

    @override
    def _new_client(
        self,
        server: _DynamicCapabilityServer,
    ) -> _YInterfaceModule.YClient: ...
    class Server(_DynamicCapabilityServer):
        class MResult(Awaitable[None], Protocol): ...

        class MParams(Protocol):
            hello: str

        class MCallContext(Protocol):
            params: _YInterfaceModule.Server.MParams

        def m(
            self,
            hello: str,
            _context: _YInterfaceModule.Server.MCallContext,
            **kwargs: Any,
        ) -> Awaitable[None]: ...
        def m_context(
            self,
            context: _YInterfaceModule.Server.MCallContext,
        ) -> Awaitable[None]: ...

    class YClient(_DynamicCapabilityClient):
        class MResult(Awaitable[None], Protocol): ...

        def m(self, hello: str | None = None) -> _YInterfaceModule.YClient.MResult: ...
        def m_request(self, hello: str | None = None) -> _YInterfaceModule.MRequest: ...

Y: _YInterfaceModule

class _ZInterfaceModule(_InterfaceModule):
    class MRequest(Protocol):
        n: int
        def send(self) -> _ZInterfaceModule.ZClient.MResult: ...

    @override
    def _new_client(
        self,
        server: _DynamicCapabilityServer,
    ) -> _ZInterfaceModule.ZClient: ...
    class Server(_DynamicCapabilityServer):
        class MResult(_DynamicStructBuilder):
            @property
            def r(self) -> float: ...
            @r.setter
            def r(self, value: float) -> None: ...

        class MResultTuple(NamedTuple):
            r: float

        class MParams(Protocol):
            n: int

        class MCallContext(Protocol):
            params: _ZInterfaceModule.Server.MParams
            @property
            def results(self) -> _ZInterfaceModule.Server.MResult: ...

        def m(
            self,
            n: int,
            _context: _ZInterfaceModule.Server.MCallContext,
            **kwargs: Any,
        ) -> Awaitable[float | _ZInterfaceModule.Server.MResultTuple | None]: ...
        def m_context(
            self,
            context: _ZInterfaceModule.Server.MCallContext,
        ) -> Awaitable[None]: ...

    class ZClient(_DynamicCapabilityClient):
        class MResult(Awaitable[MResult], Protocol):
            r: float

        def m(self, n: int | None = None) -> _ZInterfaceModule.ZClient.MResult: ...
        def m_request(self, n: int | None = None) -> _ZInterfaceModule.MRequest: ...

Z: _ZInterfaceModule

# Top-level type aliases for use in type annotations
type MResult = _ZInterfaceModule.ZClient.MResult
type SBuilder = _SStructModule.Builder
type SReader = _SStructModule.Reader
type XClient = _XInterfaceModule.XClient
type XServer = _XInterfaceModule.Server
type YClient = _YInterfaceModule.YClient
type YServer = _YInterfaceModule.Server
type ZClient = _ZInterfaceModule.ZClient
type ZServer = _ZInterfaceModule.Server
