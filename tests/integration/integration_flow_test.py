import boto3, os
import numpy as np
import matplotlib.pyplot as plt
from braket.circuits import Circuit
from braket.devices import LocalSimulator
from src.classes import Monitor

ec2_client = boto3.client("ec2")

test_instance = ec2_client.run_instances(
    ImageId='ami-0123456789abcdef0',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    MetadataOptions={
        'HttpTokens': 'required',       
        'HttpEndpoint': 'enabled',     
        'HttpPutResponseHopLimit': 2   
    }
)

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

# Test

experiment_monitor = Monitor()
experiment_monitor.config.creds.ec2_client = boto3.client(
    "ec2",
    os.environ.get("AWS_ACCESS_KEY"),
    os.environ.get("AWS_SECRET_KEY"),
    os.environ.get("AWS_DEFAULT_REGION"),
)
experiment_monitor.config.creds.cw_client = boto3.client(
    "cloudwatch",
    os.environ.get("AWS_ACCESS_KEY"),
    os.environ.get("AWS_SECRET_KEY"),
    os.environ.get("AWS_DEFAULT_REGION"),
)
experiment_monitor.monitor_cloud(experiment_monitor.config.creds, quantum_rng)
