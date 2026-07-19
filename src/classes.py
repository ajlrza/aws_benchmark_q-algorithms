from functools import wraps
import os, time, inspect, boto3, sys
from datetime import datetime, timezone
from src.config.master_config import Config
from .monitors.error_codes import error_codes
from .monitors.local.local_monitor import local_user_monitor
from .monitors.cloud.braket.braket_monitor import experiment_braket_monitor
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from .monitors.cloud.ec2.ec2_monitor import ec2_machine_cloud_monitor, ec2_instance_monitor

class Monitor:

    """
      Monitors the experiment code ran on the local machine
      and gathers local-bound metrics using the psutil library
    """

    def __init__(self):    

        """
        Initializes experiment monitor instance, used to wrap and extract params

        Args:
            experiment (Callable): The experiment function to be called and monitored

        """

        self.start_time = datetime.fromtimestamp(time.time()) 
        self.computer_time = time.time()
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.config = Config()

        self.experiment_id = f"QIntern26 Experiment"
        print(f"Start Time: {self.start_time}")
    
    def monitor_local(self, experiment_function, params: dict):
        """
        Orchestrates modules for local monitoring, acts as the main function to use for local monitoring.

        Args:
            sts_client (obj): Returned object after initializing sts client from boto3.
            experiment_function (obj): Experiment function that is not yet called.

        Returns:
            local_results: Dictionary containing results from the psutil library.
        """

        local_monitor = local_user_monitor(experiment_function, params)

        local_results = {}

        local_results["Local Machine Experiment Metrics"] =  local_monitor
        
        return local_results
    
    def monitor_cloud(config, sts_client: object, experiment_function: object):
        """
        Orchestrates modules for cloud monitoring, acts as the main function to use for cloud monitoring.

        Args:
            sts_client (obj): Returned object after initializing sts client from boto3.
            experiment_function (obj): Experiment function that is not yet called.

        Returns:
            cloud_results: Dictionary containing results from the AWS Boto3 API.
        """

        cloud_results = {}

        experiment_cloud_monitor_ec2 = ec2_machine_cloud_monitor(config, experiment_function)
     #   experiment_cloud_ec2_metrics = ec2_instance_monitor(config)

    #    experiment_cloud_monitor_braket = experiment_braket_monitor(experiment_function)

        cloud_results["EC2 Machine Experiment Metrics"] =  experiment_cloud_monitor_ec2
      #  cloud_results["EC2 Instance Experiment Metrics"] =  experiment_cloud_ec2_metrics

       # cloud_results["Braket Experiment Metrics"] =  experiment_cloud_monitor_braket
        
        return cloud_results

    
    @staticmethod
    def __get_params(func):
        """Extracts the parameters passed on the function for logging purposes"""
        @wraps(func)
        def wrapper(*args, **kwargs):

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            params = dict(bound_args.arguments)
            
            return params
        return wrapper
    
      

