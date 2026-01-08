"""Output writer for standard format."""

import shutil
from pathlib import Path
from typing import List
from .schemas import TaskPair
from .image_utils import ImageRenderer


class OutputWriter:
    """Writes tasks to standard folder structure."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_task_pair(self, task_pair: TaskPair) -> Path:
        """Write single task to disk."""
        task_dir = self.output_dir / f"{task_pair.domain}_task" / task_pair.task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Write images
        ImageRenderer.ensure_rgb(task_pair.first_image).save(task_dir / "first_frame.png")
        
        if task_pair.final_image:
            ImageRenderer.ensure_rgb(task_pair.final_image).save(task_dir / "final_frame.png")
        
        # Write prompt
        (task_dir / "prompt.txt").write_text(task_pair.prompt)
        
        # Write video if provided (preserve original extension)
        if task_pair.ground_truth_video and Path(task_pair.ground_truth_video).exists():
            video_src = Path(task_pair.ground_truth_video)
            video_ext = video_src.suffix  # .mp4 or .avi
            shutil.copy(video_src, task_dir / f"ground_truth{video_ext}")
        
        return task_dir
    
    def write_dataset(self, task_pairs: List[TaskPair]) -> Path:
        """Write all tasks to disk."""
        for pair in task_pairs:
            self.write_task_pair(pair)
        return self.output_dir
