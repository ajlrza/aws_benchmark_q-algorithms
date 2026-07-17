import os
from monitors.local.local_monitor import experiment_local_monitor
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

def experiment_braket_monitor(experiment_function, infra_monitor_class, run_result):
        
        try:
            get_instance = infra_monitor_class.braket_client.get_quantum_task()

        except ClientError:
             
             print("Client error has occured, would you like to route to local monitor?")
             response = input("Enter Y/N")

             match response:
                  
                  case "Y":
                       local_monitor = experiment_local_monitor(experiment_function)
                       return local_monitor
                  
                  case "N":
                       return 1
                  
        except NoCredentialsError:
             print("No credentials used, would you like to route to local monitor or redo?")
             response = input("Enter Y/N")

             match response:
                  
                  case "Y":
                       local_monitor = experiment_local_monitor(experiment_function)
                       return local_monitor
                  
                  case "N":
                       print("Retrieving credentials from the environment variables..")

                       access_key = os.environ.get("AWS_ACCESS_KEY")
                       secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")    

                       try:
                           new_infra_monitor_instance = infra_monitor_class(access_key, secret_key)
                           get_instance = new_infra_monitor_instance.ec2_client.describe_instances()

                       except NoCredentialsError as E:
                           print(f"{E} has occured, defaulting to local monitor...")

                           local_monitor = experiment_local_monitor(experiment_function)
                           return local_monitor
                       
        except EndpointConnectionError:
             print("Connection error, defaulting to local monitor..")

             local_monitor = experiment_local_monitor(experiment_function)
             return local_monitor

        usage_results = {}

        infra_results = {}

        tasks = {
            'get_quantum_task': infra_monitor_class.braket_client.get_quantum_task, 
            'search_quantum_tasks': infra_monitor_class.braket_client.search_quantum_tasks, 
            'get_job': infra_monitor_class.braket_client.get_job
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

        braket_usage = infra_monitor_class.braket_client.search_spending_limits(
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