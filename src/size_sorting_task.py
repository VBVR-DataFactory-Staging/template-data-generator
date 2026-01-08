"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       SIZE SORTING TASK GENERATOR                             ║
║                                                                               ║
║  Based on opencv_code/ex2.py algorithm                                        ║
║  Task: Sort scattered bars from shortest to tallest                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
from typing import Optional
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPTS FOR SIZE SORTING TASK
# ══════════════════════════════════════════════════════════════════════════════

SIZE_SORTING_PROMPTS = {
    "default": [
        "Sort the scattered bars from shortest to tallest. Align them horizontally at the bottom.",
        "Arrange the colorful bars in ascending order of height, placing them side by side on the baseline.",
        "Organize the randomly placed bars by their height, from smallest to largest, aligned at the bottom.",
    ],
    "ascending": [
        "Sort the bars from shortest to tallest and align them at the bottom baseline.",
        "Arrange the scattered rectangular bars in ascending height order along the bottom.",
    ],
    "descending": [
        "Sort the bars from tallest to shortest and align them at the bottom baseline.",
        "Arrange the scattered rectangular bars in descending height order along the bottom.",
    ],
}


def get_size_sorting_prompt(task_type: str = "default") -> str:
    """Select a random prompt for size sorting task."""
    prompts = SIZE_SORTING_PROMPTS.get(task_type, SIZE_SORTING_PROMPTS["default"])
    return random.choice(prompts)


# ══════════════════════════════════════════════════════════════════════════════
#  SIZE SORTING TASK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class SizeSortingConfig(TaskConfig):
    """Configuration for size sorting task."""
    domain: str = "size_sorting"
    image_size: tuple[int, int] = (800, 400)
    
    # Task-specific settings
    num_bars: int = 7  # Number of bars
    bar_width: int = 40  # Width of each bar
    min_height: int = 50  # Minimum bar height
    max_height: int = 250  # Maximum bar height
    sort_order: str = "ascending"  # "ascending" or "descending"


class SizeSortingTask:
    """
    Bar height sorting task.
    
    Generates input/output image pairs showing:
    - Input: Scattered bars with random positions
    - Output: Bars sorted by height and aligned at baseline
    """
    
    def __init__(
        self,
        width: int = 800,
        height: int = 400,
        num_bars: int = 7,
        bar_width: int = 40,
        min_height: int = 50,
        max_height: int = 250,
        sort_order: str = "ascending"
    ):
        self.width = width
        self.height = height
        self.num_bars = num_bars
        self.bar_width = bar_width
        self.min_height = min_height
        self.max_height = max_height
        self.sort_order = sort_order
        
        # Generate bar data
        self.data = self._generate_data()
    
    def _generate_data(self) -> list:
        """Generate bars with random heights, colors, and initial positions."""
        data = []
        
        # Generate unique random heights
        heights = set()
        while len(heights) < self.num_bars:
            heights.add(random.randint(self.min_height, self.max_height))
        heights = list(heights)
        random.shuffle(heights)
        
        for h in heights:
            # Random saturated color (RGB for PIL)
            color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            
            # Random initial position (scattered)
            rand_x = random.randint(20, self.width - self.bar_width - 20)
            rand_y = random.randint(20, self.height - h - 50)
            
            data.append({
                "height": h,
                "color": color,
                "input_pos": (rand_x, rand_y)
            })
        
        return data
    
    def render(self, state: str = "input") -> Image.Image:
        """
        Render the task state.
        
        Args:
            state: "input" for scattered bars, "output" for sorted bars
            
        Returns:
            PIL Image of the rendered state
        """
        # Create white background
        canvas = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Baseline position (bottom area)
        baseline_y = self.height - 50
        
        # Prepare data for rendering
        render_data = self.data.copy()
        
        if state == "output":
            # Sort by height
            reverse = (self.sort_order == "descending")
            render_data.sort(key=lambda x: x["height"], reverse=reverse)
            
            # Calculate starting X for centered alignment
            gap = 20
            total_width = self.num_bars * self.bar_width + (self.num_bars - 1) * gap
            start_x = (self.width - total_width) // 2
            
            # Draw baseline (visual guide)
            draw.line([(50, baseline_y), (self.width - 50, baseline_y)], 
                     fill=(200, 200, 200), width=2)
        
        # Draw bars
        for i, item in enumerate(render_data):
            h = item["height"]
            color = item["color"]
            w = self.bar_width
            
            if state == "input":
                # Use random scattered position
                x, y = item["input_pos"]
                top_left = (x, y)
                bottom_right = (x + w, y + h)
            else:
                # Calculate sorted position
                gap = 20
                x = start_x + i * (w + gap)
                y = baseline_y - h
                
                top_left = (x, y)
                bottom_right = (x + w, baseline_y)
            
            # Draw filled rectangle
            draw.rectangle([top_left, bottom_right], fill=color)
            # Draw black border
            draw.rectangle([top_left, bottom_right], outline=(0, 0, 0), width=2)
        
        return canvas
    
    def get_task_type(self) -> str:
        """Get task type for prompt selection."""
        return self.sort_order


class SizeSortingGenerator(BaseGenerator):
    """
    Generator for size sorting task pairs.
    
    Generates image pairs showing:
    - Input: Scattered bars with random positions
    - Output: Bars sorted by height and aligned at baseline
    """
    
    def __init__(self, config: SizeSortingConfig):
        super().__init__(config)
        self.config: SizeSortingConfig = config
        
        # Initialize video generator if enabled
        self.video_generator = None
        if getattr(config, 'generate_videos', False) and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(
                fps=getattr(config, 'video_fps', 10),
                output_format="mp4"
            )
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one size sorting task pair."""
        
        # Create task instance
        task = SizeSortingTask(
            width=self.config.image_size[0],
            height=self.config.image_size[1],
            num_bars=getattr(self.config, 'num_bars', 7),
            bar_width=getattr(self.config, 'bar_width', 40),
            min_height=getattr(self.config, 'min_height', 50),
            max_height=getattr(self.config, 'max_height', 250),
            sort_order=getattr(self.config, 'sort_order', 'ascending')
        )
        
        # Render input and output images
        first_image = task.render("input")
        final_image = task.render("output")
        
        # Generate video (optional)
        video_path = None
        if self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task)
        
        # Get prompt
        prompt = get_size_sorting_prompt(task.get_task_type())
        
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
        task: SizeSortingTask
    ) -> Optional[str]:
        """Generate animation video showing bars sorting and aligning."""
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
        task: SizeSortingTask,
        hold_frames: int = 5,
        transition_frames: int = 25
    ) -> list:
        """
        Create animation frames showing bars moving to sorted positions.
        
        Bars move smoothly from scattered positions to sorted alignment.
        """
        frames = []
        
        # Calculate start and end positions
        start_positions = {i: item["input_pos"] for i, item in enumerate(task.data)}
        end_positions = self._calculate_sorted_positions(task)
        
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
    
    def _calculate_sorted_positions(self, task: SizeSortingTask) -> dict:
        """Calculate the sorted end positions for each bar."""
        # Sort data by height
        sorted_indices = sorted(
            range(len(task.data)),
            key=lambda i: task.data[i]["height"],
            reverse=(task.sort_order == "descending")
        )
        
        baseline_y = task.height - 50
        gap = 20
        total_width = task.num_bars * task.bar_width + (task.num_bars - 1) * gap
        start_x = (task.width - total_width) // 2
        
        end_positions = {}
        for new_idx, original_idx in enumerate(sorted_indices):
            h = task.data[original_idx]["height"]
            x = start_x + new_idx * (task.bar_width + gap)
            y = baseline_y - h
            end_positions[original_idx] = (x, y)
        
        return end_positions
    
    def _render_interpolated_frame(
        self,
        task: SizeSortingTask,
        start_positions: dict,
        end_positions: dict,
        progress: float
    ) -> Image.Image:
        """Render a frame with bars at interpolated positions."""
        canvas = Image.new("RGB", (task.width, task.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw baseline if progress > 0.5
        if progress > 0.5:
            baseline_y = task.height - 50
            draw.line([(50, baseline_y), (task.width - 50, baseline_y)], 
                     fill=(200, 200, 200), width=2)
        
        # Draw bars at interpolated positions
        for i, item in enumerate(task.data):
            color = item["color"]
            h = item["height"]
            w = task.bar_width
            
            # Interpolate position
            sx, sy = start_positions[i]
            ex, ey = end_positions[i]
            
            # Use easing function for smoother animation
            eased_progress = self._ease_in_out(progress)
            
            cx = int(sx + (ex - sx) * eased_progress)
            cy = int(sy + (ey - sy) * eased_progress)
            
            # Interpolate bar height anchoring (scattered vs baseline-aligned)
            if progress < 0.5:
                # Keep original height representation
                bottom_y = cy + h
            else:
                # Transition to baseline alignment
                baseline_y = task.height - 50
                blend = (progress - 0.5) * 2  # 0 to 1 over second half
                bottom_y = int((cy + h) * (1 - blend) + baseline_y * blend)
            
            top_left = (cx, cy)
            bottom_right = (cx + w, bottom_y)
            
            # Draw bar
            draw.rectangle([top_left, bottom_right], fill=color)
            draw.rectangle([top_left, bottom_right], outline=(0, 0, 0), width=2)
        
        return canvas
    
    def _ease_in_out(self, t: float) -> float:
        """Ease-in-out function for smooth animation."""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
