# QMonitor Documentation

The following are the available modules from the QMonitor Package:

* monitors
* logger
* config

---

# Monitors

### `local_user_monitor()` **QMonitor.src.monitors.local.local_monitor.py**
> Extracts local machine hardware metrics through the `psutil` and `threading` libraries.

#### Function Parameters

| Parameter | Type  | Required | Description |
| :--- | :--- | :--- | :--- |
| `experiment_function` | `Callable` | Yes | Callable and uninstantiated experiment function. |
| `params` | `Dict[str, Any]` | Yes | Experiment function parameters passed from helper function. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Local machine metrics including: CPU usage, RAM usage, and I/O disk latency. |

### `ec2_instance_monitor()` **QMonitor.src.monitors.cloud.ec2.ec2_monitor.py**
> Extracts basic EC2 instance metrics through the AWS Boto3 EC2 client.

#### Function Parameters

| Parameter | Type  | Required | Description |
| :--- | :--- | :--- | :--- |
| `config` | `Object` | Yes | Initiated config dataclass for centralized credential management. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Nested dictionary containing instance details and hardware specs (vCPUs, Memory, GPU). |

### `ec2_machine_cloud_monitor()` **QMonitor.src.monitors.cloud.ec2.ec2_monitor.py**
> Extracts EC2 instance infrastructure metrics (CPU, RAM, Network, Disk) and compute time usage through the AWS Boto3 CloudWatch and EC2 clients.

#### Function Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `config` | `Object` | Yes | Initiated config dataclass for centralized credential management. |


#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Nested dictionary containing `usage_metrics` (instance ID, type, and total compute time used) and `infrastructure_metrics` (summed averages of CloudWatch data points over a 5-minute period). |

### `experiment_braket_monitor()` **QMonitor.src.monitors.cloud.braket.braket_monitor.py**
> Connects to AWS Braket via Boto3 to track task execution details and monitor account spending limits against live tasks.

#### Function Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `config` | `Object` | Yes | Initiated config dataclass containing the Boto3 Braket client. |
| `run_result` | `Any` | Yes | The actual object/response returned by the quantum experiment thread. |

#### Return Value

| Type | Description |
| :--- | :--- |
| `Dict` | Dictionary containing AWS Braket infrastructure task data (Job/Task ARNs) and usage metrics (remaining budget, actual spent, tracking periods). |

---

# Main Orchestrator

### `Monitor` **QMonitor.classes.py**
> Centralized wrapper class that initializes Boto3 sessions/clients (STS, CloudWatch, EC2, Braket) and acts as the main entry point to trigger either local or cloud monitoring workflows, preventing double executions.

#### Class Initialization Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `aws_access_key_id` | `str` | No | AWS Access Key. Defaults to `OS.environ` if not provided. |
| `aws_secret_access_key` | `str` | No | AWS Secret Key. Defaults to `OS.environ` if not provided. |
| `region_name` | `str` | No | AWS Region. Defaults to `us-east-1`. |

#### Core Methods
*   **`monitor_local(experiment_function, *args, **kwargs)`**: Binds kwargs, extracts arguments, and invokes `local_user_monitor`. Returns a dictionary containing `"Local Machine Experiment Metrics"` and `"Parameters"`.
*   **`monitor_cloud(config, experiment_function, *args, **kwargs)`**: Runs the quantum experiment strictly once within a thread, then passes the results concurrently to EC2 and Braket cloud monitors. Handles AWS fallback gracefully. Returns a dictionary containing `"EC2 Machine Experiment Metrics"`, `"EC2 Instance Experiment Metrics"`, `"Braket Experiment Metrics"`, and `"Parameters"`.

---

# Logger

### `Logger` **QMonitor.logger.py**
> Maps retrieved metrics and parameters into the main configuration dataclasses, formats the final result payload, and automatically uploads the JSON experiment log to a specified GitHub repository via the GitHub REST API. Suppresses errors if GitHub credentials are missing.

#### Class Initialization Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `monitored_results` | `Dict` | Yes | The nested metric dictionary returned by the `Monitor` class (`local_metrics` or `cloud_metrics`). |
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
