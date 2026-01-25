from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class InputManifest:
    """
    Input inventory (SSOT runtime view)

    This object answers one question only:
      - Which inputs are actually provided for THIS run?

    It does NOT guess. If you do not provide a file/path/flag, it is treated as missing.
    """

    has_event: bool = False       # CSV/XML event log OR canonical event dataframe
    has_spatial: bool = False     # event x,y present and trusted (or tracking-derived)
    has_fitness: bool = False     # XLSX / GPS / load data
    has_video: bool = False       # MP4
    has_tracking: bool = False    # explicit tracking feed (or video-derived tracking, flagged separately)
    has_doc: bool = False         # PDF/TXT/MD/DOCX/HTML context inputs

    notes: Optional[str] = None

    @staticmethod
    def from_kwargs(df_provided: bool, kwargs: Dict[str, Any]) -> "InputManifest":
        """
        Construct manifest without guessing.
        Any explicit flag/path in kwargs toggles corresponding input.

        Supported kwargs (examples):
          - event_path, csv_path, xml_path
          - xlsx_path, fitness_path
          - mp4_path, video_path
          - tracking_path
          - doc_paths (list) / pdf_path / doc_path
          - has_event / has_fitness / has_video / has_tracking / has_doc / has_spatial
        """
        def truthy(x: Any) -> bool:
            if x is None:
                return False
            if isinstance(x, bool):
                return x
            if isinstance(x, (list, tuple, dict, set)):
                return len(x) > 0
            if isinstance(x, str):
                return len(x.strip()) > 0
            return True

        # Explicit flags win
        has_event_flag = truthy(kwargs.get("has_event"))
        has_fitness_flag = truthy(kwargs.get("has_fitness"))
        has_video_flag = truthy(kwargs.get("has_video"))
        has_tracking_flag = truthy(kwargs.get("has_tracking"))
        has_doc_flag = truthy(kwargs.get("has_doc"))
        has_spatial_flag = truthy(kwargs.get("has_spatial"))

        # Paths also count as explicit provision
        has_event_path = any(truthy(kwargs.get(k)) for k in ["event_path", "csv_path", "xml_path"])
        has_fitness_path = any(truthy(kwargs.get(k)) for k in ["xlsx_path", "fitness_path"])
        has_video_path = any(truthy(kwargs.get(k)) for k in ["mp4_path", "video_path"])
        has_tracking_path = truthy(kwargs.get("tracking_path"))

        doc_keys = ["doc_paths", "pdf_path", "doc_path", "txt_path", "md_path", "html_path"]
        has_doc_path = any(truthy(kwargs.get(k)) for k in doc_keys)

        # DataFrame provided counts as EVENT input ONLY if caller passed df.
        has_event_df = bool(df_provided)

        has_event = has_event_flag or has_event_path or has_event_df
        has_fitness = has_fitness_flag or has_fitness_path
        has_video = has_video_flag or has_video_path
        has_tracking = has_tracking_flag or has_tracking_path
        has_doc = has_doc_flag or has_doc_path

        # spatial is stricter: either explicitly declared, or you can set it later after SOT checks.
        has_spatial = has_spatial_flag

        return InputManifest(
            has_event=has_event,
            has_spatial=has_spatial,
            has_fitness=has_fitness,
            has_video=has_video,
            has_tracking=has_tracking,
            has_doc=has_doc,
            notes=kwargs.get("input_notes"),
        )