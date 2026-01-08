"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      SHAPE MATCHING TASK GENERATOR                            ║
║                                                                               ║
║  Based on opencv_code/ex4.py algorithm                                        ║
║  Task: Move shapes into their matching outlines                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import math
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw
import numpy as np

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPTS FOR SHAPE MATCHING TASK
# ══════════════════════════════════════════════════════════════════════════════

SHAPE_MATCHING_PROMPTS = {
    "default": [
        "Move each colorful shape into its corresponding dark outline.",
        "Match each colored shape with its outline by moving it to the correct position.",
        "Drag each solid shape to fill its matching outline on the right side.",
    ],
    "puzzle": [
        "Complete the shape puzzle by placing each colored piece into its matching slot.",
        "Fit each shape into the correct outline, like pieces of a puzzle.",
    ],
    "sorting": [
        "Sort the shapes by moving each one to its designated outline position.",
        "Arrange the shapes by placing them over their corresponding outlines.",
    ],
}


def get_shape_matching_prompt(task_type: str = "default") -> str:
    """Select a random prompt for shape matching task."""
    prompts = SHAPE_MATCHING_PROMPTS.get(task_type, SHAPE_MATCHING_PROMPTS["default"])
    return random.choice(prompts)


# ══════════════════════════════════════════════════════════════════════════════
#  SHAPE MATCHING TASK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class ShapeMatchingConfig(TaskConfig):
    """Configuration for shape matching task."""
    domain: str = "shape_matching"
    image_size: tuple[int, int] = (800, 400)
    
    # Task-specific settings
    num_shapes: int = 4  # Number of shapes
    shape_size: int = 35  # Size (radius) of shapes


class ShapeMatchingTask:
    """
    Geometric shape matching task.
    
    Generates input/output image pairs showing:
    - Input: Colored shapes scattered on left, empty outlines on right
    - Output: Colored shapes moved to fill their matching outlines
    """
    
    # Available shape types
    SHAPE_TYPES = ["circle", "square", "triangle", "star"]
    
    # Default colors for shapes (RGB for PIL)
    SHAPE_COLORS = {
        "circle": (100, 100, 255),    # Blue
        "square": (100, 255, 100),    # Green
        "triangle": (255, 200, 100),  # Yellow/Orange
        "star": (255, 100, 255)       # Purple
    }
    
    def __init__(
        self,
        width: int = 800,
        height: int = 400,
        num_shapes: int = 4,
        shape_size: int = 35
    ):
        self.width = width
        self.height = height
        self.num_shapes = min(num_shapes, len(self.SHAPE_TYPES))
        self.shape_size = shape_size
        
        # Generate task data
        self.data = self._generate_data()
    
    def _generate_data(self) -> list:
        """Generate shapes with start and target positions."""
        data = []
        margin = 60
        
        # Select shapes for this task
        selected_shapes = random.sample(self.SHAPE_TYPES, self.num_shapes)
        
        # Generate target positions on the right side (grid layout)
        cols = 2
        rows = (self.num_shapes + 1) // 2
        right_start_x = self.width // 2
        cell_w = (self.width // 2) // cols
        cell_h = self.height // rows
        
        slots = []
        for r in range(rows):
            for c in range(cols):
                if len(slots) < self.num_shapes:
                    cx = right_start_x + c * cell_w + cell_w // 2
                    cy = r * cell_h + cell_h // 2
                    slots.append((cx, cy))
        
        random.shuffle(slots)
        
        for i, shape_type in enumerate(selected_shapes):
            # Target position (right side)
            tx, ty = slots[i]
            
            # Start position (left side, scattered)
            sx = random.randint(margin, self.width // 2 - margin)
            sy = random.randint(margin, self.height - margin)
            
            data.append({
                "type": shape_type,
                "color": self.SHAPE_COLORS.get(shape_type, (150, 150, 150)),
                "size": self.shape_size,
                "start_pos": (sx, sy),
                "target_pos": (tx, ty)
            })
        
        return data
    
    def _draw_circle(self, draw: ImageDraw.Draw, center: Tuple[int, int], 
                     size: int, color, outline_only: bool = False, outline_width: int = 3):
        """Draw a circle shape."""
        cx, cy = center
        bbox = [cx - size, cy - size, cx + size, cy + size]
        
        if outline_only:
            draw.ellipse(bbox, outline=color, width=outline_width)
        else:
            draw.ellipse(bbox, fill=color, outline=(50, 50, 50), width=1)
    
    def _draw_square(self, draw: ImageDraw.Draw, center: Tuple[int, int],
                     size: int, color, outline_only: bool = False, outline_width: int = 3):
        """Draw a square shape."""
        cx, cy = center
        bbox = [cx - size, cy - size, cx + size, cy + size]
        
        if outline_only:
            draw.rectangle(bbox, outline=color, width=outline_width)
        else:
            draw.rectangle(bbox, fill=color, outline=(50, 50, 50), width=1)
    
    def _draw_triangle(self, draw: ImageDraw.Draw, center: Tuple[int, int],
                       size: int, color, outline_only: bool = False, outline_width: int = 3):
        """Draw an equilateral triangle pointing up."""
        cx, cy = center
        points = []
        
        for i in range(3):
            angle = i * (2 * math.pi / 3) - (math.pi / 2)  # Start from top
            x = int(cx + size * math.cos(angle))
            y = int(cy + size * math.sin(angle))
            points.append((x, y))
        
        if outline_only:
            draw.polygon(points, outline=color, width=outline_width)
        else:
            draw.polygon(points, fill=color, outline=(50, 50, 50), width=1)
    
    def _draw_star(self, draw: ImageDraw.Draw, center: Tuple[int, int],
                   size: int, color, outline_only: bool = False, outline_width: int = 3):
        """Draw a 5-pointed star."""
        cx, cy = center
        points = []
        outer_r = size
        inner_r = size * 0.4
        
        for i in range(10):
            angle = i * (2 * math.pi / 10) - (math.pi / 2)
            r = outer_r if i % 2 == 0 else inner_r
            x = int(cx + r * math.cos(angle))
            y = int(cy + r * math.sin(angle))
            points.append((x, y))
        
        if outline_only:
            draw.polygon(points, outline=color, width=outline_width)
        else:
            draw.polygon(points, fill=color, outline=(50, 50, 50), width=1)
    
    def _draw_shape(self, draw: ImageDraw.Draw, shape_type: str, 
                    center: Tuple[int, int], size: int, color,
                    outline_only: bool = False, outline_width: int = 3):
        """Draw a shape based on type."""
        if shape_type == "circle":
            self._draw_circle(draw, center, size, color, outline_only, outline_width)
        elif shape_type == "square":
            self._draw_square(draw, center, size, color, outline_only, outline_width)
        elif shape_type == "triangle":
            self._draw_triangle(draw, center, size, color, outline_only, outline_width)
        elif shape_type == "star":
            self._draw_star(draw, center, size, color, outline_only, outline_width)
    
    def render(self, state: str = "input") -> Image.Image:
        """
        Render the task state.
        
        Args:
            state: "input" for shapes scattered, "output" for shapes matched
            
        Returns:
            PIL Image of the rendered state
        """
        # Create white background
        canvas = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw dividing line
        draw.line([(self.width // 2, 20), (self.width // 2, self.height - 20)],
                 fill=(200, 200, 200), width=2)
        
        # 1. Draw target outlines (always visible)
        outline_color = (80, 80, 80)
        for item in self.data:
            self._draw_shape(draw, item["type"], item["target_pos"],
                           item["size"], outline_color, outline_only=True, outline_width=3)
        
        # 2. Draw solid shapes
        for item in self.data:
            if state == "input":
                # Shapes at start positions (left side)
                pos = item["start_pos"]
            else:
                # Shapes at target positions (matching outlines)
                pos = item["target_pos"]
            
            self._draw_shape(draw, item["type"], pos, item["size"], item["color"])
        
        return canvas
    
    def get_task_type(self) -> str:
        """Get task type for prompt selection."""
        return "default"


class ShapeMatchingGenerator(BaseGenerator):
    """
    Generator for shape matching task pairs.
    
    Generates image pairs showing:
    - Input: Colored shapes scattered, empty outlines on right
    - Output: Shapes moved to fill their matching outlines
    """
    
    def __init__(self, config: ShapeMatchingConfig):
        super().__init__(config)
        self.config: ShapeMatchingConfig = config
        
        # Initialize video generator if enabled
        self.video_generator = None
        if getattr(config, 'generate_videos', False) and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(
                fps=getattr(config, 'video_fps', 10),
                output_format="mp4"
            )
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one shape matching task pair."""
        
        # Create task instance
        task = ShapeMatchingTask(
            width=self.config.image_size[0],
            height=self.config.image_size[1],
            num_shapes=getattr(self.config, 'num_shapes', 4),
            shape_size=getattr(self.config, 'shape_size', 35)
        )
        
        # Render input and output images
        first_image = task.render("input")
        final_image = task.render("output")
        
        # Generate video (optional)
        video_path = None
        if self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task)
        
        # Get prompt
        prompt = get_shape_matching_prompt(task.get_task_type())
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )
    
    def _generate_video(
        self,
        first_image: Image.Image,
        final_image: Image.Image,
        task_id: str,
        task: ShapeMatchingTask
    ) -> Optional[str]:
        """Generate animation video showing shapes moving to outlines."""
        from pathlib import Path
        import tempfile
        
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames
        frames = self._create_matching_animation_frames(task)
        
        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
    
    def _create_matching_animation_frames(
        self,
        task: ShapeMatchingTask,
        hold_frames: int = 5,
        transition_frames: int = 25
    ) -> list:
        """
        Create animation frames showing shapes moving to their outlines.
        """
        frames = []
        
        # Hold initial frame
        initial_frame = task.render("input")
        for _ in range(hold_frames):
            frames.append(initial_frame)
        
        # Transition frames - interpolate positions
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            eased_progress = self._ease_in_out(progress)
            
            frame = self._render_interpolated_frame(task, eased_progress)
            frames.append(frame)
        
        # Hold final frame
        final_frame = task.render("output")
        for _ in range(hold_frames):
            frames.append(final_frame)
        
        return frames
    
    def _render_interpolated_frame(
        self,
        task: ShapeMatchingTask,
        progress: float
    ) -> Image.Image:
        """Render a frame with shapes at interpolated positions."""
        canvas = Image.new("RGB", (task.width, task.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw dividing line
        draw.line([(task.width // 2, 20), (task.width // 2, task.height - 20)],
                 fill=(200, 200, 200), width=2)
        
        # Draw target outlines
        outline_color = (80, 80, 80)
        for item in task.data:
            task._draw_shape(draw, item["type"], item["target_pos"],
                           item["size"], outline_color, outline_only=True, outline_width=3)
        
        # Draw shapes at interpolated positions
        for item in task.data:
            sx, sy = item["start_pos"]
            tx, ty = item["target_pos"]
            
            cx = int(sx + (tx - sx) * progress)
            cy = int(sy + (ty - sy) * progress)
            
            task._draw_shape(draw, item["type"], (cx, cy), item["size"], item["color"])
        
        return canvas
    
    def _ease_in_out(self, t: float) -> float:
        """Ease-in-out function for smooth animation."""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
