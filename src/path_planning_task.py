"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      PATH PLANNING TASK GENERATOR                             ║
║                                                                               ║
║  Based on opencv_code/ex3.py algorithm                                        ║
║  Task: Find path from start to goal avoiding obstacles                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
from collections import deque
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw
import numpy as np

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPTS FOR PATH PLANNING TASK
# ══════════════════════════════════════════════════════════════════════════════

PATH_PLANNING_PROMPTS = {
    "default": [
        "Draw a continuous line from the red start circle to the green goal circle, avoiding all black obstacles.",
        "Find and draw the shortest path from the red circle to the green circle without crossing any black obstacles.",
        "Navigate from the red starting point to the green destination, plotting a path that avoids all black walls.",
    ],
    "maze": [
        "Solve the maze by drawing a path from the red start to the green goal, avoiding all black walls.",
        "Find your way through the maze from red to green, drawing a continuous line that doesn't cross obstacles.",
    ],
    "navigation": [
        "Plan a route from the red origin to the green destination that avoids all blocked cells.",
        "Draw a navigation path from start (red) to goal (green), steering clear of all obstacles (black).",
    ],
}


def get_path_planning_prompt(task_type: str = "default") -> str:
    """Select a random prompt for path planning task."""
    prompts = PATH_PLANNING_PROMPTS.get(task_type, PATH_PLANNING_PROMPTS["default"])
    return random.choice(prompts)


# ══════════════════════════════════════════════════════════════════════════════
#  PATH PLANNING TASK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class PathPlanningConfig(TaskConfig):
    """Configuration for path planning task."""
    domain: str = "path_planning"
    image_size: tuple[int, int] = (600, 400)
    
    # Task-specific settings
    grid_width: int = 15  # Number of columns
    grid_height: int = 10  # Number of rows
    cell_size: int = 40  # Pixels per cell
    obstacle_density: float = 0.25  # Percentage of cells that are obstacles


class PathPlanningTask:
    """
    Obstacle avoidance path planning task.
    
    Generates input/output image pairs showing:
    - Input: Grid map with obstacles, start point (red), and goal point (green)
    - Output: Same map with a path drawn from start to goal avoiding obstacles
    """
    
    def __init__(
        self,
        grid_width: int = 15,
        grid_height: int = 10,
        cell_size: int = 40,
        obstacle_density: float = 0.25
    ):
        self.gw = grid_width
        self.gh = grid_height
        self.cs = cell_size
        self.obstacle_density = obstacle_density
        
        # Image dimensions
        self.img_w = self.gw * self.cs
        self.img_h = self.gh * self.cs
        
        # Generate solvable maze
        self.grid = None
        self.start = None
        self.end = None
        self.path = None
        
        self._generate_solvable_map()
    
    def _generate_solvable_map(self):
        """Generate a random map that is guaranteed to be solvable."""
        max_attempts = 100
        for _ in range(max_attempts):
            self._generate_random_map()
            self.path = self._solve_bfs()
            if self.path:
                return
        
        # Fallback: create a simple solvable map
        self._create_fallback_map()
    
    def _generate_random_map(self):
        """Generate random obstacles, start, and end points."""
        # 0: empty, 1: obstacle
        self.grid = np.random.choice(
            [0, 1], 
            size=(self.gh, self.gw), 
            p=[1 - self.obstacle_density, self.obstacle_density]
        )
        
        # Select random start and end points
        attempts = 0
        while attempts < 100:
            sy, sx = random.randint(0, self.gh - 1), random.randint(0, self.gw - 1)
            ey, ex = random.randint(0, self.gh - 1), random.randint(0, self.gw - 1)
            
            # Ensure start and end are different and not on obstacles
            if (sx, sy) != (ex, ey) and self.grid[sy, sx] == 0 and self.grid[ey, ex] == 0:
                self.start = (sx, sy)
                self.end = (ex, ey)
                return
            attempts += 1
        
        # Fallback: clear some cells
        self.grid[0, 0] = 0
        self.grid[self.gh - 1, self.gw - 1] = 0
        self.start = (0, 0)
        self.end = (self.gw - 1, self.gh - 1)
    
    def _create_fallback_map(self):
        """Create a simple guaranteed-solvable map."""
        self.grid = np.zeros((self.gh, self.gw), dtype=int)
        
        # Add some obstacles in the middle
        for i in range(self.gh // 3, 2 * self.gh // 3):
            self.grid[i, self.gw // 2] = 1
        
        self.start = (0, self.gh // 2)
        self.end = (self.gw - 1, self.gh // 2)
        self.path = self._solve_bfs()
    
    def _solve_bfs(self) -> Optional[List[Tuple[int, int]]]:
        """Use BFS to find the shortest path."""
        sx, sy = self.start
        ex, ey = self.end
        
        queue = deque([(sx, sy)])
        visited = {(sx, sy): None}
        
        while queue:
            cx, cy = queue.popleft()
            
            if (cx, cy) == (ex, ey):
                # Reconstruct path
                path = []
                curr = (ex, ey)
                while curr is not None:
                    path.append(curr)
                    curr = visited[curr]
                return path[::-1]
            
            # Check 4 neighbors (up, down, left, right)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                
                if 0 <= nx < self.gw and 0 <= ny < self.gh:
                    if self.grid[ny, nx] == 0 and (nx, ny) not in visited:
                        visited[(nx, ny)] = (cx, cy)
                        queue.append((nx, ny))
        
        return None
    
    def _get_center(self, grid_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Get pixel center coordinates for a grid cell."""
        gx, gy = grid_pos
        return (int(gx * self.cs + self.cs / 2), int(gy * self.cs + self.cs / 2))
    
    def render(self, state: str = "input") -> Image.Image:
        """
        Render the task state.
        
        Args:
            state: "input" for map without path, "output" for map with path
            
        Returns:
            PIL Image of the rendered state
        """
        # Create white background
        canvas = Image.new("RGB", (self.img_w, self.img_h), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # 1. Draw grid lines
        grid_color = (240, 240, 240)
        for x in range(0, self.img_w, self.cs):
            draw.line([(x, 0), (x, self.img_h)], fill=grid_color, width=1)
        for y in range(0, self.img_h, self.cs):
            draw.line([(0, y), (self.img_w, y)], fill=grid_color, width=1)
        
        # 2. Draw obstacles (black walls)
        for y in range(self.gh):
            for x in range(self.gw):
                if self.grid[y, x] == 1:
                    top_left = (x * self.cs, y * self.cs)
                    bottom_right = ((x + 1) * self.cs, (y + 1) * self.cs)
                    draw.rectangle([top_left, bottom_right], fill=(0, 0, 0))
        
        # 3. Draw path (only in output state)
        if state == "output" and self.path:
            points = [self._get_center(p) for p in self.path]
            if len(points) >= 2:
                draw.line(points, fill=(0, 100, 255), width=4)
        
        # 4. Draw start (red) and end (green) points
        start_center = self._get_center(self.start)
        end_center = self._get_center(self.end)
        radius = int(self.cs * 0.35)
        
        # End point (green) - draw first so start overlaps if same position
        draw.ellipse(
            [end_center[0] - radius, end_center[1] - radius,
             end_center[0] + radius, end_center[1] + radius],
            fill=(0, 200, 0), outline=(0, 100, 0), width=2
        )
        
        # Start point (red)
        draw.ellipse(
            [start_center[0] - radius, start_center[1] - radius,
             start_center[0] + radius, start_center[1] + radius],
            fill=(255, 0, 0), outline=(150, 0, 0), width=2
        )
        
        return canvas
    
    def get_task_type(self) -> str:
        """Get task type for prompt selection."""
        return "default"


class PathPlanningGenerator(BaseGenerator):
    """
    Generator for path planning task pairs.
    
    Generates image pairs showing:
    - Input: Grid map with obstacles, start, and goal
    - Output: Same map with solution path drawn
    """
    
    def __init__(self, config: PathPlanningConfig):
        super().__init__(config)
        self.config: PathPlanningConfig = config
        
        # Calculate actual image size from grid
        cell_size = getattr(config, 'cell_size', 40)
        grid_width = getattr(config, 'grid_width', 15)
        grid_height = getattr(config, 'grid_height', 10)
        self.actual_image_size = (grid_width * cell_size, grid_height * cell_size)
        
        # Initialize video generator if enabled
        self.video_generator = None
        if getattr(config, 'generate_videos', False) and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(
                fps=getattr(config, 'video_fps', 10),
                output_format="mp4"
            )
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one path planning task pair."""
        
        # Create task instance
        task = PathPlanningTask(
            grid_width=getattr(self.config, 'grid_width', 15),
            grid_height=getattr(self.config, 'grid_height', 10),
            cell_size=getattr(self.config, 'cell_size', 40),
            obstacle_density=getattr(self.config, 'obstacle_density', 0.25)
        )
        
        # Render input and output images
        first_image = task.render("input")
        final_image = task.render("output")
        
        # Generate video (optional)
        video_path = None
        if self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task)
        
        # Get prompt
        prompt = get_path_planning_prompt(task.get_task_type())
        
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
        task: PathPlanningTask
    ) -> Optional[str]:
        """Generate animation video showing path being drawn."""
        from pathlib import Path
        import tempfile
        
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames
        frames = self._create_path_animation_frames(task)
        
        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
    
    def _create_path_animation_frames(
        self,
        task: PathPlanningTask,
        hold_frames: int = 5
    ) -> list:
        """
        Create animation frames showing the path being drawn step by step.
        """
        frames = []
        
        # Hold initial frame
        initial_frame = task.render("input")
        for _ in range(hold_frames):
            frames.append(initial_frame)
        
        # Animate path drawing
        if task.path:
            for i in range(1, len(task.path) + 1):
                frame = self._render_partial_path(task, task.path[:i])
                frames.append(frame)
        
        # Hold final frame
        final_frame = task.render("output")
        for _ in range(hold_frames):
            frames.append(final_frame)
        
        return frames
    
    def _render_partial_path(
        self,
        task: PathPlanningTask,
        partial_path: List[Tuple[int, int]]
    ) -> Image.Image:
        """Render the map with a partial path drawn."""
        # Create white background
        canvas = Image.new("RGB", (task.img_w, task.img_h), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw grid lines
        grid_color = (240, 240, 240)
        for x in range(0, task.img_w, task.cs):
            draw.line([(x, 0), (x, task.img_h)], fill=grid_color, width=1)
        for y in range(0, task.img_h, task.cs):
            draw.line([(0, y), (task.img_w, y)], fill=grid_color, width=1)
        
        # Draw obstacles
        for y in range(task.gh):
            for x in range(task.gw):
                if task.grid[y, x] == 1:
                    top_left = (x * task.cs, y * task.cs)
                    bottom_right = ((x + 1) * task.cs, (y + 1) * task.cs)
                    draw.rectangle([top_left, bottom_right], fill=(0, 0, 0))
        
        # Draw partial path
        if len(partial_path) >= 2:
            points = [task._get_center(p) for p in partial_path]
            draw.line(points, fill=(0, 100, 255), width=4)
        
        # Draw start and end points
        start_center = task._get_center(task.start)
        end_center = task._get_center(task.end)
        radius = int(task.cs * 0.35)
        
        draw.ellipse(
            [end_center[0] - radius, end_center[1] - radius,
             end_center[0] + radius, end_center[1] + radius],
            fill=(0, 200, 0), outline=(0, 100, 0), width=2
        )
        
        draw.ellipse(
            [start_center[0] - radius, start_center[1] - radius,
             start_center[0] + radius, start_center[1] + radius],
            fill=(255, 0, 0), outline=(150, 0, 0), width=2
        )
        
        return canvas
