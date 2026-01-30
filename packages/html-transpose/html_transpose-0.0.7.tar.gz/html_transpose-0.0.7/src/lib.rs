use pyo3::prelude::*;
use ::html_transpose as ht;
/// Transposes an HTML table string.
///
/// This function swaps rows and columns of an HTML table while preserving
/// merged cells (rowspan and colspan), attributes, and structure.
///
/// # Arguments
///
/// * `html` - A string containing an HTML table (must contain a `<table>` element)
///
/// # Returns
///
/// Returns the transposed HTML table as a string.
///
/// # Errors
///
/// Raises a `ValueError` if:
/// - No `<table>` element is found in the input
/// - The HTML parser fails
///
/// # Example
///
/// ```python
/// import html_transpose
///
/// html = """
/// <table>
///   <tr><td>A</td><td>B</td></tr>
///   <tr><td>C</td><td>D</td></tr>
/// </table>
/// """
///
/// transposed = html_transpose.transpose(html)
/// print(transposed)
/// ```
#[pyfunction]
pub fn transpose(html: &str) -> PyResult<String> {
    ht::transpose(html)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))
}

/// Python module for html_transpose
#[pymodule]
fn html_transpose(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(transpose, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
