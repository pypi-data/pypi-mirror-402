// src/lib.rs
pub mod analysis_pdfium;
pub mod types;

pub use crate::analysis_pdfium::analyze_pdf;

use pyo3::prelude::*;

#[pyfunction]
#[pyo3(name = "analyze_pdf")]
fn analyze_pdf_py(path: String) -> PyResult<String> {
    let result = analyze_pdf(&path).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?;
    let json = serde_json::to_string(&result)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(json)
}

#[pymodule]
fn pdflinkcheck_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(analyze_pdf_py, m)?)?;
    Ok(())
}
