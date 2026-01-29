"""
DimeAI Configuration Management
"""
import yaml
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG = {
    "data_dir": "~/.dimeai/data",
    "model_dir": "~/.dimeai/models",
    "gliner_model": "fastino/gliner2-base-v1",
    "embedding_model": "all-MiniLM-L6-v2",
    "train_ratio": 0.7,
    "default_epochs": 100,
}


def get_config_path() -> Path:
    return Path.home() / ".dimeai" / "config.yaml"


def load_config() -> Dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    config_path = get_config_path()
    
    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)
    
    return config


def save_config(config: Dict[str, Any]) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def set_config(key: str, value: Any) -> None:
    config = load_config()
    config[key] = value
    save_config(config)


def get_data_dir() -> Path:
    config = load_config()
    data_dir = Path(config["data_dir"]).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_model_dir() -> Path:
    config = load_config()
    model_dir = Path(config["model_dir"]).expanduser()
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir
