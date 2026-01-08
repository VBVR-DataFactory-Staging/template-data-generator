"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      SHAPE MATCHING TASK GENERATOR                            ║
║                                                                               ║
║  Implements: Move shapes into their matching outlines                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import tempfile
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


# ══════════════════════════════════════════════════════════════════════════════
#  TASK CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# Available shape types
SHAPE_TYPES = ["circle", "square", "triangle", "star"]

# Default colors for shapes (RGB for PIL)
SHAPE_COLORS = {
    "circle": (100, 100, 255),    # Blue
    "square": (100, 255, 100),    # Green
    "triangle": (255, 200, 100),  # Yellow/Orange
    "star": (255, 100, 255)       # Purple
}

# Animation parameters
HOLD_DURATION = 1.0  # seconds to hold at start/end
MOVE_DURATION = 2.0  # seconds to move


# ══════════════════════════════════════════════════════════════════════════════
#  SHAPE DRAWING UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def draw_circle(draw: ImageDraw.Draw, center: Tuple[int, int], 
                size: int, color, outline_only: bool = False, outline_width: int = 3):
    """Draw a circle shape."""
    cx, cy = center
    bbox = [cx - size, cy - size, cx + size, cy + size]
    
    if outline_only:
        draw.ellipse(bbox, outline=color, width=outline_width)
    else:
        draw.ellipse(bbox, fill=color, outline=(50, 50, 50), width=1)


def draw_square(draw: ImageDraw.Draw, center: Tuple[int, int],
                size: int, color, outline_only: bool = False, outline_width: int = 3):
    """Draw a square shape."""
    cx, cy = center
    bbox = [cx - size, cy - size, cx + size, cy + size]
    
    if outline_only:
        draw.rectangle(bbox, outline=color, width=outline_width)
    else:
        draw.rectangle(bbox, fill=color, outline=(50, 50, 50), width=1)


def draw_triangle(draw: ImageDraw.Draw, center: Tuple[int, int],
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


def draw_star(draw: ImageDraw.Draw, center: Tuple[int, int],
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


def draw_shape(draw: ImageDraw.Draw, shape_type: str, 
               center: Tuple[int, int], size: int, color,
               outline_only: bool = False, outline_width: int = 3):
    """Draw a shape based on type."""
    if shape_type == "circle":
        draw_circle(draw, center, size, color, outline_only, outline_width)
    elif shape_type == "square":
        draw_square(draw, center, size, color, outline_only, outline_width)
    elif shape_type == "triangle":
        draw_triangle(draw, center, size, color, outline_only, outline_width)
    elif shape_type == "star":
        draw_star(draw, center, size, color, outline_only, outline_width)


# ══════════════════════════════════════════════════════════════════════════════
#  TASK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class TaskGenerator(BaseGenerator):
    """
    Shape matching task generator.
    
    Creates tasks where colored shapes must be moved to match dark outlines.
    """
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.width, self.height = config.image_size
        self.num_shapes = min(config.num_shapes, len(SHAPE_TYPES))
        self.shape_size = config.shape_size
        
        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one shape matching task pair."""
        
        # Generate task data
        task_data = self._generate_task_data()
        
        # Render images
        first_image = self._render_frame(task_data, state="input")
        final_image = self._render_frame(task_data, state="output")
        
        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(task_id, task_data)
        
        # Get prompt
        prompt = get_prompt("default")
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )
    
    def _generate_task_data(self) -> dict:
        """Generate shapes with start and target positions."""
        shapes = []
        margin = 60
        
        # Select shapes for this task
        selected_shapes = random.sample(SHAPE_TYPES, self.num_shapes)
        
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
            
            shapes.append({
                "type": shape_type,
                "color": SHAPE_COLORS.get(shape_type, (150, 150, 150)),
                "size": self.shape_size,
                "start_pos": (sx, sy),
                "target_pos": (tx, ty)
            })
        
        return {"shapes": shapes}
    
    def _render_frame(self, task_data: dict, state: str = "input") -> Image.Image:
        """
        Render a frame.
        
        Args:
            task_data: Task data containing shapes
            state: "input" for shapes scattered, "output" for shapes matched
        """
        # Create white background
        canvas = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw dividing line
        draw.line([(self.width // 2, 20), (self.width // 2, self.height - 20)],
                 fill=(200, 200, 200), width=2)
        
        # 1. Draw target outlines (always visible)
        outline_color = (80, 80, 80)
        for shape in task_data["shapes"]:
            draw_shape(draw, shape["type"], shape["target_pos"],
                      shape["size"], outline_color, outline_only=True, outline_width=3)
        
        # 2. Draw solid shapes
        for shape in task_data["shapes"]:
            if state == "input":
                # Shapes at start positions (left side)
                pos = shape["start_pos"]
            else:
                # Shapes at target positions (matching outlines)
                pos = shape["target_pos"]
            
            draw_shape(draw, shape["type"], pos, shape["size"], shape["color"])
        
        return canvas
    
    def _generate_video(self, task_id: str, task_data: dict) -> Optional[str]:
        """Generate animation video showing shapes moving to outlines."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames
        frames = self._create_animation_frames(task_data)
        
        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
    
    def _create_animation_frames(self, task_data: dict) -> list:
        """Create animation frames showing shapes moving to their outlines."""
        frames = []
        fps = self.config.video_fps
        
        hold_frames = int(HOLD_DURATION * fps)
        transition_frames = int(MOVE_DURATION * fps)
        
        # Hold initial frame
        initial_frame = self._render_frame(task_data, state="input")
        for _ in range(hold_frames):
            frames.append(initial_frame)
        
        # Transition frames - interpolate positions
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            eased_progress = self._ease_in_out(progress)
            
            frame = self._render_interpolated_frame(task_data, eased_progress)
            frames.append(frame)
        
        # Hold final frame
        final_frame = self._render_frame(task_data, state="output")
        for _ in range(hold_frames):
            frames.append(final_frame)
        
        return frames
    
    def _render_interpolated_frame(self, task_data: dict, progress: float) -> Image.Image:
        """Render a frame with shapes at interpolated positions."""
        canvas = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw dividing line
        draw.line([(self.width // 2, 20), (self.width // 2, self.height - 20)],
                 fill=(200, 200, 200), width=2)
        
        # Draw target outlines
        outline_color = (80, 80, 80)
        for shape in task_data["shapes"]:
            draw_shape(draw, shape["type"], shape["target_pos"],
                      shape["size"], outline_color, outline_only=True, outline_width=3)
        
        # Draw shapes at interpolated positions
        for shape in task_data["shapes"]:
            sx, sy = shape["start_pos"]
            tx, ty = shape["target_pos"]
            
            cx = int(sx + (tx - sx) * progress)
            cy = int(sy + (ty - sy) * progress)
            
            draw_shape(draw, shape["type"], (cx, cy), shape["size"], shape["color"])
        
        return canvas
    
    def _ease_in_out(self, t: float) -> float:
        """Ease-in-out function for smooth animation."""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
