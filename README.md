# Template Data Generator 🎲

A minimal template for creating synthetic reasoning task generators. Fork this and customize it for your own task (maze, sudoku, rotation, etc.).

---

## Ground Truth Video Philosophy

> There may be many videos that could score 100% on EVAL — but our ground truth video **must** score 100%.

The ground truth video is the canonical reference answer. It is not merely *a* correct solution; it is *the* definitive solution that the evaluation system is measured against. If the ground truth itself does not achieve a perfect score on EVAL, then either the ground truth or the evaluation is broken — and that must be fixed before anything else.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/your-task-generator.git
cd your-task-generator

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
template-data-generator/
├── core/                    # ✅ KEEP: Standard utilities
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # ⚠️ CUSTOMIZE: Your task logic
│   ├── generator.py        # Your task generator
│   ├── prompts.py          # Your prompt templates
│   └── config.py           # Your configuration
├── examples/
│   └── generate.py         # Entry point
├── eval/                    # 🧪 STANDALONE: Evaluation
│   ├── verify.py           # Automated evaluation script
│   └── EVAL.md             # Evaluation guide & instructions
└── data/questions/         # Generated output
```

---

## 📦 Output Format

Every generator produces:

```
data/questions/{domain}_task/{task_id}/
├── first_frame.png          # Initial state (REQUIRED) — first frame of first_video
├── final_frame.png          # Goal state (optional) — last frame of last_video
├── prompt.txt               # Instructions (REQUIRED)
├── first_video.mp4          # Opening segment video (optional)
├── last_video.mp4           # Closing segment video (optional)
└── ground_truth.mp4         # Full video, beginning to end (optional)
```

---

## 🎨 Customization (3 Files to Modify)

### 1. Update `src/generator.py`

Replace the example chess generator with your task:

```python
from core import BaseGenerator, TaskPair, ImageRenderer

class MazeGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        self.renderer = ImageRenderer(config.image_size)
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        # 1. Generate your problem
        maze = self.create_maze()
        
        # 2. Solve it
        solution = self.solve_maze(maze)
        
        # 3. Render images
        first_image = self.render_maze(maze)
        final_image = self.render_maze_with_solution(maze, solution)
        
        # 4. Create TaskPair
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=self.select_prompt(),
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=None  # Optional
        )
```

### 2. Update `src/prompts.py`

Replace chess prompts with yours:

```python
PROMPTS = {
    "default": [
        "Animate a path from start to goal through the maze.",
        "Show the solution route navigating through corridors.",
    ]
}

def get_prompt(task_type: str = "default") -> str:
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)
```

### 3. Update `src/config.py`

**All hyperparameters go here** - both general and task-specific:

```python
from core import GenerationConfig
from pydantic import Field

class TaskConfig(GenerationConfig):
    """Your task-specific configuration."""
    # Inherits: num_samples, domain, seed, output_dir, image_size
    
    # Override defaults
    domain: str = Field(default="maze")
    image_size: tuple[int, int] = Field(default=(512, 512))
    
    # Task-specific hyperparameters
    grid_size: int = Field(default=10, description="Maze grid size")
    wall_thickness: int = Field(default=2, description="Wall thickness")
    difficulty: str = Field(default="medium", description="easy/medium/hard")
```

**Single entry point:** `python examples/generate.py --num-samples 50`

---

## 🧪 Eval Module

The `eval/` directory is standalone — it does not depend on `core/` or `src/`. It should contain everything needed to evaluate the task outputs. This could be:

- **Rule-based evaluation** — automated scoring scripts (see `eval/verify.py`)
- **Human evaluation** — rubrics, guidelines, comparison templates
- **VLM-as-judge** — prompts and scripts for using vision-language models as evaluators
- **Any combination** — whatever fits your task

See `eval/EVAL.md` for the full evaluation guide.
