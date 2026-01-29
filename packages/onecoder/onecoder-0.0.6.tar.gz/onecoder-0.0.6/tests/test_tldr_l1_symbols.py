
import pytest
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

# Try to import TLDRTool, handling imports that might fail
import sys
# Add package root to path to mimic running from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

# We need to bypass the registry import if pydantic is missing in test env
# similar to how we did in run_tldr_test.py, but for a proper test file we might assume deps.
# However, given the environment issues, let's just test the logic if we can load it.

def load_tldr_tool_class():
    import importlib.util
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../onecoder/tools/tldr_tool.py"))
    spec = importlib.util.spec_from_file_location("tldr_tool", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["tldr_tool_test_module"] = module
    spec.loader.exec_module(module)
    return module.TLDRTool

try:
    TLDRTool = load_tldr_tool_class()
    HAS_TOOL = True
except ImportError:
    HAS_TOOL = False

@pytest.fixture
def temp_py_file(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("""
class Outer:
    def method(self):
        def inner():
            pass
""")
    return str(f)

@pytest.fixture
def temp_ts_file(tmp_path):
    f = tmp_path / "test.ts"
    f.write_text("""
const x = () => {};
function y() {}
class Z {
  method() {}
}
interface I {}
type T = string;
enum E { A }
const obj = { prop: function() {} };
""")
    return str(f)

@pytest.mark.skipif(not HAS_TOOL, reason="TLDRTool could not be loaded")
def test_python_symbols(temp_py_file):
    tool = TLDRTool()
    # Mock _get_parser if tree_sitter not installed?
    # Ideally tests run in env with deps.
    if not tool.supported_languages: 
       # Should check if tree-sitter is actually available inside tool
       # The tool catches ImportError.
       pass

    res = tool.scan_file(temp_py_file)
    if "error" in res:
        pytest.skip(f"Tree-sitter error: {res['error']}")
    
    symbols = res.get("symbols", [])
    names = [s["name"] for s in symbols]
    assert "Outer" in names
    assert "method" in names
    assert "inner" in names

@pytest.mark.skipif(not HAS_TOOL, reason="TLDRTool could not be loaded")
def test_ts_symbols(temp_ts_file):
    tool = TLDRTool()
    res = tool.scan_file(temp_ts_file)
    if "error" in res:
         pytest.skip(f"Tree-sitter error: {res['error']}")

    symbols = res.get("symbols", [])
    names = [s["name"] for s in symbols]
    kinds = [s["kind"] for s in symbols]

    # Explicit named functions
    assert "y" in names
    assert "Z" in names
    assert "method" in names
    
    # Types
    assert "I" in names
    assert "T" in names
    assert "E" in names

    # Anonymous/Variable functions
    # x is a variable, but we capture the arrow function as <anonymous>
    # AND because of variable_declarator query, we capture x as function too?
    # Wait, my query: (variable_declarator name: @var.name value: (arrow_function)) @function.def
    # This captures the declarator node. The logic looks up "parent" of name (which is declarator).
    # So "x" should be in names.
    assert "x" in names
    
    # Anonymous functions (from arrow func or function expr)
    # The arrow function itself matches use (arrow_function)
    # The function expr in obj matches (function)
    assert "<anonymous>" in names
