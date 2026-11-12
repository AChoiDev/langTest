"""Unit tests for type definitions."""

from __future__ import annotations

import pytest

from qbepy import BaseType, D, L, S, W
from qbepy.ir import AggregateType, ExtType


@pytest.mark.unit
class TestBaseTypes:
    """Tests for base type values."""

    def test_word_type_value(self):
        """Test word type has correct value."""
        assert W.value == "w"

    def test_long_type_value(self):
        """Test long type has correct value."""
        assert L.value == "l"

    def test_single_type_value(self):
        """Test single type has correct value."""
        assert S.value == "s"

    def test_double_type_value(self):
        """Test double type has correct value."""
        assert D.value == "d"

    def test_base_type_enum_word(self):
        """Test BaseType enum WORD alias."""
        assert BaseType.WORD == W

    def test_base_type_enum_long(self):
        """Test BaseType enum LONG alias."""
        assert BaseType.LONG == L

    def test_base_type_enum_single(self):
        """Test BaseType enum SINGLE alias."""
        assert BaseType.SINGLE == S

    def test_base_type_enum_double(self):
        """Test BaseType enum DOUBLE alias."""
        assert BaseType.DOUBLE == D


@pytest.mark.unit
class TestAggregateType:
    """Tests for aggregate (struct) types."""

    def test_simple_aggregate_emits_type_keyword(self):
        """Test that aggregate type emits 'type' keyword."""
        point = AggregateType("point", [(ExtType.WORD, 1), (ExtType.WORD, 1)])
        il = point.emit()
        assert "type :point" in il

    def test_simple_aggregate_emits_field_types(self):
        """Test that aggregate type emits field types."""
        point = AggregateType("point", [(ExtType.WORD, 1), (ExtType.WORD, 1)])
        il = point.emit()
        assert "w" in il

    def test_aggregate_with_alignment(self):
        """Test aggregate type with explicit alignment."""
        vec = AggregateType("vec", [(ExtType.DOUBLE, 4)], align=16)
        il = vec.emit()
        assert "align 16" in il

    def test_opaque_aggregate_emits_size(self):
        """Test opaque aggregate type emits size."""
        opaque = AggregateType("opaque", is_opaque=True, opaque_size=24)
        il = opaque.emit()
        assert ":opaque" in il
        assert "24" in il
