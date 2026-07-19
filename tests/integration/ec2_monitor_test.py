import boto3, os
import numpy as np
import requests, json, base64
from datetime import datetime
import matplotlib.pyplot as plt
from braket.circuits import Circuit
from braket.devices import LocalSimulator
from src.classes import Monitor

ec2_client = boto3.client("ec2")


sts = boto3.client(
    'sts',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
    region_name=os.environ.get("AWS_DEFAULT_REGION"),
)

def quantum_rng(n_bits, shots=10000):
    """
    Generate quantum random bits using Hadamard gates.
    n_bits: number of qubits (= number of random bits per shot)
    shots: number of measurements
    """
    circuit = Circuit()
    for i in range(n_bits):
        circuit.h(i)

    device = LocalSimulator()
    result = device.run(circuit, shots=shots).result()

    return result.measurement_counts

def automated_test(experiment_function, experiment_params=None, tests=0):
    test_results = []
    experiment_monitor_result = None

    token = os.environ.get("PAT_TOKEN")
    owner = os.environ.get("GITHUB_USERNAME")
    repo = os.environ.get("REPOSITORY_NAME")

    datetime_now = datetime.now()
    path = f"test_logs/monitor_test_{datetime.now()}" 
    branch = "main"  

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}.md"

    file_content = None

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if (tests > 0):
        test_iteration = 0
        while (test_iteration != tests):

            test_iteration += 1
            
            experiment_monitor = Monitor()

            experiment_monitor_result = experiment_monitor.monitor_cloud(experiment_monitor.config.creds, quantum_rng)

            test_results.append(experiment_monitor_result)

        file_content = json.dumps(test_results, indent=2)
        encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"{test_iteration} Monitor Tests",  
            "content": encoded_content,
            "branch": branch
        }
        response = requests.put(url, json=payload, headers=headers)
        print(response)
    
    elif (tests == 0):

        experiment_monitor = Monitor()

        experiment_monitor_result = experiment_monitor.monitor_cloud(experiment_monitor.config, quantum_rng)

        file_content = json.dumps(experiment_monitor_result, indent=2)
        encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Monitor Test 1",  
            "content": encoded_content,
            "branch": branch
        }
        response = requests.put(url, json=payload, headers=headers)
        print(response)

# Test
test = automated_test(quantum_rng, experiment_params=None)