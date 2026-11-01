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
    ConfigMissing,
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
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
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
    pyclass(module = "atm_bd_types", frozen, eq, hash, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
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
    fn __str__(&self) -> String {
        self.message.clone()
    }
    #[getter]
    fn kind(&self) -> ErrorKind {
        self.kind
    }
    #[getter]
    fn message(&self) -> String {
        self.message.clone()
    }
    #[getter]
    fn fix(&self) -> String {
        self.fix.clone()
    }
    #[getter]
    #[gen_stub(override_return_type(
        type_repr = "ErrorDetail.CommandFailed | ErrorDetail.Timeout | ErrorDetail.Rejected | ErrorDetail.Unreachable | ErrorDetail.ParseFailed | ErrorDetail.NotFound | ErrorDetail.ConfigInvalid | ErrorDetail.LockHeld | ErrorDetail.IoFailed | None"
    ))]
    fn detail(&self) -> Option<ErrorDetail> {
        self.detail.clone()
    }
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
    m.add_class::<MergedPrRef>()?;
    m.add_class::<Evidence>()?;
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
    EditBody,
    Comment,
    CommentView,
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
#[cfg_attr(feature = "python", pyclass(module = "atm_bd_types", from_py_object))]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProviderOp {
    pub argv: Vec<String>,
    pub body: BodyTransport,
    pub output: OutputFormat,
    pub result: std::collections::BTreeMap<String, String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub comment: Option<String>,
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
            (PrOp::EditBody, &["number", "body_file"][..]),
            (PrOp::Comment, &["number", "body_file"][..]),
            (PrOp::CommentView, &["number"][..]),
            (PrOp::Checks, &[][..]),
            (PrOp::LookupByHead, &["head"][..]),
            (PrOp::StackLink, &[][..]),
            (PrOp::StackView, &[][..]),
        ] {
            let op = commands.get(&operation).ok_or_else(|| {
                serde::de::Error::custom(format!("missing {operation:?} operation"))
            })?;
            // Azure's invoke adapter constructs the create request body from these values.
            let azure_invoke_create = operation == PrOp::Create
                && op.body == BodyTransport::File
                && op
                    .argv
                    .starts_with(&["az".into(), "devops".into(), "invoke".into()]);
            for arg in &op.argv {
                let mut rest = arg.as_str();
                while let Some(start) = rest.find('{') {
                    let after = &rest[start + 1..];
                    let end = after.find('}').ok_or_else(|| {
                        serde::de::Error::custom(format!(
                            "{operation:?} has an unclosed placeholder"
                        ))
                    })?;
                    let name = &after[..end];
                    if ![
                        "base",
                        "head",
                        "title",
                        "body_file",
                        "number",
                        "text",
                        "organization",
                        "project",
                        "repository",
                        "stack_bead",
                        "state",
                        "thread",
                        "owner",
                        "repo",
                        "head_sha",
                        "fields",
                        "jq",
                    ]
                    .contains(&name)
                    {
                        return Err(serde::de::Error::custom(format!(
                            "{operation:?} has unknown placeholder {{{name}}}"
                        )));
                    }
                    rest = &after[end + 1..];
                }
                if rest.contains('}') {
                    return Err(serde::de::Error::custom(format!(
                        "{operation:?} has an unmatched brace"
                    )));
                }
            }
            for name in required {
                let placeholder = format!("{{{name}}}");
                let supplied_by_adapter =
                    azure_invoke_create && ["base", "head", "title"].contains(name);
                if !supplied_by_adapter && !op.argv.iter().any(|arg| arg.contains(&placeholder)) {
                    return Err(serde::de::Error::custom(format!(
                        "{operation:?} lacks {placeholder}"
                    )));
                }
            }
            if operation == PrOp::Checks
                && !op
                    .argv
                    .iter()
                    .any(|arg| arg.contains("{number}") || arg.contains("{head_sha}"))
            {
                return Err(serde::de::Error::custom(
                    "Checks lacks {number} or {head_sha}",
                ));
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
    pub head_sha: String,
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl PrRef {
    #[new]
    fn new(number: String, url: String, base: String, head_sha: String) -> Self {
        Self {
            number,
            url,
            base,
            head_sha,
        }
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

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl ProviderOp {
    #[getter]
    fn argv(&self) -> Vec<String> {
        self.argv.clone()
    }
    #[getter]
    fn body(&self) -> BodyTransport {
        self.body
    }
    #[getter]
    fn output(&self) -> OutputFormat {
        self.output
    }
    #[getter]
    fn result(&self) -> std::collections::BTreeMap<String, String> {
        self.result.clone()
    }
}

/// A merged pull request and the commit used for ancestry checks.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", get_all, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MergedPrRef {
    pub number: String,
    pub url: String,
    pub base: String,
    pub merged_at: String,
    pub merge_commit: String,
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl MergedPrRef {
    #[new]
    fn new(
        number: String,
        url: String,
        base: String,
        merged_at: String,
        merge_commit: String,
    ) -> Self {
        Self {
            number,
            url,
            base,
            merged_at,
            merge_commit,
        }
    }
}

/// Provider evidence and its attribution.
#[cfg_attr(feature = "python", pyo3_stub_gen::derive::gen_stub_pyclass)]
#[cfg_attr(
    feature = "python",
    pyclass(module = "atm_bd_types", get_all, from_py_object)
)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Evidence {
    pub body: String,
    pub url: Option<String>,
    pub author: Option<String>,
    pub updated_at: Option<String>,
}

#[cfg(feature = "python")]
#[pyo3_stub_gen::derive::gen_stub_pymethods]
#[pymethods]
impl Evidence {
    #[new]
    fn new(
        body: String,
        url: Option<String>,
        author: Option<String>,
        updated_at: Option<String>,
    ) -> Self {
        Self {
            body,
            url,
            author,
            updated_at,
        }
    }
}
