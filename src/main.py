import os
import time
import json
import base64
import inspect
import threading
import requests
import psutil
import boto3
import matplotlib as plt
from functools import wraps
from typing import Callable
from braket.circuits import Circuit
from braket.devices import LocalSimulator
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

class ExperimentMonitor:

    '''
      Monitors the experiment code ran on the local machine
      and gathers local-bound metrics using the psutil library
    '''

    def __init__(self, sts_client: object):
        
        if not sts_client:
            raise ValueError("Missing required variables: sts_client")
        
        self.access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        
        self.infra_monitor = InfrastructureMonitor(self.access_key, self.secret_key)
        self.sts_client = sts_client
        self.identity = self.sts_client.get_caller_identity()
        self.region_name = "us-east-1"

        self.results = None
        self.experiment_id = "qi26_26_QRNG_"
        self.simulator = None
        self.circuit_params = {}
        self.metrics = {}
        self.environment = {}

        self.start_time = datetime.fromtimestamp(time.time()) 
        self.computer_time = time.time()
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
        

    def __get_credentials_dict(self):
        """Helper to pass assumed role tokens to clients/resources."""
        return {
            "aws_access_key": self.access_key, 
            "aws_secret_access_key": self.secret_key, 
        }

    def __get_metrics(self):
        """Calculates current system utilization and latency in jupyter notebook."""
        return {
            "I/O latency": time.time() - self.computer_time,
            "CPU_usage": psutil.cpu_percent(interval=0.1), 
            "RAM_usage": psutil.virtual_memory().percent,
            "Datetime": datetime.now(timezone.utc).isoformat()
        }
    
    def __get_params(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            #bound_args.apply_defaults() 
            params = dict(bound_args.arguments)
            
            return params
        return wrapper
    
    
class InfrastructureMonitor:

    '''
      Monitors the cloud infrastructure and gathers AWS-bound 
      metrics using the boto3 through ec2 client and cloudwatch
      client
    '''

    def __init__(self, region_name = "us-east-1"):

        self.region_name = region_name
        self.start_time = time.time()

        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
        
        try: 
            self.sts_client = boto3.client(
                'sts', 
                **self.__get_credentials_dict(), 
            )
            self.ec2_client = boto3.client(
                'ec2', 
                **self.__get_credentials_dict()
            )
            self.cw_client = boto3.client(
                'cloudwatch', 
                **self.__get_credentials_dict(), 
            )
            self.braket_client = boto3.client(
                'braket', 
                **self.__get_credentials_dict(), 
            )

            self.assumed_role = self.sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName="InstanceMonitor",
            )
            self.creds = self.assumed_role["Credentials"]

            print(f"Managing Instance: ")
            print("Successfully assumed monitoring IAM role and EC2 instance.")

        except Exception as e:
            print(f"Failed to assume IAM role: {e}")
            raise
          
    def __get_credentials_dict(self):
        """Helper to pass assumed role tokens to clients/resources."""
        return {
            "aws_access_key_id": self.access_key, 
            "aws_secret_access_key": self.secret_key, 
        }

            
experiment_agent = ExperimentMonitor( 
    role_arn="arn:aws:iam::000000000000:role/local-mock-role", 
    region_name="us-east-1"
    )

print("----EC2 VM MONITOR----")
experiment_agent.log_to_server(ec2=True)

