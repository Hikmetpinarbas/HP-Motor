from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


def _bootstrap_repo_root() -> Path:
    """
    Ensures repo root is importable when running as `python main.py ...`.
    Keeps behavior deterministic on CI and mobile without relying on editable installs.
    """
    repo_root = Path(__file__).resolve().parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _run_tools_agent(subcommand: str) -> int:
    """
    Runs tools/copilot_sdk_agent/main.py in module-like mode.

    Equivalent to:
      python -m tools.copilot_sdk_agent.main <subcommand>
    """
    _bootstrap_repo_root()
    sys.argv = ["tools.copilot_sdk_agent.main", subcommand]
    runpy.run_module("tools.copilot_sdk_agent.main", run_name="__main__")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hp-motor",
        description="HP Motor utility runner (CI-safe).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="Run repo validation (contracts/import sanity).")
    sub.add_parser("registry-audit", help="Run registry audit and write reports/* artifacts.")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "validate":
        return _run_tools_agent("validate")

    if args.cmd == "registry-audit":
        return _run_tools_agent("registry-audit")

    raise SystemExit("Unknown command")


if __name__ == "__main__":
    raise SystemExit(main())