import os
from dataclasses import dataclass

@dataclass
class CredsConfig:
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    sts_client: object
    cw_client: object
    ec2_client: object
    braket_client: object
    region_name = "us-east-1"