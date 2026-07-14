import os
import time
import inspect
import psutil
import boto3
from functools import wraps
from monitors.error_codes import error_codes
from datetime import datetime, timezone
from monitors.local.local_monitor import experiment_local_monitor
from monitors.cloud.braket.braket_monitor import braket_cloud_monitor
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from monitors.cloud.ec2.ec2_monitor import ec2_machine_cloud_monitor, ec2_instance_monitor

class ExperimentMonitor:

    """
      Monitors the experiment code ran on the local machine
      and gathers local-bound metrics using the psutil library
    """

    def __init__(self, results):    

        """
        Initializes experiment monitor instance, used to wrap and extract params

        Args:
            results (obj): The raw string to be cleaned.

        Returns:
            str: The sanitized, lowercase string.
        """

        self.start_time = datetime.fromtimestamp(time.time()) 
        self.computer_time = time.time()
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        self.experiment_id = f"QIntern26 Experiment"

        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
    
    def monitor_local(sts_client: object, experiment_function: object):
        """
        Orchestrates modules for local monitoring, acts as the main function to use for local monitoring.

        Args:
            sts_client (obj): Returned object after initializing sts client from boto3.
            experiment_function (obj): Experiment function that is not yet called.

        Returns:
            local_results: Dictionary containing results from the psutil library.
        """

        experiment_local_monitor = experiment_local_monitor(experiment_function)

        local_results = {}

        local_results["Local Machine Experiment Metrics"] =  experiment_local_monitor
        
        return local_results
    
    def monitor_cloud(sts_client: object, experiment_function: object):
        """
        Orchestrates modules for cloud monitoring, acts as the main function to use for cloud monitoring.

        Args:
            sts_client (obj): Returned object after initializing sts client from boto3.
            experiment_function (obj): Experiment function that is not yet called.

        Returns:
            cloud_results: Dictionary containing results from the AWS Boto3 API.
        """

        experiment_cloud_monitor = ec2_machine_cloud_monitor(experiment_function)
        experiment_cloud_instance_metrics = ec2_instance_monitor(experiment_function)

        cloud_results = {}

        cloud_results["EC2 Machine Experiment Metrics"] =  experiment_cloud_monitor
        cloud_results["EC2 Instance Experiment Metrics"] =  experiment_cloud_instance_metrics
        
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
    
class InfrastructureMonitor:

    """
      Monitors the cloud infrastructure and gathers AWS-bound 
      metrics using the boto3 through ec2 client and cloudwatch
      client
    """

    def __init__(self,  region_name: str = "us-east-1", access_key: str = None, secret_key: str = None):

        self.region_name = region_name
        self.start_time = time.time()

        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")

        self.sts_client = None
        self.ec2_client = None
        self.cw_client = None
        self.braket_client = None
        self.assumed_role = None

        try: 
            self.sts_client = boto3.client(
                'sts', 
                self.access_key,
                self.secret_key 
            )
            self.ec2_client = boto3.client(
                'ec2', 
                self.access_key,
                self.secret_key 
            )
            self.cw_client = boto3.client(
                'cloudwatch', 
                self.access_key,
                self.secret_key 
            )
            self.braket_client = boto3.client(
                'braket', 
                self.access_key,
                self.secret_key 
            )
            self.assumed_role = self.sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName="InstanceMonitor",
            )
            self.creds = self.assumed_role["Credentials"]

            print(f"Managing Instance: ")
            print("Successfully assumed monitoring EC2 and Braket instance.")

        except ClientError as Error:

             error_codes = error_codes

             if (Error.response['Error']['Code'] == error_codes[Error.response['Error']['Code']]):
                 return error_codes[Error.response['Error']['Code']]
             
             print("Client error has occured, would you like to route to experiment monitor?")
             response = input("Enter Y/N")

             match response:
                  
                  case "Y":
                       print("Returning the uninstantiated ExperimentMonitor class..")
                       return ExperimentMonitor
                  
                  case "N":
                       return 1
                  
        except NoCredentialsError:
             print("No credentials used, would you like to route to local monitor or redo?")
             response = input("Enter Y/N")

             match response:
                  
                  case "Y":
                       print("Returning the uninstantiated ExperimentMonitor class..")
                       return ExperimentMonitor
                  
                  case "N":
                       print("Retrieving credentials from the environment variables..")

                       access_key = os.environ.get("AWS_ACCESS_KEY")
                       secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")    

                       try:
                           new_infra_monitor_instance = infra_monitor_class(access_key, secret_key)
                           get_instance = new_infra_monitor_instance.ec2_client.describe_instances()

                       except NoCredentialsError as E:
                           print(f"{E} has occured, defaulting to local monitor...")

                           local_monitor = experiment_local_monitor(experiment_function)
                           return local_monitor
                       
        except EndpointConnectionError:
             print("Connection error, defaulting to local monitor..")

             local_monitor = experiment_local_monitor(experiment_function)
             return local_monitor

      
experiment_agent = ExperimentMonitor( 
    role_arn="arn:aws:iam::000000000000:role/local-mock-role", 
    region_name="us-east-1"
    )

print("----EC2 VM MONITOR----")
experiment_agent.log_to_server(ec2=True)

