# Multi-view Camera Positioning Data Generator

A data generator for multi-view camera positioning reasoning tasks using Blender 5.0.

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repo-url>
cd multi-view-data-generator
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 4. Install Blender 5.0 (Linux)
Run the automatic installation script:
```bash
python scripts/install_blender.py
```
This will download Blender 5.0.0 (Linux x86_64) to `blender/` in the project root.

> The installation script only supports Linux. For other platforms, please install Blender manually:
> - macOS: `brew install --cask blender`
> - Windows: Download from https://www.blender.org/download/

### 5. Verify Installation
```bash
# Test Blender
./blender/blender-5.0.0-linux-x64/blender --version
# Or if Blender is in PATH
blender --version
```

### 6. Generate Data
```bash
# Generate 50 samples
python examples/generate.py --num-samples 50

# Generate with custom output directory
python examples/generate.py --num-samples 100 --output data/my_output

# Generate with seed (reproducible)
python examples/generate.py --num-samples 50 --seed 42

# Generate without videos (faster)
python examples/generate.py --num-samples 50 --no-videos

# Specify Blender executable path
python examples/generate.py --num-samples 50 --blender-executable ./blender/blender-5.0.0-linux-x64/blender
```

---

## 📁 Project Structure

```
multi-view-data-generator/
├── blender/                         # Blender installation (auto-installed)
│   └── blender-5.0.0-linux-x64/
│       └── blender                  # Blender executable
├── core/                            # Framework utilities
│   ├── base_generator.py
│   ├── schemas.py
│   ├── output_writer.py
│   ├── image_utils.py
│   └── video_utils.py
├── src/                             # Multi-view implementation
│   ├── __init__.py
│   ├── generator.py                 # Task generator
│   ├── config.py                    # Configuration
│   ├── prompts.py                   # Prompt templates
│   └── renderer/
│       ├── __init__.py
│       └── blender_renderer.py      # Blender renderer
├── examples/
│   └── generate.py                  # Entry point
├── scripts/
│   └── install_blender.py           # Blender installer (Linux)
├── data/questions/                  # Generated output
│   └── multi_view_camera_task/
│       └── multi_view_camera_XXXX/
│           ├── first_frame.png
│           ├── final_frame.png
│           ├── prompt.txt
│           └── ground_truth.mp4
├── requirements.txt
├── setup.py
└── README.md
```

---

## 📦 Dependencies

### Python Packages
- pillow>=10.0.0 — Image processing
- numpy>=1.24.0 — Numerical computation
- opencv-python>=4.8.0 — Video generation
- pydantic>=2.0.0 — Configuration validation

Install via:
```bash
pip install -r requirements.txt
```

### External Tools
- Blender 5.0.0 (Linux x86_64) — Auto-installed via `scripts/install_blender.py`
- Or install manually: https://www.blender.org/download/

---

## 🎨 Task Format

Each task contains:
- `first_frame.png`: Initial camera view (with target view indicator)
- `final_frame.png`: Target camera view
- `prompt.txt`: Task instruction (e.g., “Move camera from front to top-down view”)
- `ground_truth.mp4`: Camera motion animation (optional)

### Example Task
- Scene: 1–3 objects (Rubik's cube always included with fixed per-face colors; additional cube, sphere, cylinder, pyramid)
- Initial View: One of 9 preset views (front, left, right, back, diagonals, top-down)
- Target View: Different preset view
- Task: Predict/Generate the scene from target view

---

## ⚙️ Configuration

Configure generation parameters in `src/config.py`:

## 🎲 Domain Randomization (key knobs)

- 视角采样：`initial_fixed_view`（默认 top_down，可设为 None 随机）、`target_view_strategy`（random/opposite/adjacent）、`view_transition_difficulty`（easy/hard 会影响目标选择）、`view_definitions`（修改 az/el 列表）。
- 物体随机：`num_objects_range` 控制数量；Rubik 始终存在；辅助物体来自 `object_types`，尺寸范围 `primary_size_range` / `aux_size_range`；颜色 `object_colors`；位置在 `object_position_range` 内采样，并用 `min_object_spacing`+`safety_margin` 规避重叠。
- 相机与运动：`camera_fov_deg`、自适应距离（基于物体分布/FOV 计算），路径插值（top_down 沿经线下落，其他视角球面 slerp），`background_color`/光源可调亮度。
- 视频节奏：`initial_hold_frames` / `transition_frames` / `final_hold_frames` / `top_down_extra_frames` 控制停留与过渡时长。
- 复现性：`random_seed` 或 task_id 派生的种子确保同 task_id 可复现；`num_samples` 控制一次生成数量。输出目录/命名会跳过已有最大编号，避免覆盖。

```python
class TaskConfig(GenerationConfig):
    domain: str = "multi_view_camera"

    # Always start from a fixed view (default: top_down). Set to None for random.
    initial_fixed_view: str | None = "top_down"

    # View options (9 preset views)
    available_views: list[str] = ["front", "left", "right", "back", ...]

    # Object options
    num_objects_range: tuple[int, int] = (1, 3)  # 1-3 objects
    object_types: list[str] = ["cube", "sphere", "cylinder", "pyramid"]

    # Position strategy: single object at origin, multiple objects distributed
    single_object_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    object_position_range: tuple[float, float] = (-2.0, 2.0)

    # Blender settings
    blender_version: str = "5.0.0"
    camera_distance: float = 5.0
    render_engine: str = "EEVEE"  # Fast rendering (EEVEE) or "CYCLES"; Blender 5 uses "BLENDER_EEVEE" internally
    render_resolution: tuple[int, int] = (512, 512)
```

---

## 🎯 View Definitions

| View         | Azimuth | Elevation | Description             |
|--------------|---------|-----------|-------------------------|
| front        | 0°      | 0°        | Front view              |
| left         | -90°    | 0°        | Left side view          |
| right        | 90°     | 0°        | Right side view         |
| back         | 180°    | 0°        | Back view               |
| front_left   | -45°    | 30°       | Front-left diagonal     |
| front_right  | 45°     | 30°       | Front-right diagonal    |
| back_left    | -135°   | 30°       | Back-left diagonal      |
| back_right   | 135°    | 30°       | Back-right diagonal     |
| top_down     | 0°      | 90°       | Top-down view           |

---

## 📊 Data Generation Strategy

- View combinations: 9 × 8 = 72 possible view pairs  
- Object count: 1–3 objects per scene  
- Object types: 4 types × 6 colors = 24 combinations  
- Object positions: Single object at origin; multiple objects distributed randomly  
- Object sizes: Random within range  
- Prompt variants: Multiple prompt templates per view type  
- Total parameter space: > 10K unique samples

---

## 🎬 Video Generation

Videos show smooth camera motion from initial to target view:
- Initial hold (20 frames): Scene at initial view
- transition_frames=40（top_down 起始会再加 top_down_extra_frames=20，即 60）: Smooth interpolation with ease-in-out easing
- Final hold (40 frames): Scene at target view

Total: 100 frames at 10 fps ≈ 10 seconds

---

## 🔧 Troubleshooting

### Blender Not Found
- Check installation: `ls -la blender/blender-5.0.0-linux-x64/blender`
- Reinstall Blender: `python scripts/install_blender.py`
- Manual install:
  - Download from https://www.blender.org/download/
  - Extract to `blender/`
  - Ensure executable: `chmod +x blender/blender-5.0.0-linux-x64/blender`

### Rendering Errors
- Check Blender version: `./blender/blender-5.0.0-linux-x64/blender --version`
- Test Blender manually: `./blender/blender-5.0.0-linux-x64/blender --background`
- Check render logs in error messages

### Slow Generation
- Use `--no-videos` to skip video generation
- Reduce `--num-samples` for testing
- Use EEVEE engine (faster than CYCLES)

---

## 📝 Notes

- Blender version: Requires Blender 5.0.0 (API compatible)
- Platform: Installation script supports Linux x86_64 only
- Rendering: Uses EEVEE engine by default (fast, suitable for simple scenes); white background (1,1,1)
- Camera: FOV 60° by default and auto distance computation (with safety margin) to keep all objects in view; camera moves on a sphere with great-circle interpolation.
- Objects: Rubik's cube is always present (fixed Rubik color scheme); single-object case keeps it at origin. Multiple objects: Rubik plus auxiliaries distributed randomly on the XY plane
- Spacing: Controlled via `min_object_spacing` (default 0.8) plus `safety_margin` (default 0.5); positions sampled in a wider region near origin (default [-2.5, 2.5]) with spacing-aware sampling to avoid overlap.
- Sizes: Rubik size range (0.9–1.1); auxiliary objects smaller (0.3–0.6) to reduce occlusion.
- Prompts: Include fixed Rubik description, a global statement that auxiliary objects stay upright and aligned to world axes, and an auxiliary summary with type, size, position, and color. With the default max of 3 objects (Rubik + 2 auxiliaries), the longest prompt is ~100–120 words, safely under 200.

---

## 📚 References

- Blender Documentation: https://docs.blender.org/
- Template Data Generator
