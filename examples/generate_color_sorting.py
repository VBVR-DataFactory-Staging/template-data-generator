#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      COLOR SORTING TASK GENERATION                            ║
║                                                                               ║
║  Generate color-based bin sorting task dataset.                               ║
║  Task: Move colored blocks into matching color containers.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python examples/generate_color_sorting.py --num-samples 10
    python examples/generate_color_sorting.py --num-samples 100 --output data/color_sorting --seed 42
    python examples/generate_color_sorting.py --num-samples 50 --num-colors 3 --items-per-color 6
"""

import argparse
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import OutputWriter
from src import ColorSortingGenerator, ColorSortingConfig


def main():
    parser = argparse.ArgumentParser(
        description="Generate color sorting task dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python examples/generate_color_sorting.py --num-samples 10
    python examples/generate_color_sorting.py --num-samples 100 --output data/color_sorting --seed 42
    python examples/generate_color_sorting.py --num-samples 50 --num-colors 3 --items-per-color 6
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
        "--num-colors",
        type=int,
        default=2,
        help="Number of color categories (default: 2)"
    )
    parser.add_argument(
        "--items-per-color",
        type=int,
        default=4,
        help="Number of blocks per color (default: 4)"
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=25,
        help="Size of each block in pixels (default: 25)"
    )
    
    args = parser.parse_args()
    
    print(f"🎲 Generating {args.num_samples} color sorting tasks...")
    print(f"   Colors: {args.num_colors}, Items per color: {args.items_per_color}")
    
    # Configure task
    config = ColorSortingConfig(
        num_samples=args.num_samples,
        random_seed=args.seed,
        output_dir=Path(args.output),
        generate_videos=not args.no_videos,
        num_colors=args.num_colors,
        items_per_color=args.items_per_color,
        block_size=args.block_size,
    )
    
    # Generate tasks
    generator = ColorSortingGenerator(config)
    tasks = generator.generate_dataset()
    
    # Write to disk
    writer = OutputWriter(Path(args.output))
    writer.write_dataset(tasks)
    
    print(f"✅ Done! Generated {len(tasks)} tasks in {args.output}/{config.domain}_task/")


if __name__ == "__main__":
    main()
