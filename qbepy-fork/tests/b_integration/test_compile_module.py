"""Integration tests for compile_module function."""

from __future__ import annotations

import pytest

from qbepy import DataDef, Function, L, Module, W, compile_module
from qbepy.ir import Call, Global, IntConst, Return


@pytest.mark.integration
class TestCompileModule:
    """Tests for compile_module function."""

    def test_compile_simple_module(self):
        """Test compiling a simple module."""
        mod = Module()
        func = Function("test", W, export=True)
        block = func.add_block("start")
        block.terminator = Return(IntConst(42))
        mod.add_function(func)

        asm = compile_module(mod)
        assert ".text" in asm
        assert "test" in asm

    def test_compile_module_with_data(self):
        """Test compiling module with data section."""
        mod = Module()
        mod.add_data(DataDef("msg").add_string("hello").add_bytes(0))

        func = Function("main", W, export=True)
        block = func.add_block("start")
        r = func.new_temp()
        block.instructions.append(Call(Global("puts"), [(L, Global("msg"))], r, W))
        block.terminator = Return(IntConst(0))
        mod.add_function(func)

        asm = compile_module(mod)
        assert "msg" in asm
        assert "main" in asm

    def test_compile_module_with_explicit_target(self):
        """Test compiling module with specific target."""
        mod = Module()
        func = Function("test", W, export=True)
        block = func.add_block("start")
        block.terminator = Return(IntConst(0))
        mod.add_function(func)

        asm = compile_module(mod, target="amd64_sysv")
        assert asm is not None

    def test_compile_module_multiple_functions(self):
        """Test compiling module with multiple functions."""
        mod = Module()

        func1 = Function("helper", W, export=False)
        block1 = func1.add_block("start")
        block1.terminator = Return(IntConst(1))
        mod.add_function(func1)

        func2 = Function("main", W, export=True)
        block2 = func2.add_block("start")
        block2.terminator = Return(IntConst(0))
        mod.add_function(func2)

        asm = compile_module(mod)
        assert "helper" in asm
        assert "main" in asm

    def test_compile_module_with_multiple_data(self):
        """Test compiling module with multiple data definitions."""
        mod = Module()
        mod.add_data(DataDef("str1").add_string("first").add_bytes(0))
        mod.add_data(DataDef("str2").add_string("second").add_bytes(0))

        func = Function("main", W, export=True)
        block = func.add_block("start")
        block.terminator = Return(IntConst(0))
        mod.add_function(func)

        asm = compile_module(mod)
        assert "str1" in asm
        assert "str2" in asm
