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
