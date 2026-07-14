import platform
import json, base64, os
from dataclasses import asdict
import braket._sdk as braket_sdk
from config.master_config import Config
from datetime import datetime, timezone, timedelta
from classes import InfrastructureMonitor, ExperimentMonitor

def log_to_repo(
          sts_client: object, 
          results: object, 
          experiment_function, 
          monitored_results: dict, 
          notes: str, 
          benchmark_type: str):
        
        """Logs the associated data to the GitHub repo."""

        exp_monitor = ExperimentMonitor()
        infra_monitor = InfrastructureMonitor("us-east-1")

        experiment_count += 1
        exp_monitor.experiment_id += exp_monitor.experiment_id + f"00{experiment_count}"

        local_results = monitored_results["Local Machine Experiment Metrics"]
        cloud_results = monitored_results["Cloud Machine Data"]

        config = Config()

        config.creds.sts_client = sts_client

        config.exp.experiment_id = exp_monitor.experiment_id
        config.exp.benchmark_type = benchmark_type
        config.exp.timestamp = datetime.now(timezone.utc).isoformat()
        config.exp.simulator = "LocalSimulator"
        config.exp.notes = notes

        config.circ.depth = 0
        config.circ.qubits = 0
        config.circ.shots = 1000
        config.circ.gates.H = 0
        config.circ.gates.CNOT = 0
        config.circ.gates.Others = 0

        config.metric.runtime_seconds = ([local_results, cloud_results] if (local_results and cloud_results) else (local_results or cloud_results))

        config.env.braket_sdk_version = braket_sdk.__version__
        config.env.python_version = platform.python_version()
        config.env.instance_type = get_infra_attr['ec2_instance']['instance_type']

        get_experiment_params = exp_monitor.__get_params(experiment_function)

        final_experiment_log = asdict(config)

        for param, value in get_experiment_params.items():
            if (param in asdict(config.circ)):
                asdict(config.exp)['circuit_params'][param] = value
            else:
                if (param ==  asdict(config.exp)['circuit_params']['gates']):
                     asdict(config.exp)['circuit_params']['gates'][param] = value


        repo_url = os.environ.get("REPO_URL")
        functions_to_run = []
        functions_to_run.append(("EC2", infra_monitor.monitor_ec2_vm()))

        snapshot = {
            name: monitor_func for name, monitor_func in functions_to_run
        }

        parse = json.dumps(snapshot["EC2"]).encode("utf-8")
        encode_snapshot = base64.b64encode(parse)

        return snapshot