# Automated PPE Compliance Workflow

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

This repository contains a fully automated workflow for detecting Personal Protective Equipment (PPE) compliance using a live video source (RTSP streams or webcams). 

Designed as a production-ready proof of concept, this pipeline demonstrates how to deploy computer vision models into local environments while maintaining robust error handling, dynamic configuration, and self-healing execution.

## 🚀 Business Value
Manual safety compliance checks are time-consuming and prone to human error. This workflow automates the ingestion of live video feeds, tracks hardhat and safety vest compliance, and outputs structured compliance states in real time. 

## ✨ Key Integration Features
- **Dynamic Stream Probing:** Automatically tests RTSP stream health and credentials before initializing the heavy inference pipeline.
- **Self-Healing Execution:** If the upstream workflow definition changes (e.g., an image input name mismatch), the pipeline catches the exception, extracts the correct parameter, and automatically restarts.
- **Environment Driven:** Fully configurable via `.env` files, making it simple for implementation teams to deploy across different client servers without altering code.

## 🏗️ Quick Start

**1. Clone and Prepare the Environment**
```powershell
git clone [https://github.com/kenho2/ppe-demo-workflow.git](https://github.com/kenho2/ppe-demo-workflow.git)
cd ppe-demo-workflow/PPE-V2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
