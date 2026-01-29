"""
Tests for the Reasoning Visualizer Streamlit component.

These tests verify the package structure and basic API functionality.
They do not test the React frontend directly.
"""

import pytest


def test_import_component():
    """Test that the component can be imported."""
    from reasoning_visualizer import visualizer
    assert visualizer is not None
    assert callable(visualizer)


def test_version_defined():
    """Test that __version__ is defined and follows semver."""
    from reasoning_visualizer import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
    # Basic semver format check (x.y.z)
    parts = __version__.split(".")
    assert len(parts) == 3
    for part in parts:
        assert part.isdigit()


def test_public_api():
    """Test that the public API is properly exported."""
    import reasoning_visualizer
    
    # Check __all__ is defined
    assert hasattr(reasoning_visualizer, "__all__")
    assert "visualizer" in reasoning_visualizer.__all__
    assert "__version__" in reasoning_visualizer.__all__
    
    # Check metadata
    assert hasattr(reasoning_visualizer, "__author__")
    assert hasattr(reasoning_visualizer, "__license__")


def test_visualizer_function_signature():
    """Test that the visualizer function has the correct signature."""
    from reasoning_visualizer import visualizer
    import inspect
    
    sig = inspect.signature(visualizer)
    params = list(sig.parameters.keys())
    
    assert "text" in params
    assert "key" in params


def test_package_metadata():
    """Test package metadata values."""
    from reasoning_visualizer import __author__, __license__, __version__
    
    assert __author__ == "Ketan Mahandule"
    assert __license__ == "Apache-2.0"
    assert __version__ == "0.1.0"
