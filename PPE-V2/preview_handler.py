import time
from typing import Any

from workflow_helpers import extract_workflow_output_frame


class WorkflowPreviewHandler:
    """Owns callback-time preview rendering and keyboard-driven shutdown."""

    def __init__(self, cv2: Any, window_width: int, window_height: int) -> None:
        self._cv2 = cv2
        self._window_name = "Workflow Visualization"
        self._window_width = window_width
        self._window_height = window_height
        self._callback_frame_count = 0
        self._last_heartbeat = time.time()
        self._preview_started = False
        self._showing_workflow_output = False
        self._preview_warning_printed = False
        self._terminate_requested = False
        self._window_initialized = False
        self._pipeline: Any = None

    def set_pipeline(self, pipeline: Any) -> None:
        """Attach current pipeline instance so keyboard stop can terminate it."""
        self._pipeline = pipeline
        self._terminate_requested = False

    def handle_prediction(self, prediction: Any, video_frame: Any) -> None:
        """Inference callback that renders preview and handles local stop keys."""
        del video_frame

        self._callback_frame_count += 1
        now = time.time()
        if now - self._last_heartbeat >= 5:
            print(f"Stream active. Received {self._callback_frame_count} callbacks.")
            self._last_heartbeat = now

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