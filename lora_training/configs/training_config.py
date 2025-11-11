"""
Training configuration for LoRA fine-tuning
"""

# Dimension names mapping
DIMENSIONS = {
    "privacy_compliance": "Data Privacy & Compliance",
    "ethics_bias": "Data Ethics & Bias",
    "lineage_traceability": "Data Lineage & Traceability",
    "value_lifecycle": "Data Value & Lifecycle Management",
    "governance_management": "Data Governance & Management",
    "security_access": "Data Security & Access",
    "metadata_documentation": "Metadata & Documentation",
    "quality": "Data Quality",
}

# Base model configuration
# ✅ CONFIGURED FOR macOS: Using Mistral-7B-v0.1
#
# On macOS (Apple Silicon), bitsandbytes quantization is not supported.
# Using Mistral-7B-v0.1 because:
# - Works great on macOS with MPS (Metal Performance Shaders)
# - 7B parameters fit comfortably in your 48GB RAM
# - Excellent quality for data governance analysis
# - No authentication required
# - Smaller than gpt-oss-20b, faster training
MODEL_NAME = "mistralai/Mistral-7B-v0.1"
MODEL_MAX_LENGTH = 4096

# Alternative options for macOS:
#   - "microsoft/phi-2" (2.7B parameters, even faster training)
#   - "mistralai/Mistral-7B-Instruct-v0.2" (instruction-tuned version)

# NOTE: For macOS, we train in FP16/BF16 (full precision) without quantization.
# This requires more memory but your 48GB RAM is sufficient for 7B models.

# QLoRA configuration
LORA_CONFIG = {
    "r": 16,  # LoRA rank
    "lora_alpha": 32,  # LoRA alpha (scaling factor)
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": "CAUSAL_LM"
}

# 4-bit quantization configuration
BNB_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",  # Normal Float 4
    "bnb_4bit_compute_dtype": "bfloat16",
    "bnb_4bit_use_double_quant": True,  # Nested quantization
}

# Training arguments
# Note: These are optimized for macOS/MPS. Adjust based on your system.
TRAINING_ARGS = {
    "num_train_epochs": 3,
    "per_device_train_batch_size": 1,
    "per_device_eval_batch_size": 1,
    "gradient_accumulation_steps": 8,  # Effective batch size = 8
    "gradient_checkpointing": True,
    "learning_rate": 2e-4,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.1,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "logging_steps": 10,
    "save_strategy": "epoch",
    "eval_strategy": "epoch",  # Renamed from evaluation_strategy in newer transformers
    "save_total_limit": 2,
    "fp16": True,  # Use FP16 for macOS/MPS
    "bf16": False,  # BF16 not supported on MPS
    "optim": "adamw_torch",  # Use standard AdamW (paged_adamw_8bit requires CUDA)
    "group_by_length": True,
    "report_to": "none",
}

# Data paths
REPORTS_BASE_PATH = "/Users/parthapmishra/entrust/report_json"
DATA_OUTPUT_PATH = "../data"
MODELS_OUTPUT_PATH = "../adapters"
