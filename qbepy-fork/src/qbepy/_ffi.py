"""Low-level FFI bindings to QBE."""

from __future__ import annotations

from ._qbe_ffi import ffi, lib


class QBEError(Exception):
    """Error from QBE compilation."""


def compile_il(source: str, target: str | None = None) -> str:
    """
    Compile QBE IL to assembly.

    Args:
        source: QBE IL source code
        target: Target architecture (or None for default)
                Valid targets: amd64_sysv, amd64_apple, arm64, arm64_apple, rv64

    Returns:
        Assembly code as string

    Raises:
        QBEError: If compilation fails
    """
    source_bytes = source.encode("utf-8")
    target_bytes = target.encode("utf-8") if target else ffi.NULL

    output_ptr = ffi.new("char**")
    output_len = ffi.new("size_t*")

    result = lib.qbepy_compile(
        source_bytes, len(source_bytes), target_bytes, output_ptr, output_len
    )

    if result != lib.QBEPY_OK:
        error_msg = ffi.string(lib.qbepy_get_error()).decode("utf-8")
        raise QBEError(error_msg)

    try:
        if output_ptr[0] == ffi.NULL:
            msg = "No output generated"
            raise QBEError(msg)
        output = ffi.string(output_ptr[0], output_len[0]).decode("utf-8")
    finally:
        if output_ptr[0] != ffi.NULL:
            lib.qbepy_free(output_ptr[0])

    return output


def get_targets() -> list[str]:
    """Get list of available target architectures."""
    targets_str = ffi.string(lib.qbepy_get_targets()).decode("utf-8")
    return targets_str.split(",")


def get_default_target() -> str:
    """Get default target for current platform."""
    return ffi.string(lib.qbepy_get_default_target()).decode("utf-8")


def version() -> str:
    """Get QBE version string."""
    return ffi.string(lib.qbepy_version()).decode("utf-8")
