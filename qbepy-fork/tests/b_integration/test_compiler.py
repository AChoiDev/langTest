"""Integration tests for the Compiler class and IL compilation."""

from __future__ import annotations

import pytest

from qbepy import CompilationError, Compiler, compile_il


@pytest.mark.integration
class TestCompilerCreation:
    """Tests for Compiler instantiation."""

    def test_compiler_creation_succeeds(self):
        """Test that Compiler can be instantiated."""
        compiler = Compiler()
        assert compiler is not None

    def test_compiler_with_valid_target(self):
        """Test creating Compiler with valid target."""
        compiler = Compiler(target="amd64_sysv")
        assert compiler.target == "amd64_sysv"

    def test_compiler_with_invalid_target_raises(self):
        """Test that invalid target raises ValueError."""
        with pytest.raises(ValueError, match="Unknown target"):
            Compiler(target="invalid_target")


@pytest.mark.integration
class TestCompilerConfiguration:
    """Tests for Compiler configuration methods."""

    def test_set_valid_target(self):
        """Test setting a valid target after creation."""
        compiler = Compiler()
        compiler.set_target("arm64")
        assert compiler.target == "arm64"

    def test_set_invalid_target_raises(self):
        """Test that setting invalid target raises ValueError."""
        compiler = Compiler()
        with pytest.raises(ValueError, match="Unknown target"):
            compiler.set_target("invalid_target")

    def test_get_default_target_returns_valid(self):
        """Test that default target is in valid targets list."""
        compiler = Compiler()
        target = compiler.get_default_target()
        assert target in Compiler.TARGETS

    def test_get_available_targets_returns_list(self):
        """Test that available targets returns a non-empty list."""
        targets = Compiler.get_available_targets()
        assert isinstance(targets, list)
        assert len(targets) > 0

    def test_available_targets_include_common(self):
        """Test that available targets include common architectures."""
        targets = Compiler.get_available_targets()
        assert "amd64_sysv" in targets
        assert "arm64" in targets


@pytest.mark.integration
class TestCompileIL:
    """Tests for compile_il function."""

    def test_compile_simple_function(self, simple_il):
        """Test compiling a simple function."""
        asm = compile_il(simple_il)
        assert asm is not None
        assert len(asm) > 0

    def test_compile_produces_text_section(self, simple_il):
        """Test that compilation produces .text section."""
        asm = compile_il(simple_il)
        assert ".text" in asm

    def test_compile_includes_function_name(self, simple_il):
        """Test that compiled output includes function name."""
        asm = compile_il(simple_il)
        assert "test" in asm

    def test_compile_add_function(self, add_function_il):
        """Test compiling a function with parameters."""
        asm = compile_il(add_function_il)
        assert "add" in asm
        assert ".text" in asm

    def test_compile_with_explicit_target(self, simple_il):
        """Test compiling with explicit target."""
        asm = compile_il(simple_il, target="amd64_sysv")
        assert asm is not None


@pytest.mark.integration
class TestCompilationErrors:
    """Tests for compilation error handling."""

    def test_invalid_il_raises_compilation_error(self):
        """Test that invalid IL raises CompilationError."""
        with pytest.raises(CompilationError):
            compile_il("this is not valid IL")

    def test_syntax_error_raises_compilation_error(self):
        """Test that syntax errors raise CompilationError."""
        bad_il = """
function w $test() {
@start
    ret 42
"""  # Missing closing brace
        with pytest.raises(CompilationError):
            compile_il(bad_il)

    def test_undefined_reference_raises_error(self):
        """Test that undefined references raise errors."""
        bad_il = """
export function w $test() {
@start
    %r =w add %undefined, 1
    ret %r
}
"""
        with pytest.raises(CompilationError):
            compile_il(bad_il)


@pytest.mark.integration
class TestCompileWithData:
    """Tests for compiling IL with data sections."""

    def test_compile_with_data_section(self):
        """Test compiling IL with data section."""
        il = """
data $msg = { b "hello", b 0 }

export function w $main() {
@start
    ret 0
}
"""
        asm = compile_il(il)
        assert "msg" in asm

    def test_compile_with_aligned_data(self):
        """Test compiling IL with aligned data."""
        il = """
data $buffer = align 16 { z 64 }

export function w $main() {
@start
    ret 0
}
"""
        asm = compile_il(il)
        assert asm is not None


@pytest.mark.integration
class TestCompilerMethod:
    """Tests for Compiler.compile() method."""

    def test_compile_method_produces_output(self, compiler, simple_il):
        """Test that compile method produces output."""
        asm = compiler.compile(simple_il)
        assert asm is not None
        assert ".text" in asm

    def test_compile_preserves_target_setting(self, add_function_il):
        """Test that target setting is preserved across compiles."""
        compiler = Compiler(target="amd64_sysv")
        asm1 = compiler.compile(add_function_il)
        asm2 = compiler.compile(add_function_il)
        assert asm1 == asm2

    def test_compile_multiple_functions(self):
        """Test compiling multiple functions."""
        il = """
export function w $foo() {
@start
    ret 1
}

export function w $bar() {
@start
    ret 2
}
"""
        asm = compile_il(il)
        assert "foo" in asm
        assert "bar" in asm

    def test_compile_with_control_flow(self):
        """Test compiling with control flow."""
        il = """
export function w $max(w %a, w %b) {
@start
    %c =w csgtw %a, %b
    jnz %c, @a_greater, @b_greater
@a_greater
    ret %a
@b_greater
    ret %b
}
"""
        asm = compile_il(il)
        assert asm is not None
        assert "max" in asm
