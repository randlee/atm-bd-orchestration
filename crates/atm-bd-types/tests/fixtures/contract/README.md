# Contract stub snapshots

These files are snapshots of the approved `atm-core` Phase BO contract and are used only by
`tests/python/test_stubs.py` to check contract parity. They are not an editable implementation
source.

Within `atm-bd-types`, `src/python/stub.rs` is the sole owner of the static stub signatures. The
committed pair in `stubs/` is generated from that Rust source. The Python protocol declarations are
runtime objects; `test_stubs.py` checks their surfaces against the generated stubs. When the approved
contract changes, update the Rust source and generated outputs together, then refresh these snapshots
from the approved contract for the parity check.
