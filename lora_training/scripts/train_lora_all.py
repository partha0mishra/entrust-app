"""
Master training script - trains LoRA adapters for all dimensions sequentially
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add configs to path
sys.path.append(str(Path(__file__).parent.parent))
from configs.training_config import DIMENSIONS


def train_all_dimensions():
    """Train LoRA adapters for all dimensions"""
    print("="*80)
    print("TRAINING ALL DIMENSION LORA ADAPTERS")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total dimensions: {len(DIMENSIONS)}")
    print()

    results = {}
    successful = []
    failed = []

    for i, (dim_key, dim_name) in enumerate(DIMENSIONS.items(), 1):
        print("\n" + "="*80)
        print(f"DIMENSION {i}/{len(DIMENSIONS)}: {dim_name}")
        print("="*80)

        script_name = f"train_lora_{dim_key}.py"
        script_path = Path(__file__).parent / script_name

        if not script_path.exists():
            print(f"✗ Script not found: {script_name}")
            print("  Run generate_dimension_scripts.py first")
            failed.append(dim_key)
            continue

        try:
            # Run training script
            start_time = datetime.now()
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                capture_output=False
            )

            duration = (datetime.now() - start_time).total_seconds() / 60

            print(f"\n✓ {dim_name} training completed in {duration:.1f} minutes")
            successful.append(dim_key)
            results[dim_key] = "success"

        except subprocess.CalledProcessError as e:
            print(f"\n✗ {dim_name} training failed")
            failed.append(dim_key)
            results[dim_key] = "failed"
        except KeyboardInterrupt:
            print(f"\n⚠ Training interrupted by user")
            results[dim_key] = "interrupted"
            break

    # Summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nSuccessful: {len(successful)}/{len(DIMENSIONS)}")
    if successful:
        for dim in successful:
            print(f"  ✓ {DIMENSIONS[dim]}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for dim in failed:
            print(f"  ✗ {DIMENSIONS[dim]}")

    print("\n" + "="*80)

    # Save summary
    summary_file = Path(__file__).parent.parent / "training_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Training Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        f.write(f"Successful: {len(successful)}/{len(DIMENSIONS)}\n")
        for dim in successful:
            f.write(f"  ✓ {DIMENSIONS[dim]}\n")
        if failed:
            f.write(f"\nFailed: {len(failed)}\n")
            for dim in failed:
                f.write(f"  ✗ {DIMENSIONS[dim]}\n")

    print(f"Summary saved to: {summary_file}")

    return len(failed) == 0


if __name__ == "__main__":
    success = train_all_dimensions()
    sys.exit(0 if success else 1)
