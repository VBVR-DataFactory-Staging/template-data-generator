"""Base generator class."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from .schemas import TaskPair


class GenerationConfig(BaseModel):
    """Generation configuration."""
    num_samples: int
    domain: str
    difficulty: Optional[str] = None
    random_seed: Optional[int] = None
    output_dir: Path = Path("data/questions")
    image_size: tuple[int, int] = (400, 400)


class BaseGenerator(ABC):
    """Base class for task generators. Implement generate_task_pair()."""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        if config.random_seed is not None:
            import random
            import numpy as np
            random.seed(config.random_seed)
            np.random.seed(config.random_seed)
    
    @abstractmethod
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate a single task. Implement this in your generator."""
        pass
    
    def generate_dataset(self) -> List[TaskPair]:
        """Generate complete dataset."""
        pairs = []
        for i in range(self.config.num_samples):
            task_id = f"{self.config.domain}_{i:04d}"
            pair = self.generate_task_pair(task_id)
            pairs.append(pair)
            print(f"  Generated: {task_id}")
        return pairs

    def _task_signature(self, task_data: dict) -> tuple:
        """
        Generic _task_signature method for generators without custom implementation.
        Creates a signature from task_data by quantizing floats and serializing values.
        """
        def q(v: float, step: int = 5) -> int:
            return int(round(v / step) * step)
        
        def serialize_value(v):
            if isinstance(v, (int, str, bool, type(None))):
                return v
            if isinstance(v, float):
                return q(v, 5)
            if isinstance(v, tuple):
                return tuple(serialize_value(item) for item in v)
            if isinstance(v, list):
                return tuple(sorted(serialize_value(item) for item in v))
            if isinstance(v, dict):
                return tuple((k, serialize_value(v)) for k, v in sorted(v.items()))
            return str(v)
        
        skip_keys = {'temp_path', 'temp_dir', 'temp_file', 'video_temp_path', 
                     'image_temp_path', '_cache', '_internal', '_temp', 'seed', 'random_seed'}
        
        items = []
        for key, value in sorted(task_data.items()):
            if any(skip in key.lower() for skip in skip_keys):
                continue
            items.append((key, serialize_value(value)))
        
        return tuple(items)

    def _build_metadata(self, task_id: str, task_data: dict) -> dict:
        """
        Build standardized metadata for a task.
        
        Args:
            task_id: Task ID
            task_data: Parameters dict from _generate_task_data()
        
        Returns:
            Standardized metadata dict
        """
        from .metadata_builder import build_metadata
        
        return build_metadata(
            task_id=task_id,
            generator_name=self.config.domain,
            parameters=task_data,
            seed=self.config.random_seed,
        )
