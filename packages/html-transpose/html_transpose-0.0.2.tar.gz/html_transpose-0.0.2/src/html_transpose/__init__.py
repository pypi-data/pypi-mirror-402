"""
html_transpose - Python wrapper for html_transpose Rust library

A library for transposing HTML tables while preserving merged cells,
attributes, and structure.
"""

try:
    from html_transpose.html_transpose import transpose, __version__
except ImportError:
    # Fallback for development or if extension module is not built
    __version__ = "0.1.0"
    raise ImportError(
        "html_transpose extension module not found. "
        "Please install the package using: pip install html_transpose"
    )

__all__ = ["transpose", "__version__"]
