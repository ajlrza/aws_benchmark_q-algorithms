import os
import time
import datetime
import requests
import matplotlib as plt
import psutil
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from datetime import timedelta

class ExperimentMonitor:

    '''
        agent = ExperimentMonitor(
        role_arn="arn:aws:iam::123456789012:role/MyS3AccessRole",
        bucket_names=["my-app-data-bucket", "my-app-logs-bucket"]
        )
        agent.log_to_bucket(ec2=True, braket=True)
        agent.generate_viz()
    '''

    def __init__(self, role_arn: str, bucket: str, region_name: str = "us-east-1"):
        if not role_arn or not bucket:
            raise ValueError("Missing required variables: role_arn or buckets.")
            
        self.role_arn = role_arn
        self.bucket = bucket.lower()
        self.region_name = region_name
        self.start_time = time.time()
        self.bucket_list = []
        self.bucket_list.append(self.bucket)

        print(f"Role: {self.role_arn}")
        print(f"Region: {self.region_name}")
        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
        
        try: 
            self.sts_client = boto3.client("sts", region_name=self.region_name)
            self.s3_client = boto3.client('s3', **self._get_credentials_dict())

            self.assumed_role = self.sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName="ExperimentMonitor",
            )
            self.creds = self.assumed_role["Credentials"]

            self.s3_client.create_bucket(f"{self._assumed_role['AssumedRoleUser']['AssumedRoleId']}'s Bucket")

            print(f"Managing Buckets: {', '.join(self.bucket_list)}")
            print("Successfully assumed monitoring IAM role and experiment.")

        except Exception as e:
            print(f"Failed to assume IAM role: {e}")
            raise

    def __get_credentials_dict(self):
        """Helper to pass assumed role tokens to clients/resources."""
        return {
            "aws_access_key_id": self.creds["AccessKeyId"],
            "aws_secret_access_key": self.creds["SecretAccessKey"],
            "aws_session_token": self.creds["SessionToken"],
            "region_name": self.region_name
        }

    def __get_live_metrics(self):
        """Dynamically calculates current system utilization and latency."""
        return {
            "I/O latency": time.time() - self.start_time,
            "CPU_usage": psutil.cpu_percent(interval=0.1), 
            "RAM_usage": psutil.virtual_memory().percent,
            "Datetime": datetime.datetime.now().isoformat()
        }
    
    def log_to_server(self, ec2=False, braket=False):
        """Logs the associated data to Render server."""
        
        server_url = "https://onrender.com"
        functions_to_run = []

        if ec2: 
            functions_to_run.append(("EC2", self.__monitor_ec2_vm()))
        if braket: 
            functions_to_run.append(("Braket", self.__monitor_braket_vm()))
        snapshot = {
            name: monitor_func() for name, monitor_func in functions_to_run
        }

        if not functions_to_run:
            return

        try:
            response = requests.post(server_url, json=snapshot[f"{'EC2' if ec2 else 'Braket'}"], timeout=5)
            print(f"Status Code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to send metrics: {e}")
            print("\nPrinting snapshots..\n" + "=" * 25)
            for service in ["EC2", "Braket"]:
                print(f"{service} Monitored Data")
                print("-" * 25)
                print(snapshot[service])
                print() 

    def __monitor__vm(self):
        try:
            # Use assumed credentials to create client
            s3_client = boto3.client('s3', **self.__get_credentials_dict())
            s3_client.list_buckets() 
            print("S3 tracking successful.")
            
            s3_resource = boto3.resource('s3', **self.__get_credentials_dict())
            return {
                "infrastructure_metrics": {
                    "S3_resource": s3_resource,
                    "vm_metrics": self._get_live_metrics(),
                    "cw_metrics": {}
                }
            }
        except (NoCredentialsError, ClientError, EndpointConnectionError) as e:
            print(f"S3 Monitoring Error: {e}")
            return None

    def __monitor_ec2_vm(self):
        try:
            ec2_client = boto3.client('ec2', self.__get_credentials_dict())
            ec2_client.describe_instances() 
            print("EC2 tracking successful.")

            ec2_resource = boto3.resource('ec2', self.__get_credentials_dict())
            return {
                "infrastructure_metrics": {
                    "EC2_resource": ec2_resource,
                    "vm_metrics": self.__get_live_metrics(),
                    "cw_metrics": {}
                }
            }
        except (NoCredentialsError, ClientError, EndpointConnectionError) as e:
            print(f"EC2 Monitoring Error: {e}")
            return None
    
    def __monitor_braket_vm(self):
        try:
            braket_client = boto3.client('braket', **self.__get_credentials_dict())
            braket_client.search_devices(filters=[]) 
            print("Braket tracking successful.")

            return {
                "infrastructure_metrics": {
                    "Braket_client": braket_client, 
                    "vm_metrics": self.__get_live_metrics(),
                    "cw_metrics": {}
                }
            }
        except (NoCredentialsError, ClientError, EndpointConnectionError) as e:
            print(f"Braket Monitoring Error: {e}")
            return None


class InfrastructureMonitor:

    def __init__(self, role_arn: str, instance: str, region_name: str = "us-east-1"):
        if not role_arn or not instance:
            raise ValueError("Missing required variables: role_arn or buckets.")
            
        self.role_arn = role_arn
        self.instance = instance
        self.region_name = region_name
        self.start_time = time.time()
        self.bucket_list = []
        self.bucket_list.append(self.bucket)

        print(f"Role: {self.role_arn}")
        print(f"Region: {self.region_name}")
        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
        
        try: 
            self.sts_client = boto3.client("sts", region_name=self.region_name)
            self.ec2_client = boto3.client("ec2", **self._get_credentials_dict())
            self.cw_client = boto3.client("cloudwatch", **self._get_credentials_dict())

            self.assumed_role = self.sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName="InstanceMonitor",
            )
            self.creds = self.assumed_role["Credentials"]

            self.s3_client.create_bucket(f"{self._assumed_role['AssumedRoleUser']['AssumedRoleId']}'s Bucket")

            print(f"Managing Instance: {self.instance}")
            print("Successfully assumed monitoring IAM role and EC2 instance.")

        except Exception as e:
            print(f"Failed to assume IAM role: {e}")
            raise

        def get_instance_attributes(self):
            get_types = self.ec2_client.describe_instance_types(
                InstanceTypes=['t3.micro', 'm5.large']
            )

            for instance in self.get_types['InstanceTypes']:
                return {
                    "Instance": f"{instance['InstanceType']}",
                    "vCPUs": f"{instance['VCpuInfo']['DefaultVCpus']}",
                    "Memory": f"{instance['MemoryInfo']['SizeInMiB']} MiB",
                    "Processor": f"{instance['ProcessorInfo']}",
                    "GPU": f"{instance['GpuInfo']}",
                    "Hypervisor": f"{instance['Hypervisor']}"
                }
            
        def get_ec2_infrastructure_metrics(self):

            get_instance = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
            instance_id = get_instance.text

            metrics = ['CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps']
            results = {}

            for metric in metrics:
                ec2_metrics = self.cw_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric,
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=datetime.utcnow() - timedelta(minutes=5),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=['Average']
                )
                results[ec2_metrics['MetricName']] = ec2_metrics

            return results
        
        def get_braket_infrastructure_metrics(self):
            pass
     
