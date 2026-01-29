"""
Streamlit Reasoning Visualizer Component.

A beautiful, interactive component for visualizing LLM reasoning processes
with collapsible thought sections and rich markdown/LaTeX rendering.

Example usage:
    >>> import streamlit as st
    >>> from reasoning_visualizer import visualizer
    >>>
    >>> response = "<think>Let me work through this step by step...</think>The answer is 42."
    >>> visualizer(text=response)
"""

import os
import streamlit.components.v1 as components

__version__ = "0.1.0"
__author__ = "Ketan Mahandule"
__license__ = "Apache-2.0"
__all__ = ["visualizer", "__version__"]

# Create a _RELEASE constant. Set to False during development.
_RELEASE = True

if not _RELEASE:
    # Development mode: Connect to the React development server
    _component_func = components.declare_component(
        "reasoning_visualizer",
        url="http://localhost:3001",
    )
else:
    # Production mode: Point to the compiled frontend build folder
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component("reasoning_visualizer", path=build_dir)


def visualizer(text: str, key: str = None) -> None:
    """
    Render the Reasoning Visualizer component.

    Displays LLM responses with collapsible reasoning sections. The component
    automatically detects and parses various reasoning tag formats commonly
    used by models like DeepSeek, Phi, and others.

    Parameters
    ----------
    text : str
        The raw text containing reasoning tags and the answer. Supported formats:
        - ``<think>...</think>``
        - ``[THOUGHT]...[/THOUGHT]``
        - ``<reasoning>...</reasoning>``
        - ``<chain_of_thought>...</chain_of_thought>``

        If no tags are found, the entire text is displayed as the answer.

    key : str, optional
        An optional unique key that identifies this component instance.
        Required when multiple visualizers are rendered in the same container.

    Returns
    -------
    None
        This component does not return any value.

    Examples
    --------
    Basic usage with reasoning tags:

    >>> from reasoning_visualizer import visualizer
    >>> text = "<think>First, I'll analyze the problem...</think>The answer is 42."
    >>> visualizer(text=text)

    Multiple visualizers with unique keys:

    >>> visualizer(text=response1, key="viz1")
    >>> visualizer(text=response2, key="viz2")
    """
    return _component_func(text=text, key=key, default=None)
