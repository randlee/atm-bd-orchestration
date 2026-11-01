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

/// Structured context retained for machine decisions and diagnostics.
#[cfg_attr(
    feature = "python",
    pyo3_stub_gen::derive::gen_stub_pyclass_complex_enum
)]
#[cfg_attr(feature = "python", pyclass(module = "atm_bd_types", from_py_object))]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ErrorDetail {
    CommandFailed {
        argv: Vec<String>,
        code: i32,
        stderr: String,
    },
    Timeout {
        argv: Vec<String>,
        seconds: u64,
    },
    Rejected {
        argv: Vec<String>,
        status: i32,
        message: String,
    },
    Unreachable {
        argv: Vec<String>,
        message: String,
    },
    ParseFailed {
        source: String,
        message: String,
    },
    NotFound {
        what: String,
    },
    ConfigInvalid {
        key: String,
        value: String,
    },
    LockHeld {
        snapshot_age_s: Option<u64>,
    },
    IoFailed {
        path: String,
        message: String,
    },
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
    pub detail: Option<ErrorDetail>,
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl Error {
    #[new]
    #[pyo3(signature = (kind, message, fix, detail=None))]
    fn new(kind: ErrorKind, message: String, fix: String, detail: Option<ErrorDetail>) -> Self {
        Self {
            kind,
            message,
            fix,
            detail,
        }
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
    m.add_class::<ErrorDetail>()?;
    m.add_class::<PrOp>()?;
    m.add_class::<BodyTransport>()?;
    m.add_class::<OutputFormat>()?;
    m.add_class::<StackGateResult>()?;
    m.add_class::<ProviderOp>()?;
    m.add_class::<CloseVars>()?;
    m.add_class::<ProviderCommands>()?;
    m.add_class::<PrRef>()?;
    Ok(())
}

#[cfg(feature = "python")]
pyo3_stub_gen::define_stub_info_gatherer!(stub_info);

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn structured_error_round_trips_without_losing_command_context() {
        let error = Error {
            kind: ErrorKind::CommandFailed,
            message: "git failed".into(),
            fix: "install git".into(),
            detail: Some(ErrorDetail::CommandFailed {
                argv: vec!["git".into(), "status".into()],
                code: 127,
                stderr: "not found".into(),
            }),
        };
        let encoded = serde_json::to_string(&error).unwrap();
        assert_eq!(serde_json::from_str::<Error>(&encoded).unwrap(), error);
    }

    #[test]
    fn profile_serialization_is_stable() {
        assert_eq!(serde_json::to_string(&Profile::Full).unwrap(), "\"full\"");
        assert_eq!(
            serde_json::from_str::<Profile>("\"lite\"").unwrap(),
            Profile::Lite
        );
    }
}

/// Pull request operations supplied by a hosting provider.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "SCREAMING_SNAKE_CASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PrOp {
    Create,
    View,
    EditBase,
    Comment,
    Checks,
    LookupByHead,
    StackLink,
    StackView,
}

/// How a command receives a body.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "SCREAMING_SNAKE_CASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BodyTransport {
    None,
    File,
}

/// Format of a command's standard output.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", eq, eq_int, from_py_object)
)]
#[cfg_attr(feature = "python", pyo3(rename_all = "SCREAMING_SNAKE_CASE"))]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OutputFormat {
    Json,
    Text,
    ExitCode,
}

/// Result of comparing a pull request's base and pushed head to the stack.
#[cfg_attr(
    feature = "python",
    pyo3_stub_gen::derive::gen_stub_pyclass_complex_enum
)]
#[cfg_attr(feature = "python", pyclass(module = "atm_bd_types", from_py_object))]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum StackGateResult {
    Stacked {},
    NotStacked {
        expected_base: String,
        actual_base: String,
    },
    NotPushed {
        branch: String,
        head: String,
    },
    NotAncestor {
        base_sha: String,
        head_sha: String,
    },
}

/// An argv-only provider command and its response-field mapping.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", get_all, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProviderOp {
    pub argv: Vec<String>,
    pub body: BodyTransport,
    pub output: OutputFormat,
    pub result: std::collections::BTreeMap<String, String>,
}

/// Complete provider command set, validated on deserialization.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(feature = "python", pyclass(module = "atm_bd_types", from_py_object))]
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ProviderCommands(pub std::collections::BTreeMap<PrOp, ProviderOp>);

impl<'de> Deserialize<'de> for ProviderCommands {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let commands = std::collections::BTreeMap::<PrOp, ProviderOp>::deserialize(deserializer)?;
        for (operation, required) in [
            (PrOp::Create, &["base", "head", "title", "body_file"][..]),
            (PrOp::View, &["number"][..]),
            (PrOp::EditBase, &["number", "base"][..]),
            (PrOp::Comment, &["number", "body_file"][..]),
            (PrOp::Checks, &["number"][..]),
            (PrOp::LookupByHead, &["head"][..]),
            (PrOp::StackLink, &[][..]),
            (PrOp::StackView, &[][..]),
        ] {
            let op = commands.get(&operation).ok_or_else(|| {
                serde::de::Error::custom(format!("missing {operation:?} operation"))
            })?;
            for name in required {
                let placeholder = format!("{{{name}}}");
                if !op.argv.iter().any(|arg| arg.contains(&placeholder)) {
                    return Err(serde::de::Error::custom(format!(
                        "{operation:?} lacks {placeholder}"
                    )));
                }
            }
            if op.body == BodyTransport::File
                && !op.argv.iter().any(|arg| arg.contains("{body_file}"))
            {
                return Err(serde::de::Error::custom(format!(
                    "{operation:?} file body lacks {{body_file}}"
                )));
            }
        }
        Ok(Self(commands))
    }
}

/// Shared close fields; lite omits both sanity-specific values.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", get_all, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CloseVars {
    pub sanity_bead: Option<String>,
    pub max_sanity_rounds: Option<u32>,
}

/// A provider-independent pull request identity.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", get_all, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrRef {
    pub number: String,
    pub url: String,
    pub base: String,
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl PrRef {
    #[new]
    fn new(number: String, url: String, base: String) -> Self {
        Self { number, url, base }
    }
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl ProviderCommands {
    /// Parse and validate a complete provider command set without raising for malformed data.
    #[staticmethod]
    fn parse_json(raw: &str) -> (Option<ProviderCommands>, Option<Error>) {
        match serde_json::from_str(raw) {
            Ok(commands) => (Some(commands), None),
            Err(err) => (
                None,
                Some(Error {
                    kind: ErrorKind::ProviderInvalid,
                    message: err.to_string(),
                    fix: "Correct the provider command configuration".into(),
                    detail: None,
                }),
            ),
        }
    }

    /// Return the named command using the serialized operation name.
    fn command(&self, name: &str) -> Option<ProviderOp> {
        let quoted = serde_json::to_string(name).ok()?;
        let op: PrOp = serde_json::from_str(&quoted).ok()?;
        self.0.get(&op).cloned()
    }
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl CloseVars {
    #[new]
    #[pyo3(signature = (sanity_bead=None, max_sanity_rounds=None))]
    fn new(sanity_bead: Option<String>, max_sanity_rounds: Option<u32>) -> Self {
        Self {
            sanity_bead,
            max_sanity_rounds,
        }
    }
}
