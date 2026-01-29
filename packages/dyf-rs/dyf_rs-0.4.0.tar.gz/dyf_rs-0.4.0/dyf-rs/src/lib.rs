//! DYF Python Bindings - Density Yields Features
//!
//! Exposes the Rust DensityClassifier to Python via PyO3.
//! Returns raw density metrics - classification is left to the caller.

use pyo3::prelude::*;

mod density_bindings;

use density_bindings::{
    PyDensityClassifier, PyDensityReport, PyBridgeAnalysis,
    PyBitDepthStats, py_analyze_bit_depths, py_select_optimal_bit_depth,
};

/// DYF - Density Yields Features using PCA-based LSH
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyDensityClassifier>()?;
    m.add_class::<PyDensityReport>()?;
    m.add_class::<PyBridgeAnalysis>()?;
    m.add_class::<PyBitDepthStats>()?;
    m.add_function(wrap_pyfunction!(py_analyze_bit_depths, m)?)?;
    m.add_function(wrap_pyfunction!(py_select_optimal_bit_depth, m)?)?;
    Ok(())
}
