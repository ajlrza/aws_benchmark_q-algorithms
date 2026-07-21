import os
import time
import inspect
import threading
import boto3
from datetime import datetime
from QMonitor.config.master_config import Config
from .monitors.local.local_monitor import local_user_monitor
from .monitors.cloud.ec2.ec2_monitor import (
    ec2_machine_cloud_monitor,
    ec2_instance_monitor,
)
from .monitors.cloud.braket.braket_monitor import experiment_braket_monitor

class ReturnableThread(threading.Thread):
    def __init__(self, target, kwargs=None):
        super().__init__()
        self.target = target
        self.kwargs = kwargs if kwargs is not None else {}
        self.result = None

    def run(self):
        self.result = self.target(**self.kwargs)

class Monitor:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
        self.start_time = datetime.fromtimestamp(time.time())
        self.computer_time = time.time()
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        aws_session = boto3.Session(
            aws_access_key_id=aws_access_key_id or os.environ.get("AWS_ACCESS_KEY", "test"),
            aws_secret_access_key=aws_secret_access_key or os.environ.get("AWS_SECRET_KEY", "test"),
            region_name=region_name or os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )

        self.config = Config(
            creds={
                "sts_client": aws_session.client("sts"),
                "cw_client": aws_session.client("cloudwatch"),
                "ec2_client": aws_session.client("ec2"),
                "braket_client": aws_session.client("braket"),
            }
        )

        self.experiment_id = "QIntern26 Experiment"
        print(f"Start Time: {self.start_time}")

    def monitor_local(self, experiment_function, *args, **kwargs):
        params = self.__get_params(experiment_function, *args, **kwargs)
        local_monitor = local_user_monitor(experiment_function, params)

        local_results = {}
        local_results["Local Machine Experiment Metrics"] = local_monitor
        local_results["Parameters"] = params

        return local_results

    def monitor_cloud(self, config, experiment_function, *args, **kwargs):
        params = self.__get_params(experiment_function, *args, **kwargs)
        cloud_results = {}

        thread = ReturnableThread(experiment_function, kwargs=params)
        thread.start()
        thread.join()
        
        run_result = thread.result

        experiment_cloud_monitor_ec2 = ec2_machine_cloud_monitor(config, experiment_function, params)
        experiment_cloud_ec2_metrics = ec2_instance_monitor(config, experiment_function, params)
        experiment_cloud_braket_metrics = experiment_braket_monitor(config, experiment_function, params, run_result)

        cloud_results["EC2 Machine Experiment Metrics"] = experiment_cloud_monitor_ec2
        cloud_results["EC2 Instance Experiment Metrics"] = experiment_cloud_ec2_metrics
        cloud_results["Parameters"] = params

        return cloud_results

    @staticmethod
    def __get_params(func, *args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
        return dict(bound_args.arguments)