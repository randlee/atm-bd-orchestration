//! Python classes for the task-hook surface: refusals, beads, phase files, guarded writes, the ATM wire.
//!
//! Every method delegates to the contract type it wraps; each class carries its stub text beside it.
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::context;
use super::conv::conv_wrapper;
use super::either;
use super::enums::{PyErrorId, PyStage, PyStatus, PyTemplate};
use crate::plugin::{
    Bead, BeadPatch, CloseVars, Ctx, ErrorId, Evidence, Finding, HookAction, HookReply,
    HookRequest, Layer, PhaseFile, QaFail, QaPass, Refusal, Stack, Template, TemplateFile,
};

conv_wrapper! {
    Refusal => PyRefusal as "Refusal",
    Layer => PyLayer as "Layer",
    Stack => PyStack as "Stack",
    Finding => PyFinding as "Finding",
    Bead => PyBead as "Bead",
    PhaseFile => PyPhaseFile as "PhaseFile",
}

/// A typed refusal: an `ErrorId` and the named values its fix text fills.
#[pyclass(eq, frozen, from_py_object, name = "Refusal", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyRefusal(pub(crate) Refusal);

pub(crate) const REFUSAL_STUB: &str = "@typing.final
class Refusal:
    def __new__(cls, id: ErrorId, **context: str | list[str]) -> Refusal: ...
    @property
    def id(self) -> ErrorId: ...
";

fn ctx(key: &str, value: &Bound<'_, PyAny>) -> PyResult<Ctx> {
    if let Ok(one) = value.extract::<String>() {
        return Ok(Ctx::One(one));
    }
    value.extract::<Vec<String>>().map(Ctx::Many).map_err(|_| {
        PyTypeError::new_err(format!("Refusal context {key:?} must be str or list[str]"))
    })
}

#[pymethods]
impl PyRefusal {
    #[new]
    #[pyo3(signature = (id, **context))]
    fn new(id: PyErrorId, context: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let mut refusal = Refusal::new(id.into());
        for (key, value) in context.into_iter().flat_map(|c| c.iter()) {
            let key: String = key.extract()?;
            let value = ctx(&key, &value)?;
            refusal = refusal.with(&key, value);
        }
        Ok(PyRefusal(refusal))
    }

    #[getter]
    fn id(&self) -> PyErrorId {
        self.0.id.into()
    }

    fn __repr__(&self) -> String {
        format!("Refusal({})", self.0.message(None))
    }
}

/// One stack ledger layer.
#[pyclass(eq, frozen, from_py_object, name = "Layer", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyLayer(pub(crate) Layer);

pub(crate) const LAYER_STUB: &str = "@typing.final
class Layer:
    @property
    def branch(self) -> str: ...
    @property
    def head(self) -> Sha: ...
    @property
    def pr(self) -> int: ...
    @property
    def base(self) -> str: ...
";

#[pymethods]
impl PyLayer {
    #[getter]
    fn branch(&self) -> &str {
        &self.0.branch
    }
    #[getter]
    fn head(&self) -> &str {
        self.0.head.as_str()
    }
    #[getter]
    fn pr(&self) -> u64 {
        self.0.pr
    }
    #[getter]
    fn base(&self) -> &str {
        &self.0.base
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// The stage:stack bead's ledger.
#[pyclass(eq, frozen, from_py_object, name = "Stack", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyStack(pub(crate) Stack);

pub(crate) const STACK_STUB: &str = "@typing.final
class Stack:
    @property
    def layers(self) -> list[Layer]: ...
";

#[pymethods]
impl PyStack {
    #[getter]
    fn layers(&self) -> Vec<PyLayer> {
        self.0.layers.iter().cloned().map(PyLayer).collect()
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// One QA finding.
#[pyclass(eq, frozen, from_py_object, name = "Finding", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyFinding(pub(crate) Finding);

pub(crate) const FINDING_STUB: &str = "@typing.final
class Finding:
    @property
    def id(self) -> str: ...
    @property
    def blocking(self) -> bool: ...
";

#[pymethods]
impl PyFinding {
    #[getter]
    fn id(&self) -> &str {
        &self.0.id
    }
    #[getter]
    fn blocking(&self) -> bool {
        self.0.blocking
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// A QA PASS verdict.
#[pyclass(eq, frozen, from_py_object, name = "QaPass", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyQaPass(pub(crate) QaPass);

pub(crate) const QA_PASS_STUB: &str = "@typing.final
class QaPass:
    @property
    def sha(self) -> str: ...
";

#[pymethods]
impl PyQaPass {
    #[getter]
    fn sha(&self) -> &str {
        self.0.sha.as_str()
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// A QA FINDINGS verdict.
#[pyclass(eq, frozen, from_py_object, name = "QaFail", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyQaFail(pub(crate) QaFail);

pub(crate) const QA_FAIL_STUB: &str = "@typing.final
class QaFail:
    @property
    def sha(self) -> str: ...
    @property
    def findings(self) -> list[Finding]: ...
";

#[pymethods]
impl PyQaFail {
    #[getter]
    fn sha(&self) -> &str {
        self.0.sha.as_str()
    }
    #[getter]
    fn findings(&self) -> Vec<PyFinding> {
        self.0.findings.iter().cloned().map(PyFinding).collect()
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// A bead as the hooks read it.
#[pyclass(eq, frozen, from_py_object, name = "Bead", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyBead(pub(crate) Bead);

pub(crate) const BEAD_STUB: &str = r#"@typing.final
class Bead:
    @property
    def id(self) -> str: ...
    @property
    def status(self) -> Status: ...
    @property
    def stage(self) -> Stage: ...
    @property
    def assignee(self) -> str | None: ...
    @property
    def open_blockers(self) -> list[str]: ...
    @property
    def branch(self) -> str: ...
    @property
    def stack_bead(self) -> str: ...
    @property
    def sprint(self) -> str: ...
    @property
    def phase(self) -> str: ...
    def blocks(self, bead_id: str) -> bool: ...
    def layer_for(self, branch: str) -> Layer | None:
        r"""On a stack bead: its ledger layer for `branch`."""
"#;

#[pymethods]
impl PyBead {
    #[getter]
    fn id(&self) -> &str {
        &self.0.id
    }
    #[getter]
    fn status(&self) -> PyStatus {
        self.0.status.into()
    }
    #[getter]
    fn stage(&self) -> PyStage {
        self.0.stage.into()
    }
    #[getter]
    fn assignee(&self) -> Option<&str> {
        self.0.assignee.as_deref()
    }
    #[getter]
    fn open_blockers(&self) -> Vec<String> {
        self.0.open_blockers.clone()
    }
    #[getter]
    fn branch(&self) -> &str {
        &self.0.branch
    }
    #[getter]
    fn stack_bead(&self) -> &str {
        &self.0.stack_bead
    }
    #[getter]
    fn sprint(&self) -> &str {
        &self.0.sprint
    }
    #[getter]
    fn phase(&self) -> &str {
        &self.0.phase
    }
    fn blocks(&self, bead_id: &str) -> bool {
        self.0.blocks(bead_id)
    }
    fn layer_for(&self, branch: &str) -> Option<PyLayer> {
        self.0.layer_for(branch).cloned().map(PyLayer)
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// A loaded `.atm-bd/phase-<x>.toml`.
#[pyclass(
    eq,
    frozen,
    from_py_object,
    name = "PhaseFile",
    module = "atm_bd_types"
)]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyPhaseFile(pub(crate) PhaseFile);

pub(crate) const PHASE_FILE_STUB: &str = r#"@typing.final
class PhaseFile:
    @property
    def profile(self) -> str: ...
    @property
    def lead(self) -> str: ...
    def template(self, which: Template) -> str: ...
    def key(self, name: str) -> str | None:
        r"""Another top-level string key: root, integration_branch, keys a policy param names."""
"#;

#[pymethods]
impl PyPhaseFile {
    #[getter]
    fn profile(&self) -> &str {
        &self.0.profile
    }
    #[getter]
    fn lead(&self) -> &str {
        &self.0.lead
    }
    /// The template's path; `HookAction.close` resolves the path back to this template's bytes.
    fn template(&self, which: PyTemplate) -> String {
        let file = self.0.template(Template::from(which));
        context::add_template(file);
        file.path.clone()
    }
    fn key(&self, name: &str) -> Option<&str> {
        self.0.key(name)
    }
    fn __repr__(&self) -> String {
        format!(
            "PhaseFile(profile={:?}, lead={:?})",
            self.0.profile, self.0.lead
        )
    }
}

/// One guarded bead write.
#[pyclass(
    eq,
    frozen,
    from_py_object,
    name = "BeadPatch",
    module = "atm_bd_types"
)]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyBeadPatch(pub(crate) BeadPatch);

pub(crate) const BEAD_PATCH_STUB: &str = r#"@typing.final
class BeadPatch:
    r"""One guarded write: applied only if status and assignee still equal the snapshot's, else BEAD_RACED."""
    @staticmethod
    def assign(snapshot: Bead, agent: str) -> BeadPatch: ...
    @staticmethod
    def start(snapshot: Bead) -> BeadPatch: ...
    @staticmethod
    def reopen(snapshot: Bead) -> BeadPatch: ...
    @staticmethod
    def close(snapshot: Bead, evidence: Layer | QaPass | QaFail) -> BeadPatch: ...
"#;

/// `Layer | QaPass | QaFail` as `Evidence`; `None` for any other value.
fn evidence(value: &Bound<'_, PyAny>) -> Option<Evidence> {
    if let Ok(layer) = value.extract::<PyLayer>() {
        return Some(Evidence::Layer(layer.0));
    }
    if let Ok(pass) = value.extract::<PyQaPass>() {
        return Some(Evidence::QaPass(pass.0));
    }
    value
        .extract::<PyQaFail>()
        .ok()
        .map(|fail| Evidence::QaFail(fail.0))
}

#[pymethods]
impl PyBeadPatch {
    #[staticmethod]
    fn assign(snapshot: PyRef<'_, PyBead>, agent: &str) -> Self {
        PyBeadPatch(BeadPatch::assign(&snapshot.0, agent))
    }
    #[staticmethod]
    fn start(snapshot: PyRef<'_, PyBead>) -> Self {
        PyBeadPatch(BeadPatch::start(&snapshot.0))
    }
    #[staticmethod]
    fn reopen(snapshot: PyRef<'_, PyBead>) -> Self {
        PyBeadPatch(BeadPatch::reopen(&snapshot.0))
    }
    #[staticmethod]
    fn close(snapshot: PyRef<'_, PyBead>, evidence: &Bound<'_, PyAny>) -> PyResult<Self> {
        let evidence = self::evidence(evidence).ok_or_else(|| {
            PyTypeError::new_err("BeadPatch.close evidence must be Layer, QaPass or QaFail")
        })?;
        Ok(PyBeadPatch(BeadPatch::close(&snapshot.0, evidence)))
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// ATM's task-hook request.
#[pyclass(frozen, name = "HookRequest", module = "atm_bd_types")]
#[derive(Clone, Debug)]
pub(crate) struct PyHookRequest(pub(crate) HookRequest);

pub(crate) const HOOK_REQUEST_STUB: &str = "@typing.final
class HookRequest:
    @staticmethod
    def parse(stdin: str) -> HookRequest | Refusal: ...
    def is_phase_task(self) -> bool: ...
    @property
    def phase(self) -> str: ...
    @property
    def phase_config_path(self) -> str: ...
    @property
    def caller(self) -> str: ...
    @property
    def task_id(self) -> str: ...
    @property
    def assignee(self) -> str | None: ...
    @property
    def close_report(self) -> str | None: ...
    @property
    def close_reason(self) -> str | None: ...
    def qa_pass(self) -> QaPass | Refusal: ...
    def qa_findings(self) -> QaFail | Refusal: ...
";

#[pymethods]
impl PyHookRequest {
    /// `HookRequest::parse`; a decoded request becomes the one this process answers.
    #[staticmethod]
    fn parse<'py>(py: Python<'py>, stdin: &str) -> PyResult<Bound<'py, PyAny>> {
        let parsed = HookRequest::parse(stdin);
        if let Ok(request) = &parsed {
            context::set_request(request);
        }
        either(py, parsed.map(PyHookRequest))
    }
    fn is_phase_task(&self) -> bool {
        self.0.is_phase_task()
    }
    #[getter]
    fn phase(&self) -> &str {
        self.0.phase()
    }
    #[getter]
    fn phase_config_path(&self) -> String {
        self.0.phase_config_path()
    }
    #[getter]
    fn caller(&self) -> &str {
        self.0.caller()
    }
    #[getter]
    fn task_id(&self) -> &str {
        self.0.task_id()
    }
    #[getter]
    fn assignee(&self) -> Option<&str> {
        self.0.assignee()
    }
    #[getter]
    fn close_report(&self) -> Option<&str> {
        self.0.close_report()
    }
    #[getter]
    fn close_reason(&self) -> Option<&str> {
        self.0.close_reason()
    }
    fn qa_pass<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        either(py, self.0.qa_pass().map(PyQaPass))
    }
    fn qa_findings<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        either(py, self.0.qa_findings().map(PyQaFail))
    }
    fn __repr__(&self) -> String {
        format!(
            "HookRequest(hook={:?}, phase={:?}, task_id={:?})",
            self.0.hook(),
            self.0.phase(),
            self.0.task_id()
        )
    }
}

/// One `atm-action` close, or the refusal that it could not be built (no parsed request, unknown template).
#[pyclass(frozen, from_py_object, name = "HookAction", module = "atm_bd_types")]
#[derive(Clone, Debug)]
pub(crate) struct PyHookAction(pub(crate) Result<HookAction, Refusal>);

pub(crate) const HOOK_ACTION_STUB: &str = r#"@typing.final
class HookAction:
    @staticmethod
    def close(template: str, vars: Layer | QaPass | QaFail | str) -> HookAction:
        r"""atm task close --template <template> --vars <vars>; str is the give-back reason."""
"#;

fn invalid(field: &str) -> Refusal {
    Refusal::new(ErrorId::RequestInvalid).with("field", Ctx::One(field.to_owned()))
}

#[pymethods]
impl PyHookAction {
    /// `HookAction::close` for the parsed request and the template `PhaseFile.template` returned as `template`.
    #[staticmethod]
    fn close(template: &str, vars: &Bound<'_, PyAny>) -> PyResult<Self> {
        let vars = match vars.extract::<String>() {
            Ok(reason) => CloseVars::Reason { reason },
            Err(_) => evidence(vars).map(|e| CloseVars::from(&e)).ok_or_else(|| {
                PyTypeError::new_err("HookAction.close vars must be Layer, QaPass, QaFail or str")
            })?,
        };
        let action = match (context::request(), context::template(template)) {
            (None, _) => Err(invalid("request")),
            (Some(_), None) => Err(invalid("template")),
            (Some(request), Some(file)) => Ok(HookAction::close(&request, &file, vars)),
        };
        Ok(PyHookAction(action))
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// The hook's reply to ATM.
#[pyclass(frozen, name = "HookReply", module = "atm_bd_types")]
#[derive(Clone, Debug)]
pub(crate) struct PyHookReply(pub(crate) HookReply);

pub(crate) const HOOK_REPLY_STUB: &str = "@typing.final
class HookReply:
    @staticmethod
    def not_applicable() -> HookReply: ...
    @staticmethod
    def pass_through() -> HookReply: ...
    @staticmethod
    def refused(refusal: Refusal) -> HookReply: ...
    @staticmethod
    def handled(actions: list[HookAction]) -> HookReply: ...
    def to_json(self) -> str: ...
";

#[pymethods]
impl PyHookReply {
    #[staticmethod]
    fn not_applicable() -> Self {
        PyHookReply(HookReply::not_applicable())
    }
    #[staticmethod]
    fn pass_through() -> Self {
        PyHookReply(HookReply::pass_through())
    }
    #[staticmethod]
    fn refused(refusal: PyRefusal) -> Self {
        PyHookReply(HookReply::refused(refusal.0))
    }
    /// `HookReply::handled`; an action that could not be built refuses the whole reply with its refusal.
    #[staticmethod]
    fn handled(actions: Vec<PyHookAction>) -> Self {
        match actions
            .into_iter()
            .map(|a| a.0)
            .collect::<Result<Vec<_>, _>>()
        {
            Ok(actions) => PyHookReply(HookReply::handled(actions)),
            Err(refusal) => PyHookReply(HookReply::refused(refusal)),
        }
    }
    /// `HookReply::to_json` with the parsed request's hook selecting the fix table.
    fn to_json(&self) -> String {
        self.0.to_json(context::hook())
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

/// The `PhaseFiles` adapter over `.atm-bd/phase-<x>.toml`.
#[pyclass(frozen, name = "PhaseFilesCli", module = "atm_bd_types")]
#[derive(Clone, Debug, Default)]
pub(crate) struct PyPhaseFilesCli;

pub(crate) const PHASE_FILES_CLI_STUB: &str = "@typing.final
class PhaseFilesCli(PhaseFiles):
    def __new__(cls) -> PhaseFilesCli: ...
    def load(self, path: str, profile: str) -> PhaseFile | Refusal: ...
";

/// Why the store adapters refuse: they are sprint bo-10's deliverable, not this crate's yet.
const STORES_PENDING: &str = "the store adapters land in sprint bo-10";

#[pymethods]
impl PyPhaseFilesCli {
    #[new]
    fn new() -> Self {
        PyPhaseFilesCli
    }
    /// Refuses PHASE_UNREADABLE until bo-10 implements the loader.
    fn load(&self, path: &str, profile: &str) -> PyRefusal {
        PyRefusal(
            Refusal::new(ErrorId::PhaseUnreadable)
                .with("path", Ctx::One(path.to_owned()))
                .with("profile", Ctx::One(profile.to_owned()))
                .with("reason", Ctx::One(STORES_PENDING.to_owned())),
        )
    }
}

/// The beads-cache adapter.
#[pyclass(frozen, name = "CacheStore", module = "atm_bd_types")]
#[derive(Clone, Debug)]
pub(crate) struct PyCacheStore {
    phase: String,
}

pub(crate) const CACHE_STORE_STUB: &str = r#"@typing.final
class CacheStore(BeadStore):
    r"""The beads-cache adapter the hooks' entry points construct; the framework's BeadsCache port."""
    @staticmethod
    def for_phase(phase: str) -> CacheStore | Refusal: ...
    def show(self, bead_id: str) -> Bead | Refusal: ...
    def target_layer(self, qa_bead: Bead) -> Layer | Refusal: ...
    def update(self, patch: BeadPatch, actor: str) -> Refusal | None: ...
    def list(self, phase: str) -> builtins.list[Bead] | Refusal: ...
    def ready(self, phase: str) -> builtins.list[Bead] | Refusal: ...
"#;

fn cache_unavailable(phase: &str) -> PyRefusal {
    PyRefusal(
        Refusal::new(ErrorId::CacheUnavailable)
            .with("phase", Ctx::One(phase.to_owned()))
            .with("reason", Ctx::One(STORES_PENDING.to_owned())),
    )
}

impl PyRefusal {
    /// Adds one named text value to the refusal's context.
    fn with(self, key: &str, value: &str) -> Self {
        PyRefusal(self.0.with(key, Ctx::One(value.to_owned())))
    }
}

#[pymethods]
impl PyCacheStore {
    /// Refuses CACHE_UNAVAILABLE until bo-10 implements the adapter.
    #[staticmethod]
    fn for_phase(phase: &str) -> PyRefusal {
        cache_unavailable(phase)
    }
    fn show(&self, bead_id: &str) -> PyRefusal {
        cache_unavailable(&self.phase).with("bead", bead_id)
    }
    fn target_layer(&self, qa_bead: PyRef<'_, PyBead>) -> PyRefusal {
        cache_unavailable(&self.phase).with("bead", &qa_bead.0.id)
    }
    fn update(&self, patch: PyRef<'_, PyBeadPatch>, actor: &str) -> PyRefusal {
        let bead = match &patch.0 {
            BeadPatch::Assign { guard, .. }
            | BeadPatch::Start { guard }
            | BeadPatch::Reopen { guard }
            | BeadPatch::Close { guard, .. } => guard.bead_id.clone(),
        };
        cache_unavailable(&self.phase)
            .with("bead", &bead)
            .with("actor", actor)
    }
    fn list(&self, phase: &str) -> PyRefusal {
        cache_unavailable(phase)
    }
    fn ready(&self, phase: &str) -> PyRefusal {
        cache_unavailable(phase)
    }
}

/// Framework-side constructor for a `PhaseFile` (not on the plug-in surface): templates in `Template` order.
#[pyfunction]
#[pyo3(name = "_phase_file", signature = (profile, lead, templates, keys))]
pub(crate) fn phase_file(
    profile: String,
    lead: String,
    templates: [(String, String, Vec<u8>); 4],
    keys: Vec<(String, String)>,
) -> PyPhaseFile {
    let templates = templates.map(|(path, root, bytes)| TemplateFile { path, root, bytes });
    PyPhaseFile(PhaseFile {
        profile,
        lead,
        templates,
        keys,
    })
}

/// Framework-side constructor for a `Bead` (not on the plug-in surface).
///
/// `fields` sets the rest by name: `open_blockers` and `blocks_ids` take `list[str]`; `branch`, `stack_bead`,
/// `sprint`, `phase` take `str`; `checked_bead` takes `str | None`; `stack` takes `Stack | None`.
#[pyfunction]
#[pyo3(name = "_bead", signature = (id, status, stage, assignee=None, **fields))]
pub(crate) fn bead(
    id: String,
    status: PyStatus,
    stage: PyStage,
    assignee: Option<String>,
    fields: Option<&Bound<'_, PyDict>>,
) -> PyResult<PyBead> {
    let mut bead = Bead {
        id,
        status: status.into(),
        stage: stage.into(),
        assignee,
        open_blockers: Vec::new(),
        blocks_ids: Vec::new(),
        branch: String::new(),
        stack_bead: String::new(),
        sprint: String::new(),
        phase: String::new(),
        checked_bead: None,
        stack: None,
    };
    for (key, value) in fields.into_iter().flat_map(|f| f.iter()) {
        match key.extract::<String>()?.as_str() {
            "open_blockers" => bead.open_blockers = value.extract()?,
            "blocks_ids" => bead.blocks_ids = value.extract()?,
            "branch" => bead.branch = value.extract()?,
            "stack_bead" => bead.stack_bead = value.extract()?,
            "sprint" => bead.sprint = value.extract()?,
            "phase" => bead.phase = value.extract()?,
            "checked_bead" => bead.checked_bead = value.extract()?,
            "stack" => bead.stack = value.extract::<Option<PyStack>>()?.map(|s| s.0),
            other => {
                return Err(PyTypeError::new_err(format!(
                    "_bead() got an unexpected field {other:?}"
                )))
            }
        }
    }
    Ok(PyBead(bead))
}
