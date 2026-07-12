import platform
import json, base64, os
import braket._sdk as braket_sdk
from datetime import datetime, timezone, timedelta
from monitors.local.local_monitor import experiment_monitor_class
from classes import InfrastructureMonitor
from classes import ExperimentMonitor

def log_to_repo(results: object, experiment_function, monitored_results: dict, notes: str, benchmark_type: str):
        """Logs the associated data to the GitHub repo."""

        exp_monitor = ExperimentMonitor()
        infra_monitor = InfrastructureMonitor("us-east-1")
        
        get_infra_attr = infra_monitor.get_instance_attributes

        experiment_count += 1
        exp_monitor.experiment_id += exp_monitor.experiment_id + f"00{experiment_count}"

        local_results = monitored_results["Local Machine Data"]
        cloud_results = monitored_results["Cloud Machine Data"]

        experiment_log = {
            "experiment_id": exp_monitor.experiment_id,
            "benchmark_type": benchmark_type,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "simulator": "LocalSimulator",
            "circuit_params": {
                "qubits": 0,
                "depth": 0,
                "shots": 0,
                "gates": {
                    "H": 0,
                    "CNOT": 0,
                    "other": 0
                }
            },
            "metrics": {
                "circuit_fidelity_dR2": 0.0,
                "shot_noise_converged_at": "int",
                "cv_value": "float",
                "local_vs_sv1_ks_pvalue": "float",
                "gate_error_rate_tested": "float",
                "fidelity_under_noise": "float",
                "measurement_bias_pvalue": "float",
                "runtime_seconds": ([local_results, cloud_results] if (local_results and cloud_results)  else (local_results or cloud_results)),
                "cloud_overhead_seconds": cloud_results[""]
            },
            "environment": {
                "braket_sdk_version": braket_sdk.__version__,
                "python_version": platform.python_version(),
                "instance_type": get_infra_attr['ec2_instance']['instance_type']
            },
            "notes": notes
        }

        get_experiment_params = exp_monitor.__get_params(experiment_function)

        for param, value in get_experiment_params.items():
            if (param in experiment_log['circuit_params'].keys()):
                experiment_log['circuit_params'][param] = value
            else:
                if (param == experiment_log['circuit_params']['gates']):
                    experiment_log['circuit_params']['gates'][param] = value


        repo_url = os.environ.get("REPO_URL")
        functions_to_run = []
        functions_to_run.append(("EC2", infra_monitor.monitor_ec2_vm()))

        snapshot = {
            name: monitor_func for name, monitor_func in functions_to_run
        }

        parse = json.dumps(snapshot["EC2"]).encode("utf-8")
        encode_snapshot = base64.b64encode(parse)

        return snapshot