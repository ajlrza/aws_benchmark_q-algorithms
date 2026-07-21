from dataclasses import asdict, fields
import braket._sdk as braket_sdk
import platform, json, base64, os, uuid, requests
from QMonitor.config.master_config import Config
from datetime import datetime, timezone
from QMonitor.results import Results

class Logger:
    def __init__(
        self, monitored_results, notes, simulator_name, benchmark_type
    ):
        self.local_results = monitored_results if "Local Machine Experiment Metrics" in monitored_results else None
        self.cloud_results = monitored_results if "EC2 Instance Experiment Metrics" in monitored_results else None
        
        self.config = Config()
        self.benchmark_type = benchmark_type

        self.config.exp.experiment_id = f"QWorld_2026_{uuid.uuid4().hex[:8]}"
        self.config.exp.benchmark_type = benchmark_type
        self.config.exp.timestamp = str(datetime.now(timezone.utc).isoformat())
        self.config.exp.simulator = simulator_name
        self.config.exp.notes = notes

        self.config.env.braket_sdk_version = braket_sdk.__version__
        self.config.env.python_version = platform.python_version()

    def get_fields(self, dataclass_obj):
        return {f.name for f in fields(dataclass_obj)}

    def Log(self):
        if self.cloud_results and "EC2 Instance Experiment Metrics" in self.cloud_results and "ec2_instance_attributes" in self.cloud_results["EC2 Instance Experiment Metrics"]:
            first_instance_key = list(self.cloud_results["EC2 Instance Experiment Metrics"]["ec2_instance_attributes"].keys())[0]
            self.config.env.instance_type = self.cloud_results["EC2 Instance Experiment Metrics"]["ec2_instance_attributes"][first_instance_key].get("Instance", "")
        else:
            self.config.env.instance_type = ""

        local_params = self.local_results.get("Parameters", {}) if self.local_results else {}
        cloud_params = self.cloud_results.get("Parameters", {}) if self.cloud_results else {}
        get_experiment_params = local_params or cloud_params

        results_dataclass = Results(Config=asdict(self.config), Metrics={})
        
        if self.local_results:
            results_dataclass.Metrics["Local_Monitor"] = self.local_results
        if self.cloud_results:
            results_dataclass.Metrics["Cloud_Monitor"] = self.cloud_results

        for key, value in get_experiment_params.items():

            if key in self.get_fields(self.config.gates):
                setattr(self.config.gates, key, value)
                
            elif key in self.get_fields(self.config.metric):
                setattr(self.config.metric, key, value)
                
            elif key in self.get_fields(self.config.env):
                setattr(self.config.env, key, value)
                
            elif key in self.get_fields(self.config.circ):
                setattr(self.config.circ, key, value)
                
            else:
                self.config.gates.Others[key] = value

        dict_config = asdict(self.config)
        excluded = {'creds'}
        final_experiment_log = {k: v for k, v in dict_config.items() if k not in excluded}
        results_dataclass.Config = final_experiment_log

        final_payload = asdict(results_dataclass)

        token = os.environ.get("PAT_TOKEN")
        owner = os.environ.get("GITHUB_USERNAME")
        repo = os.environ.get("REPOSITORY_NAME")

        if not token or not owner or not repo:
            return

        path = f"test_logs/ec2_monitor_test_{datetime.now().isoformat()}"
        branch = "main"

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}.json"

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

        try:
            response = requests.put(url, json=payload, headers=headers, timeout=5)
            print(response)
        except requests.exceptions.RequestException:
            pass