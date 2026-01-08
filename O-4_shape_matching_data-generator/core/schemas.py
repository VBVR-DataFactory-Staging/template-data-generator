"""Pydantic schemas for task data."""

from typing import Optional, Any
from pydantic import BaseModel


class TaskPair(BaseModel):
    """A task pair with initial and final states."""
    task_id: str
    domain: str
    prompt: str
    first_image: Any  # PIL Image
    final_image: Optional[Any] = None  # PIL Image
    ground_truth_video: Optional[str] = None  # Path to video (optional)
    
    class Config:
        arbitrary_types_allowed = True
