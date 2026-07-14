import os
from dataclasses import dataclass, field
from credentials_config import CredsConfig
from experiment_config import ExpConfig, CircParams, Metrics, Environ, Gates

@dataclass
class Config:
    creds: CredsConfig = field(default_factory=CredsConfig)
    exp: ExpConfig = field(default_factory=ExpConfig)
    circ: CircParams = field(default_factory=CircParams)
    metric: Metrics = field(default_factory=Metrics)
    env: Environ = field(default_factory=Environ)
    gates: Gates = field(default_factory=Gates)