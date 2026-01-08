#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       SIZE SORTING TASK GENERATION                            ║
║                                                                               ║
║  Generate bar height sorting task dataset.                                    ║
║  Task: Sort scattered bars from shortest to tallest.                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python examples/generate_size_sorting.py --num-samples 10
    python examples/generate_size_sorting.py --num-samples 100 --output data/size_sorting --seed 42
    python examples/generate_size_sorting.py --num-samples 50 --num-bars 10 --sort-order descending
"""

import argparse
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import OutputWriter
from src import SizeSortingGenerator, SizeSortingConfig


def main():
    parser = argparse.ArgumentParser(
        description="Generate size sorting task dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python examples/generate_size_sorting.py --num-samples 10
    python examples/generate_size_sorting.py --num-samples 100 --output data/size_sorting --seed 42
    python examples/generate_size_sorting.py --num-samples 50 --num-bars 10 --sort-order descending
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
        "--num-bars",
        type=int,
        default=7,
        help="Number of bars to sort (default: 7)"
    )
    parser.add_argument(
        "--bar-width",
        type=int,
        default=40,
        help="Width of each bar in pixels (default: 40)"
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=50,
        help="Minimum bar height (default: 50)"
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=250,
        help="Maximum bar height (default: 250)"
    )
    parser.add_argument(
        "--sort-order",
        type=str,
        choices=["ascending", "descending"],
        default="ascending",
        help="Sort order: ascending or descending (default: ascending)"
    )
    
    args = parser.parse_args()
    
    print(f"🎲 Generating {args.num_samples} size sorting tasks...")
    print(f"   Bars: {args.num_bars}, Order: {args.sort_order}")
    
    # Configure task
    config = SizeSortingConfig(
        num_samples=args.num_samples,
        random_seed=args.seed,
        output_dir=Path(args.output),
        generate_videos=not args.no_videos,
        num_bars=args.num_bars,
        bar_width=args.bar_width,
        min_height=args.min_height,
        max_height=args.max_height,
        sort_order=args.sort_order,
    )
    
    # Generate tasks
    generator = SizeSortingGenerator(config)
    tasks = generator.generate_dataset()
    
    # Write to disk
    writer = OutputWriter(Path(args.output))
    writer.write_dataset(tasks)
    
    print(f"✅ Done! Generated {len(tasks)} tasks in {args.output}/{config.domain}_task/")


if __name__ == "__main__":
    main()
