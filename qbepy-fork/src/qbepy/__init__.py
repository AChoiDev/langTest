"""QBE Python Bindings - Compile QBE IL to assembly.

This package provides Python bindings for QBE (Quite Bare Engine), a minimalist
compiler backend. It includes:

1. A Compiler class that uses FFI to compile IL to assembly
2. An IR builder module for constructing QBE IL programmatically

Example usage:

    # Raw IL compilation
    import qbepy

    il = '''
    data $str = { b "hello", b 0 }
    export function w $main() {
    @start
        %r =w call $puts(l $str)
        ret 0
    }
    '''
    asm = qbepy.compile_il(il)

    # Using the IR builder
    from qbepy import Module, Function, DataDef, W, L
    from qbepy.ir import Call, Return, Global, Temporary, IntConst

    mod = Module()
    mod.add_data(DataDef("str").add_string("hello").add_bytes(0))

    func = Function("main", W, export=True)
    block = func.add_block("start")
    block.instructions.append(
        Call(Global("puts"), [(L, Global("str"))], Temporary("r"), W)
    )
    block.terminator = Return(IntConst(0))
    mod.add_function(func)

    asm = qbepy.compile_module(mod)
"""

from __future__ import annotations

from .compiler import Compiler, compile_il, compile_module
from .errors import CompilationError, QBEPyError
from .ir import (
    AggregateType,
    BaseType,
    Block,
    D,
    DataDef,
    ExtType,
    Function,
    L,
    Module,
    S,
    SubWordType,
    W,
)

__all__ = [
    "AggregateType",
    # Types
    "BaseType",
    "Block",
    "CompilationError",
    # Compiler
    "Compiler",
    "D",
    "DataDef",
    "ExtType",
    "Function",
    "L",
    # IR building
    "Module",
    "QBEPyError",
    "S",
    "SubWordType",
    "W",
    # Convenience functions
    "compile_il",
    "compile_module",
]
