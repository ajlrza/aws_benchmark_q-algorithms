import threading
import time

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