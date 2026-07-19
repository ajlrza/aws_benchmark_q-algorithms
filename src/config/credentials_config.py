import os
from dataclasses import dataclass

@dataclass
class CredsConfig:
    sts_client: object = None
    cw_client: object = None
    ec2_client: object = None
    braket_client: object = None
    region_name: str = "us-east-1"