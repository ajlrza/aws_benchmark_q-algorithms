from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError


def get_instance_attributes(infra_monitor_class):

        try:
            get_instance = infra_monitor_class.ec2_client.describe_instances()
        except ClientError:

             print("Client error has occured, would you like to route to local monitor?")
             response = input("Enter Y/N")

             match response:
                  case "Y":
                       local_monitor = local_machine_monitor(experiment_function, params: dict)
                       return local_monitor
                  case "N":
                       return 1

        ec2_instance = {
            "instance_id": get_instance["Reservations"]["Instances"]["InstanceId"],
            "image_id": get_instance["Reservations"]["Instances"]["ImageId"],
            "instance_type": get_instance["Reservations"]["Instances"]["InstanceType"],
            "architecture": get_instance["Reservations"]["Instances"]["Architecture"],
        }

        get_types = infra_monitor_class.ec2_client.describe_instance_types(
            InstanceTypes=['t3.micro', 'm5.large']
        )

        ec2_instance_attributes = None

        for instance in infra_monitor_class.get_types['InstanceTypes']:

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
            
def get_ec2_infrastructure_metrics(infra_monitor_class):

        infra_metrics = ['CPUUtilization', 'mem_used_percent', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps']
        infra_results = []

        usage_results = {}

        ram_response = None
        ram_average = 0

        for metric in infra_metrics:

            if (metric == 'mem_used_percent'):
                ram_response = infra_monitor_class.cw_client.get_metric_statistics(
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
            metrics = infra_monitor_class.cw_client.get_metric_statistics(
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

        ec2_usage = infra_monitor_class.ec2_client.describe_instances(
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