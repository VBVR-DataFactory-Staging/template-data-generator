"""
Your custom task implementation.

Files to customize:
    - config.py   : Task-specific configuration (TaskConfig)
    - generator.py: Task generation logic (TaskGenerator)
    - prompts.py  : Task prompts/instructions (get_prompt)
    - color_sorting_task.py: Color sorting task (ColorSortingGenerator)
"""

from .config import TaskConfig
from .generator import TaskGenerator
from .prompts import get_prompt
from .color_sorting_task import (
    ColorSortingConfig,
    ColorSortingTask,
    ColorSortingGenerator,
    get_color_sorting_prompt
)

__all__ = [
    "TaskConfig",
    "TaskGenerator", 
    "get_prompt",
    # Color sorting task
    "ColorSortingConfig",
    "ColorSortingTask",
    "ColorSortingGenerator",
    "get_color_sorting_prompt",
]
