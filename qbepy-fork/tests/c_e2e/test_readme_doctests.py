"""Test README.md examples using doctest."""

import pytest
import doctest
from pathlib import Path


def test_readme_examples():
    """Test all code examples in README.md using doctest."""
    # Import the setup function
    import doctest_setup
    
    # Run doctests on README.md
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md not found"
    
    # Run doctests
    results = doctest.testfile(
        str(readme_path),
        module_relative=False,
        globs=doctest_setup.global_namespace,
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        verbose=True
    )
    
    # Check results
    assert results.failed == 0, f"{results.failed} doctests failed in README.md"
    assert results.attempted > 0, "No doctests found in README.md"
    
    print(f"✓ All {results.attempted} doctests in README.md passed")


@pytest.mark.e2e
class TestReadmeExamples:
    """Test individual README examples."""
    
    def test_import_qbepy(self):
        """Test that qbepy can be imported."""
        import qbepy
        assert qbepy is not None
    
    def test_simple_il_compilation(self):
        """Test simple IL compilation from README."""
        import qbepy
        
        il = """
export function w $add(w %a, w %b) {
@start
    %r =w add %a, %b
    ret %r
}
"""
        
        # This should not raise an exception
        asm = qbepy.compile_il(il)
        assert asm is not None
        assert len(asm) > 0
        assert ".text" in asm
    
    def test_ir_builder_basic(self):
        """Test basic IR builder functionality from README."""
        import qbepy
        from qbepy import Module, Function, DataDef, W, L
        from qbepy.ir import Call, Return, Global, IntConst
        
        # Create a simple module
        mod = Module()
        mod.add_data(
            DataDef("greeting")
            .add_string("Hello, World!")
            .add_bytes(0)
        )
        
        func = Function("main", W, export=True)
        block = func.add_block("start")
        r = func.new_temp("r")
        block.instructions.append(
            Call(Global("puts"), [(L, Global("greeting"))], r, W)
        )
        block.terminator = Return(IntConst(0))
        mod.add_function(func)
        
        # This should not raise an exception
        asm = qbepy.compile_module(mod)
        assert asm is not None
        assert len(asm) > 0