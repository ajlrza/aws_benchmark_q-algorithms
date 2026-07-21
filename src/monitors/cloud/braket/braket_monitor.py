import boto3, os, threading, sys
from QMonitor.classes import Monitor
from braket.aws import AwsSession
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

class ReturnableThread(threading.Thread):
    def __init__(self, target, args=()):
        super().__init__()
        self.target = target
        self.args = args
        self.result = None

    def run(self):
        self.result = self.target(*self.args)

def experiment_braket_monitor(config, experiment_function, experiment_params):
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

    thread = ReturnableThread(experiment_function, args=(experiment_params,))
    thread.start()
    thread.join(timeout=1)

    run_result = thread.result

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

    if (len(limits_list) >= 1):

        for limit in limits_list:
            usage_results["spending_limit"] = limit["spendingLimitArn"]
            usage_results["device_arn"] = limit["deviceArn"]
            usage_results["created_at"] = limit["createdAt"]
            max_budget = float(limit["spendingLimit"])
            queued_cost = float(limit["queuedSpend"])
            actual_spent = float(limit["totalSpend"])
            remaining_budget = max_budget - (actual_spent + queued_cost)
            if remaining_budget <= max_budget - 100:
                usage_results["Warning"] = True
                usage_results["remaining_budget"] = remaining_budget
            usage_results["remaining_budget"] = remaining_budget
            braket_usage["tracking_period"] = (limit["timePeriod"]["startAt"], limit["timePeriod"]["endAt"])
    else:
        print("Limits list does not exist")

    print(infra_results, usage_results)
    
    return {
        "Braket Infrastructure Metrics": infra_results,
        "Braket Usage Metrics": usage_results
    }
       