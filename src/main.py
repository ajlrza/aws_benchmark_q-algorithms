import os
import time
import inspect
import psutil
import boto3
from datetime import datetime, timezone
from functools import wraps

class ExperimentMonitor:

    """
      Monitors the experiment code ran on the local machine
      and gathers local-bound metrics using the psutil library
    """

    def __init__(self, results):    

        self.results = results

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
            print("Successfully assumed monitoring EC2 and Braket instance.")

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

