from atm_bd_core.reported import reported_keys
from atm_bd_types import FactKind


def test_reported_keys(tmp_path):
    assert reported_keys(tmp_path) == ([], None)
    path = tmp_path / "reported-keys.json"
    path.write_text('["sent"]', encoding="utf-8")
    assert reported_keys(tmp_path) == (["sent"], None)
    path.write_text('[123]', encoding="utf-8")
    value, error = reported_keys(tmp_path)
    assert error is not None
    assert value is None and error.kind == FactKind.REPORTED_KEYS
