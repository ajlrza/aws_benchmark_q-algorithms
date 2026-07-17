import threading, psutil, time

def local_user_monitor(experiment_function, params: dict):
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
