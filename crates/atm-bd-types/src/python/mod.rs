//! pyo3 bindings: the `atm_bd_types._native` extension behind the `atm_bd_types` wheel.
//!
//! One native module carries both Python surfaces. The wheel's `atm_bd_types` package re-exports the plug-in
//! surface; `atm_bd_core` re-exports the framework surface.
//! `_stub(module)` returns each surface's `.pyi` text, assembled from the stub text each binding carries.
mod conv;
mod enums;
mod hook;
mod records;
mod stub;

use pyo3::prelude::*;
use pyo3::IntoPyObjectExt;

use crate::plugin::Refusal;

/// A value, or its typed refusal, as the `X | Refusal` the stubs return.
fn either<'py, T: IntoPyObject<'py>>(
    py: Python<'py>,
    result: Result<T, Refusal>,
) -> PyResult<Bound<'py, PyAny>> {
    match result {
        Ok(value) => value.into_bound_py_any(py),
        Err(refusal) => hook::PyRefusal(refusal).into_bound_py_any(py),
    }
}

/// `class <name>(enum.Enum):` with its members and any extra body text.
fn enum_stub(name: &str, doc: Option<&str>, members: &[&str], extra: &str) -> String {
    let mut out = format!("class {name}(enum.Enum):\n");
    if let Some(doc) = doc {
        out.push_str(&format!("    r\"\"\"{doc}\"\"\"\n"));
    }
    for member in members {
        out.push_str(&format!("    {member} = ...\n"));
    }
    out.push_str(extra);
    out
}

/// `@_record class <name>:` with one annotated field per `(name, annotation, default)`.
fn record_stub(name: &str, doc: Option<&str>, fields: &[(&str, String, Option<&str>)]) -> String {
    let mut out = format!("@_record\nclass {name}:\n");
    if let Some(doc) = doc {
        out.push_str(&format!("    r\"\"\"{doc}\"\"\"\n"));
    }
    for (field, annotation, default) in fields {
        match default {
            Some(default) => out.push_str(&format!("    {field}: {annotation} = {default}\n")),
            None => out.push_str(&format!("    {field}: {annotation}\n")),
        }
    }
    out
}

/// The `.pyi` text of `module` (`atm_bd_types` or `atm_bd_core`).
#[pyfunction]
#[pyo3(name = "_stub")]
fn stub_text(module: &str) -> PyResult<String> {
    match module {
        "atm_bd_types" => Ok(stub::plugin()),
        "atm_bd_core" => Ok(stub::framework()),
        other => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "no stub for module {other:?}"
        ))),
    }
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    use enums::*;
    use hook::*;
    use records::*;

    m.add_class::<PyStatus>()?;
    m.add_class::<PyStage>()?;
    m.add_class::<PyPatchKind>()?;
    m.add_class::<PyAssignTransition>()?;
    m.add_class::<PyStartTransition>()?;
    m.add_class::<PyCloseTransition>()?;
    m.add_class::<PyTemplate>()?;
    m.add_class::<PyErrorId>()?;
    m.add_class::<PyRefusal>()?;
    m.add_class::<PyLayer>()?;
    m.add_class::<PyStack>()?;
    m.add_class::<PyFinding>()?;
    m.add_class::<PyQaPass>()?;
    m.add_class::<PyQaFail>()?;
    m.add_class::<PyBead>()?;
    m.add_class::<PyPhaseFile>()?;
    m.add_class::<PyBeadPatch>()?;
    m.add_class::<PyHookRequest>()?;
    m.add_class::<PyHookAction>()?;
    m.add_class::<PyHookReply>()?;
    m.add_class::<PyHook>()?;
    m.add_class::<PyFactKind>()?;
    m.add_class::<PyTaskState>()?;
    m.add_class::<PyCheckState>()?;
    m.add_class::<PyTaskFact>()?;
    m.add_class::<PyTaskEvents>()?;
    m.add_class::<PyRemoteBranch>()?;
    m.add_class::<PyAncestry>()?;
    m.add_class::<PyStackFact>()?;
    m.add_class::<PyTopChecks>()?;
    m.add_class::<PyPrBase>()?;
    m.add_class::<PyCollectError>()?;
    m.add_class::<PyPhaseFacts>()?;
    m.add_class::<PyReviewTarget>()?;
    m.add_class::<PyMerged>()?;
    m.add_class::<PyAssignVars>()?;
    m.add_class::<PyAssign>()?;
    m.add_class::<PyReport>()?;
    m.add_class::<PyNotify>()?;
    m.add_class::<PyParams>()?;
    m.add_class::<PyProfile>()?;

    m.add_class::<PyActionKind>()?;
    m.add_class::<PyOutcomeKind>()?;
    m.add_class::<PyPolicy>()?;
    m.add_class::<PyViewRow>()?;
    m.add_class::<PyDecision>()?;
    m.add_class::<PyViewStep>()?;
    m.add_class::<PyViewSprint>()?;
    m.add_class::<PyViewTask>()?;
    m.add_class::<PyViewAction>()?;
    m.add_class::<PyPhaseView>()?;
    m.add_class::<PyActionOutcome>()?;
    m.add_class::<PyTickResult>()?;
    m.add_class::<PyCommandResult>()?;
    m.add_class::<PyPorts>()?;

    m.add_function(wrap_pyfunction!(stack_of, m)?)?;
    m.add_function(wrap_pyfunction!(encode_evidence, m)?)?;
    m.add_function(wrap_pyfunction!(_layer, m)?)?;
    m.add_function(wrap_pyfunction!(_stack, m)?)?;
    m.add_function(wrap_pyfunction!(phase_file, m)?)?;
    m.add_function(wrap_pyfunction!(bead, m)?)?;
    m.add_function(wrap_pyfunction!(stub_text, m)?)?;
    Ok(())
}
