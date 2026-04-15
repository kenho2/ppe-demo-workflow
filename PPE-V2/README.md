# PPE-V2 Roboflow Workflow Runner

This project runs a Roboflow Workflow on a live video source (camera index or RTSP stream), and shows the workflow visualization in an OpenCV preview window.

## Quick Start (60 Seconds)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set your `ROBOFLOW_API_KEY`, then run:

```powershell
python main.py
```

## Features

- Loads runtime settings from `.env`
- Auto-relaunches with local `.venv` Python when needed
- Probes RTSP sources before starting the workflow
- Runs `InferencePipeline.init_with_workflow(...)` with fresh definition fetch (`use_workflow_definition_cache=False`)
- Retries once automatically when workflow image input name mismatches
- Live preview window with keyboard stop (`Q` or `Esc`)

## Requirements

- Windows PowerShell (commands below use PowerShell)
- Python 3.10+
- A Roboflow API key
- A published Roboflow Workflow

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

Create `.env` from `.env.example` and update values:

```powershell
Copy-Item .env.example .env
```

Required variables:

- `ROBOFLOW_API_KEY`
- `ROBOFLOW_WORKSPACE`
- `ROBOFLOW_WORKFLOW`

Common variables:

- `VIDEO_REFERENCE`: `0` for default webcam, or full `rtsp://...` URL
- `IMAGE_INPUT_NAME`: workflow image input name (default `image`)
- `MAIN_IMAGE_INPUT_NAME`: optional override for `IMAGE_INPUT_NAME`
- `MAIN_WINDOW_WIDTH`: preview width (default `960`)
- `MAIN_WINDOW_HEIGHT`: preview height (default `540`)
- `MAIN_DEBUG_COMPLIANCE`: `1` to print compliance status to console, `0` to disable (default `1`)
- `MAIN_DEBUG_COMPLIANCE_INTERVAL_SECONDS`: minimum seconds between compliance status logs (default `5`)
- `MAIN_QUIET_WARNINGS`: `1` to suppress known SDK warning noise (default `1`)

## Run

```powershell
.\.venv\Scripts\python.exe main.py
```

You can also run:

```powershell
python main.py
```

`main.py` will relaunch itself inside `.venv` when available.

## Controls

- Press `Q` or `Esc` in the preview window to stop the pipeline.

## Console Logging

- When `MAIN_DEBUG_COMPLIANCE=1`, the app prints one periodic status line:
  - `Compliance status: compliant`
  - `Compliance status: partial-compliance`
  - `Compliance status: non-compliant`
- Log cadence is controlled by `MAIN_DEBUG_COMPLIANCE_INTERVAL_SECONDS`.

## Project Structure

- `main.py`: application entrypoint and pipeline control flow
- `runtime_config.py`: environment loading and runtime config parsing
- `workflow_helpers.py`: workflow/RTSP/retry helper utilities
- `preview_handler.py`: preview rendering and keyboard stop handling
- `requirements.txt`: Python dependencies
- `.env.example`: environment variable template

## Troubleshooting

- RTSP probe fails:
  - Verify camera credentials, URL path, and stream availability.
- Workflow input mismatch error:
  - Set `MAIN_IMAGE_INPUT_NAME` (or `IMAGE_INPUT_NAME`) to the exact workflow image input parameter name.
- Missing modules:
  - Ensure you are running with `.venv` and installed `requirements.txt`.
