"""
Base LoRA training script with QLoRA (4-bit quantization)
This script can be used to train any dimension
"""

import os
import sys
import json
import torch
from pathlib import Path
from datetime import datetime
from typing import Optional

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import Dataset

# Add configs to path
sys.path.append(str(Path(__file__).parent.parent))
from configs.training_config import (
    MODEL_NAME,
    MODEL_MAX_LENGTH,
    LORA_CONFIG,
    BNB_CONFIG,
    TRAINING_ARGS,
    MODELS_OUTPUT_PATH
)


def format_instruction(example):
    """Format example as instruction-following prompt"""
    if example.get("input"):
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
    else:
        prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Response:
{example['output']}"""

    return {"text": prompt}


def load_and_prepare_data(data_path: str, tokenizer):
    """Load and tokenize training data"""
    print(f"\nLoading data from: {data_path}")

    # Load training data
    with open(f"{data_path}/train.json", 'r') as f:
        train_data = json.load(f)

    # Load validation data
    with open(f"{data_path}/val.json", 'r') as f:
        val_data = json.load(f)

    print(f"  Train examples: {len(train_data)}")
    print(f"  Val examples: {len(val_data)}")

    # Create datasets
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)

    # Format as instruction-following
    train_dataset = train_dataset.map(format_instruction)
    val_dataset = val_dataset.map(format_instruction)

    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=MODEL_MAX_LENGTH,
            padding="max_length"
        )

    print("\nTokenizing datasets...")
    train_dataset = train_dataset.map(tokenize_function, batched=True, remove_columns=train_dataset.column_names)
    val_dataset = val_dataset.map(tokenize_function, batched=True, remove_columns=val_dataset.column_names)

    return train_dataset, val_dataset


def setup_model_and_tokenizer(model_name: str):
    """Setup model and tokenizer (with optional quantization based on platform)"""
    import platform

    print(f"\nLoading model: {model_name}")
    print(f"Platform: {platform.system()}")

    # Detect if running on macOS (where bitsandbytes doesn't work)
    is_macos = platform.system() == "Darwin"

    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
        model_max_length=MODEL_MAX_LENGTH
    )

    # Set pad token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if is_macos:
        # macOS: Load model without quantization (use MPS)
        print("Loading model in FP16 (macOS/MPS mode - no quantization)...")
        print("Note: Training will use more memory but works on Apple Silicon")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        # Linux/Windows: Check if model is pre-quantized
        is_pre_quantized = "unsloth" in model_name.lower() and "bnb-4bit" in model_name.lower()

        if is_pre_quantized:
            # Load pre-quantized model directly
            print("Loading pre-quantized model (Unsloth)...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            # Configure and apply 4-bit quantization
            print("Loading model with 4-bit quantization...")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=BNB_CONFIG["load_in_4bit"],
                bnb_4bit_quant_type=BNB_CONFIG["bnb_4bit_quant_type"],
                bnb_4bit_compute_dtype=getattr(torch, BNB_CONFIG["bnb_4bit_compute_dtype"]),
                bnb_4bit_use_double_quant=BNB_CONFIG["bnb_4bit_use_double_quant"],
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )

    # Prepare model for training
    if not is_macos:
        # Only use k-bit training prep on platforms with quantization
        model = prepare_model_for_kbit_training(model)
    else:
        # Enable gradient checkpointing for memory efficiency on macOS
        model.gradient_checkpointing_enable()

    # Configure LoRA
    print("Configuring LoRA...")
    lora_config = LoraConfig(
        r=LORA_CONFIG["r"],
        lora_alpha=LORA_CONFIG["lora_alpha"],
        target_modules=LORA_CONFIG["target_modules"],
        lora_dropout=LORA_CONFIG["lora_dropout"],
        bias=LORA_CONFIG["bias"],
        task_type=TaskType.CAUSAL_LM
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    model.print_trainable_parameters()

    return model, tokenizer


def train_lora(
    dimension: str,
    model_name: str = MODEL_NAME,
    data_path: Optional[str] = None,
    output_dir: Optional[str] = None
):
    """
    Train LoRA adapter for a specific dimension

    Args:
        dimension: Dimension name (e.g., 'privacy_compliance')
        model_name: Base model name or path
        data_path: Path to training data (defaults to ../data/{dimension})
        output_dir: Output directory for adapter (defaults to ../adapters/{dimension})
    """
    print("="*80)
    print(f"TRAINING LORA ADAPTER: {dimension}")
    print("="*80)
    print(f"Base Model: {model_name}")
    print(f"Dimension: {dimension}")
    print()

    # Set default paths
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data" / dimension

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "adapters" / dimension

    data_path = str(data_path)
    output_dir = str(output_dir)

    # Check if data exists
    if not os.path.exists(f"{data_path}/train.json"):
        print(f"ERROR: Training data not found at {data_path}/train.json")
        print("Please run prepare_training_data.py first")
        return False

    # Setup model and tokenizer
    model, tokenizer = setup_model_and_tokenizer(model_name)

    # Load and prepare data
    train_dataset, val_dataset = load_and_prepare_data(data_path, tokenizer)

    # Setup training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=TRAINING_ARGS["num_train_epochs"],
        per_device_train_batch_size=TRAINING_ARGS["per_device_train_batch_size"],
        per_device_eval_batch_size=TRAINING_ARGS["per_device_eval_batch_size"],
        gradient_accumulation_steps=TRAINING_ARGS["gradient_accumulation_steps"],
        gradient_checkpointing=TRAINING_ARGS["gradient_checkpointing"],
        learning_rate=TRAINING_ARGS["learning_rate"],
        lr_scheduler_type=TRAINING_ARGS["lr_scheduler_type"],
        warmup_ratio=TRAINING_ARGS["warmup_ratio"],
        weight_decay=TRAINING_ARGS["weight_decay"],
        max_grad_norm=TRAINING_ARGS["max_grad_norm"],
        logging_steps=TRAINING_ARGS["logging_steps"],
        save_strategy=TRAINING_ARGS["save_strategy"],
        eval_strategy=TRAINING_ARGS["eval_strategy"],
        save_total_limit=TRAINING_ARGS["save_total_limit"],
        fp16=TRAINING_ARGS["fp16"],
        bf16=TRAINING_ARGS["bf16"],
        optim=TRAINING_ARGS["optim"],
        group_by_length=TRAINING_ARGS["group_by_length"],
        report_to=TRAINING_ARGS["report_to"],
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )

    # Train
    print("\n" + "="*80)
    print("STARTING TRAINING")
    print("="*80)

    trainer.train()

    # Save final adapter
    print("\n" + "="*80)
    print("SAVING ADAPTER")
    print("="*80)

    final_output_dir = f"{output_dir}/final"
    model.save_pretrained(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)

    print(f"\n✓ Adapter saved to: {final_output_dir}")

    # Save training info
    training_info = {
        "dimension": dimension,
        "base_model": model_name,
        "training_date": datetime.now().isoformat(),
        "lora_config": LORA_CONFIG,
        "training_args": TRAINING_ARGS,
        "train_examples": len(train_dataset),
        "val_examples": len(val_dataset)
    }

    with open(f"{final_output_dir}/training_info.json", 'w') as f:
        json.dump(training_info, f, indent=2)

    print(f"✓ Training complete!")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python train_lora_base.py <dimension>")
        print("Example: python train_lora_base.py privacy_compliance")
        sys.exit(1)

    dimension = sys.argv[1]
    train_lora(dimension)
