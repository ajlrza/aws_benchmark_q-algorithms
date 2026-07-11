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

    def __init__(self, 
                 sts_client: object, 
                 access_key: str, 
                 secret_key: str, 
                 ):
        
        if not sts_client:
            raise ValueError("Missing required variables: sts_client")
        
        self.infra_monitor = InfrastructureMonitor(access_key, secret_key)
        self.sts_client = sts_client
        self.identity = self.sts_client.get_caller_identity()
        self.region_name = "us-east-1"

        self.access_key = access_key
        self.secret_key = secret_key

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
    
    def monitor_experiment(self, experiment_function, params: dict):
        initial_metrics = self.__get_metrics()
        cloud_infra_initial_metrics = self.infra_monitor.get_ec2_infrastructure_metrics()
        monitor_results = {}

        thread = threading.Thread(target=experiment_function, kwargs=params)
        thread.start()

        monitor_results["Cloud Machine Data"] = self.infra_monitor.get_ec2_infrastructure_metrics()
        monitor_results["Total Cloud CPU Usage"] = self.infra_monitor.get_ec2_infrastructure_metrics()["CPU_usage"] 
        monitor_results["Total Cloud RAM Usage"] = self.infra_monitor.get_ec2_infrastructure_metrics()["RAM_usage"]
        
        thread_count = 0

        time.sleep(1) 

        while (thread.is_alive()):
            thread_count = thread_count + 1
            print("Experiment function is currently running,.")
            time.sleep(0.5)

            monitor_results[f"Local Machine Data {thread_count}"] = self.__get_metrics()
            monitor_results["Total Local CPU Usage"] = [f"Local Machine Data {thread_count}"]["CPU_usage"] + [f"Local Machine Data {thread_count}"]["CPU_usage"]
            monitor_results["Total Local RAM Usage"] = [f"Local Machine Data {thread_count}"]["RAM_usage"] + [f"Local Machine Data {thread_count}"]["RAM_usage"]

        thread.join()

        monitor_results["Cloud Machine Data"] = self.infra_monitor.get_ec2_infrastructure_metrics()
        monitor_results["Total Cloud CPU Usage"] = self.infra_monitor.get_ec2_infrastructure_metrics()["CPU_usage"] 
        monitor_results["Total Cloud RAM Usage"] = self.infra_monitor.get_ec2_infrastructure_metrics()["RAM_usage"]
    
        return monitor_results

    def log_to_repo(self, results: object, monitored_results: dict, notes: str, benchmark_type: str):
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


        repo_url = "https://api.github.com/repos/Shel-y/qintern2026-quantum-benchmarking/contents/results"
        functions_to_run = []
        functions_to_run.append(("EC2", self.monitor_ec2_vm()))

        snapshot = {
            name: monitor_func for name, monitor_func in functions_to_run
        }

        parse = json.dumps(snapshot["EC2"]).encode("utf-8")
        encode_snapshot = base64.b64encode(parse)

        return snapshot
    

class InfrastructureMonitor:

    def __init__(self, access_key: str, secret_key: str, region_name: str = "us-east-1"):

        self.region_name = region_name
        self.start_time = time.time()

        self.access_key = access_key
        self.secret_key = secret_key

        print(f"Role: {self.role_arn}")
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

    def get_instance_attributes(self):

        get_instance = self.ec2_client.describe_instances() 

        ec2_instance = {
            "instance_id": get_instance["Reservations"]["Instances"]["InstanceId"],
            "image_id": get_instance["Reservations"]["Instances"]["ImageId"],
            "instance_type": get_instance["Reservations"]["Instances"]["InstanceType"],
            "architecture": get_instance["Reservations"]["Instances"]["Architecture"],
        }

        get_types = self.ec2_client.describe_instance_types(
            InstanceTypes=['t3.micro', 'm5.large']
        )

        ec2_instance_attributes = None

        for instance in self.get_types['InstanceTypes']:

            result = {
                "vCPUs": f"{instance['VCpuInfo']['DefaultVCpus']}",
                "Memory": f"{instance['MemoryInfo']['SizeInMiB']} MiB",
                "Processor": f"{instance['ProcessorInfo']}",
                "GPU": f"{instance['GpuInfo']}",
                "Hypervisor": f"{instance['Hypervisor']}"
            }

        ec2_logged_data = {
            "ec2_instance": ec2_instance,
            "ec2_instance_attributes": ec2_instance_attributes
        }
        
        return ec2_logged_data
            
    def get_ec2_infrastructure_metrics(self):

        infra_metrics = ['CPUUtilization', 'mem_used_percent', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps']
        infra_results = []

        usage_results = {}

        ram_response = None
        ram_average = 0

        for metric in infra_metrics:

            if (metric == 'mem_used_percent'):
                ram_response = self.cw_client.get_metric_statistics(
                Namespace='CWAgent',
                MetricName=metric,
                Dimensions=[{'Name': 'InstanceId', 'Value': 'i-0123456789abcdef0'}],
                StartTime=datetime.now(timezone.utc) - timedelta(minutes=5),
                EndTime=datetime.now(timezone.utc),
                Period=300,
                Statistics=['Average']
                )

                if not ram_response['Datapoints']:
                    ram_response['Average'] = 0.0
                else:
                    datapoints_count = len(ram_response['Datapoints'])
                    sum_datapoints = []
                    for i in range(0, datapoints_count):
                        sum_datapoints.append(ram_response['Datapoints'][i]['Average'])
                    ram_average = sum(sum_datapoints) / len(sum_datapoints)

                ram_response['RAM Summed Average'] = ram_average

                infra_results.append(ram_response)

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
        
        ec2_logged_metrics = {
            "infrastructure_metrics": infra_results,
            "usage_metrics": usage_results
        }

        return ec2_logged_metrics
          
    def __get_credentials_dict(self):
        """Helper to pass assumed role tokens to clients/resources."""
        return {
            "aws_access_key_id": self.access_key, 
            "aws_secret_access_key": self.secret_key, 
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

