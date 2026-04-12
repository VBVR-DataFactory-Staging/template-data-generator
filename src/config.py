"""Default task configuration for G-29 Chart Extreme With Data."""

from typing import Tuple

from pydantic import Field

from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """Configuration for the default chart-extreme task."""

    domain: str = Field(default="chart_extreme_with_data")
    image_size: Tuple[int, int] = Field(default=(1024, 1024))

    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos",
    )
    video_fps: int = Field(
        default=16,
        description="Video frame rate",
    )

    chart_types: Tuple[str, ...] = Field(
        default=("bar", "line", "scatter", "pie"),
        description="Chart types enabled for default generation",
    )
