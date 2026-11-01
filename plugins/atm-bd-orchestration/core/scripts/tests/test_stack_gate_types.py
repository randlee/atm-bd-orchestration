# pyright: strict
from atm_bd_types import StackGateResult
from stack_gate_types import FakeStackGate, StackGate


def test_fake_stack_gate_records_inputs_and_returns_controlled_result() -> None:
    result = StackGateResult.NotStacked("main", "develop")
    fake = FakeStackGate(result)
    gate: StackGate = fake
    assert gate.check("develop", "feature", "123", "main") is result
    assert fake.calls == [("develop", "feature", "123", "main", "origin")]
