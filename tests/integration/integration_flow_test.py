import boto3
import os
from braket.circuits import Circuit
from braket.devices import LocalSimulator
from src.classes import Monitor

ec2_client = boto3.client(
    "ec2",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

sts = boto3.client(
    "sts",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

test_instance = ec2_client.run_instances(
    ImageId="ami-0123456789abcdef0",
    MinCount=1,
    MaxCount=1,
    InstanceType="t3.micro",
    MetadataOptions={
        "HttpTokens": "required",
        "HttpEndpoint": "enabled",
        "HttpPutResponseHopLimit": 2,
    },
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

    return result


# Test

experiment_monitor = Monitor()
experiment = quantum_rng(n_bits=5, shots=10000)

experiment_monitor_local = experiment_monitor.monitor_local(
    quantum_rng(n_bits=5, shots=10000)
)

experiment_monitor_cloud_ec2 = experiment_monitor.monitor_cloud(
    experiment_monitor.config, quantum_rng(n_bits=5, shots=10000)
)

experiment_monitor_cloud_braket = experiment_monitor.monitor_cloud(
    experiment_monitor.config, quantum_rng(n_bits=5, shots=10000), experiment
)