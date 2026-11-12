"""Unit tests for instruction types."""

from __future__ import annotations

import pytest

from qbepy import L, W
from qbepy.ir import (
    Alloc,
    BinaryOp,
    Call,
    Comparison,
    Conversion,
    Copy,
    Global,
    IntConst,
    Label,
    Load,
    Phi,
    Store,
    Temporary,
    UnaryOp,
)


@pytest.mark.unit
class TestBinaryOp:
    """Tests for binary operation instructions."""

    def test_add_two_temporaries(self):
        """Test add instruction with two temporaries."""
        ins = BinaryOp("add", Temporary("r"), W, Temporary("a"), Temporary("b"))
        assert ins.emit() == "%r =w add %a, %b"

    def test_mul_with_constant(self):
        """Test multiply instruction with constant operand."""
        ins = BinaryOp("mul", Temporary("r"), W, Temporary("x"), IntConst(2))
        assert ins.emit() == "%r =w mul %x, 2"

    def test_sub_instruction(self):
        """Test subtract instruction."""
        ins = BinaryOp("sub", Temporary("r"), W, Temporary("a"), Temporary("b"))
        assert "sub" in ins.emit()


@pytest.mark.unit
class TestUnaryOp:
    """Tests for unary operation instructions."""

    def test_neg_instruction(self):
        """Test negation instruction."""
        ins = UnaryOp("neg", Temporary("r"), W, Temporary("x"))
        assert ins.emit() == "%r =w neg %x"


@pytest.mark.unit
class TestCopy:
    """Tests for copy instructions."""

    def test_copy_constant(self):
        """Test copying a constant to a temporary."""
        ins = Copy(Temporary("r"), W, IntConst(42))
        assert ins.emit() == "%r =w copy 42"

    def test_copy_temporary(self):
        """Test copying a temporary to another."""
        ins = Copy(Temporary("dst"), W, Temporary("src"))
        assert "copy" in ins.emit()
        assert "%dst" in ins.emit()
        assert "%src" in ins.emit()


@pytest.mark.unit
class TestLoad:
    """Tests for load instructions."""

    def test_load_word(self):
        """Test loading a word from memory."""
        ins = Load(Temporary("v"), W, Temporary("ptr"))
        assert ins.emit() == "%v =w load %ptr"

    def test_load_signed_byte(self):
        """Test loading with sign extension."""
        ins = Load(Temporary("v"), W, Temporary("ptr"), load_type="loadsb")
        assert "loadsb" in ins.emit()

    def test_load_unsigned_half(self):
        """Test loading unsigned halfword."""
        ins = Load(Temporary("v"), W, Temporary("ptr"), load_type="loaduh")
        assert "loaduh" in ins.emit()


@pytest.mark.unit
class TestStore:
    """Tests for store instructions."""

    def test_store_word(self):
        """Test storing a word to memory."""
        ins = Store("storew", Temporary("v"), Temporary("ptr"))
        assert ins.emit() == "storew %v, %ptr"

    def test_store_byte(self):
        """Test storing a byte to memory."""
        ins = Store("storeb", Temporary("v"), Temporary("ptr"))
        assert "storeb" in ins.emit()


@pytest.mark.unit
class TestAlloc:
    """Tests for stack allocation instructions."""

    def test_alloc_with_alignment(self):
        """Test stack allocation with alignment."""
        ins = Alloc(Temporary("ptr"), IntConst(16), align=8)
        assert ins.emit() == "%ptr =l alloc8 16"

    def test_alloc_default_alignment(self):
        """Test stack allocation with default alignment."""
        ins = Alloc(Temporary("ptr"), IntConst(32), align=4)
        assert "alloc4" in ins.emit()


@pytest.mark.unit
class TestComparison:
    """Tests for comparison instructions."""

    def test_equality_comparison(self):
        """Test equality comparison."""
        ins = Comparison("ceqw", Temporary("c"), W, Temporary("a"), Temporary("b"))
        assert ins.emit() == "%c =w ceqw %a, %b"

    def test_less_than_comparison(self):
        """Test signed less-than comparison."""
        ins = Comparison("csltw", Temporary("c"), W, Temporary("a"), Temporary("b"))
        assert "csltw" in ins.emit()


@pytest.mark.unit
class TestConversion:
    """Tests for type conversion instructions."""

    def test_sign_extend_word_to_long(self):
        """Test sign extension from word to long."""
        ins = Conversion("extsw", Temporary("r"), L, Temporary("x"))
        assert ins.emit() == "%r =l extsw %x"

    def test_truncate(self):
        """Test truncation."""
        ins = Conversion("truncw", Temporary("r"), W, Temporary("x"))
        assert "truncw" in ins.emit()


@pytest.mark.unit
class TestCall:
    """Tests for function call instructions."""

    def test_void_call(self):
        """Test void function call."""
        ins = Call(Global("puts"), [(L, Global("str"))])
        assert ins.emit() == "call $puts(l $str)"

    def test_call_with_return_value(self):
        """Test function call with return value."""
        ins = Call(
            Global("add"),
            [(W, Temporary("a")), (W, Temporary("b"))],
            result=Temporary("r"),
            result_type=W,
        )
        assert ins.emit() == "%r =w call $add(w %a, w %b)"

    def test_call_no_arguments(self):
        """Test function call with no arguments."""
        ins = Call(Global("getpid"), [], result=Temporary("pid"), result_type=W)
        assert "$getpid()" in ins.emit()


@pytest.mark.unit
class TestPhi:
    """Tests for phi node instructions."""

    def test_phi_two_predecessors(self):
        """Test phi node with two predecessors."""
        ins = Phi(
            Temporary("x"),
            W,
            [
                (Label("a"), IntConst(1)),
                (Label("b"), IntConst(2)),
            ],
        )
        assert ins.emit() == "%x =w phi @a 1, @b 2"

    def test_phi_with_temporaries(self):
        """Test phi node with temporary values."""
        ins = Phi(
            Temporary("result"),
            W,
            [
                (Label("then"), Temporary("x")),
                (Label("else"), Temporary("y")),
            ],
        )
        il = ins.emit()
        assert "phi" in il
        assert "@then" in il
        assert "@else" in il
