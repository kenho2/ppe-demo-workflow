import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


def extract_runtime_input_name(error_message: str) -> str | None:
    """Extract expected workflow runtime input name from SDK mismatch errors."""
    marker = "Detected runtime parameter `"
    start = error_message.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = error_message.find("`", start)
    if end == -1 or end <= start:
        return None
    return error_message[start:end]


def handle_pipeline_exception(
    exc: Exception,
    current_image_input_name: str,
    retry_attempted: bool,
) -> tuple[str, bool, bool]:
    """Return updated state and retry decision for pipeline exceptions."""
    message = str(exc)
    expected_input_name = extract_runtime_input_name(message)

    if (
        expected_input_name
        and expected_input_name != current_image_input_name
        and not retry_attempted
    ):
        print(
            "Workflow input name mismatch detected. "
            f"Retrying with input={expected_input_name}."
        )
        return expected_input_name, True, True

    if expected_input_name:
        print("Workflow input name mismatch.")
        print(
            "Set MAIN_IMAGE_INPUT_NAME in .env to the exact workflow input parameter name: "
            f"{expected_input_name}"
        )
    else:
        print(f"Pipeline failed: {exc}")

    return current_image_input_name, retry_attempted, False


def maybe_relaunch_with_venv() -> int | None:
    """Re-run main.py with .venv interpreter when started outside the venv."""
    if os.getenv("VIRTUAL_ENV"):
        return None
    if os.getenv("MAIN_PY_RELAUNCHED") == "1":
        return None

    script_dir = Path(__file__).resolve().parent
    venv_python = script_dir / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        return None

    env = os.environ.copy()
    env["MAIN_PY_RELAUNCHED"] = "1"
    cmd = [str(venv_python), str(script_dir / "main.py"), *sys.argv[1:]]
    return subprocess.call(cmd, env=env)


def mask_sensitive_url(url: str) -> str:
    """Hide password portion in URLs before logging."""
    try:
        parsed = urlsplit(url)
        if not parsed.username:
            return url

        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        if parsed.password is not None:
            auth = f"{parsed.username}:***@"
        else:
            auth = f"{parsed.username}@"
        netloc = f"{auth}{host}{port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
    except Exception:
        return url


def probe_rtsp_source(cv2: Any, source: Any) -> bool:
    """Quick preflight for RTSP sources to fail fast on bad streams/credentials."""
    if not isinstance(source, str) or not source.lower().startswith("rtsp://"):
        return True

    print(f"Probing RTSP source: {mask_sensitive_url(source)}")
    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    started = time.time()
    got_frame = False
    while time.time() - started < 8:
        ok, frame = cap.read()
        if ok and frame is not None:
            got_frame = True
            break
        time.sleep(0.1)
    opened = cap.isOpened()
    cap.release()

    if opened and got_frame:
        print("RTSP probe successful. Proceeding to workflow pipeline.")
        return True

    print("RTSP probe failed. Could not read frames from VIDEO_REFERENCE.")
    print("Check camera credentials, URL path, and whether another client is locking the stream.")
    return False


def extract_image_frame(candidate: Any) -> Any:
    """Normalize SDK image wrappers (or raw arrays) into a displayable frame."""
    if candidate is None:
        return None
    if hasattr(candidate, "numpy_image"):
        frame = getattr(candidate, "numpy_image")
        if hasattr(frame, "shape") and hasattr(frame, "dtype"):
            return frame
    if hasattr(candidate, "shape") and hasattr(candidate, "dtype"):
        return candidate
    return None


def extract_workflow_output_frame(prediction: Any) -> Any:
    """Pick the first known image output from workflow callback payload."""
    if not isinstance(prediction, dict):
        return None
    for key in ("output", "annotated_image"):
        frame = extract_image_frame(prediction.get(key))
        if frame is not None:
            return frame
    return None