"""End-to-end tests for target selection and cross-compilation."""

from __future__ import annotations

import pytest

from qbepy import Compiler, compile_il


@pytest.mark.e2e
class TestAllTargets:
    """Tests that verify all targets produce valid output."""

    @pytest.mark.parametrize("target", Compiler.TARGETS)
    def test_target_produces_output(self, target):
        """Test that each target produces non-empty output."""
        il = """
export function w $test() {
@start
    ret 0
}
"""
        asm = compile_il(il, target=target)
        assert asm is not None
        assert len(asm) > 0

    @pytest.mark.parametrize("target", Compiler.TARGETS)
    def test_target_produces_text_section(self, target):
        """Test that each target produces .text section."""
        il = """
export function w $test() {
@start
    ret 0
}
"""
        asm = compile_il(il, target=target)
        assert ".text" in asm


@pytest.mark.e2e
class TestAMD64Targets:
    """Tests for x86-64 targets."""

    def test_amd64_sysv_no_underscore_prefix(self):
        """Test that amd64_sysv doesn't use underscore prefix."""
        il = """
export function w $test() {
@start
    ret 42
}
"""
        asm = compile_il(il, target="amd64_sysv")
        # System V doesn't use underscore prefix
        assert "test:" in asm or ".globl test" in asm

    def test_amd64_apple_uses_underscore_prefix(self):
        """Test that amd64_apple uses underscore prefix."""
        il = """
export function w $test() {
@start
    ret 42
}
"""
        asm = compile_il(il, target="amd64_apple")
        assert "_test" in asm


@pytest.mark.e2e
class TestARM64Targets:
    """Tests for ARM64 targets."""

    def test_arm64_no_underscore_prefix(self):
        """Test that arm64 doesn't use underscore prefix."""
        il = """
export function w $test() {
@start
    ret 42
}
"""
        asm = compile_il(il, target="arm64")
        assert "test:" in asm or ".globl test" in asm

    def test_arm64_apple_uses_underscore_prefix(self):
        """Test that arm64_apple uses underscore prefix."""
        il = """
export function w $test() {
@start
    ret 42
}
"""
        asm = compile_il(il, target="arm64_apple")
        assert "_test" in asm


@pytest.mark.e2e
class TestRV64Target:
    """Tests for RISC-V 64-bit target."""

    def test_rv64_produces_valid_output(self):
        """Test that rv64 produces valid assembly."""
        il = """
export function w $test() {
@start
    ret 42
}
"""
        asm = compile_il(il, target="rv64")
        assert ".text" in asm
        assert "test" in asm


@pytest.mark.e2e
class TestCrossCompilation:
    """Tests for cross-compilation scenarios."""

    def test_same_il_different_targets_produce_different_output(self):
        """Test that same IL produces different assembly for different targets."""
        il = """
export function w $add(w %a, w %b) {
@start
    %r =w add %a, %b
    ret %r
}
"""
        asm_amd64 = compile_il(il, target="amd64_sysv")
        asm_arm64 = compile_il(il, target="arm64")
        asm_rv64 = compile_il(il, target="rv64")

        # All should be different
        assert asm_amd64 != asm_arm64
        assert asm_arm64 != asm_rv64
        assert asm_amd64 != asm_rv64

    def test_apple_vs_sysv_abi_differ(self):
        """Test that Apple and System V ABIs produce different output."""
        il = """
export function w $func() {
@start
    ret 0
}
"""
        asm_sysv = compile_il(il, target="amd64_sysv")
        asm_apple = compile_il(il, target="amd64_apple")

        # Apple should have underscore prefix, System V should not
        assert "func:" in asm_sysv or ".globl func" in asm_sysv
        assert "_func" in asm_apple


@pytest.mark.e2e
class TestTargetConsistency:
    """Tests for target setting consistency."""

    def test_target_persists_across_compiles(self):
        """Test that target setting persists across multiple compiles."""
        compiler = Compiler(target="amd64_sysv")

        il = """
export function w $test() {
@start
    ret 0
}
"""
        asm1 = compiler.compile(il)
        asm2 = compiler.compile(il)

        assert asm1 == asm2

    def test_changing_target_changes_output(self):
        """Test that changing target changes output."""
        compiler = Compiler(target="amd64_sysv")

        il = """
export function w $test() {
@start
    ret 0
}
"""
        asm_amd64 = compiler.compile(il)

        compiler.set_target("arm64")
        asm_arm64 = compiler.compile(il)

        assert asm_amd64 != asm_arm64

    def test_default_target_matches_explicit_setting(self):
        """Test that default compilation matches explicitly setting default target."""
        compiler_default = Compiler()
        default_target = compiler_default.get_default_target()

        il = """
export function w $test() {
@start
    ret 0
}
"""
        asm_default = compiler_default.compile(il)

        compiler_explicit = Compiler(target=default_target)
        asm_explicit = compiler_explicit.compile(il)

        assert asm_default == asm_explicit
