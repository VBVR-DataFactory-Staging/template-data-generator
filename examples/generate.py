#!/usr/bin/env python3
"""Multi-view Camera Positioning Data Generator Entry Point."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import OutputWriter
from src import TaskGenerator, TaskConfig


def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-view camera positioning tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
    python examples/generate.py --num-samples 50
    python examples/generate.py --num-samples 100 --output data/my_output --seed 42
    python examples/generate.py --num-samples 50 --no-videos
        """,
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        required=True,
        help="Number of task samples to generate",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/questions",
        help="Output directory (default: data/questions)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--no-videos",
        action="store_true",
        help="Disable video generation (faster)",
    )
    parser.add_argument(
        "--blender-executable",
        type=str,
        default=None,
        help="Path to Blender executable (auto-detect if not specified)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f"Generating {args.num_samples} multi-view tasks...")
    print("=" * 60)

    config = TaskConfig(
        num_samples=args.num_samples,
        random_seed=args.seed,
        output_dir=Path(args.output),
        generate_videos=not args.no_videos,
        blender_executable=Path(args.blender_executable) if args.blender_executable else None,
    )

    try:
        generator = TaskGenerator(config)
        tasks = generator.generate_dataset()

        writer = OutputWriter(Path(args.output))
        writer.write_dataset(tasks)

        print()
        print("=" * 60)
        print(f"Done! Generated {len(tasks)} tasks")
        print(f"Output: {args.output}/{config.domain}_task/")
        print("=" * 60)
    except Exception as exc:
        print()
        print("=" * 60)
        print(f"Generation failed: {exc}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
