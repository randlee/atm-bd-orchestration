"""Plan-hardening payloads remain intact even when JSON contains a CDATA terminator."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG / "skills/atm-beads/scripts"))
import sc_render

TEMPLATES = PKG / "skills/plan-hardening"
CASES = [
    ("01-plan-scope-review.xml.j2", "reviewer_findings_json", "reviewer-findings-json"),
    ("02-sprint-scope-hardening.xml.j2", "reviewer_findings_json", "reviewer-findings-json"),
    ("02-sprint-scope-hardening.xml.j2", "previous_step_json", "required-input"),
    ("03-consistency-hardening.xml.j2", "reviewer_findings_json", "reviewer-findings-json"),
    ("03-consistency-hardening.xml.j2", "previous_step_json", "required-input"),
    ("plan-critical-review.xml.j2", "previous_step_json", "previous-step-json"),
]


def payload_element(rendered: str, element: str) -> ElementTree.Element:
    """Agents read the task body as text and its prose holds `<pseudo-tags>`; only the payload element is XML."""
    close = f"</{element}>"
    return ElementTree.fromstring(rendered[rendered.index(f"<{element}>"):rendered.index(close) + len(close)])


@pytest.mark.parametrize(("template", "variable", "element"), CASES)
def test_payload_round_trips_as_xml(template: str, variable: str, element: str) -> None:
    variables = json.loads((TEMPLATES / "examples/plan-hardening-vars.example.json").read_text())
    variables.update(commit="abc123", review_focus="scope", review_questions="questions")
    payload = json.dumps({"finding": "before ]]> after & <context>"})
    variables[variable] = payload
    rendered = sc_render.render(TEMPLATES / template, variables)
    assert payload in "".join(payload_element(rendered, element).itertext())
    assert not re.search(r"&(lt|gt|amp|quot);", rendered)


def test_all_plugin_cdata_interpolations_use_the_escape_filter() -> None:
    unescaped = []
    for template in PKG.rglob("*.j2"):
        text = template.read_text(encoding="utf-8")
        for block in re.finditer(r"<!\[CDATA\[(.*?)\]\]>", text, re.DOTALL):
            for expression in re.finditer(r"{{\s*(.*?)\s*}}", block.group(1), re.DOTALL):
                if "cdata_escape" not in expression.group(1):
                    line = text.count("\n", 0, block.start(1) + expression.start()) + 1
                    unescaped.append(f"{template.relative_to(PKG)}:{line}: {expression.group(1)}")
    assert not unescaped, "\n".join(unescaped)


@pytest.mark.parametrize(("template", "variable", "element"), CASES)
def test_unescaped_payload_is_rejected_by_xml_parser(
    tmp_path: Path, template: str, variable: str, element: str
) -> None:
    variables = json.loads((TEMPLATES / "examples/plan-hardening-vars.example.json").read_text())
    variables.update(commit="abc123", review_focus="scope", review_questions="questions")
    variables[variable] = json.dumps({"finding": "before ]]> after & <context>"})
    source = (TEMPLATES / template).read_text(encoding="utf-8")
    escaped = "{{ " + variable + " | cdata_escape }}"
    assert escaped in source
    unsafe_template = tmp_path / template
    unsafe_template.write_text(source.replace(escaped, "{{ " + variable + " }}"), encoding="utf-8")
    with pytest.raises(ElementTree.ParseError):
        payload_element(sc_render.render(unsafe_template, variables), element)
