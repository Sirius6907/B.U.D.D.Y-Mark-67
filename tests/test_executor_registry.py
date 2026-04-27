import pytest
from pathlib import Path
from agent.executor import _TOOL_REGISTRY, get_base_dir, _generated_code_tool

def test_tool_registry_contains_core_tools():
    """Verify that essential tools are registered in the dispatch registry."""
    assert "web_search" in _TOOL_REGISTRY
    assert "open_app" in _TOOL_REGISTRY
    assert "file_controller" in _TOOL_REGISTRY
    assert "generated_code" in _TOOL_REGISTRY

def test_get_base_dir():
    """Verify base directory resolution works."""
    base_dir = get_base_dir()
    assert isinstance(base_dir, Path)
    assert base_dir.is_absolute()

def test_generated_code_tool_requires_description():
    """Verify fallback tool raises error on missing description."""
    with pytest.raises(ValueError, match="requires a 'description' parameter"):
        _generated_code_tool({"other_param": "value"})
