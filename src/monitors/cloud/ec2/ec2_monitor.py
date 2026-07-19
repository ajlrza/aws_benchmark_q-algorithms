import os, threading, time
from unittest.mock import MagicMock
from ....config.master_config import Config
from datetime import datetime, timezone, timedelta
from ....monitors.local.local_monitor import local_user_monitor
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

def ec2_instance_monitor(config, experiment_function):
        
        ec2_instance_description = None

        try:
             ec2_instance_description = config.creds['ec2_client'].describe_instances()

        except ClientError:
             
             print("Client error has occured, would you like to route to local monitor?")
             response = input("Enter Y/N")

             match response:
                  
                  case "Y":
                       local_monitor = local_user_monitor(experiment_function)
                       return local_monitor
                  
                  case "N":
                       return 1
                  
        except NoCredentialsError:
             print("No credentials used, would you like to route to local monitor or redo?")
             response = input("Enter Y/N")

             match response:
                  
                  case "Y":
                       local_monitor = local_user_monitor(experiment_function)
                       return local_monitor
                  
                  case "N":
                       print("Retrieving credentials from the environment variables..")

                       access_key = os.environ.get("AWS_ACCESS_KEY")
                       secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")    

                       try:
                           get_instance = config.ec2_client.describe_instances()

                       except NoCredentialsError as E:
                           print(f"{E} has occured, defaulting to local monitor...")

                           local_monitor = local_user_monitor(experiment_function)
                           return local_monitor
                       
        except EndpointConnectionError:
             print("Connection error, defaulting to local monitor..")

             local_monitor = local_user_monitor(experiment_function)
             return local_monitor
        
        if  ec2_instance_description is None:
            print("Could not retrieve AWS data. Aborting process.")
                  
        mocked_response = {
            'InstanceTypes': [
                {
                    'InstanceType': 't3.micro',
                    'VCpuInfo': {'DefaultVCpus': 2, 'DefaultCores': 1, 'DefaultThreadsPerCore': 2},
                    'MemoryInfo': {'SizeInMiB': 1024},
                    'ProcessorInfo': {'SupportedArchitectures': ['x86_64']},
                    'GpuInfo': 'No GPU',
                    'Hypervisor': 'nitro'
                },
                {
                    'InstanceType': 'm5.large',
                    'VCpuInfo': {'DefaultVCpus': 2, 'DefaultCores': 1, 'DefaultThreadsPerCore': 2},
                    'MemoryInfo': {'SizeInMiB': 8192},
                    'ProcessorInfo': {'SupportedArchitectures': ['x86_64']},
                    'GpuInfo': 'No GPU',
                    'Hypervisor': 'nitro'
                }
            ]
        }

        config.creds['ec2_client'].describe_instance_types = MagicMock(return_value=mocked_response)

        instance_types = config.creds['ec2_client'].describe_instance_types(
            InstanceTypes=['t3.micro', 'm5.large']
        )

        ec2_instance_attributes = {}

        for instance in instance_types['InstanceTypes']:

            result = {
                "Instance": f"{instance['InstanceType']}",
                "vCPUs": f"{instance['VCpuInfo']['DefaultVCpus']}",
                "Memory": f"{instance['MemoryInfo']['SizeInMiB']} MiB",
                "Processor": f"{instance.get('ProcessorInfo', 'N/A')}",
                "GPU": f"{instance.get('GpuInfo', 'No GPU')}",
                "Hypervisor": f"{instance.get('Hypervisor', 'N/A')}"
            }

            ec2_instance_attributes[f"Instance {instance}"] = result

        ec2_logged_data = {
            "ec2_instance": ec2_instance_description,
            "ec2_instance_attributes": ec2_instance_attributes
        }
        
        return ec2_logged_data
            
def ec2_machine_cloud_monitor(config):

        infra_metrics = ['CPUUtilization', 'mem_used_percent', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps']
        infra_results = []

        usage_results = {}

        ram_response = None
        ram_average = 0

        for metric in infra_metrics:

            if (metric == 'mem_used_percent'):
                ram_response = config.creds['cw_client'].get_metric_statistics(
                Namespace='CWAgent',
                MetricName=metric,
                Dimensions=[{'Name': 'InstanceId', 'Value': 'i-0123456789abcdef0'}],
                StartTime=str(datetime.now(timezone.utc) - timedelta(minutes=5)),
                EndTime=str(datetime.now(timezone.utc)),
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
            metrics = config.creds['cw_client'].get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric,
                Dimensions=[{'Name': "InstanceId", 'Value': "ami-0123456789abcdef0"}],
                StartTime=str(datetime.now(timezone.utc) - timedelta(minutes=5)),
                EndTime=str(datetime.now(timezone.utc)),
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

        ec2_usage = config.creds['ec2_client'].describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )

        reservations = ec2_usage.get('Reservations', [])

        for reservation in reservations:
            instances = reservation.get('Instances', [])
            for instance in instances:
                
                launch_time = instance.get("LaunchTime")
                if not launch_time:
                    continue
                    
                current_time = str(datetime.now(timezone.utc))
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

def experiment_dual_monitor(config, experiment_monitor_class, experiment_function, params: dict):
        """Monitors the experiment both locally and in the cloud through ec2, cloudwatch, and braket."""
        
        initial_metrics = experiment_monitor_class.__get_metrics()
        cloud_infra_initial_metrics = config.creds['ec2_client'].get_ec2_infrastructure_metrics()
        monitor_results = {}

        thread = threading.Thread(target=experiment_function, kwargs=params)
        thread.start()

        monitor_results["Cloud Machine Data"] = config.creds['ec2_client'].get_ec2_infrastructure_metrics()
        monitor_results["Total Cloud CPU Usage"] = config.creds['ec2_client'].get_ec2_infrastructure_metrics()["CPU_usage"] 
        monitor_results["Total Cloud RAM Usage"] = config.creds['ec2_client'].get_ec2_infrastructure_metrics()["RAM_usage"]
        
        thread_count = 0

        time.sleep(1) 

        while (thread.is_alive()):
            thread_count = thread_count + 1
            print("Experiment function is currently running,.")
            time.sleep(0.5)

            if (monitor_results["Total Local RAM Usage"] >= 98.00):
                  print("Out Of Memory Risk...")
                  print("Sleeping for 10 seconds..")
                  time.sleep(10)

            monitor_results["Local Machine Data"][f"Local Machine Data {thread_count}"] = experiment_monitor_class.__get_metrics()
            monitor_results["Total Local CPU Usage"][f"Local Machine Data {thread_count}"] = ["Local Machine Data"][f"Local Machine Data {thread_count}"]["CPU_usage"] + [f"Local Machine Data {thread_count}"]["CPU_usage"]
            monitor_results["Total Local RAM Usage"][f"Local Machine Data {thread_count}"] = ["Local Machine Data"][f"Local Machine Data {thread_count}"]["RAM_usage"] + [f"Local Machine Data {thread_count}"]["RAM_usage"]

        thread.join()

        monitor_results["Cloud Machine Data"] = config.creds['ec2_client'].get_ec2_infrastructure_metrics()
        monitor_results["Total Cloud CPU Usage"] = config.creds['ec2_client'].get_ec2_infrastructure_metrics()["CPU_usage"] 
        monitor_results["Total Cloud RAM Usage"] = config.creds['ec2_client'].get_ec2_infrastructure_metrics()["RAM_usage"]
    
        return monitor_results