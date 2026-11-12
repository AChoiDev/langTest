"""QBE instruction definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .types import BaseType

if TYPE_CHECKING:
    from .values import Label, Temporary, Value


@dataclass
class Instruction:
    """Base class for all instructions."""

    def emit(self) -> str:
        """Emit this instruction as QBE IL."""
        raise NotImplementedError


@dataclass
class BinaryOp(Instruction):
    """Binary arithmetic/logic operation.

    Operations: add, sub, mul, div, rem, udiv, urem,
                and, or, xor, sar, shr, shl
    """

    op: str
    result: Temporary
    result_type: BaseType
    left: Value
    right: Value

    def emit(self) -> str:
        return f"{self.result} ={self.result_type.value} {self.op} {self.left}, {self.right}"


@dataclass
class UnaryOp(Instruction):
    """Unary operation (neg)."""

    op: str
    result: Temporary
    result_type: BaseType
    operand: Value

    def emit(self) -> str:
        return f"{self.result} ={self.result_type.value} {self.op} {self.operand}"


@dataclass
class Copy(Instruction):
    """Copy operation."""

    result: Temporary
    result_type: BaseType
    value: Value

    def emit(self) -> str:
        return f"{self.result} ={self.result_type.value} copy {self.value}"


@dataclass
class Load(Instruction):
    """Memory load operation.

    Load types: load, loadsb, loadub, loadsh, loaduh, loadsw, loaduw
    """

    result: Temporary
    result_type: BaseType
    address: Value
    load_type: str = "load"

    def emit(self) -> str:
        return (
            f"{self.result} ={self.result_type.value} {self.load_type} {self.address}"
        )


@dataclass
class Store(Instruction):
    """Memory store operation.

    Store types: storeb, storeh, storew, storel, stores, stored
    """

    store_type: str
    value: Value
    address: Value

    def emit(self) -> str:
        return f"{self.store_type} {self.value}, {self.address}"


@dataclass
class Blit(Instruction):
    """Memory copy (blit) operation."""

    src: Value
    dst: Value
    size: int

    def emit(self) -> str:
        return f"blit {self.src}, {self.dst}, {self.size}"


@dataclass
class Alloc(Instruction):
    """Stack allocation.

    Alignment can be 4, 8, or 16 bytes.
    """

    result: Temporary
    size: Value
    align: int = 8

    def emit(self) -> str:
        alloc_op = f"alloc{self.align}"
        return f"{self.result} =l {alloc_op} {self.size}"


@dataclass
class Comparison(Instruction):
    """Comparison operation.

    Integer comparisons: ceqw, cnew, csltw, csgtw, cslew, csgew,
                        cultw, cugtw, culew, cugew
                        (and 'l' variants for 64-bit)
    Float comparisons: ceqs, cges, cgts, cles, clts, cnes, cos, cuos
                      (and 'd' variants for double)
    """

    op: str
    result: Temporary
    result_type: BaseType
    left: Value
    right: Value

    def emit(self) -> str:
        return f"{self.result} ={self.result_type.value} {self.op} {self.left}, {self.right}"


@dataclass
class Conversion(Instruction):
    """Type conversion operation.

    Operations: extsb, extub, extsh, extuh, extsw, extuw,
               exts, truncd, stosi, stoui, dtosi, dtoui,
               swtof, uwtof, sltof, ultof, cast
    """

    op: str
    result: Temporary
    result_type: BaseType
    operand: Value

    def emit(self) -> str:
        return f"{self.result} ={self.result_type.value} {self.op} {self.operand}"


@dataclass
class Call(Instruction):
    """Function call.

    Args are tuples of (type, value).
    """

    target: Value
    args: list[tuple[BaseType | str, Value]]
    result: Temporary | None = None
    result_type: BaseType | str | None = None
    is_variadic: bool = False

    def emit(self) -> str:
        # Format arguments
        arg_strs = []
        for arg_type, arg_val in self.args:
            if isinstance(arg_type, BaseType):
                type_str = arg_type.value
            else:
                type_str = f":{arg_type}"
            arg_strs.append(f"{type_str} {arg_val}")

        if self.is_variadic:
            arg_strs.append("...")

        args_str = ", ".join(arg_strs)

        if self.result:
            if isinstance(self.result_type, BaseType):
                type_str = self.result_type.value
            else:
                type_str = f":{self.result_type}"
            return f"{self.result} ={type_str} call {self.target}({args_str})"
        return f"call {self.target}({args_str})"


@dataclass
class Phi(Instruction):
    """Phi instruction for SSA form.

    Incoming is a list of (Label, Value) pairs.
    """

    result: Temporary
    result_type: BaseType
    incoming: list[tuple[Label, Value]]

    def emit(self) -> str:
        pairs = ", ".join(f"{label} {value}" for label, value in self.incoming)
        return f"{self.result} ={self.result_type.value} phi {pairs}"


@dataclass
class VaStart(Instruction):
    """Initialize variadic argument list."""

    va_list: Value

    def emit(self) -> str:
        return f"vastart {self.va_list}"


@dataclass
class VaArg(Instruction):
    """Fetch next variadic argument."""

    result: Temporary
    result_type: BaseType
    va_list: Value

    def emit(self) -> str:
        return f"{self.result} ={self.result_type.value} vaarg {self.va_list}"
