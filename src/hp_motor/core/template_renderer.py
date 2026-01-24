from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


class TemplateRenderer:
    """
    Minimal placeholder renderer for HP templates.

    Contract:
      - Reads markdown templates from: src/hp_motor/templates/
      - Replaces tokens like {{token}} with provided values.
      - Never invents; caller must provide safe defaults for missing fields.
    """

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        if templates_dir is None:
            # hp_motor/core/template_renderer.py -> hp_motor/templates
            self.templates_dir = Path(__file__).resolve().parent.parent / "templates"
        else:
            self.templates_dir = templates_dir

    def load(self, filename: str) -> str:
        p = self.templates_dir / filename
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""

    @staticmethod
    def render(template_text: str, ctx: Dict[str, Any]) -> str:
        out = template_text or ""
        for k, v in (ctx or {}).items():
            out = out.replace("{{" + k + "}}", "" if v is None else str(v))
        return out