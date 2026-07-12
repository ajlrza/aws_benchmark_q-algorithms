import json, base64, datetime, datetime, timezone


def log_to_repo(self, results: object, experiment_function, monitored_results: dict, notes: str, benchmark_type: str):
        """Logs the associated data to the GitHub repo."""

        infra_monitor = InfrastructureMonitor(self.access_key, self.secret_key)
        get_infra_attr = infra_monitor.get_instance_attributes

        experiment_count += 1
        self.experiment_id += self.experiment_id + f"_00{experiment_count}"
        self.results = results
        self.notes = notes

        experiment_log = {
            "experiment_id": self.experiment_id,
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
                "runtime_seconds": monitored_results[''] ,
                "cloud_overhead_seconds": "float"
            },
            "environment": {
                "braket_sdk_version": "",
                "python_version": "",
                "instance_type": get_infra_attr['ec2_instance']['instance_type']
            },
            "notes": notes
        }

        get_experiment_params = self.__get_params(experiment_function)

        for param, value in get_experiment_params.items():
            if (param in experiment_log['circuit_params'].keys()):
                experiment_log['circuit_params'][param] = value
            else:
                if (param == experiment_log['circuit_params']['gates']):
                    experiment_log['circuit_params']['gates'][param] = value


        repo_url = os.environ.get("REPO_URL")
        functions_to_run = []
        functions_to_run.append(("EC2", self.monitor_ec2_vm()))

        snapshot = {
            name: monitor_func for name, monitor_func in functions_to_run
        }

        parse = json.dumps(snapshot["EC2"]).encode("utf-8")
        encode_snapshot = base64.b64encode(parse)

        return snapshot