# Benchmarking Quantum Algorithms in the Cloud: A Comparative Study of Classical vs. Simulated Quantum Approaches on AWS
<br>

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
📂 src
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
├── 📄 .env.example
├── 📄 README.md
├── 📄 dev-config.yaml
└── 📄 prod-config.yaml
📂 assets
└── 🖼️ Infrastructure.png
```

## Infrastructure
![Infrastructure Diagram](assets/Infrastructure.png)

### Terraform ```.gitignore``` File
```
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
pip install git+[https://github.com/ajlrza/qintern2026-project-infrastructure.git](https://github.com/ajlrza/qintern2026-project-infrastructure.git)
```

# QMonitor Example Usage 
```python
import os
import boto3
from QMonitor.classes import Monitor
from QMonitor.logger import log_to_repo

# AWS Setup (Pre-existing in your notebook) 
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = 'us-east-1'

sts = boto3.client(
    'sts',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Experiment Setup
def quantum_rng(n_bits, shots=10000):
    """
    Generate quantum random bits using Hadamard gates.
    (Your existing experiment logic goes here)
    """
    # Dummy return for example structure
    return {'1010': 668, '1111': 651}

#  QMonitor Integration Workflow

# Step 1: Initialize the Monitor
experiment_monitor = Monitor()

# Step 2: Define Experiment Parameters
experiment_params = {
    "n_bits": 4, 
    "shots": 10000
}

# Step 3: Execute and Monitor
# Pass the function object (without calling it) and its parameters
```
## LOCAL MONITOR
```python
local_metrics = experiment_monitor.monitor_local(quantum_rng, experiment_params)

print("Monitoring Complete. Results:", local_metrics)
# Step 4: Log Results to GitHub (Local Version)
log_to_repo(
    sts_client=sts,
    experiment_function=quantum_rng,
    monitored_results={
        "Cloud Machine Data": None,                
        "Local Machine Experiment Metrics": local_metrics
    },
    notes="Local QRNG benchmark testing.",
    benchmark_type="QRNG"
)
```
## CLOUD/AWS MONITOR
```python
cloud_metrics = experiment_monitor.monitor_cloud(
    config=experiment_monitor.config, 
    experiment_function=quantum_rng
)

print("Monitoring Complete. Results:", cloud_metrics)

# Step 4: Log Results to GitHub (AWS/CLoud Version)
log_to_repo(
    sts_client=sts,
    experiment_function=quantum_rng,
    monitored_results={
        "Cloud Machine Data": cloud_metrics,
        "Local Machine Experiment Metrics": None
    },
    notes="Cloud QRNG benchmark testing on AWS infrastructure.",
    benchmark_type="QRNG"
)
```

Note on Cloud Monitoring: 
If monitor_cloud detects missing or invalid AWS credentials, it will trigger an interactive prompt in your terminal asking if you would like to switch to local monitoring or input credentials manually. Ensure your AWS_ACCESS_KEY and AWS_SECRET_KEY are exported in your environment to ensure a seamless automated run.
