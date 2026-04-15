import os
import warnings
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeConfig:
    """Immutable runtime settings resolved from environment variables."""

    api_key: str
    workspace_name: str
    workflow_id: str
    video_reference: Any
    image_input_name: str
    window_width: int
    window_height: int


def load_runtime_config() -> RuntimeConfig:
    """Load .env, apply warning policy, and return normalized runtime settings."""

    from dotenv import load_dotenv

    load_dotenv()

    quiet_warnings = os.getenv("MAIN_QUIET_WARNINGS", "1").strip().lower() not in {"0", "false", "no"}
    if quiet_warnings:
        os.environ.setdefault("CORE_MODEL_SAM_ENABLED", "False")
        os.environ.setdefault("CORE_MODEL_SAM3_ENABLED", "False")
        os.environ.setdefault("CORE_MODEL_GAZE_ENABLED", "False")
        os.environ.setdefault("CORE_MODEL_YOLO_WORLD_ENABLED", "False")

        warnings.filterwarnings("ignore", message=r"Importing from timm\.models\.layers is deprecated.*")
        warnings.filterwarnings("ignore", message=r"The `ensure_cv2_image_for_annotation` was deprecated.*")
        warnings.filterwarnings("ignore", message=r"Field name \"schema\".*")
        warnings.filterwarnings("ignore", message=r"Specified provider '.*ExecutionProvider'.*Available providers:.*")
        warnings.filterwarnings("ignore", message=r".*init_with_workflow is experimental.*")

    video_reference: Any = os.getenv("VIDEO_REFERENCE", "0")
    if isinstance(video_reference, str) and video_reference.isdigit():
        # Accept camera index passed via env as string (e.g. "0").
        video_reference = int(video_reference)

    return RuntimeConfig(
        api_key=os.getenv("ROBOFLOW_API_KEY", "YOUR_ROBOFLOW_API_KEY"),
        workspace_name=os.getenv("ROBOFLOW_WORKSPACE", "kens-workspace-vdhed"),
        workflow_id=os.getenv("ROBOFLOW_WORKFLOW", "ppe-compliance-tracking-logging-final"),
        video_reference=video_reference,
        image_input_name=os.getenv("MAIN_IMAGE_INPUT_NAME") or os.getenv("IMAGE_INPUT_NAME", "input"),
        window_width=int(os.getenv("MAIN_WINDOW_WIDTH", "960")),
        window_height=int(os.getenv("MAIN_WINDOW_HEIGHT", "540")),
    )