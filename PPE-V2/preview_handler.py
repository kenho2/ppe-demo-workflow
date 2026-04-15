import time
from typing import Any

from workflow_helpers import extract_workflow_output_frame


class WorkflowPreviewHandler:
    """Owns callback-time preview rendering and keyboard-driven shutdown."""

    _STATUS_COMPLIANT = "compliant"
    _STATUS_PARTIAL = "partial_compliance"
    _STATUS_NON_COMPLIANT = "non_compliant"

    def __init__(
        self,
        cv2: Any,
        window_width: int,
        window_height: int,
        compliance_debug: bool,
        compliance_debug_interval_seconds: float,
    ) -> None:
        self._cv2 = cv2
        self._window_name = "Workflow Visualization"
        self._window_width = window_width
        self._window_height = window_height
        self._preview_started = False
        self._showing_workflow_output = False
        self._preview_warning_printed = False
        self._terminate_requested = False
        self._window_initialized = False
        self._pipeline: Any = None
        self._compliance_debug = compliance_debug
        self._compliance_debug_interval_seconds = max(0.5, compliance_debug_interval_seconds)
        self._last_compliance_debug_time = 0.0
        self._helmet_tokens = ("helmet", "hardhat", "hard hat", "hard-hat")
        self._vest_tokens = ("vest", "safety vest", "safety-vest", "high vis", "high-vis")

    @staticmethod
    def _value_from_detection(item: Any, key: str) -> Any:
        if isinstance(item, dict):
            return item.get(key)
        return getattr(item, key, None)

    @classmethod
    def _label_from_detection(cls, item: Any) -> str | None:
        for key in ("class", "class_name", "label", "name"):
            value = cls._value_from_detection(item, key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()

        nested_prediction = cls._value_from_detection(item, "prediction")
        if nested_prediction is not None and nested_prediction is not item:
            for key in ("class", "class_name", "label", "name"):
                value = cls._value_from_detection(nested_prediction, key)
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()

        return None

    def _extract_detected_labels(self, prediction: Any) -> set[str]:
        if not isinstance(prediction, dict):
            return set()

        labels: set[str] = set()

        raw_detections = prediction.get("raw_detections")
        if isinstance(raw_detections, dict):
            raw_predictions = raw_detections.get("predictions")
            if isinstance(raw_predictions, list):
                for item in raw_predictions:
                    label = self._label_from_detection(item)
                    if label:
                        labels.add(label)

        detections = prediction.get("tracked_detections")
        if isinstance(detections, list):
            for item in detections:
                label = self._label_from_detection(item)
                if label:
                    labels.add(label)

        return labels

    @staticmethod
    def _has_token_match(labels: set[str], tokens: tuple[str, ...]) -> bool:
        for label in labels:
            normalized = label.strip().lower().replace("_", " ").replace("-", " ")
            if any(token in normalized for token in tokens):
                return True
        return False

    def _derive_compliance_status(self, prediction: Any) -> str:
        # Fallback used when server-side compliance_state is absent.
        labels = self._extract_detected_labels(prediction)
        has_helmet = self._has_token_match(labels, self._helmet_tokens)
        has_vest = self._has_token_match(labels, self._vest_tokens)

        if has_helmet and has_vest:
            return self._STATUS_COMPLIANT
        if has_helmet or has_vest:
            return self._STATUS_PARTIAL
        if labels:
            return self._STATUS_NON_COMPLIANT

        if isinstance(prediction, dict):
            state_value = prediction.get("compliance_state")
            if isinstance(state_value, str):
                normalized = self._normalize_status(state_value)
                if normalized is not None:
                    return normalized

        return self._STATUS_NON_COMPLIANT

    @classmethod
    def _normalize_status(cls, raw_status: str) -> str | None:
        normalized = raw_status.strip().lower().replace("-", "_")
        if normalized in {cls._STATUS_COMPLIANT, cls._STATUS_PARTIAL, cls._STATUS_NON_COMPLIANT}:
            return normalized
        if "non" in normalized and "compliant" in normalized:
            return cls._STATUS_NON_COMPLIANT
        if "partial" in normalized:
            return cls._STATUS_PARTIAL
        if "compliant" in normalized:
            return cls._STATUS_COMPLIANT
        return None

    @staticmethod
    def _server_compliance_status(prediction: dict[str, Any]) -> str | None:
        state = prediction.get("compliance_state")
        if not isinstance(state, str) or not state.strip():
            return None
        return WorkflowPreviewHandler._normalize_status(state)

    @staticmethod
    def _status_label(status: str) -> str:
        if status == WorkflowPreviewHandler._STATUS_PARTIAL:
            return "partial-compliance"
        return status.replace("_", "-")

    def _maybe_print_compliance_debug(self, prediction: Any) -> None:
        if not self._compliance_debug:
            return

        now = time.time()
        # Emit status at a fixed cadence instead of every callback.
        if now - self._last_compliance_debug_time < self._compliance_debug_interval_seconds:
            return

        status = None
        if isinstance(prediction, dict):
            # Prefer workflow-produced status when available.
            status = self._server_compliance_status(prediction)
        if status is None:
            status = self._derive_compliance_status(prediction)

        print(f"Compliance status: {self._status_label(status)}")
        self._last_compliance_debug_time = now

    def set_pipeline(self, pipeline: Any) -> None:
        """Attach current pipeline instance so keyboard stop can terminate it."""
        self._pipeline = pipeline
        self._terminate_requested = False

    def handle_prediction(self, prediction: Any, video_frame: Any) -> None:
        """Inference callback that renders preview and handles local stop keys."""
        del video_frame

        self._maybe_print_compliance_debug(prediction)

        workflow_frame = extract_workflow_output_frame(prediction)
        preview_frame = workflow_frame

        if preview_frame is not None:
            if not self._window_initialized:
                self._cv2.namedWindow(self._window_name, self._cv2.WINDOW_NORMAL)
                self._cv2.resizeWindow(self._window_name, self._window_width, self._window_height)
                self._window_initialized = True
            self._cv2.imshow(self._window_name, preview_frame)
            if not self._preview_started:
                self._preview_started = True
                print("Preview window opened. Press Q or Esc to stop.")
            if workflow_frame is not None and not self._showing_workflow_output:
                self._showing_workflow_output = True
                print("Displaying workflow visualization output.")
        elif not self._preview_warning_printed:
            self._preview_warning_printed = True
            print("Could not extract preview frame from callback payload yet.")

        if not self._terminate_requested:
            # Keep UI responsive and allow manual stop without killing the process.
            key = self._cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                self._terminate_requested = True
                print("Termination requested from keyboard (Q/Esc). Stopping pipeline...")
                if self._pipeline is not None:
                    self._pipeline.terminate()