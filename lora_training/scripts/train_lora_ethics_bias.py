"""
Train LoRA adapter for Data Ethics & Bias
Auto-generated script
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

from train_lora_base import train_lora

if __name__ == "__main__":
    success = train_lora(
        dimension="ethics_bias",
        # model_name can be overridden here if needed
        # model_name="path/to/custom/model"
    )

    sys.exit(0 if success else 1)
