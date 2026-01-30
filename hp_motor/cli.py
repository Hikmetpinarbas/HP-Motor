import argparse, json
from pathlib import Path
from hp_motor.pipeline import run_pipeline

def main() -> int:
    p = argparse.ArgumentParser(prog="hp_motor", description="HP Motor Lite Core CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Run lite-core pipeline and output report json")
    r.add_argument("--events", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--vendor", default="generic")

    a = p.parse_args()
    if a.cmd == "run":
        rep = run_pipeline(Path(a.events), vendor=a.vendor)
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: wrote {out}")
        return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
