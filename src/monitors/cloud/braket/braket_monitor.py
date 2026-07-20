import boto3, os
from QMonitor.classes import Monitor
from braket.aws import AwsSession
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

def experiment_braket_monitor(config, experiment_function, run_result, experiment_params):
    device = None

    try:
        device = config.creds['braket_client'].search_devices()
    except ClientError:
        try:
            cw_new_client = boto3.client(
                "cloudwatch",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                region_name="us-east-1",
            )
        except NoCredentialsError:
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
        except NoCredentialsError:
            local_monitor = Monitor()
            return local_monitor.monitor_local(experiment_function, experiment_params)
    except EndpointConnectionError:
        local_monitor = Monitor()
        return local_monitor.monitor_local(experiment_function, experiment_params)

    usage_results = {}
    infra_results = {}

    task_arn = getattr(run_result, "task_metadata", run_result).id if hasattr(run_result, "task_metadata") else getattr(run_result, "id", "")
    device_arn = getattr(run_result, "task_metadata", run_result).deviceId if hasattr(run_result, "task_metadata") else ""
    
    job_arn_fallback = getattr(run_result, "arn", "arn:aws:braket:us-east-1:123456789012:job/invalid-job-for-task")

    tasks = {
        "get_quantum_task": config.creds['braket_client'].get_quantum_task,
        "search_quantum_tasks": config.creds['braket_client'].search_quantum_tasks,
        "get_job": config.creds['braket_client'].get_job,
    }

    tasks_config = {
        "get_quantum_task": lambda: {"quantumTaskArn": task_arn},
        "search_quantum_tasks": lambda: {
            "filters": [
                {
                    "name": "quantumTaskArn",
                    "values": [task_arn],
                    "operator": "EQUAL",
                }
            ]
        },
        "get_job": lambda: {"jobArn": job_arn_fallback},
    }

    for task, task_value in tasks.items():
        try:
            result = task_value(**tasks_config[task]())
            infra_results[task] = result
        except Exception as e:
            infra_results[task] = {"Error": str(e)}

    braket_usage = config.creds['braket_client'].search_spending_limits(
        maxResults=5,
        filters=[{"name": "deviceArn", "values": [device_arn], "operator": "EQUAL"}],
    )

    limits_list = braket_usage.get("spendingLimits", [])

    for limit in limits_list:
        limit["spendingLimitArn"]
        limit["deviceArn"]
        limit["createdAt"]
        start_time = limit["timePeriod"]["startAt"]
        end_time = limit["timePeriod"]["endAt"]
        max_budget = float(limit["spendingLimit"])
        queued_cost = float(limit["queuedSpend"])
        actual_spent = float(limit["totalSpend"])
        remaining_budget = max_budget - (actual_spent + queued_cost)
        if remaining_budget <= max_budget - 100:
            limit["Warning"] = True
        braket_usage["trackingPeriod"] = (start_time, end_time)

    usage_results["Braket_usage"] = braket_usage

    print(infra_results, usage_results)
    
    return {
        "Braket Infrastructure Metrics": infra_results,
        "Braket Usage Metrics": usage_results
    }
                    return local_monitor_metrics

    except NoCredentialsError:
        print("No credentials used, would you like to route to local monitor or redo?")
        response = input("Enter Y/N")

        if (response == "Y"):
                local_monitor = Monitor()
                local_monitor_metrics = local_monitor.monitor_local(
                    experiment_function, experiment_params
                )
                return local_monitor_metrics
        elif (response == "N"):
                try:
                    cw_new_client = boto3.client(
                        "cloudwatch",
                        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                        aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
                        region_name="us-east-1",
                    )
                except NoCredentialsError as E:
                    print(f"{E} has occured, defaulting to local monitor...")
                    local_monitor = Monitor()
                    local_monitor_metrics = local_monitor.monitor_local(
                        experiment_function, experiment_params
                    )
                    return local_monitor_metrics

    except EndpointConnectionError:
        print("Connection error, defaulting to local monitor..")
        local_monitor = Monitor()
        local_monitor_metrics = local_monitor.monitor_local(
            experiment_function, experiment_params
        )
        return local_monitor_metrics

    usage_results = {}
    infra_results = {}

    task_arn = getattr(run_result, "task_metadata", run_result).id if hasattr(run_result, "task_metadata") else getattr(run_result, "id", "")
    device_arn = getattr(run_result, "task_metadata", run_result).deviceId if hasattr(run_result, "task_metadata") else ""
    
    job_arn_fallback = getattr(run_result, "arn", "arn:aws:braket:us-east-1:123456789012:job/invalid-job-for-task")

    tasks = {
        "get_quantum_task": config.creds['braket_client'].get_quantum_task,
        "search_quantum_tasks": config.creds['braket_client'].search_quantum_tasks,
        "get_job": config.creds['braket_client'].get_job,
    }

    tasks_config = {
        "get_quantum_task": lambda: {"quantumTaskArn": task_arn},
        "search_quantum_tasks": lambda: {
            "filters": [
                {
                    "name": "quantumTaskArn",
                    "values": [task_arn],
                    "operator": "EQUAL",
                }
            ]
        },
        "get_job": lambda: {"jobArn": job_arn_fallback},
    }

    for task, task_value in tasks.items():
        try:
            result = task_value(**tasks_config[task]())
            infra_results[task] = result
        except Exception as e:
            infra_results[task] = {"Error": str(e)}

    braket_usage = config.creds['braket_client'].search_spending_limits(
        maxResults=5,
        filters=[{"name": "deviceArn", "values": [device_arn], "operator": "EQUAL"}],
    )

    limits_list = braket_usage.get("spendingLimits", [])

    for limit in limits_list:
        limit["spendingLimitArn"]
        limit["deviceArn"]
        limit["createdAt"]
        start_time = limit["timePeriod"]["startAt"]
        end_time = limit["timePeriod"]["endAt"]
        max_budget = float(limit["spendingLimit"])
        queued_cost = float(limit["queuedSpend"])
        actual_spent = float(limit["totalSpend"])
        remaining_budget = max_budget - (actual_spent + queued_cost)
        if remaining_budget <= max_budget - 100:
            braket_usage["spendingLimits"]["Warning"] = True
        braket_usage["trackingPeriod"] = (start_time, end_time)

    usage_results["Braket_usage"] = braket_usage

    print(infra_results, usage_results)
    
    return {
        "Braket Infrastructure Metrics": infra_results,
        "Braket Usage Metrics": usage_results
    }
