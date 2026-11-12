"""Unit tests for value types."""

from __future__ import annotations

import math

import pytest

from qbepy.ir import FloatConst, Global, IntConst, Label, Temporary


@pytest.mark.unit
class TestTemporary:
    """Tests for Temporary (SSA register) values."""

    def test_temporary_string_has_percent_prefix(self):
        """Test that temporary string representation has % prefix."""
        t = Temporary("x")
        assert str(t) == "%x"

    def test_temporary_preserves_name(self):
        """Test that temporary preserves its name."""
        t = Temporary("my_var")
        assert "my_var" in str(t)


@pytest.mark.unit
class TestGlobal:
    """Tests for Global (symbol) values."""

    def test_global_string_has_dollar_prefix(self):
        """Test that global string representation has $ prefix."""
        g = Global("main")
        assert str(g) == "$main"

    def test_global_preserves_name(self):
        """Test that global preserves its name."""
        g = Global("my_function")
        assert "my_function" in str(g)


@pytest.mark.unit
class TestLabel:
    """Tests for Label (block reference) values."""

    def test_label_string_has_at_prefix(self):
        """Test that label string representation has @ prefix."""
        label = Label("start")
        assert str(label) == "@start"

    def test_label_preserves_name(self):
        """Test that label preserves its name."""
        label = Label("loop_body")
        assert "loop_body" in str(label)


@pytest.mark.unit
class TestIntConst:
    """Tests for integer constant values."""

    def test_int_const_positive(self):
        """Test positive integer constant."""
        c = IntConst(42)
        assert str(c) == "42"

    def test_int_const_zero(self):
        """Test zero integer constant."""
        c = IntConst(0)
        assert str(c) == "0"

    def test_int_const_negative(self):
        """Test negative integer constant."""
        c = IntConst(-1)
        assert str(c) == "-1"


@pytest.mark.unit
class TestFloatConst:
    """Tests for floating-point constant values."""

    def test_float_const_double_has_d_prefix(self):
        """Test that double constant has d_ prefix."""
        f = FloatConst(math.pi)
        assert str(f).startswith("d_")

    def test_float_const_single_has_s_prefix(self):
        """Test that single constant has s_ prefix."""
        f = FloatConst(math.pi, is_single=True)
        assert str(f).startswith("s_")

    def test_float_const_preserves_value(self):
        """Test that float constant preserves approximate value."""
        f = FloatConst(3.14)
        assert "3.14" in str(f)
