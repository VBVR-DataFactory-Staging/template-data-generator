#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           TASK GENERATION SCRIPT                              ║
║                                                                               ║
║  Run this to generate your dataset.                                           ║
║  Customize TaskConfig and TaskGenerator in src/ for your task.                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python examples/generate.py --num-samples 100
    python examples/generate.py --num-samples 100 --output data/my_task --seed 42
"""

import argparse
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import OutputWriter
from src import TaskGenerator, TaskConfig


def main():
    parser = argparse.ArgumentParser(
        description="Generate task dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python examples/generate.py --num-samples 10
    python examples/generate.py --num-samples 100 --output data/output --seed 42
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
        default="./data/questions",
        help="Output directory (default: ./data/questions)"
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
    
    args = parser.parse_args()
    
    print(f"🎲 Generating {args.num_samples} tasks...")
    
    # ──────────────────────────────────────────────────────────────────────────
    #  Configure your task here
    #  Add any additional TaskConfig parameters as needed
    # ──────────────────────────────────────────────────────────────────────────
    
    config = TaskConfig(
        num_samples=args.num_samples,
        random_seed=args.seed,
        output_dir=Path(args.output),
        generate_videos=not args.no_videos,
    )
    
    # Generate tasks
    generator = TaskGenerator(config)
    tasks = generator.generate_dataset()
    
    # Write to disk
    writer = OutputWriter(Path(args.output))
    writer.write_dataset(tasks)
    
    print(f"✅ Done! Generated {len(tasks)} tasks in {args.output}/{config.domain}_task/")


if __name__ == "__main__":
    main()
