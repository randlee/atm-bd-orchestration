//! The hook process's request and template context.
//!
//! The contract's Python surface omits two inputs the Rust wire needs: `HookAction.close(template, vars)` takes a
//! template path where Rust takes the request and the template's bytes, and `HookReply.to_json()` takes no hook
//! where Rust takes the hook that selects the fix table. A hook process serves exactly one request, so the
//! binding remembers the last parsed request and every template a `PhaseFile.template` call handed out.
use std::sync::{Mutex, PoisonError};

use crate::plugin::{Hook, HookRequest, TemplateFile};

struct HookContext {
    request: Option<HookRequest>,
    templates: Vec<TemplateFile>,
}

static CONTEXT: Mutex<HookContext> = Mutex::new(HookContext {
    request: None,
    templates: Vec::new(),
});

fn with<R>(f: impl FnOnce(&mut HookContext) -> R) -> R {
    // The context holds plain data; a panic elsewhere cannot leave it half-written, so a poisoned lock is usable.
    let mut guard = CONTEXT.lock().unwrap_or_else(PoisonError::into_inner);
    f(&mut guard)
}

/// Records the request `HookRequest.parse` decoded; later actions and replies answer it.
pub(crate) fn set_request(request: &HookRequest) {
    with(|c| c.request = Some(request.clone()));
}

/// The parsed request, if any.
pub(crate) fn request() -> Option<HookRequest> {
    with(|c| c.request.clone())
}

/// The hook of the parsed request; `None` (no fix table) when no request parsed.
pub(crate) fn hook() -> Option<Hook> {
    with(|c| c.request.as_ref().map(HookRequest::hook))
}

/// Remembers a template a phase file handed out, replacing an earlier one with the same path.
pub(crate) fn add_template(template: &TemplateFile) {
    with(|c| {
        c.templates.retain(|t| t.path != template.path);
        c.templates.push(template.clone());
    });
}

/// The template a phase file handed out under `path`.
pub(crate) fn template(path: &str) -> Option<TemplateFile> {
    with(|c| c.templates.iter().find(|t| t.path == path).cloned())
}
