mod menu;
mod events;
mod handle;
mod engine;
mod utils;

use pyo3::prelude::*;

#[pymodule]
fn _cactuscat(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(engine::start_engine, m)?)?;
    m.add_class::<handle::CactusHandle>()?;
    Ok(())
}
