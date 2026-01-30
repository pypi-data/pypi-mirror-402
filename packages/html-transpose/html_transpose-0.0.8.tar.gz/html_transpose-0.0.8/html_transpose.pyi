"""Python wrapper for html_transpose - a Rust library for transposing HTML tables."""

__version__: str

def transpose(html: str) -> str:
    """Transposes an HTML table string.
    
    This function swaps rows and columns of an HTML table while preserving
    merged cells (rowspan and colspan), attributes, and structure.
    
    Args:
        html: A string containing an HTML table (must contain a `<table>` element)
    
    Returns:
        The transposed HTML table as a string.
    
    Raises:
        ValueError: If no `<table>` element is found in the input or if the HTML parser fails.
    
    Example:
        >>> import html_transpose
        >>> html = \"\"\"
        ... <table>
        ...   <tr><td>A</td><td>B</td></tr>
        ...   <tr><td>C</td><td>D</td></tr>
        ... </table>
        ... \"\"\"
        >>> transposed = html_transpose.transpose(html)
        >>> print(transposed)
    """
    ...
