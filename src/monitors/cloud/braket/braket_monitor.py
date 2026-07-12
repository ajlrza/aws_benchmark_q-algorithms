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