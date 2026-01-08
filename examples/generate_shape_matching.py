#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      SHAPE MATCHING TASK GENERATION                           ║
║                                                                               ║
║  Generate geometric shape matching task dataset.                              ║
║  Task: Move shapes into their matching outlines.                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python examples/generate_shape_matching.py --num-samples 10
    python examples/generate_shape_matching.py --num-samples 100 --output data/shapes --seed 42
    python examples/generate_shape_matching.py --num-samples 50 --num-shapes 3 --shape-size 40
"""

import argparse
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import OutputWriter
from src import ShapeMatchingGenerator, ShapeMatchingConfig


def main():
    parser = argparse.ArgumentParser(
        description="Generate shape matching task dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python examples/generate_shape_matching.py --num-samples 10
    python examples/generate_shape_matching.py --num-samples 100 --output data/shapes --seed 42
    python examples/generate_shape_matching.py --num-samples 50 --num-shapes 3 --shape-size 40
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
        "--num-shapes",
        type=int,
        default=4,
        help="Number of shapes (max 4: circle, square, triangle, star)"
    )
    parser.add_argument(
        "--shape-size",
        type=int,
        default=35,
        help="Size of shapes in pixels (default: 35)"
    )
    
    args = parser.parse_args()
    
    print(f"🎲 Generating {args.num_samples} shape matching tasks...")
    print(f"   Shapes: {args.num_shapes}, Size: {args.shape_size}px")
    
    # Configure task
    config = ShapeMatchingConfig(
        num_samples=args.num_samples,
        random_seed=args.seed,
        output_dir=Path(args.output),
        generate_videos=not args.no_videos,
        num_shapes=args.num_shapes,
        shape_size=args.shape_size,
    )
    
    # Generate tasks
    generator = ShapeMatchingGenerator(config)
    tasks = generator.generate_dataset()
    
    # Write to disk
    writer = OutputWriter(Path(args.output))
    writer.write_dataset(tasks)
    
    print(f"✅ Done! Generated {len(tasks)} tasks in {args.output}/{config.domain}_task/")


if __name__ == "__main__":
    main()
