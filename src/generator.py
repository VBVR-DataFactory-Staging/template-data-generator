"""Multi-view Camera Positioning Task Generator."""

from __future__ import annotations

import math
import random
import tempfile
import re
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair
from core.video_utils import VideoGenerator

from .config import TaskConfig
from .prompts import DEFAULT_ORIENTATION_INFO, VIEW_NAME_MAP, get_prompt
from .renderer.blender_renderer import BlenderRenderer


class TaskGenerator(BaseGenerator):
    """Generator for multi-view camera positioning tasks."""

    def __init__(self, config: TaskConfig):
        super().__init__(config)

        try:
            self.renderer = BlenderRenderer(
                blender_executable=config.blender_executable,
                blender_version=config.blender_version,
                render_resolution=config.render_resolution,
                render_engine=config.render_engine,
                background_color=config.background_color,
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"Failed to initialize Blender renderer: {exc}\n"
                "Please run: python scripts/install_blender.py"
            ) from exc

        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(
                fps=config.video_fps, output_format="mp4"
            )

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate a single multi-view task."""
        task_data = self._sample_task_data(task_id)

        initial_view = task_data["initial_view"]
        target_view = task_data["target_view"]
        camera_distance = task_data["camera_distance"]

        initial_def = self.config.view_definitions[initial_view]
        target_def = self.config.view_definitions[target_view]

        initial_quat = self._build_orientation_quaternion(
            initial_def["azimuth"], initial_def["elevation"]
        )
        target_quat = self._build_orientation_quaternion(
            target_def["azimuth"], target_def["elevation"]
        )
        initial_forward = self._quaternion_forward(initial_quat)
        target_forward = self._quaternion_forward(target_quat)
        initial_location = tuple(-(initial_forward * camera_distance))
        target_location = tuple(-(target_forward * camera_distance))

        first_image = self.renderer.render_scene(
            objects=task_data["objects"],
            camera_azimuth=initial_def["azimuth"],
            camera_elevation=initial_def["elevation"],
            camera_distance=camera_distance,
            rotation_quaternion=tuple(initial_quat.tolist()),
            camera_location=initial_location,
        )
        first_image = self._annotate_camera_pose(
            first_image,
            initial_view,
            initial_def["azimuth"],
            initial_def["elevation"],
            target_def["azimuth"] - initial_def["azimuth"],
            target_def["elevation"] - initial_def["elevation"],
            rotation_quaternion=initial_quat,
        )
        first_image = self._draw_view_indicator(first_image, target_view)

        final_image = self.renderer.render_scene(
            objects=task_data["objects"],
            camera_azimuth=target_def["azimuth"],
            camera_elevation=target_def["elevation"],
            camera_distance=camera_distance,
            rotation_quaternion=tuple(target_quat.tolist()),
            camera_location=target_location,
        )
        final_image = self._annotate_camera_pose(
            final_image,
            target_view,
            target_def["azimuth"],
            target_def["elevation"],
            0.0,
            0.0,
            rotation_quaternion=target_quat,
        )

        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_camera_motion_video(
                task_data["objects"],
                initial_def["azimuth"],
                initial_def["elevation"],
                target_def["azimuth"],
                target_def["elevation"],
                initial_view,
                target_view,
                task_id,
                task_data,
                camera_distance,
            )

        primary_obj = next((obj for obj in task_data["objects"] if obj.get("id") == "obj_primary"), None)
        rubik_info = self._build_rubik_info(primary_obj)
        object_summary = self._build_object_summary(task_data["objects"])
        orientation_info = DEFAULT_ORIENTATION_INFO

        prompt = get_prompt(
            initial_view=initial_view,
            target_view=target_view,
            num_objects=len(task_data["objects"]),
            object_summary=object_summary,
            rubik_info=rubik_info,
            orientation_info=orientation_info,
        )

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path,
        )

    def generate_dataset(self):
        """Generate dataset while avoiding overwriting existing tasks."""
        base_dir = self.config.output_dir / f"{self.config.domain}_task"
        start_idx = 0
        if base_dir.exists():
            pattern = re.compile(rf"{re.escape(self.config.domain)}_(\d+)$")
            existing_indices = []
            for path in base_dir.iterdir():
                if path.is_dir():
                    m = pattern.match(path.name)
                    if m:
                        try:
                            existing_indices.append(int(m.group(1)))
                        except ValueError:
                            pass
            if existing_indices:
                start_idx = max(existing_indices) + 1

        pairs = []
        for i in range(self.config.num_samples):
            idx = start_idx + i
            task_id = f"{self.config.domain}_{idx:04d}"
            pair = self.generate_task_pair(task_id)
            pairs.append(pair)
            print(f"  Generated: {task_id}")
        return pairs

    def _sample_task_data(self, task_id: str) -> dict:
        """Sample task data for one scene."""
        seed = int(hash(task_id) % (2**31))
        random.seed(seed)
        np.random.seed(seed)

        initial_view, target_view = self._sample_view_pair()

        num_objects = random.randint(*self.config.num_objects_range)

        objects = []
        used_objects: list[dict] = []

        # Always include the primary object (Rubik's cube by default)
        primary_position = self.config.single_object_position
        primary_size = random.uniform(*self.config.primary_size_range)
        objects.append(
            {
                "id": "obj_primary",
                "type": self.config.primary_object_type,
                "position": primary_position,
                "size": primary_size,
                "color": (1.0, 1.0, 1.0),  # not used; faces carry colors
                "face_colors": self.config.rubik_face_colors,
            }
        )
        primary_radius = self._object_radius(self.config.primary_object_type, primary_size)
        used_objects.append({"pos": primary_position, "radius": primary_radius})

        # Add auxiliary objects if needed
        for i in range(num_objects - 1):
            obj_type = random.choice(self.config.object_types) if self.config.object_types else "cube"
            obj_size = random.uniform(*self.config.aux_size_range)
            radius = self._object_radius(obj_type, obj_size)

            position = self._sample_position(radius, used_objects)
            used_objects.append({"pos": position, "radius": radius})

            objects.append(
                {
                    "id": f"obj_aux_{i}",
                    "type": obj_type,
                    "position": position,
                    "size": obj_size,
                    "color": random.choice(self.config.object_colors),
                }
            )

        return {
            "initial_view": initial_view,
            "target_view": target_view,
            "objects": objects,
            "camera_distance": self._compute_camera_distance(objects),
        }

    def _format_position(self, position: tuple[float, float, float]) -> str:
        """Format a 3D position for prompts."""
        try:
            x, y, z = position  # type: ignore
        except Exception:
            x, y, z = 0.0, 0.0, 0.0
        return f"({float(x):.2f}, {float(y):.2f}, {float(z):.2f})"

    def _format_color(self, color: Optional[tuple[float, float, float]]) -> str:
        """Format an RGB color tuple for prompts."""
        if color is None:
            return "unspecified color"
        try:
            r, g, b = color[:3]  # type: ignore
            return f"rgb({float(r):.2f}, {float(g):.2f}, {float(b):.2f})"
        except Exception:
            return str(color)

    def _format_size(self, size: Optional[float]) -> str:
        """Format a scalar size for prompts."""
        try:
            return f"{float(size):.2f}"
        except Exception:
            return "unspecified size"

    def _matrix_to_quaternion(self, matrix: np.ndarray) -> np.ndarray:
        """Convert a 3x3 rotation matrix to a quaternion (w, x, y, z)."""
        m = matrix
        trace = m[0, 0] + m[1, 1] + m[2, 2]
        if trace > 0.0:
            s = math.sqrt(trace + 1.0) * 2.0
            w = 0.25 * s
            x = (m[2, 1] - m[1, 2]) / s
            y = (m[0, 2] - m[2, 0]) / s
            z = (m[1, 0] - m[0, 1]) / s
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
            w = (m[2, 1] - m[1, 2]) / s
            x = 0.25 * s
            y = (m[0, 1] + m[1, 0]) / s
            z = (m[0, 2] + m[2, 0]) / s
        elif m[1, 1] > m[2, 2]:
            s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
            w = (m[0, 2] - m[2, 0]) / s
            x = (m[0, 1] + m[1, 0]) / s
            y = 0.25 * s
            z = (m[1, 2] + m[2, 1]) / s
        else:
            s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
            w = (m[1, 0] - m[0, 1]) / s
            x = (m[0, 2] + m[2, 0]) / s
            y = (m[1, 2] + m[2, 1]) / s
            z = 0.25 * s
        q = np.array([w, x, y, z], dtype=np.float64)
        return q / (np.linalg.norm(q) + 1e-9)

    def _quaternion_to_matrix(self, q: np.ndarray) -> np.ndarray:
        """Convert quaternion (w, x, y, z) to a 3x3 rotation matrix."""
        w, x, y, z = q
        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z

        return np.array(
            [
                [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
                [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
                [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
            ],
            dtype=np.float64,
        )

    def _quaternion_slerp(self, q0: np.ndarray, q1: np.ndarray, t: float) -> np.ndarray:
        """Slerp between two quaternions (w, x, y, z)."""
        q0 = q0 / (np.linalg.norm(q0) + 1e-9)
        q1 = q1 / (np.linalg.norm(q1) + 1e-9)
        dot = float(np.dot(q0, q1))
        if dot < 0.0:
            q1 = -q1
            dot = -dot
        if dot > 0.9995:
            result = q0 + t * (q1 - q0)
            return result / (np.linalg.norm(result) + 1e-9)
        theta_0 = math.acos(dot)
        sin_theta_0 = math.sin(theta_0)
        theta = theta_0 * t
        sin_theta = math.sin(theta)
        s0 = math.cos(theta) - dot * sin_theta / (sin_theta_0 + 1e-9)
        s1 = sin_theta / (sin_theta_0 + 1e-9)
        return s0 * q0 + s1 * q1

    def _build_orientation_quaternion(self, azimuth: float, elevation: float) -> np.ndarray:
        """Build a stable camera orientation quaternion from azimuth/elevation with fixed roll."""
        # Azimuth/elevation define the camera position on the sphere; forward points from camera to origin.
        forward = -self._angles_to_vector(azimuth, elevation)
        world_up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        if abs(np.dot(forward, world_up)) > 0.995:
            world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        right = np.cross(forward, world_up)
        if np.linalg.norm(right) < 1e-9:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        else:
            right /= np.linalg.norm(right)
        up_vec = np.cross(right, forward)
        if np.linalg.norm(up_vec) < 1e-9:
            up_vec = world_up
        else:
            up_vec /= np.linalg.norm(up_vec)
        rot_mat = np.array(
            [
                [right[0], up_vec[0], -forward[0]],
                [right[1], up_vec[1], -forward[1]],
                [right[2], up_vec[2], -forward[2]],
            ],
            dtype=np.float64,
        )
        return self._matrix_to_quaternion(rot_mat)

    def _quaternion_forward(self, q: np.ndarray) -> np.ndarray:
        """Get camera forward vector from a quaternion (camera to origin)."""
        rot = self._quaternion_to_matrix(q)
        # Camera forward corresponds to -Z in camera local frame.
        forward = -rot[:, 2]
        norm = np.linalg.norm(forward)
        return forward / (norm + 1e-9)

    def _build_rubik_info(self, primary_obj: Optional[dict]) -> str:
        """Create a fixed description of the Rubik's cube for the prompt."""
        primary = primary_obj or {}
        position = primary.get("position", self.config.single_object_position)
        face_colors = primary.get("face_colors", self.config.rubik_face_colors)

        pos_str = self._format_position(position)

        def face_color(axis: str) -> str:
            return self._format_color(face_colors.get(axis))

        return (
            f"Primary object is a Rubik's cube at {pos_str}, aligned with the world axes with "
            f"face colors (+X: {face_color('+X')}, -X: {face_color('-X')}, "
            f"+Y: {face_color('+Y')}, -Y: {face_color('-Y')}, "
            f"+Z: {face_color('+Z')}, -Z: {face_color('-Z')})."
        )

    def _build_object_summary(self, objects: list[dict]) -> str:
        """Summarize auxiliary objects for inclusion in prompts."""
        parts = []
        for obj in objects:
            if obj.get("id") == "obj_primary":
                continue
            obj_type = obj.get("type", "object")
            pos_str = self._format_position(obj.get("position", (0.0, 0.0, 0.0)))
            color_str = self._format_color(obj.get("color"))
            size_str = self._format_size(obj.get("size"))
            parts.append(f"{obj_type} (size {size_str}) at {pos_str} in {color_str}")
        return "; ".join(parts) if parts else "none"

    def _sample_view_pair(self) -> tuple[str, str]:
        """Sample initial and target camera views."""
        available = self.config.available_views.copy()

        if self.config.initial_fixed_view:
            initial_view = self.config.initial_fixed_view
            if initial_view not in available:
                initial_view = "front"
        else:
            initial_view = (
                "front" if self.config.initial_view_strategy == "fixed" else random.choice(available)
            )

        available.remove(initial_view)

        if self.config.target_view_strategy == "opposite":
            target_view = self._get_opposite_view(initial_view, available)
        elif self.config.target_view_strategy == "adjacent":
            target_view = self._get_adjacent_view(initial_view, available)
        elif self.config.view_transition_difficulty == "easy":
            target_view = self._get_adjacent_view(initial_view, available)
        elif self.config.view_transition_difficulty == "hard":
            target_view = self._get_distant_view(initial_view, available)
        else:
            target_view = random.choice(available)

        return initial_view, target_view

    def _get_opposite_view(self, view: str, available: list[str]) -> str:
        opposite_map = {
            "front": "back",
            "back": "front",
            "left": "right",
            "right": "left",
            "front_left": "back_right",
            "front_right": "back_left",
            "back_left": "front_right",
            "back_right": "front_left",
        }
        opposite = opposite_map.get(view)
        if opposite and opposite in available:
            return opposite
        return available[0]

    def _get_adjacent_view(self, view: str, available: list[str]) -> str:
        adjacent_map = {
            "front": ["front_left", "front_right", "left", "right"],
            "left": ["front_left", "back_left", "front", "back"],
            "right": ["front_right", "back_right", "front", "back"],
            "back": ["back_left", "back_right", "left", "right"],
            "front_left": ["front", "left", "top_down"],
            "front_right": ["front", "right", "top_down"],
            "back_left": ["back", "left", "top_down"],
            "back_right": ["back", "right", "top_down"],
            "top_down": ["front", "back", "left", "right"],
        }
        candidates = [v for v in adjacent_map.get(view, ["front"]) if v in available]
        return random.choice(candidates) if candidates else available[0]

    def _get_distant_view(self, view: str, available: list[str]) -> str:
        if view == "front":
            candidates = [v for v in ["back", "top_down"] if v in available]
        elif view == "top_down":
            candidates = [v for v in ["front", "back", "left", "right"] if v in available]
        else:
            candidates = [v for v in ["top_down", "back"] if v in available]
        return random.choice(candidates) if candidates else available[0]

    def _object_radius(self, obj_type: str, size: float) -> float:
        """Approximate bounding radius for spacing and camera distance."""
        if obj_type == "sphere":
            return size
        if obj_type in {"cylinder", "pyramid"}:
            return size * 0.7
        return size * 0.9  # cube/rubik/default

    def _sample_position(self, radius: float, used_objects: list[dict]) -> tuple[float, float, float]:
        """Sample a position that respects spacing from existing objects."""
        max_attempts = 200
        r_min = self.config.object_position_range[0]
        r_max = self.config.object_position_range[1]
        for _ in range(max_attempts):
            x = random.uniform(r_min, r_max)
            y = random.uniform(r_min, r_max)
            candidate = (x, y, 0.0)
            too_close = False
            for u in used_objects:
                dx = candidate[0] - u["pos"][0]
                dy = candidate[1] - u["pos"][1]
                dist_sq = dx * dx + dy * dy
                spacing = radius + u["radius"] + self.config.min_object_spacing + self.config.safety_margin
                min_dist = spacing * spacing
                if dist_sq < min_dist:
                    too_close = True
                    break
            if not too_close:
                return candidate

        # Fallback: place on a ring outside all extents
        largest = max(
            (math.sqrt(u["pos"][0] ** 2 + u["pos"][1] ** 2) + u["radius"] for u in used_objects),
            default=0.0,
        )
        min_ring = largest + radius + self.config.min_object_spacing + self.config.safety_margin + 0.1
        angle = random.uniform(0, 2 * math.pi)
        return (
            min_ring * math.cos(angle),
            min_ring * math.sin(angle),
            0.0,
        )

    def _angles_to_vector(self, azimuth: float, elevation: float) -> np.ndarray:
        """Convert azimuth/elevation (deg) to unit vector."""
        az = np.radians(azimuth)
        el = np.radians(elevation)
        x = np.cos(el) * np.cos(az)
        y = np.cos(el) * np.sin(az)
        z = np.sin(el)
        vec = np.array([x, y, z], dtype=np.float64)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def _vector_to_angles(self, vec: np.ndarray) -> tuple[float, float]:
        """Convert unit vector to azimuth/elevation (deg)."""
        x, y, z = vec
        az = np.degrees(np.arctan2(y, x))
        el = np.degrees(np.arctan2(z, np.sqrt(x * x + y * y)))
        return az, el
    
    def _quat_to_axes(self, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return right, up, forward vectors from a quaternion."""
        rot = self._quaternion_to_matrix(q)
        right = rot[:, 0]
        up_vec = rot[:, 1]
        forward = -rot[:, 2]
        return right, up_vec, forward

    def _slerp_vectors(self, v0: np.ndarray, v1: np.ndarray, t: float) -> np.ndarray:
        """Spherical linear interpolation between two unit vectors."""
        v0 = v0 / (np.linalg.norm(v0) + 1e-9)
        v1 = v1 / (np.linalg.norm(v1) + 1e-9)
        dot = np.clip(np.dot(v0, v1), -1.0, 1.0)
        if dot > 0.9995:
            # nearly parallel -> lerp then renormalize
            vec = v0 + t * (v1 - v0)
            return vec / (np.linalg.norm(vec) + 1e-9)
        theta = np.arccos(dot)
        sin_theta = np.sin(theta)
        a = np.sin((1 - t) * theta) / (sin_theta + 1e-9)
        b = np.sin(t * theta) / (sin_theta + 1e-9)
        return a * v0 + b * v1

    def _compute_camera_distance(self, objects: list[dict]) -> float:
        """Compute a camera distance that keeps all objects in view."""
        base = self.config.camera_distance
        max_radius = 0.0
        for obj in objects:
            x, y, _ = obj["position"]
            radius = self._object_radius(obj["type"], obj["size"])
            extent = (x * x + y * y) ** 0.5 + radius + self.config.safety_margin
            if extent > max_radius:
                max_radius = extent

        fov_rad = math.radians(self.config.camera_fov_deg) if self.config.camera_fov_deg > 1e-3 else math.radians(60.0)
        trig_distance = (max_radius / max(1e-6, math.tan(fov_rad / 2.0))) * 1.1
        return max(base, max_radius * 1.8, trig_distance)

    def _draw_view_indicator(self, image: Image.Image, target_view: str) -> Image.Image:
        """Draw target view indicator on the first frame."""
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
            )
        except Exception:
            font = ImageFont.load_default()

        view_name = VIEW_NAME_MAP.get(target_view, target_view)
        text = f"-> {view_name}"

        bbox = draw.textbbox((20, 20), text, font=font)
        draw.rectangle(bbox, fill=(255, 255, 255, 200), outline=(255, 0, 0), width=2)

        draw.text((22, 22), text, fill=(255, 0, 0), font=font)
        return image.convert("RGB")

    def _annotate_camera_pose(
        self,
        image: Image.Image,
        view_name: str,
        azimuth: float,
        elevation: float,
        yaw_delta: float = 0.0,
        pitch_delta: float = 0.0,
        rotation_quaternion: Optional[np.ndarray] = None,
    ) -> Image.Image:
        """Overlay camera pose info on an image."""
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
            )
        except Exception:
            font = ImageFont.load_default()

        text = f"{view_name} (az {azimuth:.0f}°, el {elevation:.0f}°)"
        if yaw_delta or pitch_delta:
            text += f" | Δyaw {yaw_delta:.0f}°, Δpitch {pitch_delta:.0f}°"
        bbox = draw.textbbox((20, 60), text, font=font)
        draw.rectangle(bbox, fill=(255, 255, 255, 200), outline=(0, 0, 0), width=2)
        draw.text((22, 62), text, fill=(0, 0, 0), font=font)
        image = self._draw_axes_icon(image, azimuth, elevation, rotation_quaternion)
        return image.convert("RGB")

    def _draw_axes_icon(
        self,
        image: Image.Image,
        azimuth: float,
        elevation: float,
        rotation_quaternion: Optional[np.ndarray] = None,
    ) -> Image.Image:
        """Draw a small XYZ axes icon based on camera orientation."""
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        draw = ImageDraw.Draw(image)

        if rotation_quaternion is not None:
            right, up_vec, forward = self._quat_to_axes(rotation_quaternion)
        else:
            forward = self._angles_to_vector(azimuth, elevation)
            world_up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
            if abs(np.dot(forward, world_up)) > 0.99:
                world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
            right = np.cross(forward, world_up)
            right /= np.linalg.norm(right) + 1e-9
            up_vec = np.cross(right, forward)
            up_vec /= np.linalg.norm(up_vec) + 1e-9

        axes = {
            "X": (np.array([1.0, 0.0, 0.0]), (255, 0, 0)),
            "Y": (np.array([0.0, 1.0, 0.0]), (0, 180, 0)),
            "Z": (np.array([0.0, 0.0, 1.0]), (0, 0, 255)),
        }

        cx = image.width - 70
        cy = image.height - 70
        scale = 50

        for label, (vec, color) in axes.items():
            sx = float(np.dot(vec, right))
            sy = float(np.dot(vec, up_vec))
            ex = cx + sx * scale
            ey = cy - sy * scale
            draw.line((cx, cy, ex, ey), fill=color, width=3)
            draw.text((ex + 4, ey - 4), label, fill=color)

        return image

    def _generate_camera_motion_video(
        self,
        objects: list,
        initial_azimuth: float,
        initial_elevation: float,
        target_azimuth: float,
        target_elevation: float,
        initial_view: str,
        target_view: str,
        task_id: str,
        task_data: dict,
        camera_distance: float,
    ) -> str:
        """Generate a camera motion animation."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = []

        start_quat = self._build_orientation_quaternion(initial_azimuth, initial_elevation)
        end_quat = self._build_orientation_quaternion(target_azimuth, target_elevation)
        start_forward = self._quaternion_forward(start_quat)
        end_forward = self._quaternion_forward(end_quat)
        start_loc = tuple(-(start_forward * camera_distance))
        end_loc = tuple(-(end_forward * camera_distance))

        first_frame = self.renderer.render_scene(
            objects=objects,
            camera_azimuth=initial_azimuth,
            camera_elevation=initial_elevation,
            camera_distance=camera_distance,
            rotation_quaternion=tuple(start_quat.tolist()),
            camera_location=start_loc,
        )
        first_frame = self._annotate_camera_pose(
            first_frame, "initial", initial_azimuth, initial_elevation, rotation_quaternion=start_quat
        )
        for _ in range(self.config.initial_hold_frames):
            frames.append(first_frame)

        num_transition_frames = self.config.transition_frames
        if initial_view == "top_down":
            num_transition_frames += self.config.top_down_extra_frames
        for i in range(num_transition_frames):
            progress = i / (num_transition_frames - 1) if num_transition_frames > 1 else 1.0
            eased_progress = progress * progress * (3.0 - 2.0 * progress)

            quat = self._quaternion_slerp(start_quat, end_quat, eased_progress)
            forward_vec = self._quaternion_forward(quat)
            dir_vec = -forward_vec  # direction from origin to camera
            azimuth, elevation = self._vector_to_angles(dir_vec)
            camera_loc = tuple(-(forward_vec * camera_distance))

            frame = self.renderer.render_scene(
                objects=objects,
                camera_azimuth=azimuth,
                camera_elevation=elevation,
                camera_distance=camera_distance,
                rotation_quaternion=tuple(quat.tolist()),
                camera_location=camera_loc,
            )
            yaw_delta = azimuth - target_azimuth if target_azimuth is not None else 0.0
            pitch_delta = elevation - target_elevation if target_elevation is not None else 0.0
            frame = self._annotate_camera_pose(
                frame,
                "moving",
                azimuth,
                elevation,
                yaw_delta,
                pitch_delta,
                rotation_quaternion=quat,
            )
            frames.append(frame)

        final_frame = self.renderer.render_scene(
            objects=objects,
            camera_azimuth=target_azimuth,
            camera_elevation=target_elevation,
            camera_distance=camera_distance,
            rotation_quaternion=tuple(end_quat.tolist()),
            camera_location=end_loc,
        )
        final_frame = self._annotate_camera_pose(
            final_frame, "target", target_azimuth, target_elevation, 0.0, 0.0, rotation_quaternion=end_quat
        )
        for _ in range(self.config.final_hold_frames):
            frames.append(final_frame)

        max_frames = int(self.config.max_video_duration * self.config.video_fps)
        if len(frames) > max_frames:
            frames = frames[:max_frames]

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
