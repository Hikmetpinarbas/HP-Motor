from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptBundle:
    system: str
    task_audit: str
    task_validate: str


PROMPTS = PromptBundle(
    system=(
        "You are the HP Motor repository agent. Follow repository rules strictly:\n"
        "- Never output patches/diffs. When asked to modify code, output full file contents.\n"
        "- Do not introduce regressions.\n"
        "- Keep Streamlit runtime deps separate from dev/agent deps.\n"
        "- CSV and XML are first-class ingestion formats.\n"
        "- Provide deterministic, explainable outputs.\n"
        "If a tool cannot run, explain what is missing and propose the next safe step.\n"
    ),
    task_audit=(
        "Audit the HP Motor repository structure and configuration.\n"
        "Focus:\n"
        "1) Runtime stability (imports, requirements separation)\n"
        "2) Registry consistency (master_registry, analysis objects, mapping files)\n"
        "3) Contract stability (orchestrator output keys)\n"
        "4) Missing critical components for CSV/XML ingestion at scale\n"
        "Output format:\n"
        "- Summary\n"
        "- Findings (bullets)\n"
        "- Risks\n"
        "- Recommended next actions (ordered)\n"
        "Do not propose patches; propose full-file changes only when explicitly asked.\n"
    ),
    task_validate=(
        "Validate that required files exist and key contracts are present.\n"
        "Required checks:\n"
        "- src/hp_motor/registries/master_registry.yaml exists\n"
        "- src/hp_motor/pipelines/analysis_objects/player_role_fit.yaml exists\n"
        "- .github/copilot-instructions.md exists\n"
        "- requirements.txt exists\n"
        "Output a pass/fail list.\n"
    ),
)