"""QBE value types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Temporary:
    """Function-scope temporary variable (%name)."""

    name: str

    def __str__(self) -> str:
        return f"%{self.name}"


@dataclass(frozen=True)
class Global:
    """Global symbol ($name)."""

    name: str

    def __str__(self) -> str:
        return f"${self.name}"


@dataclass(frozen=True)
class Label:
    """Block label (@name)."""

    name: str

    def __str__(self) -> str:
        return f"@{self.name}"


@dataclass(frozen=True)
class IntConst:
    """Integer constant."""

    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class FloatConst:
    """Floating-point constant.

    QBE uses special syntax for floats:
      s_<float> for single precision
      d_<double> for double precision
    """

    value: float
    is_single: bool = False

    def __str__(self) -> str:
        prefix = "s_" if self.is_single else "d_"
        return f"{prefix}{self.value}"


@dataclass(frozen=True)
class TypeRef:
    """Reference to an aggregate type (:typename)."""

    name: str

    def __str__(self) -> str:
        return f":{self.name}"


# Type alias for any value that can be used as an operand
Value = Temporary | Global | IntConst | FloatConst | TypeRef
