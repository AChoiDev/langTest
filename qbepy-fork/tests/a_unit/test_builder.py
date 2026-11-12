"""Unit tests for IR builder classes (Block, Function, DataDef, Module)."""

from __future__ import annotations

import pytest

from qbepy import Block, DataDef, Function, Module, W
from qbepy.ir import (
    AggregateType,
    BinaryOp,
    ExtType,
    IntConst,
    Label,
    Return,
    Temporary,
)


@pytest.mark.unit
class TestBlock:
    """Tests for Block class."""

    def test_block_stores_name(self):
        """Test that block stores its name."""
        block = Block("start")
        assert block.name == "start"

    def test_block_creates_label(self):
        """Test that block creates corresponding label."""
        block = Block("start")
        assert block.label == Label("start")

    def test_block_emit_includes_label(self):
        """Test that emitted block includes label."""
        block = Block("entry")
        block.terminator = Return(IntConst(0))
        il = block.emit()
        assert "@entry" in il

    def test_block_emit_includes_terminator(self):
        """Test that emitted block includes terminator."""
        block = Block("start")
        block.terminator = Return(IntConst(42))
        il = block.emit()
        assert "ret 42" in il

    def test_block_emit_includes_instructions(self):
        """Test that emitted block includes instructions."""
        block = Block("start")
        block.instructions.append(
            BinaryOp("add", Temporary("r"), W, Temporary("a"), Temporary("b"))
        )
        block.terminator = Return(Temporary("r"))
        il = block.emit()
        assert "%r =w add" in il
        assert "ret %r" in il


@pytest.mark.unit
class TestFunction:
    """Tests for Function class."""

    def test_function_stores_name(self):
        """Test that function stores its name."""
        func = Function("test", W)
        assert func.name == "test"

    def test_function_stores_return_type(self):
        """Test that function stores return type."""
        func = Function("test", W)
        assert func.return_type == W

    def test_function_stores_params(self):
        """Test that function stores parameters."""
        func = Function("add", W, params=[(W, "a"), (W, "b")])
        assert len(func.params) == 2

    def test_function_export_in_emit(self):
        """Test that exported function emits 'export' keyword."""
        func = Function("main", W, export=True)
        il = func.emit()
        assert "export" in il

    def test_function_non_export_omits_keyword(self):
        """Test that non-exported function omits 'export' keyword."""
        func = Function("helper", W, export=False)
        il = func.emit()
        assert "export" not in il

    def test_new_temp_creates_unique_names(self):
        """Test that new_temp creates unique temporary names."""
        func = Function("test", W)
        t1 = func.new_temp("x")
        t2 = func.new_temp("x")
        assert str(t1) != str(t2)

    def test_add_block_creates_block(self):
        """Test that add_block creates and returns a block."""
        func = Function("test", W)
        block = func.add_block("start")
        assert block.name == "start"

    def test_add_block_adds_to_function(self):
        """Test that add_block adds block to function."""
        func = Function("test", W)
        func.add_block("start")
        assert len(func.blocks) == 1

    def test_function_emit_includes_signature(self):
        """Test that emitted function includes signature."""
        func = Function("add", W, params=[(W, "a"), (W, "b")], export=True)
        il = func.emit()
        assert "function w $add" in il
        assert "w %a" in il
        assert "w %b" in il


@pytest.mark.unit
class TestDataDef:
    """Tests for DataDef class."""

    def test_data_def_stores_name(self):
        """Test that data definition stores its name."""
        data = DataDef("msg")
        assert data.name == "msg"

    def test_add_bytes_emits_b_directive(self):
        """Test that add_bytes emits 'b' directive."""
        data = DataDef("bytes").add_bytes(1, 2, 3)
        il = data.emit()
        assert "b 1 2 3" in il

    def test_add_string_emits_quoted_string(self):
        """Test that add_string emits quoted string."""
        data = DataDef("str").add_string("hello")
        il = data.emit()
        assert '"hello"' in il

    def test_add_zero_emits_z_directive(self):
        """Test that add_zero emits 'z' directive."""
        data = DataDef("buf").add_zero(16)
        il = data.emit()
        assert "z 16" in il

    def test_export_emits_keyword(self):
        """Test that exported data emits 'export' keyword."""
        data = DataDef("msg", export=True).add_string("test")
        il = data.emit()
        assert "export" in il

    def test_alignment_emits_align_directive(self):
        """Test that alignment emits 'align' directive."""
        data = DataDef("aligned", align=16).add_words(1, 2, 3, 4)
        il = data.emit()
        assert "align 16" in il

    def test_fluent_api_chaining(self):
        """Test that DataDef methods can be chained."""
        data = DataDef("msg").add_string("hello").add_bytes(0)
        il = data.emit()
        assert '"hello"' in il
        assert "b 0" in il


@pytest.mark.unit
class TestModule:
    """Tests for Module class."""

    def test_module_starts_empty(self):
        """Test that new module has no functions."""
        mod = Module()
        assert len(mod.functions) == 0

    def test_add_function_increases_count(self):
        """Test that add_function increases function count."""
        mod = Module()
        func = Function("test", W)
        mod.add_function(func)
        assert len(mod.functions) == 1

    def test_add_data_increases_count(self):
        """Test that add_data increases data count."""
        mod = Module()
        data = DataDef("msg").add_string("hello")
        mod.add_data(data)
        assert len(mod.data) == 1

    def test_add_type_increases_count(self):
        """Test that add_type increases type count."""
        mod = Module()
        typ = AggregateType("point", [(ExtType.WORD, 2)])
        mod.add_type(typ)
        assert len(mod.types) == 1

    def test_module_emit_includes_data(self):
        """Test that emitted module includes data definitions."""
        mod = Module()
        mod.add_data(DataDef("str").add_string("hello").add_bytes(0))
        il = mod.emit()
        assert "data $str" in il

    def test_module_emit_includes_functions(self):
        """Test that emitted module includes functions."""
        mod = Module()
        func = Function("main", W, export=True)
        block = func.add_block("start")
        block.terminator = Return(IntConst(0))
        mod.add_function(func)
        il = mod.emit()
        assert "function w $main" in il

    def test_fluent_api_chaining(self):
        """Test that Module methods can be chained."""
        mod = (
            Module().add_data(DataDef("x").add_words(42)).add_function(Function("f", W))
        )
        assert len(mod.data) == 1
        assert len(mod.functions) == 1
