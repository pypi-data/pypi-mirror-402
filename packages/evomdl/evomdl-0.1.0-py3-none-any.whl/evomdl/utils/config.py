import yaml
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "defaults"

def load_config(config_name):
    """Load a YAML config from the defaults directory."""
    path = DEFAULT_CONFIG_PATH / f"{config_name}.yaml"
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_default_model_config():
    return load_config("models")

def get_default_pipeline_config():
    return load_config("pipelines")
