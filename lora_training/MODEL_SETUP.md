# Model Setup Explanation

## ✅ Configuration Complete!

Your LoRA training system is now configured to use **`openai/gpt-oss-20b`** - the same model you're using in LM Studio, just in a trainable format.

## Understanding the Model Formats

### What You Have in LM Studio
```
~/.lmstudio/models/unsloth/gpt-oss-20b-GGUF/gpt-oss-20b-Q4_K_S.gguf
```

This is:
- **GGUF format**: Quantized model for fast inference
- **Q4_K_S**: 4-bit quantization (smaller file size)
- **Purpose**: Running the model in LM Studio
- **Cannot be used for**: Training or fine-tuning

### What You'll Use for Training
```python
MODEL_NAME = "openai/gpt-oss-20b"
```

This is:
- **HuggingFace format**: Full precision weights in PyTorch/safetensors format
- **Purpose**: LoRA fine-tuning
- **Will be downloaded automatically** when you first run training
- **Same base model** as your GGUF file, just unquantized

## The Training Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Start with base model (openai/gpt-oss-20b)              │
│    Downloaded from HuggingFace (auto)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Train LoRA adapters (one per dimension)                  │
│    Saved to: lora_training/adapters/{dimension}/            │
│    Format: HuggingFace PEFT adapters                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Convert to GGUF (for LM Studio)                          │
│    Saved to: lora_training/models/{dimension}_model.gguf    │
│    This merges adapter + base model, then quantizes         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Use in LM Studio                                         │
│    Load the fine-tuned GGUF model for dimension analysis    │
└─────────────────────────────────────────────────────────────┘
```

## Why We Can't Use Your GGUF File Directly

GGUF files are **post-quantization** and have:
- Reduced precision (4-bit instead of 16/32-bit)
- Optimized structure for inference only
- No gradient computation support
- No way to extract original weights

Think of it like this:
- **GGUF file** = Compressed JPEG image (fast to view, can't edit)
- **HuggingFace model** = Original RAW image (slower, but fully editable)

## What Happens on First Run

When you run training for the first time:

1. **Model Download** (~10-20 GB)
   ```
   Downloading openai/gpt-oss-20b from HuggingFace...
   This may take 10-30 minutes depending on your internet speed
   ```

2. **Cached Locally**
   ```
   ~/.cache/huggingface/hub/models--openai--gpt-oss-20b/
   ```

3. **Future runs**: Model loads from cache instantly

## Storage Requirements

| Component | Size | Location |
|-----------|------|----------|
| Base model (downloaded once) | ~15-20 GB | `~/.cache/huggingface/` |
| LoRA adapters (8 dimensions) | ~100-300 MB each | `lora_training/adapters/` |
| GGUF models (8 dimensions) | ~4-8 GB each | `lora_training/models/` |
| Training data | ~10-50 MB | `lora_training/data/` |
| **Total** | ~55-90 GB | Various |

## Quick Start

Now that the model is configured, you can start training:

```bash
# 1. Install dependencies
cd lora_training
pip install -r requirements.txt

# 2. Prepare training data from your reports
python3 scripts/prepare_training_data.py

# 3. Train all dimensions (or start with one for testing)
python3 scripts/train_lora_all.py

# 4. Convert to GGUF for LM Studio
python3 scripts/convert_to_gguf.py
```

## Alternative: Use Pre-quantized Base Model

If you want to save some download time and storage, you can use Unsloth's pre-quantized version:

```python
# In configs/training_config.py, change to:
MODEL_NAME = "unsloth/gpt-oss-20b-unsloth-bnb-4bit"
```

This:
- ✅ Already quantized for QLoRA (4-bit)
- ✅ Optimized by Unsloth for faster training
- ✅ Smaller download (~5-8 GB vs 15-20 GB)
- ✅ Still fully trainable

## Need Help?

- **Full documentation**: `README.md`
- **Quick start**: `QUICKSTART.md`
- **Find models**: `python3 scripts/find_lm_studio_models.py`
- **Configuration**: `configs/training_config.py`

## Summary

✅ **Model configured**: `openai/gpt-oss-20b`
✅ **Same model as your LM Studio GGUF** (just trainable format)
✅ **Will auto-download** on first training run
✅ **Ready to start training!**

Run the Quick Start commands above to begin fine-tuning your data governance models!
