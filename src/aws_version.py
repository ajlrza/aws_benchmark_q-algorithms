import os
import time
import json
import base64
from datetime import datetime, timezone, timedelta
import requests
from braket.circuits import Circuit
from braket.devices import LocalSimulator
import matplotlib as plt
import psutil
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

class ExperimentMonitor:

    '''
        agent = ExperimentMonitor(
        role_arn="arn:aws:iam::123456789012:role/MyS3AccessRole",
        bucket_names=["my-app-data-bucket", "my-app-logs-bucket"]
        )
        agent.log_to_bucket(ec2=True, braket=True)
        agent.generate_viz()
    '''

    def __init__(self, role_arn: str, region_name: str = "us-east-1"):
        if not role_arn:
            raise ValueError("Missing required variables: role_arn or buckets.")
            
        self.role_arn = role_arn
        self.region_name = region_name
        
        self.start_time = datetime.fromtimestamp(time.time()) 
        self.computer_time = time.time()
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Role: {self.role_arn}")
        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
        
        try: 
            self.sts_client = boto3.client(
                "sts", 
                **self.__get_credentials_dict(),
                endpoint_url=LOCALSTACK_URL,
                )

            self.assumed_role = self.sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName="ExperimentMonitor",
            )
            self.creds = self.assumed_role["Credentials"]

            print("Successfully monitoring experiment.")

        except Exception as e:
            print(f"Failed to assume IAM role: {e}")
            raise

    def __get_credentials_dict(self):
        """Helper to pass assumed role tokens to clients/resources."""
        return {
            "aws_access_key_id": "test", #self.creds["AccessKeyId"],
            "aws_secret_access_key": "test", #self.creds["SecretAccessKey"],
            "aws_session_token": "test",#self.creds["SessionToken"],
            "region_name": "us-east-1"#self.region_name
        }

    def __get_live_metrics(self):
        """Dynamically calculates current system utilization and latency in jupyter notebook."""
        return {
            "I/O latency": time.time() - self.computer_time,
            "CPU_usage": psutil.cpu_percent(interval=0.1), 
            "RAM_usage": psutil.virtual_memory().percent,
            "Datetime": datetime.now(timezone.utc).isoformat()
        }
    
    def log_to_server(self, ec2=False, braket=False):
        """Logs the associated data to Render server."""

        server_url = "https://api.github.com/repos/Shel-y/qintern2026-quantum-benchmarking/contents/results"
        functions_to_run = []

        if ec2: 
            functions_to_run.append(("EC2", self.monitor_ec2_vm()))
        if braket: 
            functions_to_run.append(("Braket", self.monitor_braket_vm()))
        snapshot = {
            name: monitor_func for name, monitor_func in functions_to_run
        }

        if not functions_to_run:
            return

        parse = json.dumps(snapshot[f"{'EC2' if ec2 else 'Braket'}"]).encode("utf-8")
        encode_snapshot = base64.b64encode(parse)

        return snapshot

    def __monitor__vm(self) -> object:
        try:
            # Use assumed credentials to create client
            self.s3_client.list_buckets() 
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

    def monitor_ec2_vm(self) -> object:
        try:

            ec2_client = boto3.client(
                'ec2', 
                **self.__get_credentials_dict(), 
                endpoint_url=LOCALSTACK_URL,
            )

            get_instance = ec2_client.describe_instances() 

            ec2_instance_log = {
                "instance_id": get_instance["Reservations"]["Instances"]["InstanceId"],
                "image_id": get_instance["Reservations"]["Instances"]["ImageId"],
                "instance_type": get_instance["Reservations"]["Instances"]["InstanceType"],
                "architecture": get_instance["Reservations"]["Instances"]["Architecture"],
            }

            result = {
                "infrastructure_log": {
                    "EC2_config": ec2_instance_log,
                    "psutil_metrics": self.__get_live_metrics(),
                }
            }
            print(result)

        except (NoCredentialsError, ClientError, EndpointConnectionError) as e:
            print(f"EC2 Monitoring Error: {e}")
            return None
    
    def monitor_braket_vm(self):
        try:
            braket_client = boto3.client(
                'braket', 
                **self.__get_credentials_dict(), 
                endpoint_url=LOCALSTACK_URL,
            )
            braket_client.search_devices(filters=[]) 
            print("Braket tracking successful.")

            result = {
                "infrastructure_metrics": {
                    "Braket_client": braket_client, 
                    "psutil_metrics": self.__get_live_metrics(),
                }
            }
            print(result)

        except (NoCredentialsError, ClientError, EndpointConnectionError) as e:
            print(f"Braket Monitoring Error: {e}")
            return None

class InfrastructureMonitor:

    def __init__(self, role_arn: str, region_name: str = "us-east-1"):

        self.role_arn = role_arn
        self.region_name = region_name
        self.start_time = time.time()

        print(f"Role: {self.role_arn}")
        print(f"Region: {self.region_name}")
        print(f"Start Time: {self.start_time}")
        
        try: 

            self.sts_client = boto3.client(
                'sts', 
                **self.__get_credentials_dict(), 
                endpoint_url=LOCALSTACK_URL,
            )
            self.ec2_client = boto3.client(
                'ec2', 
                endpoint_url=LOCALSTACK_URL,
                **self.__get_credentials_dict()
            )
            self.cw_client = boto3.client(
                'cloudwatch', 
                **self.__get_credentials_dict(), 
                endpoint_url=LOCALSTACK_URL,
            )
            self.braket_client = boto3.client(
                'braket', 
                **self.__get_credentials_dict(), 
                endpoint_url=LOCALSTACK_URL,
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

    def get_instance_attributes(self):
        paginator = None

        if (self.ec2_paginator("describe_instance_types")):
            paginated = self.ec2_paginator("describe_instance_types")

        get_types = self.ec2_client.describe_instance_types(
            InstanceTypes=['t3.micro', 'm5.large']
        )

        result = None

        for instance in self.get_types['InstanceTypes']:

            result = {
                "Instance": f"{instance['InstanceType']}",
                "vCPUs": f"{instance['VCpuInfo']['DefaultVCpus']}",
                "Memory": f"{instance['MemoryInfo']['SizeInMiB']} MiB",
                "Processor": f"{instance['ProcessorInfo']}",
                "GPU": f"{instance['GpuInfo']}",
                "Hypervisor": f"{instance['Hypervisor']}"
            }

        print(result)
            
    def get_ec2_infrastructure_metrics(self):

        #get_instance = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
        #instance_id = get_instance.text

        infra_metrics = ['CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps']
        infra_results = []

        usage_results = {}

        for metric in infra_metrics:
            average = 0
            metrics = self.cw_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric,
                Dimensions=[{'Name': 'InstanceId', 'Value': 'i-0123456789abcdef0'}],
                StartTime=datetime.now(timezone.utc) - timedelta(minutes=5),
                EndTime=datetime.now(timezone.utc),
                Period=300,
                Statistics=['Average']
            )

            if not metrics['Datapoints']:
                metrics['Average'] = 0.0

            else:
                datapoints_count = len(metrics['Datapoints'])
                sum_datapoints = []
                for i in range(0, datapoints_count):
                    sum_datapoints.append(metrics['Datapoints'][i]['Average'])
                average = sum(sum_datapoints) / len(sum_datapoints)

            metrics[f'${metric} Summed Average'] = average
            
            infra_results.append(metrics)

        ec2_usage = self.ec2_client.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )

        # add resoucrse usage and spends for braket later

        reservations = ec2_usage.get('Reservations', [])

        for reservation in reservations:
            instances = reservation.get('Instances', [])
            for instance in instances:
                
                launch_time = instance.get("LaunchTime")
                if not launch_time:
                    continue
                    
                current_time = datetime.now(timezone.utc)
                compute_time_used = current_time - launch_time

                
                usage_results["EC2_usage"] = {
                    'instance_id': instance.get("InstanceId"),
                    'instance_type': instance.get("InstanceType"),
                    'time_used': str(compute_time_used)  
                }
        
        print(infra_results)
        
    def __get_credentials_dict(self):
        """Helper to pass assumed role tokens to clients/resources."""
        return {
            "aws_access_key_id": "test", #self.creds["AccessKeyId"],
            "aws_secret_access_key": "test", #self.creds["SecretAccessKey"],
            "aws_session_token": "test",#self.creds["SessionToken"],
            "region_name": "us-east-1"#self.region_name
        }
        
    def get_braket_infrastructure_metrics(self, run_result):

        usage_results = {}

        infra_results = {}

        tasks = {
            'get_quantum_task': self.braket_client.get_quantum_task, 
            'search_quantum_tasks': self.braket_client.search_quantum_tasks, 
            'get_job': self.braket_client.get_job
        }
        
        tasks_config = {
            'get_quantum_task': lambda: {"quantumTaskArn": run_result.id}, 
            'search_quantum_tasks': lambda: {"filters": [{'name': 'quantumTaskArn', 'values': [run_result.id], 'operator': 'EQUAL'}]}, 
            'get_job': lambda: {"jobArn": run_result.arn}
        }

        for task, task_value in tasks.items():
            result = task_value(
                **tasks_config[task]()
            )
            infra_results[task] = result

        braket_usage = self.braket_client.search_spending_limits(
            maxResults=5,
            filters=[
                {
                    'name': 'deviceArn',
                    'values': [run_result.id],
                    'operator': 'EQUAL'
                }
            ]
        )

        limits_list = braket_usage['spendingLimits']

        for limit in limits_list:

            limit_arn = limit['spendingLimitArn']
            device = limit['deviceArn']
            created_date = limit['createdAt']
            
            start_time = limit['timePeriod']['startAt']
            end_time = limit['timePeriod']['endAt']
            
            max_budget = float(limit['spendingLimit'])
            queued_cost = float(limit['queuedSpend'])
            actual_spent = float(limit['totalSpend'])
            
            remaining_budget = max_budget - (actual_spent + queued_cost)
            if (remaining_budget <= max_budget - 100):
                braket_usage['spendingLimits']['Warning'] = True
            
            braket_usage['trackingPeriod'] = (start_time, end_time)           
            
        usage_results['Braket_usage'] = braket_usage

        print(infra_results, usage_results)

            
experiment_agent = ExperimentMonitor( 
    role_arn="arn:aws:iam::000000000000:role/local-mock-role", 
    region_name="us-east-1"
    )

print("----EC2 VM MONITOR----")
experiment_agent.log_to_server(ec2=True)

