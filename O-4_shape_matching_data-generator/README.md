# O-4 Shape Matching Data Generator 🔷

A data generator for creating synthetic "Shape Matching" reasoning tasks. This generator creates datasets where colored shapes must be moved into their corresponding dark outlines.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/vm-dataset/O-4_shape_matching_data-generator.git
cd O-4_shape_matching_data-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate tasks
python examples/generate.py --num-samples 50
```

---

## 📁 Structure

```
O-4_shape_matching_data-generator/
├── core/                    # Standard utilities
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # Shape matching task logic
│   ├── generator.py        # Shape matching generator
│   ├── prompts.py          # Task prompt templates
│   └── config.py           # Task configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
```

---

## 📦 Output Format

This generator produces:

```
data/questions/shape_matching_task/{task_id}/
├── first_frame.png          # Initial state with shapes scattered (REQUIRED)
├── final_frame.png          # Final state with shapes matching outlines (REQUIRED)
├── prompt.txt               # Instructions (REQUIRED)
└── ground_truth.mp4         # Solution video (OPTIONAL)
```

---

## 🎯 Task Description

This generator creates **shape matching tasks** with the following characteristics:

1. **Initial Frame**: A scene containing:
   - Colored shapes scattered on the left side (circle, square, triangle, star)
   - Dark outline targets on the right side (matching the shapes)
   - White background with a dividing line

2. **Animation Process**: Each colored shape moves from its starting position to its matching outline

3. **Final Frame**: All colored shapes are aligned with their corresponding outlines

4. **Task Requirements**:
   - Move each colorful shape into its corresponding dark outline
   - Shapes must match their target outlines exactly

### Task Specifications

- **Domain**: `shape_matching`
- **Image size**: 800×400 pixels
- **Background**: Pure white with a dividing line
- **FPS**: 30 frames per second
- **Shapes**: circle / square / triangle / star (up to 4 shapes)
- **Animation**: hold 1s at start → linear move 2s → hold 1s at end
- **Target outlines**: Always visible on the right side

### Prompt Format

The prompt provides clear instructions for the task:

```
Move each colorful shape into its corresponding dark outline.
```

---

## 🎨 Customization

### Basic Usage

```bash
# Generate 100 samples
python examples/generate.py --num-samples 100

# Custom output directory
python examples/generate.py --num-samples 50 --output data/my_shapes

# Set random seed for reproducibility
python examples/generate.py --num-samples 50 --seed 42

# Disable video generation
python examples/generate.py --num-samples 50 --no-videos
```

### Configuration

Modify [src/config.py](src/config.py) to customize:

- `domain`: Task domain name (default: `shape_matching`)
- `image_size`: Image dimensions (default: `(800, 400)`)
- `num_shapes`: Number of shapes in task (default: `4`, max: `4`)
- `shape_size`: Size of shapes in pixels (default: `35`)
- `video_fps`: Video frame rate (default: `30`)

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
