//! Frozen Python records for the cron facts, actions, profile and the framework's view and tick types.
//!
//! Each record wraps its contract struct; the constructor takes every field in order, getters convert back, and
//! the stub (`@_record class ...`) is generated from the same field list and each field's `Conv::py_type`.
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

use super::conv::{conv_wrapper, Conv};
use super::record_stub;
use crate::framework::{
    ActionOutcome, CommandResult, Decision, PhaseView, Policy, TickResult, ViewAction, ViewRow,
    ViewSprint, ViewStep, ViewTask,
};
use crate::plugin::{
    Action, Ancestry, AssignVars, CollectError, Merged, ParamValue, Params, PhaseFacts, PrBase,
    Profile, RemoteBranch, ReviewTarget, StackFact, TaskEvents, TaskFact, TopChecks,
};

/// A record constructor's arguments, matched to its fields by position, then by name.
struct RecordArgs<'py> {
    record: &'static str,
    values: Vec<(&'static str, Option<Bound<'py, PyAny>>)>,
}

impl<'py> RecordArgs<'py> {
    fn new(
        record: &'static str,
        fields: &[&'static str],
        args: &Bound<'py, PyTuple>,
        kwargs: Option<&Bound<'py, PyDict>>,
    ) -> PyResult<Self> {
        if args.len() > fields.len() {
            return Err(PyTypeError::new_err(format!(
                "{record}() takes {} fields but {} were given",
                fields.len(),
                args.len()
            )));
        }
        let mut values: Vec<_> = fields.iter().map(|f| (*f, None)).collect();
        for (slot, value) in values.iter_mut().zip(args.iter()) {
            slot.1 = Some(value);
        }
        for (key, value) in kwargs.into_iter().flat_map(|k| k.iter()) {
            let key: String = key.extract()?;
            let slot = values
                .iter_mut()
                .find(|(field, _)| *field == key)
                .ok_or_else(|| {
                    PyTypeError::new_err(format!("{record}() got an unexpected field {key:?}"))
                })?;
            if slot.1.replace(value).is_some() {
                return Err(PyTypeError::new_err(format!(
                    "{record}() got field {key:?} twice"
                )));
            }
        }
        Ok(RecordArgs { record, values })
    }

    /// The value given for `field`, else `fallback`; a TypeError when neither exists or it does not convert.
    fn take<T>(&mut self, field: &str, fallback: Option<T>) -> PyResult<T>
    where
        T: for<'a> FromPyObject<'a, 'py>,
    {
        let given = self
            .values
            .iter_mut()
            .find(|(f, _)| *f == field)
            .and_then(|(_, v)| v.take());
        match (given, fallback) {
            (Some(value), _) => value.extract::<T>().map_err(|e| {
                let e: PyErr = e.into();
                PyTypeError::new_err(format!("{}() field {field:?}: {e}", self.record))
            }),
            (None, Some(fallback)) => Ok(fallback),
            (None, None) => Err(PyTypeError::new_err(format!(
                "{}() missing field {field:?}",
                self.record
            ))),
        }
    }
}

/// Declares `$py`, a frozen record pyclass named `$name` wrapping the struct `$rust`, field for field.
///
/// A field may carry a constructor default (`= rust_default => "stub default"`).
macro_rules! record {
    (
        $py:ident = $rust:ident as $name:literal in $module:literal, doc $doc:expr;
        { $($field:ident : $ty:ty $(= $default:expr => $stub_default:literal)?),+ $(,)? }
    ) => {
        #[pyclass(eq, frozen, from_py_object, name = $name, module = $module)]
        #[derive(Clone, Debug, PartialEq)]
        pub(crate) struct $py(pub(crate) $rust);

        conv_wrapper! { $rust => $py as $name }

        impl $py {
            /// This record's stub text.
            pub(crate) fn stub() -> String {
                record_stub($name, $doc, &[$((stringify!($field), <$ty as Conv>::py_type(), None $(.or(Some($stub_default)))?)),+])
            }
        }

        #[pymethods]
        impl $py {
            /// Takes every field in order, positionally or by name, like a frozen dataclass.
            #[new]
            #[pyo3(signature = (*args, **kwargs))]
            fn new(args: &Bound<'_, PyTuple>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
                let mut fields = RecordArgs::new($name, &[$(stringify!($field)),+], args, kwargs)?;
                Ok($py($rust { $($field: {
                    let fallback: Option<<$ty as Conv>::Py> = None $(.or(Some($default)))?;
                    <$ty as Conv>::from_py(fields.take(stringify!($field), fallback)?)?
                }),+ }))
            }

            $(
                #[getter]
                fn $field(&self) -> <$ty as Conv>::Py { Conv::to_py(&self.0.$field) }
            )+

            fn __repr__(&self) -> String { format!("{:?}", self.0) }
        }
    };
}

record! {
    PyTaskFact = TaskFact as "TaskFact" in "atm_bd_types", doc None;
    { task_id: String, assignee: String, state: crate::plugin::TaskState, bead_id: Option<String> }
}

record! {
    PyTaskEvents = TaskEvents as "TaskEvents" in "atm_bd_types", doc None;
    { task_id: String, reminders_since_start: u32, last_start: Option<i64> }
}

record! {
    PyRemoteBranch = RemoteBranch as "RemoteBranch" in "atm_bd_types", doc None;
    { name: String, head: crate::plugin::Sha }
}

record! {
    PyAncestry = Ancestry as "Ancestry" in "atm_bd_types", doc None;
    { below: String, above: String, is_ancestor: bool }
}

record! {
    PyStackFact = StackFact as "StackFact" in "atm_bd_types", doc None;
    { bead: crate::plugin::Bead, stack: crate::plugin::Stack, trunk: String, since: Option<i64> }
}

record! {
    PyTopChecks = TopChecks as "TopChecks" in "atm_bd_types", doc None;
    { head: crate::plugin::Sha, state: crate::plugin::CheckState }
}

record! {
    PyPrBase = PrBase as "PrBase" in "atm_bd_types", doc None;
    { pr: u64, base: String }
}

record! {
    PyCollectError = CollectError as "CollectError" in "atm_bd_types", doc Some("A failed read; its fact is None this tick.");
    { kind: crate::plugin::FactKind, argv: Vec<String>, message: String, fix: String }
}

record! {
    PyPhaseFacts = PhaseFacts as "PhaseFacts" in "atm_bd_types",
    doc Some("A fact is None when its read failed this tick (see errors).");
    {
        phase: String,
        now: i64,
        phase_file: crate::plugin::PhaseFile,
        tasks: Option<Vec<TaskFact>> = None => "None",
        task_events: Option<Vec<TaskEvents>> = None => "None",
        reported_keys: Option<Vec<String>> = None => "None",
        remote_branches: Option<Vec<RemoteBranch>> = None => "None",
        ancestry: Option<Vec<Ancestry>> = None => "None",
        beads: Option<Vec<crate::plugin::Bead>> = None => "None",
        ready: Option<Vec<crate::plugin::Bead>> = None => "None",
        stack: Option<StackFact> = None => "None",
        top_checks: Option<TopChecks> = None => "None",
        pr_bases: Option<Vec<PrBase>> = None => "None",
        errors: Vec<CollectError> = Vec::new() => "...",
    }
}

record! {
    PyMerged = Merged as "Merged" in "atm_bd_types", doc None;
    { sha: String }
}

record! {
    PyReviewTarget = ReviewTarget as "ReviewTarget" in "atm_bd_types", doc None;
    { repo: String, pr_number: u64, branch: String, commit: String }
}

record! {
    PyAssignVars = AssignVars as "AssignVars" in "atm_bd_types", doc None;
    { task_id: String, phase: String, profile: String, review: Option<ReviewTarget> = None => "None" }
}

/// `Action::Assign`'s fields, as the `Assign` record.
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct AssignFields {
    key: String,
    to: String,
    bead_id: String,
    template: String,
    vars: AssignVars,
}

/// `Action::Report`'s fields, as the `Report` record.
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct ReportFields {
    key: String,
    queue: String,
    bead_id: Option<String>,
    text: String,
}

/// `Action::Notify`'s fields, as the `Notify` record.
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct NotifyFields {
    to: String,
    keys: Vec<String>,
}

record! {
    PyAssign = AssignFields as "Assign" in "atm_bd_types", doc None;
    { key: String, to: String, bead_id: String, template: String, vars: AssignVars }
}

record! {
    PyReport = ReportFields as "Report" in "atm_bd_types",
    doc Some("A Report whose key is already in REPORTED_KEYS stays a view row only.");
    { key: String, queue: String, bead_id: Option<String>, text: String }
}

record! {
    PyNotify = NotifyFields as "Notify" in "atm_bd_types", doc None;
    { to: String, keys: Vec<String> }
}

/// `Assign | Report | Notify`, the Python face of `Action`.
#[derive(Clone, Debug, FromPyObject, IntoPyObject)]
pub(crate) enum PyAction {
    Assign(PyAssign),
    Report(PyReport),
    Notify(PyNotify),
}

impl Conv for Action {
    type Py = PyAction;
    fn py_type() -> String {
        "Action".to_owned()
    }
    fn to_py(&self) -> PyAction {
        match self.clone() {
            Action::Assign {
                key,
                to,
                bead_id,
                template,
                vars,
            } => PyAction::Assign(PyAssign(AssignFields {
                key,
                to,
                bead_id,
                template,
                vars,
            })),
            Action::Report {
                key,
                queue,
                bead_id,
                text,
            } => PyAction::Report(PyReport(ReportFields {
                key,
                queue,
                bead_id,
                text,
            })),
            Action::Notify { to, keys } => PyAction::Notify(PyNotify(NotifyFields { to, keys })),
        }
    }
    fn from_py(value: PyAction) -> PyResult<Self> {
        Ok(match value {
            PyAction::Assign(PyAssign(AssignFields {
                key,
                to,
                bead_id,
                template,
                vars,
            })) => Action::Assign {
                key,
                to,
                bead_id,
                template,
                vars,
            },
            PyAction::Report(PyReport(ReportFields {
                key,
                queue,
                bead_id,
                text,
            })) => Action::Report {
                key,
                queue,
                bead_id,
                text,
            },
            PyAction::Notify(PyNotify(NotifyFields { to, keys })) => Action::Notify { to, keys },
        })
    }
}

/// The `params` table of a profile's policy.toml.
#[pyclass(eq, frozen, from_py_object, name = "Params", module = "atm_bd_types")]
#[derive(Clone, Debug, PartialEq)]
pub(crate) struct PyParams(pub(crate) Params);

conv_wrapper! { Params => PyParams as "Params" }

pub(crate) const PARAMS_STUB: &str = r#"@typing.final
class Params:
    r"""The params table of the profile's policy.toml."""
    def __init__(self, values: list[tuple[str, builtins.int | str]]) -> None: ...
    def int(self, name: str) -> builtins.int | None: ...
    def text(self, name: str) -> str | None: ...
"#;

#[pymethods]
impl PyParams {
    /// Each value is an `int` or a `str`; anything else is a TypeError (POLICY_BAD_PARAMS is the policy loader's).
    #[new]
    fn new(values: Vec<(String, Bound<'_, PyAny>)>) -> PyResult<Self> {
        let values = values
            .into_iter()
            .map(|(name, value)| {
                let value = if let Ok(text) = value.extract::<String>() {
                    ParamValue::Text(text)
                } else if let Ok(int) = value.extract::<i64>() {
                    ParamValue::Int(int)
                } else {
                    return Err(PyTypeError::new_err(format!(
                        "param {name:?} is neither int nor str"
                    )));
                };
                Ok((name, value))
            })
            .collect::<PyResult<_>>()?;
        Ok(PyParams(Params { values }))
    }
    fn int(&self, name: &str) -> Option<i64> {
        self.0.int(name)
    }
    fn text(&self, name: &str) -> Option<&str> {
        self.0.text(name)
    }
    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

record! {
    PyProfile = Profile as "Profile" in "atm_bd_types",
    doc Some(concat!(
        "A plug-in's profile.toml: the team pipeline (stages in order), ATM hook -> script, templates, policy, ",
        "optional cron script. Paths relative to the manifest."
    ));
    {
        name: String,
        stages: Vec<String>,
        hooks: std::collections::BTreeMap<crate::plugin::Hook, String>,
        templates: std::collections::BTreeMap<crate::plugin::Template, String>,
        policy: String,
        cron: Option<String> = None => "None",
    }
}

record! {
    PyPolicy = Policy as "Policy" in "atm_bd_core",
    doc Some("policy.toml, loaded before any read: POLICY_BAD_PARAMS (a param neither int nor text), PROFILE_MISMATCH.");
    { profile: String, params: Params, notify_template: String }
}

record! {
    PyViewRow = ViewRow as "ViewRow" in "atm_bd_core", doc None;
    { queue: String, key: String, bead_id: Option<String>, text: String, since: Option<i64> }
}

record! {
    PyDecision = Decision as "Decision" in "atm_bd_core",
    doc Some("One tick's decide result after dedupe: actions to execute; Reports already sent stay rows only.");
    { actions: Vec<Action>, rows: Vec<ViewRow> }
}

record! {
    PyViewStep = ViewStep as "ViewStep" in "atm_bd_core", doc None;
    {
        bead_id: String,
        stage: crate::plugin::Stage,
        status: crate::plugin::Status,
        assignee: Option<String>,
        ready: bool,
    }
}

record! {
    PyViewSprint = ViewSprint as "ViewSprint" in "atm_bd_core", doc None;
    { id: String, title: String, status: crate::plugin::Status, depends_on: Vec<String>, steps: Vec<ViewStep> }
}

record! {
    PyViewTask = ViewTask as "ViewTask" in "atm_bd_core", doc None;
    { task_id: String, assignee: String, state: crate::plugin::TaskState, reminders: u32, since: Option<i64> }
}

record! {
    PyViewAction = ViewAction as "ViewAction" in "atm_bd_core", doc Some("outcome None: planned, not executed.");
    {
        kind: crate::framework::ActionKind,
        to: String,
        bead_id: Option<String>,
        key: String,
        outcome: Option<crate::framework::OutcomeKind>,
    }
}

record! {
    PyPhaseView = PhaseView as "PhaseView" in "atm_bd_core", doc None;
    {
        phase: String,
        root_id: String,
        root_closed: bool,
        lead: String,
        generated_at: i64,
        sprints: Vec<ViewSprint>,
        tasks: Vec<ViewTask>,
        rows: Vec<ViewRow>,
        actions: Vec<ViewAction>,
        top_ci: Option<crate::plugin::CheckState>,
        errors: Vec<CollectError>,
    }
}

record! {
    PyActionOutcome = ActionOutcome as "ActionOutcome" in "atm_bd_core", doc None;
    { action: Action, kind: crate::framework::OutcomeKind, failure: Option<crate::plugin::Refusal> }
}

record! {
    PyTickResult = TickResult as "TickResult" in "atm_bd_core", doc None;
    { facts: PhaseFacts, decision: Decision, view: PhaseView, outcomes: Vec<ActionOutcome> }
}

record! {
    PyCommandResult = CommandResult as "CommandResult" in "atm_bd_core", doc None;
    { code: i32, stdout: String, stderr: String }
}

/// The framework's ports: a `CommandRunner` and a `BeadsCache`, both Python objects.
#[pyclass(frozen, name = "Ports", module = "atm_bd_core")]
#[derive(Debug)]
pub(crate) struct PyPorts {
    #[pyo3(get)]
    runner: Py<PyAny>,
    #[pyo3(get)]
    cache: Py<PyAny>,
}

#[pymethods]
impl PyPorts {
    #[new]
    fn new(runner: Py<PyAny>, cache: Py<PyAny>) -> Self {
        PyPorts { runner, cache }
    }
}

impl PyPorts {
    /// The `Ports` record stub: its fields are the two protocol ports.
    pub(crate) fn stub() -> String {
        record_stub(
            "Ports",
            None,
            &[
                ("runner", "CommandRunner".to_owned(), None),
                ("cache", "BeadsCache".to_owned(), None),
            ],
        )
    }
}
