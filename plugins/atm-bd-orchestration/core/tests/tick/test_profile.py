"""Profile, policy and cron loading refuse with the contract ErrorIds."""
from pathlib import Path

import pytest
from atm_bd_core.profile import load_cron, load_policy, load_profile
from atm_bd_core.tick import tick
from atm_bd_types import ErrorId, Hook, Params, PhaseFacts, Refusal, Template
from atm_bd_core import Policy
from atm_bd_types._native import _phase_file

from .helpers import Collector, Runner, make_primary, make_profile, ports, refusal_id


def test_contract_profile_loads_with_typed_hooks_and_templates(tmp_path):
    loaded = load_profile(make_profile(tmp_path))
    assert not isinstance(loaded, Refusal)
    assert loaded.profile.name == "lite" and loaded.profile.stages == ["dev", "qa", "land"]
    assert set(loaded.profile.hooks) == {Hook.TASK_ASSIGN, Hook.TASK_START, Hook.TASK_CLOSE}
    assert set(loaded.profile.templates) == {Template.REFUSE, Template.DEV_CLOSE, Template.QA_PASS,
                                             Template.QA_FINDINGS, Template.LAND_CLOSE}
    policy = load_policy(loaded)
    assert isinstance(policy, Policy) and policy.params.text("qa_agent") == "qa-agent"
    cron = load_cron(loaded)
    assert cron is not None and not isinstance(cron, Refusal)


def test_make_profile_tracks_shipped_inputs(tmp_path, monkeypatch):
    from . import helpers

    shipped = tmp_path / "shipped"
    (shipped / "scripts").mkdir(parents=True)
    (shipped / "profile.toml").write_text('name = "first"\n', encoding="utf-8")
    (shipped / "scripts/atm-bd-cron.py").write_text('MARKER = "first"\n', encoding="utf-8")
    monkeypatch.setattr(helpers, "SHIPPED", shipped)
    for marker in ("first", "second"):
        (shipped / "profile.toml").write_text(f'name = "{marker}"\n', encoding="utf-8")
        (shipped / "scripts/atm-bd-cron.py").write_text(f'MARKER = "{marker}"\n', encoding="utf-8")
        profile = make_profile(tmp_path / marker)
        assert profile.read_text(encoding="utf-8") == f'name = "{marker}"\n'
        assert (profile.parent / "scripts/atm-bd-cron.py").read_text(encoding="utf-8") == f'MARKER = "{marker}"\n'


@pytest.mark.parametrize("edit", [
    lambda p: p.unlink(),
    lambda p: p.write_text("name = [", encoding="utf-8"),
    lambda p: p.write_text(p.read_text(encoding="utf-8") + 'extra = "x"\n', encoding="utf-8"),
    lambda p: p.write_text(p.read_text(encoding="utf-8").replace('"task.close"', '"task.other"'), encoding="utf-8"),
    lambda p: (p.parent / "templates/qa-pass.md.j2").unlink(),
    lambda p: p.write_text(p.read_text(encoding="utf-8").replace('stages = ["dev", "qa", "land"]', "stages = []"),
                           encoding="utf-8"),
], ids=["missing", "malformed", "unknown-key", "unknown-hook", "missing-template", "no-stages"])
def test_bad_profile_refuses_profile_mismatch(tmp_path, edit):
    path = make_profile(tmp_path)
    edit(path)
    assert refusal_id(load_profile(path)) == ErrorId.PROFILE_MISMATCH


@pytest.mark.parametrize("policy", [
    "[params\n", '[params]\nflag = true\n', '[params]\nlist = [1]\n', 'params = "x"\n', 'other = 1\n',
    'notify_template = "templates/missing.j2"\n',
], ids=["malformed", "bool", "array", "params-not-table", "unknown-key", "missing-notify-template"])
def test_bad_policy_refuses_policy_bad_params(tmp_path, policy):
    loaded = load_profile(make_profile(tmp_path))
    assert not isinstance(loaded, Refusal)
    (loaded.root / "policy.toml").write_text(policy, encoding="utf-8")
    refused = load_policy(loaded)
    assert isinstance(refused, Refusal) and refused.id == ErrorId.POLICY_BAD_PARAMS


def test_policy_naming_another_profile_refuses_profile_mismatch(tmp_path):
    loaded = load_profile(make_profile(tmp_path))
    assert not isinstance(loaded, Refusal)
    (loaded.root / "policy.toml").write_text('profile = "other"\n[params]\n', encoding="utf-8")
    refused = load_policy(loaded)
    assert isinstance(refused, Refusal) and refused.id == ErrorId.PROFILE_MISMATCH


@pytest.mark.parametrize("policy", [None, "[params\n"], ids=["missing", "malformed"])
def test_tick_refuses_policy_bad_params_before_collecting(tmp_path, policy):
    profile = make_profile(tmp_path)
    if policy is None:
        (profile.parent / "policy.toml").unlink()
    else:
        (profile.parent / "policy.toml").write_text(policy, encoding="utf-8")
    make_primary(tmp_path)
    collector, runner = Collector(), Runner()
    result = tick(profile, "bo", tmp_path / "primary", ports=ports(runner), now=1, collector=collector)
    assert isinstance(result, Refusal) and result.id == ErrorId.POLICY_BAD_PARAMS
    assert collector.calls == 0 and runner.calls == []


@pytest.mark.parametrize("script", ["raise RuntimeError('boom')\n", "x = 1\n", "def decide(:\n"],
                         ids=["raises", "no-decide", "syntax"])
def test_bad_cron_script_refuses_profile_mismatch(tmp_path, script):
    path = make_profile(tmp_path)
    (path.parent / "scripts/atm-bd-cron.py").write_text(script, encoding="utf-8")
    loaded = load_profile(path)
    assert not isinstance(loaded, Refusal)
    assert refusal_id(load_cron(loaded)) == ErrorId.PROFILE_MISMATCH


def test_host_source_names_no_profile():
    package = Path(__file__).resolve().parents[2] / "atm_bd_core"
    paths = [package / name for name in ("tick.py", "execute.py", "profile.py")]
    paths += [path for name in ("collect", "store") for path in (package / name).rglob("*.py")]
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for profile in ("lite", "orchestration", "quality-mgr", "qa_agent", "qa_template"):
            assert profile not in text, f"{path.relative_to(package)} names {profile!r}"


def test_shipped_lite_profile_loads():
    skill = Path(__file__).resolve().parents[3] / "skills/atm-bd-lite/profile.toml"
    loaded = load_profile(skill)
    assert not isinstance(loaded, Refusal), loaded
    policy = load_policy(loaded)
    assert isinstance(policy, Policy) and policy.params.text("qa_agent") == "quality-mgr"
    cron = load_cron(loaded)
    assert cron is not None and not isinstance(cron, Refusal)


TEMPLATES = [(f"/r/{n}", "/r", b"ok") for n in range(5)]


@pytest.mark.parametrize("body", ["return None", "return ['assign']"], ids=["not-a-list", "not-an-action"])
def test_decide_returning_non_actions_raises(tmp_path, body):
    path = make_profile(tmp_path)
    (path.parent / "scripts/atm-bd-cron.py").write_text(f"def decide(facts, params):\n    {body}\n", encoding="utf-8")
    loaded = load_profile(path)
    assert not isinstance(loaded, Refusal)
    cron = load_cron(loaded)
    assert cron is not None and not isinstance(cron, Refusal)
    with pytest.raises(TypeError, match="decide returned"):
        cron.decide(PhaseFacts("bo", 0, _phase_file("lite", "lead", TEMPLATES, [])), Params([]))


@pytest.mark.parametrize("entry", ['missing = "qa_agent"', 'qa_agent = "missing"'])
def test_startup_unknown_policy_param_refuses(tmp_path, entry):
    path = make_profile(tmp_path)
    source = path.read_text(encoding="utf-8").split("\n[startup]", 1)[0]
    path.write_text(f"{source}\n[startup]\n{entry}\n", encoding="utf-8")
    assert refusal_id(load_profile(path)) == ErrorId.PROFILE_MISMATCH
