"""ZMFH CLI entrypoint."""
from __future__ import annotations


def _run_selftest_script(code: str, env: dict) -> tuple[int, str, str]:
    import tempfile, shutil, subprocess, sys
    from pathlib import Path
    td = tempfile.mkdtemp(prefix="zmfh_selftest_exec_")
    try:
        p = Path(td) / "t.py"
        p.write_text(code, encoding="utf-8")
        cp = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, env=env)
        return cp.returncode, cp.stdout, cp.stderr
    finally:
        shutil.rmtree(td, ignore_errors=True)


import argparse

from zmfh.cli.doctor import cmd_doctor
from zmfh.cli_config import cmd_config_find, cmd_config_show, cmd_config_validate, cmd_init
from zmfh.cli.policy_cmd import cmd_policy_check, cmd_policy_show, cmd_policy_validate
from zmfh.cli.selftest_cmd import cmd_selftest
from zmfh.cli.status_cmd import cmd_status
from zmfh.cli.trace_cmd import cmd_trace, cmd_trace_clear


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="zmfh")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Show health / configuration report")

    p_status = sub.add_parser("status", help="Show runtime status (JSON)")
    p_status.add_argument("--compact", action="store_true", help="Print compact JSON")

    p_policy = sub.add_parser("policy", help="Inspect / validate policy")
    sp = p_policy.add_subparsers(dest="policy_cmd", required=True)
    sp.add_parser("show", help="Print effective loaded policy")
    p_check = sp.add_parser("check", help="Explain how policy treats an import")
    p_check.add_argument("fullname", help="Module fullname, e.g. 'requests'")
    p_val = sp.add_parser("validate", help="Validate a policy JSON file")
    p_val.add_argument("path", help="Path to policy JSON")

    p_trace = sub.add_parser("trace", help="Show recent ZMFH events")
    p_trace.add_argument("--tail", type=int, default=50, help="Number of events/lines")
    p_trace.add_argument("--pretty", action="store_true", help="Pretty JSON output (in-memory)")
    p_trace.add_argument("--clear", action="store_true", help="Clear trace buffer/file")

    # config/init
p_cfg = sub.add_parser("config", help="config ops")
cfg_sub = p_cfg.add_subparsers(dest="config_cmd", required=True)
cfg_sub.add_parser("find", help="print discovered config path")
cfg_sub.add_parser("show", help="print merged config")
p_val2 = cfg_sub.add_parser("validate", help="validate config file")
p_val2.add_argument("path", nargs="?", default=None)
sub.add_parser("init", help="write ./.zmfh templates")

sub.add_parser("selftest", help="Run end-to-end smoke tests")


    args = parser.parse_args(argv)

    if args.cmd == "doctor":
        return cmd_doctor()

    if args.cmd == "status":
        return cmd_status(pretty=(not args.compact))

    if args.cmd == "policy":
        if args.policy_cmd == "show":
            return cmd_policy_show()
        if args.policy_cmd == "check":
            return cmd_policy_check(args.fullname)
        if args.policy_cmd == "validate":
            return cmd_policy_validate(args.path)
        return 2

    if args.cmd == "trace":
        if args.clear:
            return cmd_trace_clear()
        return cmd_trace(tail=int(args.tail), pretty=bool(args.pretty))

    if args.cmd == "selftest":
        return cmd_selftest()

    return 1
