import os, boto3
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

def ec2_instance_monitor(config, experiment_function, experiment_params):
    ec2_instance_description = None
    cw_client_instance = None

    try:
        ec2_instance_description = config.creds["ec2_client"].describe_instances()
    except ClientError:
        try:
            cw_client_instance = boto3.client(
                "cloudwatch",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                region_name="us-east-1",
            )
        except NoCredentialsError:
            from QMonitor.classes import Monitor
            local_monitor = Monitor()
            return local_monitor.monitor_local(experiment_function, experiment_params)
    except NoCredentialsError:
        try:
            cw_client_instance = boto3.client(
                "cloudwatch",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                region_name="us-east-1",
            )
        except NoCredentialsError:
            from QMonitor.classes import Monitor
            local_monitor = Monitor()
            return local_monitor.monitor_local(experiment_function, experiment_params)
    except EndpointConnectionError:
        from QMonitor.classes import Monitor
        local_monitor = Monitor()
        return local_monitor.monitor_local(experiment_function, experiment_params)

    instance_types = config.creds["ec2_client"].describe_instance_types(
        InstanceTypes=["t3.micro", "m5.large"]
    )

    ec2_instance_attributes = {}

    for instance in instance_types["InstanceTypes"]:
        result = {
            "Instance": f"{instance['InstanceType']}",
            "vCPUs": f"{instance['VCpuInfo']['DefaultVCpus']}",
            "Memory": f"{instance['MemoryInfo']['SizeInMiB']} MiB",
            "Processor": f"{instance.get('ProcessorInfo', 'N/A')}",
            "GPU": f"{instance.get('GpuInfo', 'No GPU')}",
            "Hypervisor": f"{instance.get('Hypervisor', 'N/A')}",
        }
        ec2_instance_attributes[f"Instance {instance['InstanceType']}"] = result

    ec2_logged_data = {
        "ec2_instance": ec2_instance_description,
        "ec2_instance_attributes": ec2_instance_attributes,
    }

    return ec2_logged_data

def ec2_machine_cloud_monitor(config, experiment_function, experiment_params):
    infra_metrics = [
        "CPUUtilization",
        "mem_used_percent",
        "NetworkIn",
        "NetworkOut",
        "DiskReadOps",
        "DiskWriteOps",
    ]
    infra_results = []
    usage_results = {}
    ram_response = None
    ram_average = 0

    cw_client_instance = config.creds["cw_client"]

    try:
        cw_client_instance.list_dashboards(PaginationConfig={"MaxItems": 1})
    except ClientError:
        try:
            cw_new_client = boto3.client(
                "cloudwatch",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                region_name="us-east-1",
            )
            cw_client_instance = cw_new_client
        except NoCredentialsError:
            from QMonitor.classes import Monitor
            local_monitor = Monitor()
            return local_monitor.monitor_local(experiment_function, experiment_params)
    except NoCredentialsError:
        try:
            cw_new_client = boto3.client(
                "cloudwatch",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                region_name="us-east-1",
            )
            cw_client_instance = cw_new_client
        except NoCredentialsError:
            from QMonitor.classes import Monitor
            local_monitor = Monitor()
            return local_monitor.monitor_local(experiment_function, experiment_params)
    except EndpointConnectionError:
        from QMonitor.classes import Monitor
        local_monitor = Monitor()
        return local_monitor.monitor_local(experiment_function, experiment_params)

    experiment_function(**experiment_params)

    ec2_usage = config.creds["ec2_client"].describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    detected_instance_id = ""
    detected_image_id = ""
    detected_instance_type = ""
    
    reservations = ec2_usage.get("Reservations", [])
    for reservation in reservations:
        instances = reservation.get("Instances", [])
        for instance in instances:
            detected_instance_id = instance.get("InstanceId", "")
            detected_image_id = instance.get("ImageId", "")
            detected_instance_type = instance.get("InstanceType", "")
            
            launch_time = instance.get("LaunchTime")
            if not launch_time:
                continue

            current_time = datetime.now(timezone.utc)
            compute_time_used = current_time - launch_time

            usage_results["EC2_usage"] = {
                "instance_id": detected_instance_id,
                "instance_type": detected_instance_type,
                "time_used": str(compute_time_used),
            }

    if detected_instance_id:
        for metric in infra_metrics:
            if metric == "mem_used_percent":
                ram_response = cw_client_instance.get_metric_statistics(
                    Namespace="CWAgent",
                    MetricName=metric,
                    Dimensions=[
                        {"Name": "InstanceId", "Value": detected_instance_id},
                        {"Name": "ImageId", "Value": detected_image_id},
                        {"Name": "InstanceType", "Value": detected_instance_type}
                    ],
                    StartTime=datetime.now(timezone.utc) - timedelta(minutes=5),
                    EndTime=datetime.now(timezone.utc),
                    Period=300,
                    Statistics=["Average"],
                )

                if not ram_response.get("Datapoints"):
                    ram_response["RAM Summed Average"] = 0.0
                else:
                    datapoints_count = len(ram_response["Datapoints"])
                    sum_datapoints = []
                    for i in range(0, datapoints_count):
                        ram_response["Datapoints"][i]["Timestamp"] = str(ram_response["Datapoints"][i]["Timestamp"])
                        sum_datapoints.append(ram_response["Datapoints"][i]["Average"])
                    ram_average = sum(sum_datapoints) / len(sum_datapoints)
                    ram_response["RAM Summed Average"] = ram_average

                infra_results.append(ram_response)
                continue

            average = 0
            metrics = cw_client_instance.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric,
                Dimensions=[{"Name": "InstanceId", "Value": detected_instance_id}],
                StartTime=datetime.now(timezone.utc) - timedelta(minutes=5),
                EndTime=datetime.now(timezone.utc),
                Period=300,
                Statistics=["Average"],
            )

            if not metrics.get("Datapoints"):
                metrics[f"{metric} Summed Average"] = 0.0
            else:
                datapoints_count = len(metrics["Datapoints"])
                sum_datapoints = []
                for i in range(0, datapoints_count):
                    metrics["Datapoints"][i]["Timestamp"] = str(metrics["Datapoints"][i]["Timestamp"])
                    sum_datapoints.append(metrics["Datapoints"][i]["Average"])
                average = sum(sum_datapoints) / len(sum_datapoints)
                metrics[f"{metric} Summed Average"] = average

            infra_results.append(metrics)

    ec2_logged_metrics = {
        "infrastructure_metrics": infra_results,
        "usage_metrics": usage_results,
    }

    return ec2_logged_metrics