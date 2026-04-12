"""Default G-29 Chart Extreme With Data task generator."""

import math
import random
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .data_scenarios import generate_realistic_data, get_scenario_for_chart_type
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """Generate chart tasks that ask the model to highlight an extreme value."""

    HIGHLIGHT_COLOR = (255, 0, 0)
    HIGHLIGHT_WIDTH = 12
    SERIES_COLORS = [
        (70, 130, 180),
        (255, 140, 0),
        (32, 178, 170),
        (138, 43, 226),
        (255, 99, 71),
    ]

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one chart task pair."""

        task_data = self._generate_task_data()
        first_image = self._render_chart(task_data, highlight=False)
        final_image = self._render_chart(task_data, highlight=True)

        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id)

        prompt = get_prompt(
            chart_type=task_data["chart_type"],
            extreme_type=task_data["extreme_type"],
            metadata=task_data["metadata"],
        )

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path,
            metadata=self._build_metadata(task_id, task_data),
        )

    def _generate_task_data(self) -> Dict:
        chart_type = random.choice(list(self.config.chart_types))
        scenario = get_scenario_for_chart_type(chart_type)
        values, x_values = generate_realistic_data(scenario)
        values = self._ensure_unique_extremes(values, chart_type)

        labels = self._choose_labels(scenario.metadata.data_labels, len(values))
        metadata = {
            "title": scenario.metadata.title,
            "x_label": scenario.metadata.x_label,
            "y_label": scenario.metadata.y_label,
            "x_unit": scenario.metadata.x_unit,
            "y_unit": scenario.metadata.y_unit,
            "data_labels": labels,
        }

        extreme_type = random.choice(["max", "min"])
        target_value = max(values) if extreme_type == "max" else min(values)
        target_index = values.index(target_value)

        task_data = {
            "chart_type": chart_type,
            "values": values,
            "x_values": x_values if chart_type == "scatter" else None,
            "metadata": metadata,
            "extreme_type": extreme_type,
            "target_index": target_index,
            "target_value": target_value,
        }
        task_data["highlight_box"] = self._compute_highlight_box(task_data)
        return task_data

    def _generate_video(self, first_image: Image.Image, final_image: Image.Image, task_id: str) -> str:
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / f"{task_id}_ground_truth.mp4"
        result = self.video_generator.create_crossfade_video(
            first_image,
            final_image,
            output_path,
            hold_frames=8,
            transition_frames=24,
        )
        return str(result) if result else None

    def _choose_labels(self, labels: List[str], count: int) -> List[str]:
        if not labels:
            return [str(index + 1) for index in range(count)]
        if len(labels) <= count:
            return labels[:count]
        start = random.randint(0, len(labels) - count)
        return labels[start : start + count]

    def _ensure_unique_extremes(self, values: List[float], chart_type: str) -> List[float]:
        updated = list(values)
        precision = 1 if chart_type in ("line", "scatter", "pie") else 0
        minimum_step = 0.1 if precision == 1 else 1.0

        while len(set(updated)) != len(updated):
            counts = {}
            for value in updated:
                counts[value] = counts.get(value, 0) + 1
            for index, value in enumerate(updated):
                if counts[value] > 1:
                    updated[index] = round(value + minimum_step * (index + 1), precision)

        if chart_type == "pie":
            total = sum(updated)
            updated = [round(value / total * 100.0, 1) for value in updated]
            while len(set(updated)) != len(updated):
                max_index = updated.index(max(updated))
                min_index = updated.index(min(updated))
                updated[max_index] = round(updated[max_index] + 0.1, 1)
                updated[min_index] = round(max(updated[min_index] - 0.1, 0.1), 1)

        return updated

    def _get_font(self, size: int) -> ImageFont.ImageFont:
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _text_size(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
        bbox = draw.textbbox((0, 0), str(text), font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_text_centered(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        center: Tuple[int, int],
        font: ImageFont.ImageFont,
        fill: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        width, height = self._text_size(draw, text, font)
        draw.text((center[0] - width / 2, center[1] - height / 2), text, fill=fill, font=font)

    def _chart_bounds(self) -> Tuple[int, int, int, int]:
        width, height = self.config.image_size
        return (
            int(width * 0.16),
            int(height * 0.18),
            int(width * 0.90),
            int(height * 0.80),
        )

    def _compute_highlight_box(self, task_data: Dict) -> List[int]:
        chart_type = task_data["chart_type"]
        if chart_type == "bar":
            return self._compute_bar_box(task_data["values"], task_data["target_index"])
        if chart_type == "line":
            return self._compute_line_box(task_data["values"], task_data["target_index"])
        if chart_type == "scatter":
            return self._compute_scatter_box(task_data["x_values"], task_data["values"], task_data["target_index"])
        return self._compute_pie_box(task_data["values"], task_data["target_index"])

    def _compute_bar_box(self, values: List[float], target_index: int) -> List[int]:
        left, top, right, bottom = self._chart_bounds()
        plot_width = right - left
        plot_height = bottom - top
        slot_width = plot_width / float(len(values))
        bar_width = slot_width * 0.55
        padding = 10
        maximum = max(values)
        minimum = min(values)
        value_range = max(maximum - minimum, 1e-6)

        x_left = left + target_index * slot_width + (slot_width - bar_width) / 2.0
        x_right = x_left + bar_width
        bar_height = ((values[target_index] - minimum) / value_range) * plot_height
        y_top = bottom - bar_height
        return [
            int(max(0, x_left - padding)),
            int(max(0, y_top - padding)),
            int(min(self.config.image_size[0] - 1, x_right + padding)),
            int(min(self.config.image_size[1] - 1, bottom + padding)),
        ]

    def _compute_line_box(self, values: List[float], target_index: int) -> List[int]:
        points = self._line_points(values)
        x, y = points[target_index]
        padding = 28
        return self._square_box(x, y, padding)

    def _compute_scatter_box(self, x_values: List[float], y_values: List[float], target_index: int) -> List[int]:
        points = self._scatter_points(x_values, y_values)
        x, y = points[target_index]
        padding = 28
        return self._square_box(x, y, padding)

    def _compute_pie_box(self, values: List[float], target_index: int) -> List[int]:
        width, height = self.config.image_size
        center_x = width // 2
        center_y = int(height * 0.54)
        radius = int(min(width, height) * 0.28)
        total = float(sum(values))
        start_angle = -90.0
        for index, value in enumerate(values):
            angle = (value / total) * 360.0
            end_angle = start_angle + angle
            if index == target_index:
                sample_points = [(center_x, center_y)]
                steps = max(int(abs(angle) // 3), 10)
                for step in range(steps + 1):
                    theta = math.radians(start_angle + (end_angle - start_angle) * step / float(steps))
                    sample_points.append(
                        (
                            center_x + radius * math.cos(theta),
                            center_y + radius * math.sin(theta),
                        )
                    )
                x_values = [point[0] for point in sample_points]
                y_values = [point[1] for point in sample_points]
                padding = 14
                return [
                    int(max(0, min(x_values) - padding)),
                    int(max(0, min(y_values) - padding)),
                    int(min(width - 1, max(x_values) + padding)),
                    int(min(height - 1, max(y_values) + padding)),
                ]
            start_angle = end_angle
        return [0, 0, width - 1, height - 1]

    def _square_box(self, x: float, y: float, padding: int) -> List[int]:
        width, height = self.config.image_size
        return [
            int(max(0, x - padding)),
            int(max(0, y - padding)),
            int(min(width - 1, x + padding)),
            int(min(height - 1, y + padding)),
        ]

    def _line_points(self, values: List[float]) -> List[Tuple[float, float]]:
        left, top, right, bottom = self._chart_bounds()
        plot_width = right - left
        plot_height = bottom - top
        maximum = max(values)
        minimum = min(values)
        value_range = max(maximum - minimum, 1e-6)
        x_padding = plot_width * 0.08
        y_padding = plot_height * 0.08
        usable_width = plot_width - 2 * x_padding
        usable_height = plot_height - 2 * y_padding
        points = []
        for index, value in enumerate(values):
            x_ratio = 0.5 if len(values) == 1 else index / float(len(values) - 1)
            x = left + x_padding + usable_width * x_ratio
            y_ratio = (value - minimum) / value_range
            y = bottom - y_padding - usable_height * y_ratio
            points.append((x, y))
        return points

    def _scatter_points(self, x_values: List[float], y_values: List[float]) -> List[Tuple[float, float]]:
        left, top, right, bottom = self._chart_bounds()
        plot_width = right - left
        plot_height = bottom - top
        x_padding = plot_width * 0.08
        y_padding = plot_height * 0.08
        usable_width = plot_width - 2 * x_padding
        usable_height = plot_height - 2 * y_padding
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)
        x_range = max(max_x - min_x, 1e-6)
        y_range = max(max_y - min_y, 1e-6)

        points = []
        for x_value, y_value in zip(x_values, y_values):
            x = left + x_padding + usable_width * ((x_value - min_x) / x_range)
            y = bottom - y_padding - usable_height * ((y_value - min_y) / y_range)
            points.append((x, y))
        return points

    def _render_chart(self, task_data: Dict, highlight: bool) -> Image.Image:
        chart_type = task_data["chart_type"]
        if chart_type == "bar":
            return self._render_bar_chart(task_data, highlight)
        if chart_type == "line":
            return self._render_line_chart(task_data, highlight)
        if chart_type == "scatter":
            return self._render_scatter_chart(task_data, highlight)
        return self._render_pie_chart(task_data, highlight)

    def _draw_title(self, draw: ImageDraw.ImageDraw, title: str) -> None:
        title_font = self._get_font(34)
        self._draw_text_centered(draw, title, (self.config.image_size[0] // 2, 56), title_font)

    def _draw_axis_frame(self, draw: ImageDraw.ImageDraw, metadata: Dict) -> None:
        left, top, right, bottom = self._chart_bounds()
        axis_color = (0, 0, 0)
        draw.line((left, bottom, right, bottom), fill=axis_color, width=3)
        draw.line((left, bottom, left, top), fill=axis_color, width=3)

        label_font = self._get_font(22)
        if metadata.get("x_label"):
            self._draw_text_centered(draw, metadata["x_label"], ((left + right) // 2, int(self.config.image_size[1] * 0.89)), label_font)
        if metadata.get("y_label"):
            draw.text((24, top - 18), metadata["y_label"], fill=axis_color, font=label_font)

    def _render_bar_chart(self, task_data: Dict, highlight: bool) -> Image.Image:
        img = Image.new("RGB", self.config.image_size, "white")
        draw = ImageDraw.Draw(img)
        metadata = task_data["metadata"]
        values = task_data["values"]
        labels = metadata["data_labels"]
        left, top, right, bottom = self._chart_bounds()
        plot_width = right - left
        plot_height = bottom - top
        slot_width = plot_width / float(len(values))
        bar_width = slot_width * 0.55
        maximum = max(values)
        minimum = min(values)
        value_range = max(maximum - minimum, 1e-6)
        title = metadata.get("title")
        if title:
            self._draw_title(draw, title)
        self._draw_axis_frame(draw, metadata)

        tick_font = self._get_font(18)
        value_font = self._get_font(18)
        for tick in range(6):
            tick_ratio = tick / 5.0
            y = bottom - plot_height * tick_ratio
            draw.line((left - 8, y, left, y), fill=(0, 0, 0), width=2)
            tick_value = minimum + value_range * tick_ratio
            tick_text = f"{tick_value:.0f}" if value_range >= 20 else f"{tick_value:.1f}"
            width, height = self._text_size(draw, tick_text, tick_font)
            draw.text((left - width - 14, y - height / 2), tick_text, fill=(0, 0, 0), font=tick_font)

        for index, value in enumerate(values):
            x_left = left + index * slot_width + (slot_width - bar_width) / 2.0
            x_right = x_left + bar_width
            bar_height = ((value - minimum) / value_range) * plot_height
            y_top = bottom - bar_height
            draw.rectangle((x_left, y_top, x_right, bottom), fill=self.SERIES_COLORS[index % len(self.SERIES_COLORS)], outline=(60, 60, 60), width=2)
            self._draw_text_centered(draw, str(labels[index]), (int((x_left + x_right) / 2), bottom + 28), tick_font)
            value_text = f"{value:.0f}" if value_range >= 20 else f"{value:.1f}"
            self._draw_text_centered(draw, value_text, (int((x_left + x_right) / 2), int(y_top - 18)), value_font, fill=(70, 70, 70))

        if highlight:
            draw.rectangle(task_data["highlight_box"], outline=self.HIGHLIGHT_COLOR, width=self.HIGHLIGHT_WIDTH)

        return img

    def _render_line_chart(self, task_data: Dict, highlight: bool) -> Image.Image:
        img = Image.new("RGB", self.config.image_size, "white")
        draw = ImageDraw.Draw(img)
        metadata = task_data["metadata"]
        values = task_data["values"]
        labels = metadata["data_labels"]
        points = self._line_points(values)
        title = metadata.get("title")
        if title:
            self._draw_title(draw, title)
        self._draw_axis_frame(draw, metadata)

        line_color = (54, 92, 173)
        tick_font = self._get_font(18)
        value_font = self._get_font(18)
        left, top, right, bottom = self._chart_bounds()
        maximum = max(values)
        minimum = min(values)
        value_range = max(maximum - minimum, 1e-6)
        plot_height = bottom - top

        for tick in range(6):
            tick_ratio = tick / 5.0
            y = bottom - plot_height * tick_ratio
            draw.line((left - 8, y, left, y), fill=(0, 0, 0), width=2)
            tick_value = minimum + value_range * tick_ratio
            tick_text = f"{tick_value:.1f}"
            width, height = self._text_size(draw, tick_text, tick_font)
            draw.text((left - width - 14, y - height / 2), tick_text, fill=(0, 0, 0), font=tick_font)

        for index in range(len(points) - 1):
            draw.line((points[index], points[index + 1]), fill=line_color, width=5)

        for index, point in enumerate(points):
            x, y = point
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=line_color, outline=(255, 255, 255), width=2)
            self._draw_text_centered(draw, str(labels[index]), (int(x), bottom + 28), tick_font)
            self._draw_text_centered(draw, f"{values[index]:.1f}", (int(x), int(y - 22)), value_font, fill=(70, 70, 70))

        if highlight:
            draw.rectangle(task_data["highlight_box"], outline=self.HIGHLIGHT_COLOR, width=self.HIGHLIGHT_WIDTH)

        return img

    def _render_scatter_chart(self, task_data: Dict, highlight: bool) -> Image.Image:
        img = Image.new("RGB", self.config.image_size, "white")
        draw = ImageDraw.Draw(img)
        metadata = task_data["metadata"]
        x_values = task_data["x_values"]
        y_values = task_data["values"]
        points = self._scatter_points(x_values, y_values)
        title = metadata.get("title")
        if title:
            self._draw_title(draw, title)
        self._draw_axis_frame(draw, metadata)

        point_color = (54, 92, 173)
        label_font = self._get_font(18)
        for index, (x, y) in enumerate(points):
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=point_color, outline=(255, 255, 255), width=2)
            draw.text((x + 12, y - 12), f"({x_values[index]:.1f}, {y_values[index]:.1f})", fill=(70, 70, 70), font=label_font)

        self._draw_scatter_ticks(draw, x_values, y_values)

        if highlight:
            draw.rectangle(task_data["highlight_box"], outline=self.HIGHLIGHT_COLOR, width=self.HIGHLIGHT_WIDTH)

        return img

    def _draw_scatter_ticks(self, draw: ImageDraw.ImageDraw, x_values: List[float], y_values: List[float]) -> None:
        left, top, right, bottom = self._chart_bounds()
        plot_width = right - left
        plot_height = bottom - top
        font = self._get_font(18)
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        for tick in range(5):
            ratio = tick / 4.0
            x = left + plot_width * ratio
            value = min_x + (max_x - min_x) * ratio
            text = f"{value:.1f}"
            self._draw_text_centered(draw, text, (int(x), bottom + 28), font)

            y = bottom - plot_height * ratio
            y_value = min_y + (max_y - min_y) * ratio
            label = f"{y_value:.1f}"
            width, height = self._text_size(draw, label, font)
            draw.text((left - width - 14, y - height / 2), label, fill=(0, 0, 0), font=font)

    def _render_pie_chart(self, task_data: Dict, highlight: bool) -> Image.Image:
        img = Image.new("RGB", self.config.image_size, "white")
        draw = ImageDraw.Draw(img)
        values = task_data["values"]
        metadata = task_data["metadata"]
        labels = metadata["data_labels"]
        if metadata.get("title"):
            self._draw_title(draw, metadata["title"])

        width, height = self.config.image_size
        center_x = width // 2
        center_y = int(height * 0.54)
        radius = int(min(width, height) * 0.28)
        total = float(sum(values))
        start_angle = -90.0
        label_font = self._get_font(18)
        percent_font = self._get_font(20)

        for index, value in enumerate(values):
            extent = 360.0 * value / total
            end_angle = start_angle + extent
            color = self.SERIES_COLORS[index % len(self.SERIES_COLORS)]
            draw.pieslice(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                start_angle,
                end_angle,
                fill=color,
                outline="white",
                width=2,
            )

            mid_angle = math.radians((start_angle + end_angle) / 2.0)
            label_x = center_x + math.cos(mid_angle) * radius * 1.18
            label_y = center_y + math.sin(mid_angle) * radius * 1.18
            text = f"{labels[index]} ({value:.1f}%)"
            self._draw_text_centered(draw, text, (int(label_x), int(label_y)), label_font)

            inner_x = center_x + math.cos(mid_angle) * radius * 0.55
            inner_y = center_y + math.sin(mid_angle) * radius * 0.55
            self._draw_text_centered(draw, f"{value:.1f}%", (int(inner_x), int(inner_y)), percent_font)
            start_angle = end_angle

        if highlight:
            draw.rectangle(task_data["highlight_box"], outline=self.HIGHLIGHT_COLOR, width=self.HIGHLIGHT_WIDTH)

        return img
