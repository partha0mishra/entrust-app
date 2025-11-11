# Quick Start Guide

## ✅ Model Already Configured!

Your `configs/training_config.py` is already set to use **`openai/gpt-oss-20b`** - the same model you're using in LM Studio (just the trainable version instead of the GGUF format).

### Understanding Model Formats

- **GGUF files** (like your `gpt-oss-20b-Q4_K_S.gguf`): For inference only, cannot be trained
- **HuggingFace models** (like `openai/gpt-oss-20b`): Full precision, can be fine-tuned with LoRA

### Your Current Configuration

Edit `configs/training_config.py` if you want to change the model:

```python
# Currently configured (in configs/training_config.py):
MODEL_NAME = "openai/gpt-oss-20b"  # ✅ Already set!

# Alternative options:
# MODEL_NAME = "unsloth/gpt-oss-20b-unsloth-bnb-4bit"  # Pre-optimized by Unsloth
# MODEL_NAME = "mistralai/Mistral-7B-v0.1"  # Different model
# MODEL_NAME = "microsoft/phi-2"  # Smaller, faster training
```

## Next Steps

### Step 1: Install Dependencies

```bash
cd lora_training
pip install -r requirements.txt
```

**If you have CUDA GPU:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Step 2: Prepare Training Data

```bash
python3 scripts/prepare_training_data.py
```

This scans `~/entrust/report_json/` and extracts training examples.

### Step 3: Train LoRA Adapters

**Option A: Train a single dimension (faster, for testing)**
```bash
python3 scripts/train_lora_privacy_compliance.py
```

**Option B: Train all dimensions (recommended)**
```bash
python3 scripts/train_lora_all.py
```

This will train all 8 dimensions sequentially (~16-32 hours total on GPU).

### Step 4: Convert to GGUF (for LM Studio)

```bash
# Convert all trained adapters to GGUF format
python3 scripts/convert_to_gguf.py

# Or convert a specific dimension
python3 scripts/convert_to_gguf.py --dimension privacy_compliance
```

## 📋 Recommended Models for Training

### Your Model (Configured)
- **openai/gpt-oss-20b** (21B parameters, 3.6B active) ✅
  - Same model you use in LM Studio
  - Excellent for reasoning and analysis
  - Will be auto-downloaded on first run
  - Apache 2.0 license

### Alternative Options

**Small Models (Good for Testing)**
- **microsoft/phi-2** (2.7B parameters)
  - Fast training (~1-2 hours/dimension)
  - Good quality
  - No authentication required

**Medium Models (Balanced)**
- **mistralai/Mistral-7B-v0.1** (7B parameters)
  - Excellent quality
  - Reasonable training time (~2-4 hours/dimension)
  - No authentication required

**Large Models**
- **meta-llama/Llama-2-7b-hf** (7B parameters)
  - State-of-the-art quality
  - Requires HuggingFace authentication
  - Request access first on HuggingFace website

## 🔑 HuggingFace Authentication

For gated models:

```bash
# Install CLI
pip install huggingface_hub[cli]

# Login
huggingface-cli login

# Enter your token from https://huggingface.co/settings/tokens
```

## 💾 Hardware Requirements

| Model Size | VRAM (QLoRA) | Training Time/Dimension |
|------------|--------------|-------------------------|
| 2.7B (Phi-2) | 8-10 GB | 1-2 hours |
| 7B (Mistral/Llama-2) | 12-16 GB | 2-4 hours |
| 13B (Llama-2) | 20-24 GB | 4-8 hours |

## 🆘 Troubleshooting

### "Repository Not Found" Error

The model name is incorrect or requires authentication.

**Solution:**
1. Run `python3 scripts/find_lm_studio_models.py`
2. Use one of the suggested models
3. Or download a model manually

### "401 Unauthorized" Error

You're trying to access a gated model without authentication.

**Solution:**
```bash
huggingface-cli login
```

### Out of Memory (OOM)

Your GPU doesn't have enough memory.

**Solutions:**
1. Use a smaller model (phi-2 instead of Llama-2)
2. Reduce batch size in `configs/training_config.py`:
   ```python
   "per_device_train_batch_size": 1
   ```
3. Increase gradient accumulation:
   ```python
   "gradient_accumulation_steps": 16
   ```

## 📚 More Help

- Full documentation: `README.md`
- Model finder: `python3 scripts/find_lm_studio_models.py`
- Configuration: `configs/training_config.py`
