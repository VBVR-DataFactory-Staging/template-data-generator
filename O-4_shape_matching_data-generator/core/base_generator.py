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
