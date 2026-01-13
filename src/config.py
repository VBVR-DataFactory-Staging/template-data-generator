"""Multi-view Camera Positioning Task Configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field

from core import GenerationConfig

BLENDER_VERSION = "5.0.0"


class TaskConfig(GenerationConfig):
    """Task configuration for the multi-view camera positioning generator."""

    domain: str = Field(default="multi_view_camera")
    image_size: tuple[int, int] = Field(default=(512, 512))

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
    max_video_duration: float = Field(default=10.0)

    # Available camera views
    available_views: list[str] = Field(
        default=[
            "front",
            "left",
            "right",
            "back",
            "front_left",
            "front_right",
            "back_left",
            "back_right",
            "top_down",
        ]
    )

    # View angle definitions (azimuth, elevation in degrees)
    view_definitions: dict[str, dict[str, float]] = Field(
        default={
            "front": {"azimuth": 0, "elevation": 0},
            "left": {"azimuth": -90, "elevation": 0},
            "right": {"azimuth": 90, "elevation": 0},
            "back": {"azimuth": 180, "elevation": 0},
            "front_left": {"azimuth": -45, "elevation": 30},
            "front_right": {"azimuth": 45, "elevation": 30},
            "back_left": {"azimuth": -135, "elevation": 30},
            "back_right": {"azimuth": 135, "elevation": 30},
            "top_down": {"azimuth": 0, "elevation": 89.9},
        }
    )

    # View selection strategies
    initial_fixed_view: Optional[str] = Field(
        default="top_down",
        description="If set, always use this view as the initial camera (e.g., 'top_down').",
    )
    initial_view_strategy: str = Field(default="random")  # "random" or "fixed"
    target_view_strategy: str = Field(default="random")  # "random", "opposite", "adjacent"
    view_transition_difficulty: str = Field(default="medium")  # "easy", "medium", "hard"

    # Object parameters
    num_objects_range: tuple[int, int] = Field(default=(1, 3))
    primary_object_type: str = Field(default="rubik")
    primary_size_range: tuple[float, float] = Field(default=(0.9, 1.1))
    aux_size_range: tuple[float, float] = Field(default=(0.3, 0.6))
    object_types: list[str] = Field(default=["cube", "sphere", "cylinder", "pyramid"])

    # Object positions: single object at origin, multiple objects randomized near origin
    single_object_position: tuple[float, float, float] = Field(default=(0.0, 0.0, 0.0))
    object_position_range: tuple[float, float] = Field(default=(-1.5, 1.5))
    min_object_spacing: float = Field(default=0.5)
    safety_margin: float = Field(default=0.3)

    # Object colors (RGB 0-1) for auxiliary objects
    object_colors: list[tuple[float, float, float]] = Field(
        default=[
            (1.0, 0.3, 0.3),  # bright red
            (0.3, 1.0, 0.3),  # bright green
            (0.3, 0.3, 1.0),  # bright blue
            (1.0, 1.0, 0.3),  # bright yellow
            (1.0, 0.4, 1.0),  # bright magenta
            (0.3, 1.0, 1.0),  # bright cyan
        ]
    )
    # Rubik's cube face colors (fixed mapping)
    rubik_face_colors: dict[str, tuple[float, float, float]] = Field(
        default={
            "+X": (1.0, 0.0, 0.0),   # right - red
            "-X": (1.0, 0.5, 0.0),   # left - orange
            "+Y": (0.0, 1.0, 0.0),   # front - green
            "-Y": (0.0, 0.0, 1.0),   # back - blue
            "+Z": (0.05, 0.05, 0.05),   # top - black for contrast
            "-Z": (1.0, 1.0, 0.0),   # bottom - yellow
        }
    )

    # Blender settings
    blender_version: str = Field(default=BLENDER_VERSION)
    blender_executable: Optional[Path] = Field(default=None)  # None = auto-detect

    camera_distance: float = Field(default=5.0)
    camera_fov_deg: float = Field(default=60.0)
    render_resolution: tuple[int, int] = Field(default=(512, 512))
    render_engine: str = Field(default="EEVEE")  # Accepts "EEVEE"/"BLENDER_EEVEE"/"CYCLES"

    # Background color (RGB 0-1)
    background_color: tuple[float, float, float] = Field(default=(1.0, 1.0, 1.0))

    # Video timing
    initial_hold_frames: int = Field(default=20)
    transition_frames: int = Field(default=40)
    final_hold_frames: int = Field(default=40)
    top_down_extra_frames: int = Field(default=20)
