"""
Your task configuration.

CUSTOMIZE THIS FILE to define your task-specific settings.
Inherits common settings from core.GenerationConfig
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Your task-specific configuration.
    
    CUSTOMIZE THIS CLASS to add your task's hyperparameters.
    
    Inherited from GenerationConfig:
        - num_samples: int          # Number of samples to generate
        - domain: str               # Task domain name
        - difficulty: Optional[str] # Difficulty level
        - random_seed: Optional[int] # For reproducibility
        - output_dir: Path          # Where to save outputs
        - image_size: tuple[int, int] # Image dimensions
    """
    
    # ======================================================================
    #  OVERRIDE DEFAULTS
    # ======================================================================
    
    domain: str = Field(default="my_task")
    image_size: tuple[int, int] = Field(default=(512, 512))
    
    # ======================================================================
    #  VIDEO SETTINGS
    # ======================================================================
    
    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )
    
    video_fps: int = Field(
        default=10,
        description="Video frame rate"
    )
    
    # ======================================================================
    #  TASK-SPECIFIC SETTINGS
    # ======================================================================
    
    # Add your custom settings here
