"""QBE Intermediate Representation builder.

This module provides a Pythonic API for constructing QBE IL programs.
"""

from __future__ import annotations

from .builder import Block, DataDef, Function, Module
from .control import Branch, Halt, Jump, Return, Terminator
from .instructions import (
    Alloc,
    BinaryOp,
    Blit,
    Call,
    Comparison,
    Conversion,
    Copy,
    Instruction,
    Load,
    Phi,
    Store,
    UnaryOp,
    VaArg,
    VaStart,
)
from .types import AggregateType, BaseType, D, ExtType, L, S, SubWordType, W
from .values import FloatConst, Global, IntConst, Label, Temporary, TypeRef, Value

__all__ = [
    "AggregateType",
    "Alloc",
    # Types
    "BaseType",
    "BinaryOp",
    "Blit",
    # Builders
    "Block",
    "Branch",
    "Call",
    "Comparison",
    "Conversion",
    "Copy",
    "D",
    "DataDef",
    "ExtType",
    "FloatConst",
    "Function",
    "Global",
    "Halt",
    # Instructions
    "Instruction",
    "IntConst",
    "Jump",
    "L",
    "Label",
    "Load",
    "Module",
    "Phi",
    "Return",
    "S",
    "Store",
    "SubWordType",
    # Values
    "Temporary",
    # Control flow
    "Terminator",
    "TypeRef",
    "UnaryOp",
    "VaArg",
    "VaStart",
    "Value",
    "W",
]
