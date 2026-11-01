//! Shared, serializable contracts for ATM bead orchestration.

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Orchestration profile of a phase.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "UPPERCASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Profile {
    Full,
    Lite,
}

/// Hosting provider for pull request operations.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "UPPERCASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Provider {
    Github,
    Azure,
}

/// Supported close transitions.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "SCREAMING_SNAKE_CASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Transition {
    DevClose,
    FixClose,
    QaPass,
    QaFail,
    Refused,
}

/// Stable categories for recoverable failures.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "SCREAMING_SNAKE_CASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ErrorKind {
    CommandFailed,
    Timeout,
    Rejected,
    Unreachable,
    ParseFailed,
    NotFound,
    ConfigInvalid,
    LockHeld,
    IoFailed,
    ProfileMismatch,
    ProviderInvalid,
}

/// A failure and an actionable recovery instruction.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", get_all, frozen, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Error {
    pub kind: ErrorKind,
    pub message: String,
    pub fix: String,
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl Error {
    #[new]
    fn new(kind: ErrorKind, message: String, fix: String) -> Self {
        Self { kind, message, fix }
    }
}

#[cfg(feature = "python")]
#[pymodule]
fn atm_bd_types(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Profile>()?;
    m.add_class::<Provider>()?;
    m.add_class::<Transition>()?;
    m.add_class::<ErrorKind>()?;
    m.add_class::<Error>()?;
    Ok(())
}

#[cfg(feature = "python")]
pyo3_stub_gen::define_stub_info_gatherer!(stub_info);

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn profile_serialization_is_stable() {
        assert_eq!(serde_json::to_string(&Profile::Full).unwrap(), "\"full\"");
        assert_eq!(
            serde_json::from_str::<Profile>("\"lite\"").unwrap(),
            Profile::Lite
        );
    }
}
