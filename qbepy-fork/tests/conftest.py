"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from qbepy import Compiler


# Pytest markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (uses FFI)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full workflows)")


@pytest.fixture
def compiler() -> Compiler:
    """Return a Compiler instance with default target."""
    return Compiler()


@pytest.fixture
def simple_il() -> str:
    """Return a simple IL program that returns 42."""
    return """
export function w $test() {
@start
    ret 42
}
"""


@pytest.fixture
def add_function_il() -> str:
    """Return an IL program with an add function."""
    return """
export function w $add(w %a, w %b) {
@start
    %r =w add %a, %b
    ret %r
}
"""
