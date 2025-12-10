"""Base configuration for the evaluation framework.

This module contains generic configuration that applies to any domain.
Domain-specific configuration (e.g., resume optimization criteria)
should be placed in config_resume.py or a domain/ subdirectory.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class EvalConfig:
    """Base evaluation configuration."""
    
    # Database settings
    db_path: str = "./data/evals.db"
    
    # Evaluation settings
    default_evaluator_id: str = "default"
    randomize_candidate_order: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "./logs/evals"
    
    # UI settings
    ui_port: int = 8502
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "db_path": self.db_path,
            "default_evaluator_id": self.default_evaluator_id,
            "randomize_candidate_order": self.randomize_candidate_order,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_dir": self.log_dir,
            "ui_port": self.ui_port,
        }


@dataclass
class StageConfig:
    """Configuration for a pipeline stage."""
    stage_id: str
    display_name: str
    description: str
    criteria: List[str]  # Evaluation criteria names
    criteria_weights: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "display_name": self.display_name,
            "description": self.description,
            "criteria": self.criteria,
            "criteria_weights": self.criteria_weights,
        }


@dataclass
class ModelConfig:
    """Configuration for a model candidate."""
    model_id: str
    display_name: str
    provider: str  # e.g., "openrouter", "vertex", "cerebras"
    prompt_version: str = "default"
    default_temperature: float = 0.65
    default_max_tokens: int = 32000
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "provider": self.provider,
            "prompt_version": self.prompt_version,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
        }


def get_default_config() -> EvalConfig:
    """Return default evaluation configuration."""
    return EvalConfig()


def load_config_from_file(config_path: str) -> EvalConfig:
    """Load configuration from a YAML or JSON file."""
    import json
    import yaml
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path) as f:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)
    
    return EvalConfig(**data)
