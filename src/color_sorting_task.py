"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       COLOR SORTING TASK GENERATOR                            ║
║                                                                               ║
║  Based on opencv_code/ex1.py algorithm                                        ║
║  Task: Move colored blocks into matching color containers                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
from typing import Optional
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPTS FOR COLOR SORTING TASK
# ══════════════════════════════════════════════════════════════════════════════

COLOR_SORTING_PROMPTS = {
    "default": [
        "The image shows scattered colored blocks and empty containers. Move each block into the container that matches its color. Arrange the blocks neatly inside the containers.",
        "Sort the colored blocks by moving each one into the container of the same color. Organize them neatly in a grid pattern inside each container.",
        "Categorize the scattered colored blocks by placing each block into its matching colored container. Arrange them in an orderly manner.",
    ],
    "two_colors": [
        "The image shows blue and yellow blocks scattered around two containers. Sort the blocks by placing each one in the container that matches its color.",
        "Move all the colored blocks into their corresponding containers - blue blocks go in the blue container, yellow blocks go in the yellow container.",
    ],
    "multi_colors": [
        "Sort the multi-colored blocks by placing each one into the container that matches its color. Arrange them neatly inside.",
        "The image shows blocks of various colors and multiple containers. Move each block into the container of matching color.",
    ],
}


def get_color_sorting_prompt(task_type: str = "default") -> str:
    """Select a random prompt for color sorting task."""
    prompts = COLOR_SORTING_PROMPTS.get(task_type, COLOR_SORTING_PROMPTS["default"])
    return random.choice(prompts)


# ══════════════════════════════════════════════════════════════════════════════
#  COLOR SORTING TASK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class ColorSortingConfig(TaskConfig):
    """Configuration for color sorting task."""
    domain: str = "color_sorting"
    image_size: tuple[int, int] = (600, 400)
    
    # Task-specific settings
    num_colors: int = 2  # Number of color categories
    items_per_color: int = 4  # Number of blocks per color
    block_size: int = 25  # Size of each block in pixels


class ColorSortingTask:
    """
    Color-based bin sorting task.
    
    Generates input/output image pairs showing:
    - Input: Scattered colored blocks with empty containers
    - Output: Blocks sorted into matching color containers
    """
    
    # Available colors (RGB format for PIL)
    AVAILABLE_COLORS = {
        "yellow": (255, 215, 0),     # Gold yellow
        "blue": (0, 100, 255),       # Blue
        "red": (220, 60, 60),        # Red
        "green": (60, 180, 60),      # Green
        "purple": (150, 80, 200),    # Purple
        "orange": (255, 140, 0),     # Orange
    }
    
    def __init__(
        self,
        width: int = 600,
        height: int = 400,
        num_colors: int = 2,
        items_per_color: int = 4,
        block_size: int = 25
    ):
        self.width = width
        self.height = height
        self.num_colors = num_colors
        self.items_per_color = items_per_color
        self.block_size = block_size
        
        # Select colors for this task
        self.selected_colors = self._select_colors()
        
        # Generate containers and items
        self.bins = self._generate_bins()
        self.items = self._generate_items()
    
    def _select_colors(self) -> dict:
        """Select random colors for this task instance."""
        color_names = list(self.AVAILABLE_COLORS.keys())
        selected_names = random.sample(color_names, min(self.num_colors, len(color_names)))
        return {name: self.AVAILABLE_COLORS[name] for name in selected_names}
    
    def _generate_bins(self) -> list:
        """Generate container positions based on number of colors."""
        bins = []
        color_names = list(self.selected_colors.keys())
        
        # Container dimensions
        bin_width = 150
        bin_height = 100
        
        # Calculate spacing for containers at bottom
        total_bin_width = len(color_names) * bin_width
        spacing = (self.width - total_bin_width) // (len(color_names) + 1)
        
        # Container Y position (bottom area)
        bin_y = self.height - bin_height - 50
        
        for i, color_name in enumerate(color_names):
            bin_x = spacing + i * (bin_width + spacing)
            bins.append({
                "rect": (bin_x, bin_y, bin_width, bin_height),
                "color": color_name
            })
        
        return bins
    
    def _generate_items(self) -> list:
        """Generate scattered item positions for input state."""
        items = []
        
        for color_name in self.selected_colors.keys():
            for i in range(self.items_per_color):
                # Random position in upper area (avoiding containers)
                rand_x = random.randint(50, self.width - 50)
                rand_y = random.randint(50, self.height // 2 - 30)
                
                items.append({
                    "color_name": color_name,
                    "color_val": self.selected_colors[color_name],
                    "size": self.block_size,
                    "start_pos": (rand_x, rand_y),
                    "id": f"{color_name}_{i}"
                })
        
        return items
    
    def _get_sorted_positions(self) -> dict:
        """Calculate sorted positions for blocks inside containers."""
        target_positions = {}
        counters = {name: 0 for name in self.selected_colors.keys()}
        
        for item in self.items:
            color_name = item["color_name"]
            idx = counters[color_name]
            counters[color_name] += 1
            
            # Find matching container
            bin_data = next(b for b in self.bins if b["color"] == color_name)
            bx, by, bw, bh = bin_data["rect"]
            
            # Grid layout inside container (2 columns)
            cols = 2
            row = idx // cols
            col = idx % cols
            
            # Calculate position with padding
            padding_x = bw // 3
            padding_y = bh // 3
            
            target_x = bx + padding_x * (col + 1)
            target_y = by + padding_y * (row + 1) - 10
            
            target_positions[item["id"]] = (int(target_x), int(target_y))
        
        return target_positions
    
    def render(self, state: str = "input") -> Image.Image:
        """
        Render the task state.
        
        Args:
            state: "input" for scattered blocks, "output" for sorted blocks
            
        Returns:
            PIL Image of the rendered state
        """
        # Create white background
        canvas = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # 1. Draw containers (empty rectangles)
        for b in self.bins:
            bx, by, bw, bh = b["rect"]
            color = self.selected_colors[b["color"]]
            # Draw thick border rectangle
            draw.rectangle(
                [bx, by, bx + bw, by + bh],
                outline=color,
                width=4
            )
        
        # 2. Draw items (filled blocks)
        target_map = self._get_sorted_positions()
        
        for item in self.items:
            color = item["color_val"]
            size = item["size"]
            
            if state == "input":
                cx, cy = item["start_pos"]
            else:
                cx, cy = target_map[item["id"]]
            
            # Calculate block corners
            half = size // 2
            top_left = (cx - half, cy - half)
            bottom_right = (cx + half, cy + half)
            
            # Draw filled block
            draw.rectangle([top_left, bottom_right], fill=color)
            # Add border for contrast
            draw.rectangle([top_left, bottom_right], outline=(50, 50, 50), width=1)
        
        return canvas
    
    def get_task_type(self) -> str:
        """Get task type for prompt selection."""
        if self.num_colors == 2:
            return "two_colors"
        elif self.num_colors > 2:
            return "multi_colors"
        return "default"


class ColorSortingGenerator(BaseGenerator):
    """
    Generator for color sorting task pairs.
    
    Generates image pairs showing:
    - Input: Scattered colored blocks
    - Output: Blocks sorted into matching containers
    """
    
    def __init__(self, config: ColorSortingConfig):
        super().__init__(config)
        self.config: ColorSortingConfig = config
        
        # Initialize video generator if enabled
        self.video_generator = None
        if getattr(config, 'generate_videos', False) and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(
                fps=getattr(config, 'video_fps', 10),
                output_format="mp4"
            )
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one color sorting task pair."""
        
        # Create task instance
        task = ColorSortingTask(
            width=self.config.image_size[0],
            height=self.config.image_size[1],
            num_colors=getattr(self.config, 'num_colors', 2),
            items_per_color=getattr(self.config, 'items_per_color', 4),
            block_size=getattr(self.config, 'block_size', 25)
        )
        
        # Render input and output images
        first_image = task.render("input")
        final_image = task.render("output")
        
        # Generate video (optional)
        video_path = None
        if self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task)
        
        # Get prompt
        prompt = get_color_sorting_prompt(task.get_task_type())
        
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
        task: ColorSortingTask
    ) -> Optional[str]:
        """Generate animation video showing blocks moving to containers."""
        from pathlib import Path
        import tempfile
        
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames
        frames = self._create_sorting_animation_frames(task)
        
        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
    
    def _create_sorting_animation_frames(
        self,
        task: ColorSortingTask,
        hold_frames: int = 5,
        transition_frames: int = 20
    ) -> list:
        """
        Create animation frames showing blocks moving to containers.
        
        Blocks move smoothly from scattered positions to sorted positions.
        """
        frames = []
        
        # Get start and end positions
        start_positions = {item["id"]: item["start_pos"] for item in task.items}
        end_positions = task._get_sorted_positions()
        
        # Hold initial frame
        initial_frame = task.render("input")
        for _ in range(hold_frames):
            frames.append(initial_frame)
        
        # Transition frames - interpolate positions
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            
            # Create frame with interpolated positions
            frame = self._render_interpolated_frame(task, start_positions, end_positions, progress)
            frames.append(frame)
        
        # Hold final frame
        final_frame = task.render("output")
        for _ in range(hold_frames):
            frames.append(final_frame)
        
        return frames
    
    def _render_interpolated_frame(
        self,
        task: ColorSortingTask,
        start_positions: dict,
        end_positions: dict,
        progress: float
    ) -> Image.Image:
        """Render a frame with blocks at interpolated positions."""
        canvas = Image.new("RGB", (task.width, task.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw containers
        for b in task.bins:
            bx, by, bw, bh = b["rect"]
            color = task.selected_colors[b["color"]]
            draw.rectangle([bx, by, bx + bw, by + bh], outline=color, width=4)
        
        # Draw items at interpolated positions
        for item in task.items:
            item_id = item["id"]
            color = item["color_val"]
            size = item["size"]
            
            # Interpolate position
            sx, sy = start_positions[item_id]
            ex, ey = end_positions[item_id]
            
            cx = int(sx + (ex - sx) * progress)
            cy = int(sy + (ey - sy) * progress)
            
            # Draw block
            half = size // 2
            draw.rectangle([cx - half, cy - half, cx + half, cy + half], fill=color)
            draw.rectangle([cx - half, cy - half, cx + half, cy + half], outline=(50, 50, 50), width=1)
        
        return canvas
