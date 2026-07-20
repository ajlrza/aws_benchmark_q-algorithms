from dataclasses import asdict
import braket._sdk as braket_sdk
import platform
import json
import base64
import os
import requests
from QMonitor.config.master_config import Config
from datetime import datetime, timezone
from QMonitor.results import Results

class Logger:
    def __init__(
        self, monitored_results, notes, benchmark_type
    ):
        self.local_results = monitored_results if "Local Machine Experiment Metrics" in monitored_results else None
        self.cloud_results = monitored_results if "EC2 Instance Experiment Metrics" in monitored_results else None
        
        self.config = Config()
        self.benchmark_type = benchmark_type

        self.experiment_count = 0
        self.config.exp.experiment_id = "QWorld 2026" + f"00{self.experiment_count}"
        self.config.exp.benchmark_type = benchmark_type
        self.config.exp.timestamp = str(datetime.now(timezone.utc).isoformat())
        self.config.exp.simulator = "LocalSimulator"
        self.config.exp.notes = notes

        self.config.circ.depth = 0
        self.config.circ.qubits = 0
        self.config.circ.shots = 1000
        self.config.circ.gates.H = 0
        self.config.circ.gates.CNOT = 0
        self.config.circ.gates.Others = 0

        self.config.env.braket_sdk_version = braket_sdk.__version__
        self.config.env.python_version = platform.python_version()

    def Log(self):
        if self.cloud_results and "EC2 Instance Experiment Metrics" in self.cloud_results and "ec2_instance_attributes" in self.cloud_results["EC2 Instance Experiment Metrics"]:
            first_instance_key = list(self.cloud_results["EC2 Instance Experiment Metrics"]["ec2_instance_attributes"].keys())[0]
            self.config.env.instance_type = self.cloud_results["EC2 Instance Experiment Metrics"]["ec2_instance_attributes"][first_instance_key].get("Instance", "")
        else:
            self.config.env.instance_type = ""

        get_experiment_params = {}

        if (self.local_results == None):
            get_experiment_params = self.cloud_results.get("Parameters", {})
        elif (self.cloud_results == None):
            get_experiment_params = self.local_results.get("Parameters", {})
        elif (self.cloud_results != None and self.local_results != None):
            get_experiment_params = {
                "local_monitored_params": self.local_results.get("Parameters", {}),
                "cloud_monitored_params": self.cloud_results.get("Parameters", {})
            }

        results_dataclass = Results(Config=asdict(self.config), Metrics={})
        
        if self.local_results:
            results_dataclass.Metrics["Local_Monitor"] = self.local_results
        if self.cloud_results:
            results_dataclass.Metrics["Cloud_Monitor"] = self.cloud_results

        for key, value in get_experiment_params.items():
            if (len(get_experiment_params.keys()) == 1):
                dict_config = asdict(self.config)
                excluded = {'creds', 'exp'}
                final_experiment_log = {k: v for k, v in dict_config.items() if k not in excluded}
                results_dataclass.Config = final_experiment_log

                if hasattr(self.config.circ, key):
                    results_dataclass.Metrics[key] = value
                elif hasattr(self.config.circ.gates, key):
                    results_dataclass.Metrics[key] = value
                    
            elif (len(get_experiment_params.keys()) == 2):
                dict_config = asdict(self.config)
                excluded = {'creds', 'exp'}
                final_experiment_log = {k: v for k, v in dict_config.items() if k not in excluded}
                results_dataclass.Config = final_experiment_log

                if hasattr(self.config.circ, key):
                    results_dataclass.Metrics[key] = value
                elif hasattr(self.config.circ.gates, key):
                    results_dataclass.Metrics[key] = value

        final_payload = asdict(results_dataclass)

        token = os.environ.get("PAT_TOKEN")
        owner = os.environ.get("GITHUB_USERNAME")
        repo = os.environ.get("REPOSITORY_NAME")

        path = f"test_logs/ec2_monitor_test_{datetime.now().isoformat()}"
        branch = "main"

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}.md"

        file_content = json.dumps(final_payload, indent=2)
        encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Experiment {self.benchmark_type} EC2 Monitor ",
            "content": encoded_content,
            "branch": branch,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.put(url, json=payload, headers=headers, timeout=5)
        print(response)