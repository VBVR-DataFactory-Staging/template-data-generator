"""Blender renderer for multi-view camera tasks (Blender 5.0)."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

BLENDER_VERSION = "5.0.0"


class BlenderRenderer:
    """Thin wrapper around Blender for rendering simple scenes."""

    def __init__(
        self,
        blender_executable: Optional[Path] = None,
        blender_version: str = BLENDER_VERSION,
        render_resolution: Tuple[int, int] = (512, 512),
        render_engine: str = "EEVEE",
        background_color: Tuple[float, float, float] = (0.96, 0.96, 0.94),
    ):
        self.blender_version = blender_version
        self.blender_exec = self._find_blender(blender_executable)
        self.render_resolution = render_resolution
        self.render_engine = self._normalize_engine(render_engine)
        self.background_color = background_color

        if self.blender_exec is None:
            raise RuntimeError(
                f"Blender {blender_version} not found or not runnable. Please install:\n"
                "  Run: python scripts/install_blender.py\n"
                "  Or install manually from: https://www.blender.org/download/"
            )

    def _find_blender(self, custom_path: Optional[Path]) -> Optional[Path]:
        """Find a Blender executable (prefer local install)."""
        if custom_path and Path(custom_path).exists():
            candidate = Path(custom_path)
            if self._verify_blender(candidate):
                return candidate

        project_root = Path(__file__).parent.parent.parent
        blender_exe_name = f"blender-{self.blender_version}-linux-x64"
        local_blender = project_root / "blender" / blender_exe_name / "blender"

        if local_blender.exists() and self._verify_blender(local_blender):
            return local_blender

        try:
            result = subprocess.run(
                ["which", "blender"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                exe_path = result.stdout.strip().split("\n")[0]
                candidate = Path(exe_path)
                if candidate.exists() and self._verify_blender(candidate):
                    return candidate
        except Exception:
            pass

        return None

    def _verify_blender(self, path: Path) -> bool:
        """Ensure a candidate Blender executable can run headless."""
        try:
            result = subprocess.run(
                [str(path), "--background", "--version"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _normalize_engine(self, engine: str) -> str:
        """Normalize render engine names for Blender 5.0."""
        normalized = engine.upper()
        if normalized == "EEVEE":
            return "BLENDER_EEVEE"
        if normalized == "WORKBENCH":
            return "BLENDER_WORKBENCH"
        return normalized

    def render_scene(
        self,
        objects: List[Dict],
        camera_azimuth: float,
        camera_elevation: float,
        camera_distance: float = 5.0,
        output_path: Optional[Path] = None,
        rotation_quaternion: Optional[Tuple[float, float, float, float]] = None,
        camera_location: Optional[Tuple[float, float, float]] = None,
    ) -> Image.Image:
        """Render a scene from a specific view."""
        if output_path is None:
            output_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            output_path = Path(output_file.name)
            output_file.close()

        script = self._generate_blender_script(
            objects,
            camera_azimuth,
            camera_elevation,
            camera_distance,
            output_path,
            rotation_quaternion,
            camera_location,
        )
        stdout, stderr, returncode = self._run_blender_script(script)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(
                "Blender did not produce an image file. "
                "Verify Blender installation or run scripts/install_blender.py.\n"
                f"STDOUT: {stdout}\nSTDERR: {stderr}"
            )

        with Image.open(output_path) as img:
            image = img.copy()

        if output_path.exists() and str(output_path).startswith(tempfile.gettempdir()):
            try:
                output_path.unlink()
            except Exception:
                pass

        return image

    def _generate_blender_script(
        self,
        objects: List[Dict],
        camera_azimuth: float,
        camera_elevation: float,
        camera_distance: float,
        output_path: Path,
        rotation_quaternion: Optional[Tuple[float, float, float, float]],
        camera_location: Optional[Tuple[float, float, float]],
    ) -> str:
        """Create a Blender Python script compatible with Blender 5.0."""
        quat_str = (
            f"({rotation_quaternion[0]}, {rotation_quaternion[1]}, {rotation_quaternion[2]}, {rotation_quaternion[3]})"
            if rotation_quaternion
            else "None"
        )
        cam_loc_str = (
            f"({camera_location[0]}, {camera_location[1]}, {camera_location[2]})"
            if camera_location
            else "None"
        )
        script = f"""import bpy
import math
import mathutils
from mathutils import Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.context.scene.render.engine = '{self.render_engine}'
bpy.context.scene.render.resolution_x = {self.render_resolution[0]}
bpy.context.scene.render.resolution_y = {self.render_resolution[1]}

world = bpy.context.scene.world
if not world.use_nodes:
    world.use_nodes = True
world.node_tree.nodes.clear()
bg_node = world.node_tree.nodes.new('ShaderNodeBackground')
bg_output = world.node_tree.nodes.new('ShaderNodeOutputWorld')
bg_node.inputs['Color'].default_value = {self.background_color + (1.0,)}
bg_node.inputs['Strength'].default_value = 2.0
world.node_tree.links.new(bg_node.outputs['Background'], bg_output.inputs['Surface'])

# Add a sun light for brighter illumination
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (5.0, -5.0, 8.0)
sun.rotation_euler = (math.radians(50), math.radians(0), math.radians(30))

camera_data = bpy.data.cameras.new(name='Camera')
camera = bpy.data.objects.new('Camera', camera_data)
bpy.context.scene.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.angle = math.radians({getattr(self, "camera_fov_deg", 60.0) if hasattr(self, "camera_fov_deg") else 60.0})
camera.data.clip_start = 0.05
camera.data.clip_end = 200.0

if {cam_loc_str} is None:
    azimuth_rad = math.radians({camera_azimuth})
    elevation_rad = math.radians({camera_elevation})
    distance = {camera_distance}
    x = distance * math.cos(elevation_rad) * math.cos(azimuth_rad)
    y = distance * math.cos(elevation_rad) * math.sin(azimuth_rad)
    z = distance * math.sin(elevation_rad)
    camera.location = (x, y, z)
else:
    camera.location = {cam_loc_str}

if {quat_str} is None:
    forward = (Vector((0, 0, 0)) - Vector(camera.location)).normalized()
    world_up = Vector((0.0, 0.0, 1.0))
    if abs(forward.dot(world_up)) > 0.995:
        # Near-polar views (e.g., top-down) can produce unstable roll; lock up to +Y for determinism.
        world_up = Vector((0.0, 1.0, 0.0))
    right = forward.cross(world_up)
    if right.length < 1e-6:
        right = Vector((1.0, 0.0, 0.0))
    else:
        right.normalize()
    up_vec = right.cross(forward)
    if up_vec.length < 1e-6:
        up_vec = world_up
    else:
        up_vec.normalize()
    # Build rotation matrix to align camera local axes: +X=right, +Y=up, -Z=forward
    rot_mat = mathutils.Matrix((
        (right.x, up_vec.x, -forward.x),
        (right.y, up_vec.y, -forward.y),
        (right.z, up_vec.z, -forward.z),
    ))
    camera.rotation_euler = rot_mat.to_euler()
else:
    camera.rotation_mode = 'QUATERNION'
    camera.rotation_quaternion = {quat_str}

"""

        for i, obj in enumerate(objects):
            obj_type = obj["type"]
            pos = obj["position"]
            size = obj["size"]
            color = obj["color"]

            if obj_type == "cube":
                script += f"""bpy.ops.mesh.primitive_cube_add(size=2.0, location={pos})
obj_{i} = bpy.context.active_object
obj_{i}.scale = ({size/2}, {size/2}, {size/2})
"""
            elif obj_type == "sphere":
                script += f"""bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location={pos})
obj_{i} = bpy.context.active_object
obj_{i}.scale = ({size}, {size}, {size})
"""
            elif obj_type == "cylinder":
                script += f"""bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, location={pos})
obj_{i} = bpy.context.active_object
obj_{i}.scale = ({size/2}, {size/2}, {size/2})
"""
            elif obj_type == "pyramid":
                script += f"""bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, location={pos})
obj_{i} = bpy.context.active_object
obj_{i}.scale = ({size/2}, {size/2}, {size/2})
"""
            elif obj_type == "rubik":
                face_colors = obj.get("face_colors", {
                    "+X": (1.0, 0.0, 0.0),
                    "-X": (1.0, 0.5, 0.0),
                    "+Y": (0.0, 1.0, 0.0),
                    "-Y": (0.0, 0.0, 1.0),
                    "+Z": (1.0, 1.0, 1.0),
                    "-Z": (1.0, 1.0, 0.0),
                })
                script += f"""# Rubik's cube
rubik_faces_{i} = {face_colors}
bpy.ops.mesh.primitive_cube_add(size=2.0, location={pos})
obj_{i} = bpy.context.active_object
obj_{i}.scale = ({size/2}, {size/2}, {size/2})
obj_{i}.data.materials.clear()
face_keys_{i} = list(rubik_faces_{i}.keys())
for key in face_keys_{i}:
    col = rubik_faces_{i}[key]
    mat = bpy.data.materials.new(name=f'RubikFace_{i}_' + key)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        if 'Base Color' in bsdf.inputs:
            bsdf.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0)
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = 0.35
        if 'Specular' in bsdf.inputs:
            bsdf.inputs['Specular'].default_value = 0.25
    obj_{i}.data.materials.append(mat)

for poly in obj_{i}.data.polygons:
    n = poly.normal
    axis_key = '+X' if n.x >= 0 else '-X'
    axis_val = abs(n.x)
    if abs(n.y) > axis_val:
        axis_val = abs(n.y)
        axis_key = '+Y' if n.y >= 0 else '-Y'
    if abs(n.z) > axis_val:
        axis_key = '+Z' if n.z >= 0 else '-Z'
    try:
        poly.material_index = face_keys_{i}.index(axis_key)
    except ValueError:
        poly.material_index = 0
"""
            if obj_type != "rubik":
                script += f"""mat_{i} = bpy.data.materials.new(name='Material_{i}')
mat_{i}.use_nodes = True
bsdf_{i} = mat_{i}.node_tree.nodes.get('Principled BSDF')
if bsdf_{i}:
    if 'Base Color' in bsdf_{i}.inputs:
        bsdf_{i}.inputs['Base Color'].default_value = {color + (1.0,)}
    if 'Metallic' in bsdf_{i}.inputs:
        bsdf_{i}.inputs['Metallic'].default_value = 0.0
    if 'Roughness' in bsdf_{i}.inputs:
        bsdf_{i}.inputs['Roughness'].default_value = 0.5
obj_{i}.data.materials.append(mat_{i})

"""

        script += f"""output_path = r'{str(output_path.absolute())}'
bpy.context.scene.render.filepath = output_path
bpy.ops.render.render(write_still=True)
"""
        return script

    def _run_blender_script(self, script: str):
        """Execute a generated Blender Python script."""
        script_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        script_file.write(script)
        script_file.close()
        script_path = Path(script_file.name)

        try:
            result = subprocess.run(
                [str(self.blender_exec), "--background", "--python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "Blender rendering failed:\n"
                    f"STDOUT: {result.stdout}\n"
                    f"STDERR: {result.stderr}"
                )
        finally:
            if script_path.exists():
                script_path.unlink()

        return result.stdout, result.stderr, result.returncode

    def render_animation(
        self,
        objects: List[Dict],
        initial_azimuth: float,
        initial_elevation: float,
        target_azimuth: float,
        target_elevation: float,
        camera_distance: float,
        num_frames: int,
        output_dir: Path,
    ) -> List[Path]:
        """Render a sequence of frames for camera motion."""
        frames: List[Path] = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i in range(num_frames):
            progress = i / (num_frames - 1) if num_frames > 1 else 1.0
            eased_progress = progress * progress * (3.0 - 2.0 * progress)

            azimuth = initial_azimuth + (target_azimuth - initial_azimuth) * eased_progress
            elevation = initial_elevation + (
                target_elevation - initial_elevation
            ) * eased_progress

            frame_path = output_dir / f"frame_{i:04d}.png"
            self.render_scene(
                objects, azimuth, elevation, camera_distance, frame_path
            )
            frames.append(frame_path)

        return frames
