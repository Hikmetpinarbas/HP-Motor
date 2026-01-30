import argparse
import json
from pathlib import Path

from hp_motor.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hp_motor", description="HP Motor Lite Core CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Run lite-core pipeline and output report json")
    r.add_argument("--events", required=True, help="Path to events (.json/.jsonl/.csv)")
    r.add_argument("--out", required=True, help="Output report path (json)")
    r.add_argument("--vendor", default="generic", help="Vendor mapping key")
    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "run":
        report = run_pipeline(Path(args.events), vendor=args.vendor)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: wrote {out}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
