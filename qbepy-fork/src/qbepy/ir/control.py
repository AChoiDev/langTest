"""QBE control flow instructions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .values import Label, Value


@dataclass
class Terminator:
    """Base class for block terminators."""

    def emit(self) -> str:
        """Emit this terminator as QBE IL."""
        raise NotImplementedError


@dataclass
class Jump(Terminator):
    """Unconditional jump."""

    target: Label

    def emit(self) -> str:
        return f"jmp {self.target}"


@dataclass
class Branch(Terminator):
    """Conditional branch (jump if non-zero)."""

    condition: Value
    if_true: Label
    if_false: Label

    def emit(self) -> str:
        return f"jnz {self.condition}, {self.if_true}, {self.if_false}"


@dataclass
class Return(Terminator):
    """Function return."""

    value: Value | None = None

    def emit(self) -> str:
        if self.value is not None:
            return f"ret {self.value}"
        return "ret"


@dataclass
class Halt(Terminator):
    """Program halt (unreachable code marker)."""

    def emit(self) -> str:
        return "hlt"
