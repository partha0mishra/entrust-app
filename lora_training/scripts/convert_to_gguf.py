"""
Convert LoRA adapters to GGUF format for use with LM Studio
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import argparse

# Add configs to path
sys.path.append(str(Path(__file__).parent.parent))
from configs.training_config import DIMENSIONS, MODEL_NAME


def merge_lora_with_base(
    base_model_path: str,
    lora_adapter_path: str,
    output_path: str
):
    """
    Merge LoRA adapter with base model

    Args:
        base_model_path: Path to base model
        lora_adapter_path: Path to LoRA adapter
        output_path: Output path for merged model
    """
    print(f"\nMerging LoRA adapter with base model...")
    print(f"  Base model: {base_model_path}")
    print(f"  LoRA adapter: {lora_adapter_path}")
    print(f"  Output: {output_path}")

    try:
        from peft import PeftModel, PeftConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        # Try with device_map="auto" first
        try:
            # Load base model
            print("\n  Loading base model...")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                offload_folder=None,  # Prevent disk offloading that causes meta device issues
                offload_state_dict=False  # Keep state dict in memory
            )

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(base_model_path)

            # Load LoRA adapter
            print("  Loading LoRA adapter...")
            model = PeftModel.from_pretrained(base_model, lora_adapter_path)

        except (KeyError, RuntimeError) as e:
            # If we get a KeyError or RuntimeError (offloading issue), retry without device_map
            print(f"\n  ⚠ Offloading issue detected ({type(e).__name__}), retrying without device_map...")

            # Clean up
            if 'base_model' in locals():
                del base_model
            if 'model' in locals():
                del model
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()

            # Load base model without device_map - load everything to CPU/MPS
            print("  Loading base model (without device_map)...")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                torch_dtype=torch.float16,
                device_map=None,  # Explicitly disable device_map
                low_cpu_mem_usage=False  # Load all at once to avoid meta tensors
            )

            tokenizer = AutoTokenizer.from_pretrained(base_model_path)

            # Load LoRA adapter
            print("  Loading LoRA adapter...")
            model = PeftModel.from_pretrained(base_model, lora_adapter_path)

        # Merge adapter into base model
        print("  Merging adapter...")
        model = model.merge_and_unload()

        # Save merged model
        print("  Saving merged model...")
        os.makedirs(output_path, exist_ok=True)
        model.save_pretrained(output_path)
        tokenizer.save_pretrained(output_path)

        print(f"✓ Merged model saved to: {output_path}")
        return True

    except Exception as e:
        print(f"✗ Error merging model: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "Q4_K_M"
):
    """
    Convert model to GGUF format

    Args:
        model_path: Path to HuggingFace model
        output_path: Output path for GGUF file
        quantization: Quantization type (Q4_K_M, Q5_K_M, Q8_0, etc.)
    """
    print(f"\nConverting to GGUF format...")
    print(f"  Input model: {model_path}")
    print(f"  Output: {output_path}")
    print(f"  Quantization: {quantization}")

    # Check if llama.cpp is available
    llama_cpp_path = os.path.expanduser("~/llama.cpp")
    if not os.path.exists(llama_cpp_path):
        print(f"\n⚠ llama.cpp not found at {llama_cpp_path}")
        print("  Please clone and build llama.cpp:")
        print("    git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp")
        print("    cd ~/llama.cpp && make")
        return False

    convert_script = Path(llama_cpp_path) / "convert_hf_to_gguf.py"
    quantize_bin = Path(llama_cpp_path) / "llama-quantize"

    if not convert_script.exists():
        print(f"✗ Conversion script not found: {convert_script}")
        return False

    try:
        # Step 1: Convert to GGUF F16
        print("\n  Step 1: Converting to GGUF (F16)...")
        f16_output = f"{output_path}.f16.gguf"

        result = subprocess.run(
            [
                sys.executable,
                str(convert_script),
                model_path,
                "--outfile", f16_output,
                "--outtype", "f16"
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print("  ✓ F16 GGUF created")

        # Step 2: Quantize
        if quantization != "f16":
            print(f"\n  Step 2: Quantizing to {quantization}...")
            quantized_output = f"{output_path}.{quantization}.gguf"

            if not quantize_bin.exists():
                print(f"  ⚠ Quantize binary not found: {quantize_bin}")
                print(f"  Using F16 version: {f16_output}")
                return True

            result = subprocess.run(
                [
                    str(quantize_bin),
                    f16_output,
                    quantized_output,
                    quantization
                ],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"  ✓ Quantized GGUF created: {quantized_output}")

            # Remove F16 version to save space
            if os.path.exists(f16_output):
                os.remove(f16_output)
                print("  ✓ Removed intermediate F16 file")

        print(f"\n✓ GGUF conversion complete!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Conversion failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_dimension_adapter(
    dimension: str,
    base_model: str = MODEL_NAME,
    quantization: str = "Q4_K_M",
    keep_merged: bool = False
):
    """
    Convert a dimension's LoRA adapter to GGUF

    Args:
        dimension: Dimension key (e.g., 'privacy_compliance')
        base_model: Base model name or path
        quantization: GGUF quantization type
        keep_merged: Keep merged HF model (requires more disk space)
    """
    print("="*80)
    print(f"CONVERTING {DIMENSIONS.get(dimension, dimension).upper()} TO GGUF")
    print("="*80)

    # Paths
    adapters_dir = Path(__file__).parent.parent / "adapters"
    models_dir = Path(__file__).parent.parent / "models"

    lora_path = adapters_dir / dimension / "final"
    merged_path = models_dir / f"{dimension}_merged"
    gguf_path = models_dir / f"{dimension}_model"

    # Check if LoRA adapter exists
    if not lora_path.exists():
        print(f"✗ LoRA adapter not found: {lora_path}")
        print("  Train the adapter first using train_lora_{dimension}.py")
        return False

    # Step 1: Merge LoRA with base model
    print("\n" + "="*80)
    print("STEP 1: MERGING LORA WITH BASE MODEL")
    print("="*80)

    if not merge_lora_with_base(base_model, str(lora_path), str(merged_path)):
        return False

    # Step 2: Convert to GGUF
    print("\n" + "="*80)
    print("STEP 2: CONVERTING TO GGUF")
    print("="*80)

    os.makedirs(models_dir, exist_ok=True)

    if not convert_to_gguf(str(merged_path), str(gguf_path), quantization):
        return False

    # Clean up merged model if requested
    if not keep_merged and merged_path.exists():
        print(f"\nCleaning up merged model: {merged_path}")
        shutil.rmtree(merged_path)
        print("✓ Merged model removed")

    print("\n" + "="*80)
    print("CONVERSION COMPLETE")
    print("="*80)
    print(f"GGUF model location: {models_dir}")
    print(f"\nYou can now load this model in LM Studio!")
    print("="*80)

    return True


def convert_all_dimensions(
    base_model: str = MODEL_NAME,
    quantization: str = "Q4_K_M",
    keep_merged: bool = False
):
    """Convert all dimension adapters to GGUF"""
    print("="*80)
    print("CONVERTING ALL DIMENSION ADAPTERS TO GGUF")
    print("="*80)

    successful = []
    failed = []

    for dim_key, dim_name in DIMENSIONS.items():
        print(f"\n\nProcessing: {dim_name}")

        if convert_dimension_adapter(dim_key, base_model, quantization, keep_merged):
            successful.append(dim_key)
        else:
            failed.append(dim_key)

    # Summary
    print("\n" + "="*80)
    print("CONVERSION SUMMARY")
    print("="*80)
    print(f"Successful: {len(successful)}/{len(DIMENSIONS)}")
    for dim in successful:
        print(f"  ✓ {DIMENSIONS[dim]}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for dim in failed:
            print(f"  ✗ {DIMENSIONS[dim]}")

    return len(failed) == 0


def main():
    parser = argparse.ArgumentParser(description="Convert LoRA adapters to GGUF format")
    parser.add_argument(
        "--dimension",
        type=str,
        help="Specific dimension to convert (leave empty for all)"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default=MODEL_NAME,
        help=f"Base model path (default: {MODEL_NAME})"
    )
    parser.add_argument(
        "--quantization",
        type=str,
        default="Q4_K_M",
        choices=["Q4_0", "Q4_K_M", "Q5_0", "Q5_K_M", "Q8_0", "f16"],
        help="GGUF quantization type (default: Q4_K_M)"
    )
    parser.add_argument(
        "--keep-merged",
        action="store_true",
        help="Keep merged HuggingFace model (requires more disk space)"
    )

    args = parser.parse_args()

    if args.dimension:
        # Convert specific dimension
        if args.dimension not in DIMENSIONS:
            print(f"Error: Unknown dimension '{args.dimension}'")
            print(f"Valid dimensions: {', '.join(DIMENSIONS.keys())}")
            sys.exit(1)

        success = convert_dimension_adapter(
            args.dimension,
            args.base_model,
            args.quantization,
            args.keep_merged
        )
    else:
        # Convert all dimensions
        success = convert_all_dimensions(
            args.base_model,
            args.quantization,
            args.keep_merged
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
