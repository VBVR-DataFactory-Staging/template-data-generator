#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      PATH PLANNING TASK GENERATION                            ║
║                                                                               ║
║  Generate obstacle avoidance path planning task dataset.                      ║
║  Task: Find path from start to goal avoiding obstacles.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python examples/generate_path_planning.py --num-samples 10
    python examples/generate_path_planning.py --num-samples 100 --output data/path --seed 42
    python examples/generate_path_planning.py --num-samples 50 --grid-width 20 --grid-height 15
"""

import argparse
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import OutputWriter
from src import PathPlanningGenerator, PathPlanningConfig


def main():
    parser = argparse.ArgumentParser(
        description="Generate path planning task dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python examples/generate_path_planning.py --num-samples 10
    python examples/generate_path_planning.py --num-samples 100 --output data/path --seed 42
    python examples/generate_path_planning.py --num-samples 50 --grid-width 20 --grid-height 15
        """
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        required=True,
        help="Number of task samples to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/questions",
        help="Output directory (default: data/questions)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--no-videos",
        action="store_true",
        help="Disable video generation"
    )
    parser.add_argument(
        "--grid-width",
        type=int,
        default=15,
        help="Grid width in cells (default: 15)"
    )
    parser.add_argument(
        "--grid-height",
        type=int,
        default=10,
        help="Grid height in cells (default: 10)"
    )
    parser.add_argument(
        "--cell-size",
        type=int,
        default=40,
        help="Cell size in pixels (default: 40)"
    )
    parser.add_argument(
        "--obstacle-density",
        type=float,
        default=0.25,
        help="Obstacle density 0.0-1.0 (default: 0.25)"
    )
    
    args = parser.parse_args()
    
    print(f"🎲 Generating {args.num_samples} path planning tasks...")
    print(f"   Grid: {args.grid_width}x{args.grid_height}, Obstacle density: {args.obstacle_density}")
    
    # Configure task
    config = PathPlanningConfig(
        num_samples=args.num_samples,
        random_seed=args.seed,
        output_dir=Path(args.output),
        generate_videos=not args.no_videos,
        grid_width=args.grid_width,
        grid_height=args.grid_height,
        cell_size=args.cell_size,
        obstacle_density=args.obstacle_density,
    )
    
    # Generate tasks
    generator = PathPlanningGenerator(config)
    tasks = generator.generate_dataset()
    
    # Write to disk
    writer = OutputWriter(Path(args.output))
    writer.write_dataset(tasks)
    
    print(f"✅ Done! Generated {len(tasks)} tasks in {args.output}/{config.domain}_task/")


if __name__ == "__main__":
    main()
