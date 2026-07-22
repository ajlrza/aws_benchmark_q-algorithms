# Benchmarking Quantum Algorithms in the Cloud: A Comparative Study of Classical vs. Simulated Quantum Approaches on AWS
<br>

> [!IMPORTANT]
> **Note on AWS Billing & Cost Safety:** 
> **Set Native AWS Budgets:** Always set hard budget alerts and spending limits directly inside your AWS Billing Dashboard on the AWS Console. AWS is the only entity that can physically block a paid request from executing when a budget cap is hit; a Python monitoring package cannot block it for you.

This repository contains the infrastructure for the
**QWorld Qinternship 2026 - Project 26**

It contains:
- Logging
- Monitoring
- Infrastructure as Code
- YAML
- .env.example
- Workflows

## Repository Structure
```text
📂 QMonitor
├── 📁 logger
│   └── 📄 logger.py
├── 📁 monitors
│   ├── 📁 local
│   │   └── 📄 local_monitor.py
│   ├── 📁 cloud
│   │   └── 📁 braket
│   │   │   └── 📄 braket_monitor.py
│   │   └──📁 ec2
│   │       └── 📄 ec2_monitor.py
│   │
├── 📄 pyproject.toml
├── 📄 README.md
└── 📄 REFERENCES.md
└── 📄 terraform.tf
📂 assets
└── 🖼️ Infrastructure.png
```

## Infrastructure
![Infrastructure Diagram](assets/Infrastructure.png)

### Terraform `.gitignore` File
```text
**/.terraform/*

*.tfstate
*.tfstate.*

crash.log
crash.*.log

*.tfvars
*.tfvars.json
```

# QMonitor: User Workflow Guide

QMonitor is a Python-based Monitor & Log Tool for AWS EC2, Braket, and Local Machine. 
This guide outlines how to install the package and integrate it into your quantum experiments.

## Prerequisites

Before using QMonitor, ensure your environment meets the following requirements:
*   **Python Version:** Python 3.8 or higher is required.
*   **Environment Variables:** You must configure the following environment variables for AWS and GitHub integrations:
    *   **AWS:** `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, and `AWS_DEFAULT_REGION`. 
    *   **GitHub Logging:** `PAT_TOKEN`, `GITHUB_USERNAME`, and `REPOSITORY_NAME`.

## Installation

You can install the `QMonitor` package directly from the Git repository using pip.

```bash
pip install git+https://github.com/ajlrza/qintern2026-project-infrastructure.git
```

# QMonitor Example Usage 
```python
import os
import boto3
from QMonitor.monitor import Monitor
from QMonitor.logger import Logger

# AWS Setup (Pre-existing in your notebook) 
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = 'us-east-1'

# Experiment Setup
def quantum_rng(n_bits, shots=10000):
    """
    Generate quantum random bits using Hadamard gates.
    (Your existing experiment logic goes here)
    """
    # Dummy return for example structure
    return {'1010': 668, '1111': 651}

# QMonitor Integration Workflow

# Step 1: Initialize the Monitor
experiment_monitor = Monitor()

# Step 2: Define Experiment Parameters
experiment_params = {
    "n_bits": 4, 
    "shots": 10000
}
```

## LOCAL MONITOR
```python
# Step 3: Execute and Monitor (Local)
local_metrics = experiment_monitor.monitor_local(quantum_rng, **experiment_params)

print("Monitoring Complete. Results:", local_metrics)

# Step 4: Log Results to GitHub (Local Version)
logger = Logger(
    monitored_results=local_metrics,
    notes="Local QRNG benchmark testing.",
    simulator_name="LocalSimulator",
    benchmark_type="QRNG"
)
logger.Log()
```

## CLOUD/AWS MONITOR
```python
# Step 3: Execute and Monitor (Cloud)
cloud_metrics = experiment_monitor.monitor_cloud(
    experiment_monitor.config,
)

print("Monitoring Complete. Results:", cloud_metrics)

# Step 4: Log Results to GitHub (AWS/Cloud Version)
logger = Logger(
    monitored_results=cloud_metrics,
    notes="Cloud QRNG benchmark testing on AWS infrastructure.",
    simulator_name="SV1",
    benchmark_type="QRNG"
)
logger.Log()
```

**Note on Cloud Monitoring Fallback:** 
If `monitor_cloud` detects missing or invalid AWS credentials, it will no longer crash or trigger interactive prompts. Instead, it will automatically and seamlessly fall back to executing a single local monitoring session, ensuring your experiment and logs are safely completed without redundant runtime.
