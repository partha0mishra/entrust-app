"""
Find LM Studio models on your system
"""

import os
from pathlib import Path
import platform


def find_lm_studio_models():
    """Locate LM Studio models directory based on OS"""
    system = platform.system()

    # Possible LM Studio model locations
    possible_paths = []

    if system == "Darwin":  # macOS
        possible_paths = [
            Path.home() / "Library/Application Support/LM Studio/models",
            Path.home() / ".cache/lm-studio/models",
        ]
    elif system == "Windows":
        possible_paths = [
            Path(os.environ.get("USERPROFILE", "")) / ".cache/lm-studio/models",
            Path(os.environ.get("LOCALAPPDATA", "")) / "LM Studio/models",
        ]
    else:  # Linux
        possible_paths = [
            Path.home() / ".cache/lm-studio/models",
            Path.home() / ".local/share/LM Studio/models",
        ]

    print("="*80)
    print("SEARCHING FOR LM STUDIO MODELS")
    print("="*80)
    print(f"Operating System: {system}")
    print()

    found_models = []

    for path in possible_paths:
        if path.exists():
            print(f"✓ Found LM Studio directory: {path}")
            print()

            # List all models
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        # Check if it looks like a model directory
                        has_config = (item / "config.json").exists()
                        has_tokenizer = any([
                            (item / "tokenizer.json").exists(),
                            (item / "tokenizer_config.json").exists(),
                            (item / "tokenizer.model").exists(),
                        ])
                        has_model = any([
                            (item / "pytorch_model.bin").exists(),
                            list(item.glob("*.safetensors")),
                            list(item.glob("*.gguf")),
                        ])

                        if has_config or has_tokenizer or has_model:
                            found_models.append(item)
                            print(f"  Model: {item.name}")
                            print(f"    Path: {item}")
                            print(f"    Config: {'✓' if has_config else '✗'}")
                            print(f"    Tokenizer: {'✓' if has_tokenizer else '✗'}")
                            print(f"    Model files: {'✓' if has_model else '✗'}")
                            print()
            except PermissionError:
                print(f"  ⚠ Permission denied accessing directory")
        else:
            print(f"✗ Not found: {path}")

    print("="*80)
    print("SUMMARY")
    print("="*80)

    if found_models:
        print(f"Found {len(found_models)} model(s)")
        print()
        print("To use one of these models, update configs/training_config.py:")
        print()
        for i, model in enumerate(found_models[:5], 1):  # Show first 5
            print(f'{i}. MODEL_NAME = "{model}"')
        print()
    else:
        print("No LM Studio models found.")
        print()
        print("Options:")
        print("  1. Download a model in LM Studio first")
        print("  2. Use a HuggingFace model (requires authentication for gated models)")
        print("  3. Download a model manually to a local directory")
        print()
        print("Popular open-source models for training:")
        print('  - MODEL_NAME = "meta-llama/Llama-2-7b-hf"')
        print('  - MODEL_NAME = "mistralai/Mistral-7B-v0.1"')
        print('  - MODEL_NAME = "microsoft/phi-2"')
        print('  - MODEL_NAME = "tiiuae/falcon-7b"')
        print()
        print("For gated models (like Llama), you'll need:")
        print("  1. Request access on HuggingFace")
        print("  2. Login: huggingface-cli login")
        print()

    return found_models


def check_huggingface_auth():
    """Check if user is authenticated with HuggingFace"""
    from huggingface_hub import HfFolder

    token = HfFolder.get_token()
    if token:
        print("✓ HuggingFace authentication: Logged in")
        return True
    else:
        print("✗ HuggingFace authentication: Not logged in")
        print()
        print("To login to HuggingFace:")
        print("  huggingface-cli login")
        print()
        print("This is required for gated models like Llama-2")
        return False


if __name__ == "__main__":
    found_models = find_lm_studio_models()

    print()
    print("="*80)
    print("HUGGINGFACE AUTHENTICATION")
    print("="*80)
    check_huggingface_auth()

    print()
    print("="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Choose a model from above or download one")
    print("2. Update MODEL_NAME in configs/training_config.py")
    print("3. Run: python3 scripts/prepare_training_data.py")
    print("="*80)
