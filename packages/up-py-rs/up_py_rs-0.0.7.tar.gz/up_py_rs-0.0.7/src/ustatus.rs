use up_rust::UStatus as RustUStatus;

use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct UStatus {
    inner: RustUStatus,
}