"""
Your custom task implementation.

Files to customize:
    - config.py   : Task-specific configuration (TaskConfig)
    - generator.py: Task generation logic (TaskGenerator)
    - prompts.py  : Task prompts/instructions (get_prompt)
    - shape_matching_task.py: Shape matching task (ShapeMatchingGenerator)
"""

from .config import TaskConfig
from .generator import TaskGenerator
from .prompts import get_prompt
from .shape_matching_task import (
    ShapeMatchingConfig,
    ShapeMatchingTask,
    ShapeMatchingGenerator,
    get_shape_matching_prompt
)

__all__ = [
    "TaskConfig",
    "TaskGenerator", 
    "get_prompt",
    # Shape matching task
    "ShapeMatchingConfig",
    "ShapeMatchingTask",
    "ShapeMatchingGenerator",
    "get_shape_matching_prompt",
]
