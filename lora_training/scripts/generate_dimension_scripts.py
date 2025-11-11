"""
Generate dimension-specific training scripts
"""

import sys
from pathlib import Path

# Add configs to path
sys.path.append(str(Path(__file__).parent.parent))
from configs.training_config import DIMENSIONS


SCRIPT_TEMPLATE = '''"""
Train LoRA adapter for {dimension_name}
Auto-generated script
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

from train_lora_base import train_lora

if __name__ == "__main__":
    success = train_lora(
        dimension="{dimension_key}",
        # model_name can be overridden here if needed
        # model_name="path/to/custom/model"
    )

    sys.exit(0 if success else 1)
'''


def generate_scripts():
    """Generate train_lora_{dimension}.py scripts"""
    scripts_dir = Path(__file__).parent

    print("Generating dimension-specific training scripts...")
    print("="*60)

    for dim_key, dim_name in DIMENSIONS.items():
        script_name = f"train_lora_{dim_key}.py"
        script_path = scripts_dir / script_name

        script_content = SCRIPT_TEMPLATE.format(
            dimension_name=dim_name,
            dimension_key=dim_key
        )

        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make executable
        script_path.chmod(0o755)

        print(f"✓ Created: {script_name}")

    print("="*60)
    print(f"Generated {len(DIMENSIONS)} training scripts")
    print()


if __name__ == "__main__":
    generate_scripts()
