# ZMFH

ZMFH is a Python import governance layer.

Goals:
- Auto-apply on install (no user code changes)
- Fail-open by default: ZMFH must not break Python or user projects
- Clear diagnostics when enabled

Quick start:
- Install: `pip install zmfh`
- Disable: `ZMFH_DISABLE=1`
- Diagnostics: `ZMFH_DIAG=1` then run `python -m zmfh doctor`

Status:
- v1.0.0: Stable import governance core (auto-apply, policy enforcement, deletion diagnostics).
