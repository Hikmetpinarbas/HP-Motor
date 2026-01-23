from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from tools.copilot_sdk_agent.auditor.report_schema import AuditReport, Finding, derive_status


def _safe_read_text(p: Path, limit: int = 250_000) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")[:limit]


def _load_yaml(p: Path) -> Optional[Dict[str, Any]]:
    if not p.exists():
        return None
    try:
        return yaml.safe_load(_safe_read_text(p)) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def _list_yaml_files(dir_path: Path) -> List[Path]:
    if not dir_path.exists():
        return []
    out: List[Path] = []
    for ext in ("*.yml", "*.yaml"):
        out.extend(sorted(dir_path.glob(ext)))
    return out


def _guess_registry_metrics(reg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    if reg is None:
        return [], "missing"

    if isinstance(reg, list):
        return [x for x in reg if isinstance(x, dict)], "root(list)"

    if isinstance(reg.get("metrics"), list):
        return [x for x in reg["metrics"] if isinstance(x, dict)], "metrics"

    r = reg.get("registry")
    if isinstance(r, dict) and isinstance(r.get("metrics"), list):
        return [x for x in r["metrics"] if isinstance(x, dict)], "registry.metrics"

    return [], "unknown"


def _metric_id(m: Dict[str, Any]) -> Optional[str]:
    for k in ("metric_id", "id", "key", "name_id"):
        v = m.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _extract_metric_refs_from_ao(ao: Dict[str, Any]) -> List[str]:
    """
    Supports both:
      - ao.metric_bundle: [metric_id...]
      - ao.deliverables.required_metrics: [metric_id...]
    """
    refs: List[str] = []

    if not isinstance(ao, dict):
        return refs

    mb = ao.get("metric_bundle")
    if isinstance(mb, list):
        refs.extend([str(x).strip() for x in mb if str(x).strip()])

    deliver = ao.get("deliverables")
    if isinstance(deliver, dict):
        rm = deliver.get("required_metrics")
        if isinstance(rm, list):
            refs.extend([str(x).strip() for x in rm if str(x).strip()])

    # uniq preserve order
    seen = set()
    out = []
    for r in refs:
        if r not in seen:
            out.append(r)
            seen.add(r)
    return out


def _extract_plot_ids_from_ao(ao: Dict[str, Any]) -> List[str]:
    if not isinstance(ao, dict):
        return []
    deliver = ao.get("deliverables")
    if not isinstance(deliver, dict):
        return []
    plots = deliver.get("plots")
    if isinstance(plots, list):
        return [str(x).strip() for x in plots if str(x).strip()]
    return []


class RegistryAuditor:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.master_registry_path = repo_root / "src" / "hp_motor" / "registries" / "master_registry.yaml"
        self.analysis_objects_dir = repo_root / "src" / "hp_motor" / "pipelines" / "analysis_objects"
        self.mappings_dir = repo_root / "src" / "hp_motor" / "registries" / "mappings"

    def run(self) -> AuditReport:
        rid = f"registry_audit_{int(time.time())}"
        findings: List[Finding] = []

        if not self.master_registry_path.exists():
            findings.append(
                Finding(
                    code="REG_MISSING_MASTER",
                    severity="ERROR",
                    title="master_registry.yaml missing",
                    detail=f"Expected at: {self.master_registry_path.as_posix()}",
                    file=self.master_registry_path.as_posix(),
                )
            )

        if not self.analysis_objects_dir.exists():
            findings.append(
                Finding(
                    code="AO_DIR_MISSING",
                    severity="ERROR",
                    title="analysis_objects directory missing",
                    detail=f"Expected at: {self.analysis_objects_dir.as_posix()}",
                    file=self.analysis_objects_dir.as_posix(),
                )
            )

        reg = _load_yaml(self.master_registry_path) if self.master_registry_path.exists() else None
        if isinstance(reg, dict) and "__parse_error__" in reg:
            findings.append(
                Finding(
                    code="REG_PARSE_ERROR",
                    severity="ERROR",
                    title="master_registry.yaml cannot be parsed",
                    detail=str(reg.get("__parse_error__")),
                    file=self.master_registry_path.as_posix(),
                )
            )
            reg = None

        metrics, metrics_loc = _guess_registry_metrics(reg or {})
        if reg is not None and not metrics:
            findings.append(
                Finding(
                    code="REG_NO_METRICS",
                    severity="ERROR",
                    title="No metrics found in master registry",
                    detail=f"Could not find metrics list. Location guess: {metrics_loc}",
                    file=self.master_registry_path.as_posix(),
                )
            )

        metric_ids: List[str] = []
        missing_id_count = 0
        field_gaps = 0

        for m in metrics:
            mid = _metric_id(m)
            if not mid:
                missing_id_count += 1
                continue
            metric_ids.append(mid)

            if not m.get("label") and not m.get("name"):
                field_gaps += 1
            if not m.get("description"):
                field_gaps += 1

        dupes = sorted({x for x in metric_ids if metric_ids.count(x) > 1})
        if dupes:
            findings.append(
                Finding(
                    code="REG_DUP_METRIC_ID",
                    severity="ERROR",
                    title="Duplicate metric_id values",
                    detail=f"Duplicates: {', '.join(dupes[:30])}" + (" ..." if len(dupes) > 30 else ""),
                    file=self.master_registry_path.as_posix(),
                )
            )

        if missing_id_count > 0:
            findings.append(
                Finding(
                    code="REG_METRIC_ID_MISSING",
                    severity="WARN",
                    title="Some metrics are missing metric_id",
                    detail=f"{missing_id_count} metric entries have no metric_id/id/key.",
                    file=self.master_registry_path.as_posix(),
                )
            )

        if field_gaps > 0:
            findings.append(
                Finding(
                    code="REG_METRIC_FIELDS_GAPS",
                    severity="INFO",
                    title="Some metrics lack label/description",
                    detail=f"Detected {field_gaps} missing label/name/description fields across metrics (soft schema).",
                    file=self.master_registry_path.as_posix(),
                )
            )

        metric_id_set = set(metric_ids)

        ao_files = _list_yaml_files(self.analysis_objects_dir) if self.analysis_objects_dir.exists() else []
        if not ao_files:
            findings.append(
                Finding(
                    code="AO_NONE",
                    severity="WARN",
                    title="No analysis objects found",
                    detail=f"No YAML files in {self.analysis_objects_dir.as_posix()}",
                    file=self.analysis_objects_dir.as_posix(),
                )
            )

        ao_metric_refs_total = 0
        ao_missing_metric_refs: Dict[str, List[str]] = {}
        ao_plot_ids_total = 0

        for p in ao_files:
            ao = _load_yaml(p)
            if isinstance(ao, dict) and "__parse_error__" in (ao or {}):
                findings.append(
                    Finding(
                        code="AO_PARSE_ERROR",
                        severity="ERROR",
                        title="Analysis object YAML cannot be parsed",
                        detail=str((ao or {}).get("__parse_error__")),
                        file=p.as_posix(),
                    )
                )
                continue

            metric_refs = _extract_metric_refs_from_ao(ao or {})
            ao_metric_refs_total += len(metric_refs)

            missing = [m for m in metric_refs if m not in metric_id_set]
            if missing:
                ao_missing_metric_refs[p.name] = missing

            plot_ids = _extract_plot_ids_from_ao(ao or {})
            ao_plot_ids_total += len(plot_ids)

        if ao_missing_metric_refs:
            first_key = next(iter(ao_missing_metric_refs.keys()))
            sample = ao_missing_metric_refs[first_key][:15]
            findings.append(
                Finding(
                    code="AO_REF_UNKNOWN_METRIC",
                    severity="ERROR",
                    title="Analysis Objects reference unknown metric_ids",
                    detail=(
                        f"{len(ao_missing_metric_refs)} AO file(s) reference missing metrics. "
                        f"Example: {first_key} -> {', '.join(sample)}"
                        + (" ..." if len(ao_missing_metric_refs[first_key]) > 15 else "")
                    ),
                    file=self.analysis_objects_dir.as_posix(),
                )
            )

        mapping_files = _list_yaml_files(self.mappings_dir) if self.mappings_dir.exists() else []
        if not mapping_files:
            findings.append(
                Finding(
                    code="MAP_NONE",
                    severity="WARN",
                    title="No provider mapping files detected",
                    detail=f"No YAML files found under {self.mappings_dir.as_posix()}",
                    file=self.mappings_dir.as_posix(),
                )
            )

        status = derive_status(findings)
        summary = (
            f"Registry audit complete. metrics={len(metric_ids)}, analysis_objects={len(ao_files)}, "
            f"ao_metric_refs={ao_metric_refs_total}, plots_in_aos={ao_plot_ids_total}. status={status}."
        )

        report = AuditReport(
            report_id=rid,
            status=status,
            summary=summary,
            stats={
                "metrics_count": len(metric_ids),
                "analysis_object_count": len(ao_files),
                "ao_metric_refs_total": ao_metric_refs_total,
                "ao_plot_ids_total": ao_plot_ids_total,
                "mapping_file_count": len(mapping_files),
                "master_registry_location_guess": metrics_loc,
            },
            findings=findings,
            risks=[],
            next_actions=[],
        )
        return report

    def render_markdown(self, report: AuditReport) -> str:
        lines: List[str] = []
        lines.append("# HP Motor Registry Audit")
        lines.append("")
        lines.append(f"- **report_id:** `{report.report_id}`")
        lines.append(f"- **status:** `{report.status}`")
        lines.append(f"- **summary:** {report.summary}")
        lines.append("")
        lines.append("## Stats")
        for k, v in (report.stats or {}).items():
            lines.append(f"- **{k}:** {v}")
        lines.append("")
        lines.append("## Findings")
        if not report.findings:
            lines.append("- (none)")
        else:
            for f in report.findings:
                loc = f" ({f.file})" if f.file else ""
                lines.append(f"- **[{f.severity}] {f.code}** — {f.title}{loc}")
                lines.append(f"  - {f.detail}")
        lines.append("")
        return "\n".join(lines)

    def write_artifacts(self, report: AuditReport) -> AuditReport:
        reports_dir = self.repo_root / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        json_path = reports_dir / f"{report.report_id}.json"
        md_path = reports_dir / f"{report.report_id}.md"

        json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self.render_markdown(report), encoding="utf-8")

        report.artifacts["json"] = json_path.as_posix()
        report.artifacts["md"] = md_path.as_posix()
        return report