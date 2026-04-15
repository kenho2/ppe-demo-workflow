from typing import Any
from preview_handler import WorkflowPreviewHandler
from runtime_config import load_runtime_config
from workflow_helpers import (
    handle_pipeline_exception,
    maybe_relaunch_with_venv,
    probe_rtsp_source,
)


def main() -> int:
    # Start in the project venv when launched from a global interpreter.
    relaunched_exit_code = maybe_relaunch_with_venv()
    if relaunched_exit_code is not None:
        return relaunched_exit_code

    config = load_runtime_config()

    # Delay heavy imports until after venv relaunch/config setup.
    import cv2
    from inference import InferencePipeline

    pipeline: Any = None
    preview_handler = WorkflowPreviewHandler(
        cv2=cv2,
        window_width=config.window_width,
        window_height=config.window_height,
    )

    if not probe_rtsp_source(cv2, config.video_reference):
        return 1

    current_image_input_name = config.image_input_name
    retry_attempted = False

    try:
        while True:
            print(
                f"Starting workflow pipeline: workspace={config.workspace_name}, workflow={config.workflow_id}, input={current_image_input_name}"
            )

            try:
                pipeline = InferencePipeline.init_with_workflow(
                    api_key=config.api_key,
                    workspace_name=config.workspace_name,
                    workflow_id=config.workflow_id,
                    video_reference=config.video_reference,
                    on_prediction=preview_handler.handle_prediction,
                    image_input_name=current_image_input_name,
                    use_workflow_definition_cache=False,
                )
                # Allow keyboard stop (Q/Esc) to terminate the active pipeline.
                preview_handler.set_pipeline(pipeline)
                pipeline.start()
                pipeline.join()
                break
            except Exception as exc:
                current_image_input_name, retry_attempted, should_retry = handle_pipeline_exception(
                    exc=exc,
                    current_image_input_name=current_image_input_name,
                    retry_attempted=retry_attempted,
                )
                if should_retry:
                    continue
                return 1
    finally:
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
