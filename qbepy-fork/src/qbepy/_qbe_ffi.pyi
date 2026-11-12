"""Type stubs for CFFI-generated _qbe_ffi module."""

from typing import Any

class FFI:
    """CFFI FFI instance."""

    NULL: Any
    def new(self, cdecl: str) -> Any: ...
    def string(self, cdata: Any, maxlen: int = ...) -> bytes: ...

class Lib:
    """CFFI lib instance with QBE wrapper functions."""

    QBEPY_OK: int
    QBEPY_ERROR: int

    def qbepy_get_error(self) -> Any: ...
    def qbepy_clear_error(self) -> None: ...
    def qbepy_compile(
        self,
        input: bytes,
        input_len: int,
        target: bytes | Any,
        output: Any,
        output_len: Any,
    ) -> int: ...
    def qbepy_free(self, ptr: Any) -> None: ...
    def qbepy_get_targets(self) -> Any: ...
    def qbepy_get_default_target(self) -> Any: ...
    def qbepy_version(self) -> Any: ...

ffi: FFI
lib: Lib
