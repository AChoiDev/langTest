"""High-level QBE compiler interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ._ffi import QBEError, compile_il as _compile_il, get_default_target, get_targets
from .errors import CompilationError

if TYPE_CHECKING:
    from .ir.builder import Module

Target = Literal["amd64_sysv", "amd64_apple", "arm64", "arm64_apple", "rv64"]


class Compiler:
    """QBE compiler interface.

    Provides methods to compile QBE IL to native assembly code.

    Example:
        >>> compiler = Compiler()
        >>> il = '''
        ... export function w $add(w %a, w %b) {
        ... @start
        ...     %r =w add %a, %b
        ...     ret %r
        ... }
        ... '''
        >>> asm = compiler.compile(il)
    """

    TARGETS: list[str] = ["amd64_sysv", "amd64_apple", "arm64", "arm64_apple", "rv64"]

    def __init__(self, target: Target | None = None):
        """Initialize compiler.

        Args:
            target: Target architecture. If None, uses platform default.
                    Valid targets: amd64_sysv, amd64_apple, arm64, arm64_apple, rv64

        Raises:
            ValueError: If target is not a valid target name.
        """
        if target and target not in self.TARGETS:
            msg = f"Unknown target: {target}. Valid targets: {self.TARGETS}"
            raise ValueError(msg)
        self.target = target

    def compile(self, il: str) -> str:
        """Compile QBE IL to assembly.

        Args:
            il: QBE IL source code

        Returns:
            Generated assembly code as a string

        Raises:
            CompilationError: If compilation fails
        """
        try:
            return _compile_il(il, self.target)
        except QBEError as e:
            raise CompilationError(str(e), source=il) from e

    def compile_module(self, module: Module) -> str:
        """Compile a Module to assembly.

        Args:
            module: IR Module object

        Returns:
            Generated assembly code as a string

        Raises:
            CompilationError: If compilation fails
        """
        il = module.emit()
        return self.compile(il)

    def set_target(self, target: Target) -> None:
        """Set the compilation target.

        Args:
            target: Target architecture name

        Raises:
            ValueError: If the target is not recognized
        """
        if target not in self.TARGETS:
            msg = (
                f"Unknown target: {target}. "
                f"Available targets: {', '.join(self.TARGETS)}"
            )
            raise ValueError(msg)
        self.target = target

    @staticmethod
    def get_default_target() -> str:
        """Get QBE's default target for the current platform.

        Returns:
            The default target name
        """
        return get_default_target()

    @staticmethod
    def get_available_targets() -> list[str]:
        """Get list of available compilation targets.

        Returns:
            List of target names
        """
        return get_targets()


def compile_il(il: str, target: Target | None = None) -> str:
    """Compile QBE IL text to assembly.

    Convenience function that creates a Compiler and compiles the IL.

    Args:
        il: QBE intermediate language source code
        target: Target architecture (e.g., 'amd64_sysv', 'arm64').
                If None, uses QBE's default for the current platform.

    Returns:
        Generated assembly code as a string

    Raises:
        CompilationError: If compilation fails

    Example:
        >>> il = '''
        ... export function w $main() {
        ... @start
        ...     ret 0
        ... }
        ... '''
        >>> asm = compile_il(il)
    """
    compiler = Compiler(target)
    return compiler.compile(il)


def compile_module(module: Module, target: Target | None = None) -> str:
    """Compile a Module to assembly.

    Convenience function that creates a Compiler and compiles the module.

    Args:
        module: A Module containing type definitions, data, and functions
        target: Target architecture (e.g., 'amd64_sysv', 'arm64').
                If None, uses QBE's default for the current platform.

    Returns:
        Generated assembly code as a string

    Raises:
        CompilationError: If compilation fails
    """
    compiler = Compiler(target)
    return compiler.compile_module(module)
