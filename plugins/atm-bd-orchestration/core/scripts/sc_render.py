# pyright: strict
"""Render one template file with the sc-compose Python wheel.

Scripts and tests render through `render()` instead of running the
`sc-compose render` CLI: no var files, no stdout parsing, and the template's
own directory is the confining root, so the result never depends on the
caller's working directory. The wheel and the CLI are the same version, in the
`sc-compose >=` range in the package manifest.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import sc_compose
from atm_bd_types import Error, ErrorKind, Profile
from phase_profile import require_profile
from result import Err, Ok, Result

RenderError = sc_compose.ScComposeError


def render(template: str | Path, variables: Mapping[str, Any]) -> str:
    """The rendered text, newline-terminated as `sc-compose render` prints it.

    Always strict (`--strict`); there is no lenient render. A referenced
    variable that is missing or undeclared raises, naming the variable and the
    template. A `.json` template's output must parse, as the CLI's checked render requires;
    the wheel does not check it (sc-compose#787; delete this check when it does). Raises
    `RenderError`; `error_text(exc)` is its message.
    """
    path = Path(template).resolve()
    render_variables = dict(variables)
    # Existing templates need no provider config. A provider-using template declares
    # the provider variable in its front matter, so strict render still rejects typos.
    if "provider." in path.read_text(encoding="utf-8") and "provider" not in render_variables:
        import repo_config
        from providers import render_context
        from result import Err
        try:
            config = repo_config.load()
        except repo_config.ConfigNotFound:
            config = {"provider": "github"}
        provider = render_context(config)
        if isinstance(provider, Err):
            raise sc_compose.ScRenderError(provider.error.message)
        render_variables["provider"] = provider.value
    request = sc_compose.ComposeRequest(
        str(path.parent), sc_compose.ComposeMode.file(str(path)), vars_input=render_variables,
        policy=sc_compose.ComposePolicy(strict_undeclared_variables=True))
    text = sc_compose.compose_file(request).rendered_text
    if path.name.removesuffix(".j2").endswith(".json"):
        try:
            json.loads(text)
        except ValueError as exc:
            raise sc_compose.ScRenderError(
                f"ERR_RENDER_JSON_MALFORMED: rendered output failed the checked-render contract: {exc}") from exc
    return text if text.endswith("\n") else text + "\n"


def error_text(exc: BaseException) -> str:
    """The sc-compose diagnostic (`ERR_...: ... | location=...`) of a `RenderError`."""
    return str(exc.args[0]) if exc.args else str(exc)


def render_dispatch(template: str | Path, variables: Mapping[str, Any], phase_file: Path,
                    expected: Profile) -> Result[str]:
    """Gate a dispatch on its phase profile before reading or rendering its template."""
    profile = require_profile(phase_file, expected)
    if isinstance(profile, Err):
        return profile
    try:
        return Ok(render(template, variables))
    except (RenderError, OSError) as exc:
        return Err(Error(ErrorKind.PARSE_FAILED, error_text(exc), "Repair the dispatch template or its variables."))
