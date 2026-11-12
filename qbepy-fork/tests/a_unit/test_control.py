"""Unit tests for control flow instructions."""

from __future__ import annotations

import pytest

from qbepy.ir import Branch, Halt, IntConst, Jump, Label, Return, Temporary


@pytest.mark.unit
class TestJump:
    """Tests for unconditional jump terminator."""

    def test_jump_emits_jmp_keyword(self):
        """Test that jump emits 'jmp' keyword."""
        jmp = Jump(Label("next"))
        assert jmp.emit() == "jmp @next"

    def test_jump_includes_target_label(self):
        """Test that jump includes target label."""
        jmp = Jump(Label("loop_start"))
        assert "@loop_start" in jmp.emit()


@pytest.mark.unit
class TestBranch:
    """Tests for conditional branch terminator."""

    def test_branch_emits_jnz_keyword(self):
        """Test that branch emits 'jnz' keyword."""
        br = Branch(Temporary("c"), Label("then"), Label("else"))
        assert "jnz" in br.emit()

    def test_branch_includes_condition(self):
        """Test that branch includes condition operand."""
        br = Branch(Temporary("cond"), Label("then"), Label("else"))
        assert "%cond" in br.emit()

    def test_branch_includes_both_targets(self):
        """Test that branch includes both target labels."""
        br = Branch(Temporary("c"), Label("true_branch"), Label("false_branch"))
        il = br.emit()
        assert "@true_branch" in il
        assert "@false_branch" in il

    def test_branch_format(self):
        """Test exact branch format."""
        br = Branch(Temporary("c"), Label("then"), Label("else"))
        assert br.emit() == "jnz %c, @then, @else"


@pytest.mark.unit
class TestReturn:
    """Tests for return terminator."""

    def test_void_return(self):
        """Test void return (no value)."""
        ret = Return()
        assert ret.emit() == "ret"

    def test_return_with_temporary(self):
        """Test return with temporary value."""
        ret = Return(Temporary("r"))
        assert ret.emit() == "ret %r"

    def test_return_with_constant(self):
        """Test return with constant value."""
        ret = Return(IntConst(0))
        assert ret.emit() == "ret 0"

    def test_return_with_negative_constant(self):
        """Test return with negative constant."""
        ret = Return(IntConst(-1))
        assert ret.emit() == "ret -1"


@pytest.mark.unit
class TestHalt:
    """Tests for halt (unreachable) terminator."""

    def test_halt_emits_hlt_keyword(self):
        """Test that halt emits 'hlt' keyword."""
        hlt = Halt()
        assert hlt.emit() == "hlt"
