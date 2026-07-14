import threading
import psutil
from datetime import datetime, timezone
import time

def experiment_local_monitor(experiment_function, params: dict):
        """Calculates system utilization and latency in the local machine."""

        monitor_results = {}
        thread_count = 0
        time.sleep(1) 

        thread = threading.Thread(target=experiment_function, kwargs=params)
        thread.start()
        
        while (thread.is_alive()):
            thread_count = thread_count + 1
            print("Experiment function is currently running,.")
            time.sleep(0.5)

            if (psutil.virtual_memory().percent >= 98.00):
                  print("Out Of Memory Risk...")
                  print("Sleeping for 10 seconds..")
                  time.sleep(10)

            monitor_results[f"Local CPU Usage: Thread {thread_count}"] = psutil.cpu_percent(interval=0.1) 
            monitor_results[f"Local RAM Usage: Thread {thread_count}"] = psutil.virtual_memory().percent
            monitor_results[f"Local I/O Disk Latency: Thread {thread_count}"] = psutil.disk_io_counters()

        return monitor_results


def experiment_dual_monitor(infra_monitor_class, experiment_monitor_class, experiment_function, params: dict):
        """Monitors the experiment both locally and in the cloud through ec2, cloudwatch, and braket."""
        infra_monitor_instance = infra_monitor_class()
        
        initial_metrics = experiment_monitor_class.__get_metrics()
        cloud_infra_initial_metrics = infra_monitor_instance.get_ec2_infrastructure_metrics()
        monitor_results = {}

        thread = threading.Thread(target=experiment_function, kwargs=params)
        thread.start()

        monitor_results["Cloud Machine Data"] = infra_monitor_instance.get_ec2_infrastructure_metrics()
        monitor_results["Total Cloud CPU Usage"] = infra_monitor_instance.get_ec2_infrastructure_metrics()["CPU_usage"] 
        monitor_results["Total Cloud RAM Usage"] = infra_monitor_instance.get_ec2_infrastructure_metrics()["RAM_usage"]
        
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
            monitor_results["Total Local CPU Usage"] = [f"Local Machine Data {thread_count}"]["CPU_usage"] + [f"Local Machine Data {thread_count}"]["CPU_usage"]
            monitor_results["Total Local RAM Usage"] = [f"Local Machine Data {thread_count}"]["RAM_usage"] + [f"Local Machine Data {thread_count}"]["RAM_usage"]

        thread.join()

        monitor_results["Cloud Machine Data"] = infra_monitor_instance.get_ec2_infrastructure_metrics()
        monitor_results["Total Cloud CPU Usage"] = infra_monitor_instance.get_ec2_infrastructure_metrics()["CPU_usage"] 
        monitor_results["Total Cloud RAM Usage"] = infra_monitor_instance.get_ec2_infrastructure_metrics()["RAM_usage"]
    
        return monitor_results