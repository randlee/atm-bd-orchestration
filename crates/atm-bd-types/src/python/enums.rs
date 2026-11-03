//! Python enums for the contract's enums: one pyclass per Rust enum, converted both ways, stub text generated.
use pyo3::prelude::*;

use super::conv::Conv;
use super::hook::{PyBead, PyHookRequest};
use super::{either, enum_stub};
use crate::framework::{ActionKind, OutcomeKind};
use crate::plugin::{
    AssignTransition, CheckState, CloseTransition, ErrorId, FactKind, Hook, PatchKind, Stage,
    StartTransition, Status, TaskState, Template,
};

/// Declares `$py`, the Python enum `$name` for the Rust enum `$rust`, member for member.
///
/// Members are `Rust = "PYTHON"`, or `Py => Rust = "PYTHON"` when the pyclass member needs another Rust name.
/// `stub` is extra stub text appended to the class body (a `select` signature); extra pymethods follow the members.
macro_rules! py_enum {
    (
        $py:ident = $rust:ident as $name:literal in $module:literal, doc $doc:expr, stub $extra:expr;
        { $($var:ident = $pyname:literal),+ $(,)? }
        $($methods:tt)*
    ) => {
        py_enum! {
            $py = $rust as $name in $module, doc $doc, stub $extra;
            { $($var => $var = $pyname),+ }
            $($methods)*
        }
    };
    (
        $py:ident = $rust:ident as $name:literal in $module:literal, doc $doc:expr, stub $extra:expr;
        { $($var:ident => $rvar:ident = $pyname:literal),+ $(,)? }
        $($methods:tt)*
    ) => {
        #[pyclass(eq, hash, frozen, from_py_object, name = $name, module = $module)]
        #[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
        pub(crate) enum $py { $(#[pyo3(name = $pyname)] $var),+ }

        impl From<$py> for $rust {
            fn from(value: $py) -> Self { match value { $($py::$var => $rust::$rvar),+ } }
        }

        impl From<$rust> for $py {
            fn from(value: $rust) -> Self { match value { $($rust::$rvar => $py::$var),+ } }
        }

        impl Conv for $rust {
            type Py = $py;
            fn py_type() -> String { $name.to_owned() }
            fn to_py(&self) -> $py { (*self).into() }
            fn from_py(value: $py) -> PyResult<Self> { Ok(value.into()) }
        }

        impl $py {
            /// This enum's stub text.
            pub(crate) fn stub() -> String { enum_stub($name, $doc, &[$($pyname),+], $extra) }
        }

        #[pymethods]
        impl $py {
            /// The member name, as `enum.Enum.name`.
            #[getter]
            fn name(&self) -> &'static str { match self { $(Self::$var => $pyname),+ } }

            fn __repr__(&self) -> String { format!("{}.{}", $name, self.name()) }

            $($methods)*
        }
    };
}

py_enum! {
    PyStatus = Status as "Status" in "atm_bd_types", doc None,
    stub "    @staticmethod\n    def parse(value: str) -> Status | None: ...\n    def as_str(self) -> str: ...\n";
    { Open = "OPEN", InProgress = "IN_PROGRESS", Blocked = "BLOCKED", Deferred = "DEFERRED", Closed = "CLOSED" }
    #[staticmethod]
    fn parse(value: &str) -> Option<Self> { Status::parse(value).map(Into::into) }
    fn as_str(&self) -> &'static str { Status::from(*self).as_str() }
}

py_enum! {
    PyStage = Stage as "Stage" in "atm_bd_types", doc Some("The bead's stage label; unknown labels are OTHER."),
    stub "    @staticmethod\n    def parse(value: str) -> Stage: ...\n    def as_str(self) -> str: ...\n";
    { Dev = "DEV", Fix = "FIX", Qa = "QA", Land = "LAND", Stack = "STACK", Other = "OTHER" }
    #[staticmethod]
    fn parse(value: &str) -> Self { Stage::parse(value).into() }
    fn as_str(&self) -> &'static str { Stage::from(*self).as_str() }
}

py_enum! {
    PyPatchKind = PatchKind as "PatchKind" in "atm_bd_types", doc Some("The guarded patch operation."),
    stub "    def as_str(self) -> str: ...\n";
    { Assign = "ASSIGN", Start = "START", Reopen = "REOPEN", Close = "CLOSE" }
    fn as_str(&self) -> &'static str { PatchKind::from(*self).as_str() }
}

py_enum! {
    PyAssignTransition = AssignTransition as "AssignTransition" in "atm_bd_types", doc None,
    stub "    @staticmethod\n    def select(status: Status, assignee: str | None, wanted: str) -> AssignTransition: ...\n";
    { AssignSame = "ASSIGN_SAME", Assign = "ASSIGN", AssignClosed = "ASSIGN_CLOSED", AssignNotReady = "ASSIGN_NOT_READY" }

    /// `AssignTransition::select`.
    #[staticmethod]
    #[pyo3(signature = (status, assignee, wanted))]
    fn select(status: PyStatus, assignee: Option<String>, wanted: &str) -> Self {
        AssignTransition::select(status.into(), assignee.as_deref(), wanted).into()
    }
}

py_enum! {
    PyStartTransition = StartTransition as "StartTransition" in "atm_bd_types", doc None,
    stub "    @staticmethod\n    def select(status: Status) -> StartTransition: ...\n";
    { Start = "START", StartAgain = "START_AGAIN", StartClosed = "START_CLOSED", StartNotReady = "START_NOT_READY" }

    /// `StartTransition::select`.
    #[staticmethod]
    fn select(status: PyStatus) -> Self {
        StartTransition::select(status.into()).into()
    }
}

py_enum! {
    PyCloseTransition = CloseTransition as "CloseTransition" in "atm_bd_types", doc None,
    stub concat!(
        "    @staticmethod\n    def select(req: HookRequest, bead: Bead) -> CloseTransition | Refusal:\n",
        "        r\"\"\"outcome x stage (x verdict kind for QA); REQUEST_INVALID / QA_VERDICT when they do not decode.\"\"\"\n",
    );
    { GiveBack = "GIVE_BACK", WorkClose = "WORK_CLOSE", QaPass = "QA_PASS", QaFindings = "QA_FINDINGS", Land = "LAND" }

    /// `CloseTransition::select`: a transition, or the refusal when outcome or verdict do not decode.
    #[staticmethod]
    fn select<'py>(
        py: Python<'py>, req: PyRef<'py, PyHookRequest>, bead: PyRef<'py, PyBead>,
    ) -> PyResult<Bound<'py, PyAny>> {
        either(py, CloseTransition::select(&req.0, &bead.0).map(PyCloseTransition::from))
    }
}

py_enum! {
    PyTemplate = Template as "Template" in "atm_bd_types", doc None, stub "";
    { Refuse = "REFUSE", DevClose = "DEV_CLOSE", QaPass = "QA_PASS", QaFindings = "QA_FINDINGS", LandClose = "LAND_CLOSE" }
}

py_enum! {
    PyErrorId = ErrorId as "ErrorId" in "atm_bd_types", doc None, stub "";
    {
        RequestInvalid = "REQUEST_INVALID", PhaseUnreadable = "PHASE_UNREADABLE", ProfileMismatch = "PROFILE_MISMATCH",
        CacheUnavailable = "CACHE_UNAVAILABLE", BeadNotFound = "BEAD_NOT_FOUND", BeadNotReady = "BEAD_NOT_READY",
        BeadClosed = "BEAD_CLOSED", BeadRaced = "BEAD_RACED", AssignNotLead = "ASSIGN_NOT_LEAD",
        TaskNotAssignee = "TASK_NOT_ASSIGNEE", CloseReasonEmpty = "CLOSE_REASON_EMPTY",
        CloseReportNotInline = "CLOSE_REPORT_NOT_INLINE", StackNotRecorded = "STACK_NOT_RECORDED",
        QaVerdict = "QA_VERDICT", QaNotOnStack = "QA_NOT_ON_STACK", QaNothingToReview = "QA_NOTHING_TO_REVIEW",
        FindingsNotPoured = "FINDINGS_NOT_POURED", PolicyBadParams = "POLICY_BAD_PARAMS", LandEvidence = "LAND_EVIDENCE",
    }
}

py_enum! {
    PyHook = Hook as "Hook" in "atm_bd_types", doc Some("The ATM task hook a script is registered for."), stub "";
    { Assign => TaskAssign = "TASK_ASSIGN", Start => TaskStart = "TASK_START", Close => TaskClose = "TASK_CLOSE" }
}

py_enum! {
    PyFactKind = FactKind as "FactKind" in "atm_bd_types", doc None, stub "";
    {
        Tasks = "TASKS", TaskEvents = "TASK_EVENTS", ReportedKeys = "REPORTED_KEYS", RemoteBranches = "REMOTE_BRANCHES",
        Ancestry = "ANCESTRY", Beads = "BEADS", Ready = "READY", Stack = "STACK", TopChecks = "TOP_CHECKS",
        PrBases = "PR_BASES",
    }
}

py_enum! {
    PyTaskState = TaskState as "TaskState" in "atm_bd_types", doc None, stub "";
    { Assigned = "ASSIGNED", Active = "ACTIVE", Complete = "COMPLETE" }
}

py_enum! {
    PyCheckState = CheckState as "CheckState" in "atm_bd_types", doc None, stub "";
    { Passing = "PASSING", Failing = "FAILING", Pending = "PENDING", None = "NONE" }
}

py_enum! {
    PyActionKind = ActionKind as "ActionKind" in "atm_bd_core", doc None, stub "";
    { Assign = "ASSIGN", Report = "REPORT", Notify = "NOTIFY" }
}

py_enum! {
    PyOutcomeKind = OutcomeKind as "OutcomeKind" in "atm_bd_core", doc None, stub "";
    { Sent = "SENT", Failed = "FAILED", DryRun = "DRY_RUN" }
}
