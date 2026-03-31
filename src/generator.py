"""
Your custom task generator.

CUSTOMIZE THIS FILE to implement your data generation logic.
Replace the placeholder implementation with your own task.
"""

import random
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """
    Your custom task generator.
    
    IMPLEMENT THIS CLASS for your specific task.
    
    Required:
        - generate_task_pair(task_id) -> TaskPair
    
    The base class provides:
        - self.config: Your TaskConfig instance
        - generate_dataset(): Loops and calls generate_task_pair() for each sample
        - _build_metadata(task_id, task_data): Build standardized metadata dict
        - _task_signature(task_data): Compute dedup signature from task parameters
    """
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)
        
        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one task pair."""
        
        # 1. Generate task data (your task-specific parameters)
        task_data = self._generate_task_data()
        
        # 2. Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)
        
        # 3. Generate videos (optional)
        video_path = None
        first_video_path = None
        last_video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task_data)
            # Optional: generate first/last segment videos
            # first_video_path = self._generate_first_video(first_image, task_id, task_data)
            # last_video_path = self._generate_last_video(final_image, task_id, task_data)
        
        # 4. Select prompt
        prompt = get_prompt(task_data.get("type", "default"))
        
        # 5. Build metadata for dedup tracking
        metadata = self._build_metadata(task_id, task_data)
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            first_video=first_video_path,
            last_video=last_video_path,
            ground_truth_video=video_path,
            metadata=metadata,
        )
    
    # ======================================================================
    #  TASK-SPECIFIC METHODS - Replace these with your own logic
    # ======================================================================
    
    def _generate_task_data(self) -> dict:
        """
        Generate the parameters for one task instance.
        
        Returns a dict of task parameters. These parameters are:
        - Used to render images and videos
        - Stored in metadata.json for deduplication (via param_hash)
        
        Replace this with your own task logic.
        """
        # Placeholder: generate a random color-change task
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
        ]
        color_a = random.choice(colors)
        color_b = random.choice([c for c in colors if c != color_a])
        
        return {
            "type": "default",
            "color_a": color_a,
            "color_b": color_b,
        }
    
    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render the initial state image. Replace with your rendering logic."""
        img = self.renderer.create_blank_image(bg_color=task_data["color_a"])
        draw = ImageDraw.Draw(img)
        w, h = img.size
        draw.text((w // 4, h // 2), "Initial State", fill=(255, 255, 255))
        return img
    
    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render the final/goal state image. Replace with your rendering logic."""
        img = self.renderer.create_blank_image(bg_color=task_data["color_b"])
        draw = ImageDraw.Draw(img)
        w, h = img.size
        draw.text((w // 4, h // 2), "Final State", fill=(255, 255, 255))
        return img
    
    def _generate_video(
        self,
        first_image: Image.Image,
        final_image: Image.Image,
        task_id: str,
        task_data: dict,
    ) -> str:
        """Generate ground truth video (full, beginning to end). Replace with your animation logic."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Default: simple crossfade between initial and final
        result = self.video_generator.create_crossfade_video(
            first_image, final_image, video_path
        )
        
        return str(result) if result else None
    
    def _generate_first_video(
        self,
        first_image: Image.Image,
        task_id: str,
        task_data: dict,
    ) -> str:
        """
        Generate the first segment video (optional).
        
        The first frame of this video corresponds to first_frame.png.
        Replace with your own logic for producing the opening video segment.
        """
        # Placeholder: override in your generator to produce the opening segment
        return None
    
    def _generate_last_video(
        self,
        final_image: Image.Image,
        task_id: str,
        task_data: dict,
    ) -> str:
        """
        Generate the last segment video (optional).
        
        The last frame of this video corresponds to final_frame.png.
        Replace with your own logic for producing the closing video segment.
        """
        # Placeholder: override in your generator to produce the closing segment
        return None
