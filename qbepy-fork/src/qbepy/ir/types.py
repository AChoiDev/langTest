"""QBE type definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BaseType(Enum):
    """Base types for temporaries and function returns."""

    WORD = "w"  # 32-bit integer
    LONG = "l"  # 64-bit integer
    SINGLE = "s"  # 32-bit float
    DOUBLE = "d"  # 64-bit float


class ExtType(Enum):
    """Extended types for data and aggregate fields."""

    BYTE = "b"  # 8-bit
    HALF = "h"  # 16-bit halfword
    WORD = "w"  # 32-bit word
    LONG = "l"  # 64-bit long
    SINGLE = "s"  # 32-bit float
    DOUBLE = "d"  # 64-bit float


class SubWordType(Enum):
    """Sub-word types for ABI compatibility."""

    SIGNED_BYTE = "sb"
    UNSIGNED_BYTE = "ub"
    SIGNED_HALF = "sh"
    UNSIGNED_HALF = "uh"


# Convenience aliases
W = BaseType.WORD
L = BaseType.LONG
S = BaseType.SINGLE
D = BaseType.DOUBLE


@dataclass
class AggregateType:
    """User-defined aggregate type (struct/union).

    Example:
        # type :point = { w, w }
        point = AggregateType("point", [(ExtType.WORD, 1), (ExtType.WORD, 1)])

        # type :vec = align 16 { d 4 }
        vec = AggregateType("vec", [(ExtType.DOUBLE, 4)], align=16)
    """

    name: str
    fields: list[tuple[ExtType | str, int]] = field(default_factory=list)
    align: int | None = None
    is_opaque: bool = False
    opaque_size: int | None = None

    def emit(self) -> str:
        """Emit this type definition as QBE IL."""
        align_str = f"align {self.align} " if self.align else ""

        if self.is_opaque:
            return f"type :{self.name} = {align_str}{{ {self.opaque_size} }}"

        parts = []
        for field_type, count in self.fields:
            if isinstance(field_type, ExtType):
                type_str = field_type.value
            else:
                # Nested aggregate type reference
                type_str = f":{field_type}"

            if count > 1:
                parts.append(f"{type_str} {count}")
            else:
                parts.append(type_str)

        fields_str = ", ".join(parts)
        return f"type :{self.name} = {align_str}{{ {fields_str} }}"
