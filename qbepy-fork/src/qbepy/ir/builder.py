"""QBE IR builder classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .types import AggregateType, BaseType
from .values import Global, Label, Temporary

if TYPE_CHECKING:
    from .control import Terminator
    from .instructions import Instruction, Phi


@dataclass
class Block:
    """A basic block in a function.

    Each block has:
    - A label name
    - Optional phi instructions (for SSA)
    - Regular instructions
    - A terminator (jump, branch, return, or halt)
    """

    name: str
    phis: list[Phi] = field(default_factory=list)
    instructions: list[Instruction] = field(default_factory=list)
    terminator: Terminator | None = None

    @property
    def label(self) -> Label:
        """Get this block's label."""
        return Label(self.name)

    def emit(self) -> str:
        """Emit this block as QBE IL."""
        lines = [f"@{self.name}"]

        for phi in self.phis:
            lines.append(f"\t{phi.emit()}")

        for ins in self.instructions:
            lines.append(f"\t{ins.emit()}")

        if self.terminator:
            lines.append(f"\t{self.terminator.emit()}")

        return "\n".join(lines)


@dataclass
class Function:
    """A function definition.

    Example:
        # export function w $add(w %a, w %b) { ... }
        func = Function("add", BaseType.WORD,
                       params=[(BaseType.WORD, "a"), (BaseType.WORD, "b")],
                       export=True)
    """

    name: str
    return_type: BaseType | str | None = None
    params: list[tuple[BaseType | str, str]] = field(default_factory=list)
    export: bool = False
    vararg: bool = False
    blocks: list[Block] = field(default_factory=list)
    _temp_counter: int = field(default=0, repr=False)

    def new_temp(self, prefix: str = "t") -> Temporary:
        """Create a new unique temporary variable."""
        self._temp_counter += 1
        return Temporary(f"{prefix}.{self._temp_counter}")

    def add_block(self, name: str) -> Block:
        """Add a new basic block to this function."""
        block = Block(name)
        self.blocks.append(block)
        return block

    def emit(self) -> str:
        """Emit this function as QBE IL."""
        lines = []

        if self.export:
            lines.append("export")

        # Return type
        if self.return_type:
            if isinstance(self.return_type, BaseType):
                ret_str = self.return_type.value
            else:
                ret_str = f":{self.return_type}"
        else:
            ret_str = ""

        # Parameters
        param_strs = []
        for param_type, param_name in self.params:
            if isinstance(param_type, BaseType):
                type_str = param_type.value
            else:
                type_str = f":{param_type}"
            param_strs.append(f"{type_str} %{param_name}")

        if self.vararg:
            param_strs.append("...")

        params_str = ", ".join(param_strs)

        lines.append(f"function {ret_str} ${self.name}({params_str}) {{")

        for block in self.blocks:
            lines.append(block.emit())

        lines.append("}")

        return "\n".join(lines)


@dataclass
class DataDef:
    """A data definition.

    Example:
        # data $str = { b "hello world", b 0 }
        data = DataDef("str")
        data.add_string("hello world")
        data.add_bytes(0)
    """

    name: str
    export: bool = False
    align: int | None = None
    section: str | None = None
    items: list = field(default_factory=list)

    def add_bytes(self, *values: int) -> DataDef:
        """Add byte values."""
        self.items.append(("b", list(values)))
        return self

    def add_halfs(self, *values: int) -> DataDef:
        """Add half-word (16-bit) values."""
        self.items.append(("h", list(values)))
        return self

    def add_words(self, *values: int) -> DataDef:
        """Add word (32-bit) values."""
        self.items.append(("w", list(values)))
        return self

    def add_longs(self, *values: int | Global) -> DataDef:
        """Add long (64-bit) values or global references."""
        self.items.append(("l", list(values)))
        return self

    def add_singles(self, *values: float) -> DataDef:
        """Add single-precision float values."""
        formatted = [f"s_{v}" for v in values]
        self.items.append(("s", formatted))
        return self

    def add_doubles(self, *values: float) -> DataDef:
        """Add double-precision float values."""
        formatted = [f"d_{v}" for v in values]
        self.items.append(("d", formatted))
        return self

    def add_string(self, s: str) -> DataDef:
        """Add a string (as bytes). Does NOT add null terminator."""
        # Escape the string for QBE
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        self.items.append(("b", [f'"{escaped}"']))
        return self

    def add_zero(self, count: int) -> DataDef:
        """Add zero-initialized padding."""
        self.items.append(("z", count))
        return self

    def add_ref(self, name: str, offset: int = 0) -> DataDef:
        """Add a reference to another global symbol."""
        if offset:
            self.items.append(("l", [f"${name} + {offset}"]))
        else:
            self.items.append(("l", [f"${name}"]))
        return self

    def emit(self) -> str:
        """Emit this data definition as QBE IL."""
        lines = []

        if self.export:
            lines.append("export")

        if self.section:
            lines.append(f'section "{self.section}"')

        align_str = f"align {self.align} " if self.align else ""
        lines.append(f"data ${self.name} = {align_str}{{")

        for item in self.items:
            if item[0] == "z":
                lines.append(f"\tz {item[1]}")
            else:
                type_char, values = item
                vals_str = " ".join(str(v) for v in values)
                # Handle empty values (shouldn't happen but be safe)
                if vals_str:
                    lines.append(f"\t{type_char} {vals_str},")

        lines.append("}")

        return "\n".join(lines)


@dataclass
class Module:
    """A complete QBE IL module.

    Contains type definitions, data definitions, and functions.
    """

    types: list[AggregateType] = field(default_factory=list)
    data: list[DataDef] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)

    def add_type(self, type_def: AggregateType) -> Module:
        """Add a type definition."""
        self.types.append(type_def)
        return self

    def add_data(self, data_def: DataDef) -> Module:
        """Add a data definition."""
        self.data.append(data_def)
        return self

    def add_function(self, func: Function) -> Module:
        """Add a function definition."""
        self.functions.append(func)
        return self

    def emit(self) -> str:
        """Emit this module as QBE IL."""
        parts = []

        for t in self.types:
            parts.append(t.emit())

        for d in self.data:
            parts.append(d.emit())

        for f in self.functions:
            parts.append(f.emit())

        return "\n\n".join(parts)
