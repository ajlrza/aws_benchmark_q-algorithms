# QMonitor Documentation

The following are the available modules from the QMonitor Package

* monitors
* loggers
* config

# Monitors

### `local_user_monitor()` **QMonitor.src.monitors.local.local_monitor.py**
> Extracts local machine hardware metrics through ```psutil``` and ```threading``` libraries.

#### Function Parameters

| Parameter | Type  | Required | Description |
| :--- | :--- | :--- | :--- |
| `experiment_function` | `Callable` | Yes | Callable and uninstantiated experiment function. |
| `params` | `Dict[str, Any]` | Yes | Experiment function parameters passed from helper function. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Local machine metrics including: CPU usage, RAM usage, I/O disk latency |

Example Output
```json
{
  "Local CPU Usage: Thread 1": 14.5,
  "Local RAM Usage: Thread 1": 62.3,
  "Local I/O Disk Latency: Thread 1": "sdiskio(read_count=874312, write_count=349811, read_bytes=4294967296, write_bytes=1073741824, read_time=14502, write_time=3910, read_merged_count=12, write_merged_count=84, busy_time=18491)",
  "Local CPU Usage: Thread 2": 22.1,
  "Local RAM Usage: Thread 2": 63.8,
  "Local I/O Disk Latency: Thread 2": "sdiskio(read_count=874350, write_count=349900, read_bytes=4295967296, write_bytes=1074741824, read_time=14510, write_time=3915, read_merged_count=12, write_merged_count=84, busy_time=18500)",
  "Local CPU Usage: Thread 3": 18.3,
  "Local RAM Usage: Thread 3": 64.1,
  "Local I/O Disk Latency: Thread 3": "sdiskio(read_count=874400, write_count=350100, read_bytes=4296967296, write_bytes=1075741824, read_time=14520, write_time=3925, read_merged_count=12, write_merged_count=84, busy_time=18520)",
  "Datetime": "2026-07-21 12:11:44.123456+00:00"
}
```

### `ec2_instance_monitor()` **QMonitor.src.monitors.cloud.ec2.ec2_monitor.py**
> Extracts EC2 instance basic metrics through ```AWS Boto3``` EC2 client.

#### Function Parameters

| Parameter | Type  | Required | Description |
| :--- | :--- | :--- | :--- |
| `config` | `Object` | Yes | Initiated config dataclass for centralized credential management. |
| `experiment_function` | `Callable` | Yes | Callable and uninstantiated experiment function. |
| `params` | `Dict[str, Any]` | Yes | Experiment function parameters passed from helper function. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | EC2 instance infrastructure and usage metrics including: CPU Utilization, Memory Used Percentage, Network I/O, Disk I/O |

Example Output
```json
{
  "usage_metrics": {
    "EC2_usage": {
      "instance_id": "i-0123456789abcdef0",
      "instance_type": "t3.xlarge",
      "time_used": "3 days, 14:22:05.819201"
    }
  },
  "infrastructure_metrics": [
    {
      "Label": "mem_used_percent",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 48.35,
          "Unit": "Percent"
        }
      ],
      "ResponseMetadata": {
        "HTTPStatusCode": 200,
        "HTTPHeaders": { ... }
      },
      "RAM Summed Average": 48.35
    },
    {
      "Label": "CPUUtilization",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 12.4,
          "Unit": "Percent"
        }
      ],
      "ResponseMetadata": { ... },
      "CPUUtilization Summed Average": 12.4
    },
    {
      "Label": "NetworkIn",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 1048576.0,
          "Unit": "Bytes"
        }
      ],
      "ResponseMetadata": { ... },
      "NetworkIn Summed Average": 1048576.0
    },
    {
      "Label": "NetworkOut",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 524288.0,
          "Unit": "Bytes"
        }
      ],
      "ResponseMetadata": { ... },
      "NetworkOut Summed Average": 524288.0
    },
    {
      "Label": "DiskReadOps",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 150.0,
          "Unit": "Count"
        }
      ],
      "ResponseMetadata": { ... },
      "DiskReadOps Summed Average": 150.0
    },
    {
      "Label": "DiskWriteOps",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 42.0,
          "Unit": "Count"
        }
      ],
      "ResponseMetadata": { ... },
      "DiskWriteOps Summed Average": 42.0
    }
  ]
}
```

### `ec2_machine_cloud_monitor()` **QMonitor.src.monitors.cloud.ec2.ec2_monitor.py**
> Extracts EC2 instance infrastructure metrics (CPU, RAM, Network, Disk) and compute time usage through the `AWS Boto3` CloudWatch and EC2 clients.

#### Function Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `config` | `Object` | Yes | Initiated config dataclass for centralized credential management. |
| `experiment_function` | `Callable` | Yes | Callable and uninstantiated experiment function. |
| `experiment_params` | `Dict[str, Any]` | Yes | Experiment function parameters passed from helper function. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Nested dictionary containing `usage_metrics` (instance ID, type, and total compute time used) and `infrastructure_metrics` (summed averages of CloudWatch data points over a 5-minute period). |

**Example Output**
```json
{
  "usage_metrics": {
    "EC2_usage": {
      "instance_id": "i-0123456789abcdef0",
      "instance_type": "t3.xlarge",
      "time_used": "3 days, 14:22:05.819201"
    }
  },
  "infrastructure_metrics": [
    {
      "Label": "mem_used_percent",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 48.35,
          "Unit": "Percent"
        }
      ],
      "ResponseMetadata": {
        "HTTPStatusCode": 200,
        "HTTPHeaders": { }
      },
      "RAM Summed Average": 48.35
    },
    {
      "Label": "CPUUtilization",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 12.4,
          "Unit": "Percent"
        }
      ],
      "ResponseMetadata": { },
      "CPUUtilization Summed Average": 12.4
    },
    {
      "Label": "NetworkIn",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 1048576.0,
          "Unit": "Bytes"
        }
      ],
      "ResponseMetadata": { },
      "NetworkIn Summed Average": 1048576.0
    },
    {
      "Label": "NetworkOut",
      "Datapoints": [
        {
          "Timestamp": "2026-07-21T12:13:00Z",
          "Average": 524288.0,
          "Unit": "Bytes"
        }
      ],
      "ResponseMetadata": { },
      "NetworkOut Summed Average":
```

### `experiment_braket_monitor()` **QMonitor.src.monitors.cloud.braket.braket_monitor.py**
> Executes a quantum experiment on AWS Braket in a threaded environment, extracting task execution details and account spending limit metrics using the `AWS Boto3` Braket client.

#### Function Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `config` | `Object` | Yes | Initiated config dataclass containing the Boto3 Braket client. |
| `experiment_function` | `Callable` | Yes | Callable and uninstantiated experiment function to be threaded. |
| `experiment_params` | `Dict[str, Any]` | Yes | Experiment function parameters passed from helper function. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Dictionary containing AWS Braket infrastructure task data (Job/Task ARNs) and usage metrics (Remaining budget, actual spent, tracking periods). |

**Example Output**
```json
{
  "Braket Infrastructure Metrics": {
    "get_quantum_task": {
      "quantumTaskArn": "arn:aws:braket:us-east-1:123456789012:quantum-task/abc123xx-...",
      "status": "COMPLETED",
      "deviceArn": "arn:aws:braket:::device/qpu/rigetti/Aspen-M-3"
    },
    "search_quantum_tasks": {
      "quantumTasks": [ ... ]
    },
    "get_job": {
      "jobArn": "arn:aws:braket:us-east-1:123456789012:job/invalid-job-for-task",
      "status": "FAILED"
    }
  },
  "Braket Usage Metrics": {
    "spending_limit": "arn:aws:braket:us-east-1:123456789012:spending-limit/...",
    "device_arn": "arn:aws:braket:::device/qpu/rigetti/Aspen-M-3",
    "created_at": "2026-07-21 12:15:00+00:00",
    "remaining_budget": 85.50,
    "Warning": true
  }
}
```
---

# Main Orchestrator

### `Monitor` **QMonitor.classes.py**
> Centralized wrapper class that initializes Boto3 sessions/clients (STS, CloudWatch, EC2, Braket) and acts as the main entry point to trigger either local or cloud monitoring workflows.

#### Class Initialization Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `aws_access_key_id` | `str` | No | AWS Access Key. Defaults to `OS.environ` if not provided. |
| `aws_secret_access_key` | `str` | No | AWS Secret Key. Defaults to `OS.environ` if not provided. |
| `region_name` | `str` | No | AWS Region. Defaults to `us-east-1`. |

#### Core Methods
*   **`monitor_local(experiment_function)`**: Extracts wrapped arguments and invokes `local_user_monitor`. Returns a dictionary of `"Local Machine Experiment Metrics"`.
*   **`monitor_cloud(config, experiment_function)`**: Extracts wrapped arguments and invokes EC2 and Braket cloud monitors concurrently. Returns a dictionary of `"EC2 Machine Experiment Metrics"` and `"EC2 Instance Experiment Metrics"`.

---

# Loggers

### `Logger` **QMonitor.loggers.py**
> Maps retrieved metrics and parameters into the main configuration dataclasses, formats the final result payload, and automatically uploads the JSON experiment log to a specified GitHub repository via the GitHub REST API.

#### Class Initialization Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `monitored_results` | `Dict` | Yes | The nested metric dictionary returned by the `Monitor` class. |
| `notes` | `str` | Yes | Custom user notes regarding the specific experiment run. |
| `simulator_name` | `str` | Yes | Name of the quantum simulator or hardware device used. |
| `benchmark_type` | `str` | Yes | Identifier for the type of benchmark being executed. |

#### Core Methods
*   **`Log()`**: Processes the `monitored_results`, extracts instance and environment data (SDK versions, instances), merges everything into the `Results` dataclass, encodes it in Base64, and PUTs it to GitHub. 
    *   *Required Environment Variables:* `PAT_TOKEN` (GitHub Personal Access Token), `GITHUB_USERNAME`, `REPOSITORY_NAME`.

---

# Config

### `Config` & Sub-Dataclasses **QMonitor.config**
> A modular configuration management system using Python `dataclasses` to cleanly track and store hardware constraints, circuit properties, and credentials over the lifespan of a single experiment run.

#### Available Dataclasses

| Class | Purpose | Key Attributes |
| :--- | :--- | :--- |
| `Config` | The master dataclass containing all sub-configurations. | `creds`, `exp`, `circ`, `metric`, `env`, `gates` |
| `CredsConfig` | Manages active Boto3 client instances. | `sts_client`, `cw_client`, `ec2_client`, `braket_client` |
| `ExpConfig` | Metadata about the experiment run itself. | `experiment_id`, `benchmark_type`, `timestamp`, `simulator` |
| `CircParams` | Captures the structural parameters of the quantum circuit. | `qubits`, `depth`, `shots`, `gates` |
| `Gates` | Tracks specific gate usage counts within the circuit. | `H`, `CNOT`, `Others` |
| `Metrics` | Target metrics to be measured/tested during the benchmark. | `circuit_fidelity_dR2`, `runtime_seconds`, `cloud_overhead_seconds` |
| `Environ` | Execution environment metadata. | `braket_sdk_version`, `python_version`, `instance_type` |
