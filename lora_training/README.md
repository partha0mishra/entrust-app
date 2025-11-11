# LoRA Fine-tuning for Data Governance Reports

This directory contains scripts and tools for fine-tuning LoRA adapters on your generated data governance reports. The fine-tuned models can be used with LM Studio for enhanced, domain-specific analysis.

## 📁 Directory Structure

```
lora_training/
├── configs/
│   └── training_config.py          # Training hyperparameters and settings
├── scripts/
│   ├── prepare_training_data.py    # Extract training data from reports
│   ├── train_lora_base.py          # Base training script
│   ├── train_lora_{dimension}.py   # Dimension-specific scripts (auto-generated)
│   ├── train_lora_all.py           # Master training script
│   ├── convert_to_gguf.py          # Convert adapters to GGUF format
│   └── generate_dimension_scripts.py
├── data/                            # Training datasets (generated)
├── adapters/                        # Trained LoRA adapters (generated)
├── models/                          # GGUF models for LM Studio (generated)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🚀 Quick Start

### 0. Configure Base Model (REQUIRED!)

**Before you start**, you MUST configure the base model:

```bash
# Find your models
python3 scripts/find_lm_studio_models.py

# Edit configs/training_config.py and set MODEL_NAME
# See QUICKSTART.md for detailed instructions
```

### 1. Install Dependencies

```bash
cd lora_training
pip install -r requirements.txt
```

**Note:** If you have CUDA GPU, install PyTorch with CUDA support first:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 2. Prepare Training Data

Extract training examples from your JSON reports:

```bash
python scripts/prepare_training_data.py
```

This will:
- Scan `~/entrust/report_json/` for all dimension reports
- Extract instruction-response pairs from LLM analyses
- Create train/val splits
- Save datasets to `data/{dimension}/`

### 3. Train LoRA Adapters

#### Option A: Train a Specific Dimension

```bash
python scripts/train_lora_privacy_compliance.py
```

Available dimensions:
- `privacy_compliance`
- `ethics_bias`
- `lineage_traceability`
- `value_lifecycle`
- `governance_management`
- `security_access`
- `metadata_documentation`
- `quality`

#### Option B: Train All Dimensions

```bash
python scripts/train_lora_all.py
```

This will train all 8 dimensions sequentially.

### 4. Convert to GGUF for LM Studio

#### Convert a Specific Dimension

```bash
python scripts/convert_to_gguf.py --dimension privacy_compliance
```

#### Convert All Dimensions

```bash
python scripts/convert_to_gguf.py
```

#### Advanced Options

```bash
python scripts/convert_to_gguf.py \
  --dimension privacy_compliance \
  --quantization Q4_K_M \
  --base-model /path/to/base/model \
  --keep-merged
```

Quantization options:
- `Q4_K_M` (default) - 4-bit quantization, medium quality
- `Q5_K_M` - 5-bit quantization, higher quality
- `Q8_0` - 8-bit quantization, highest quality
- `f16` - 16-bit floating point, no quantization

## ⚙️ Configuration

Edit `configs/training_config.py` to customize:

### Model Configuration
```python
MODEL_NAME = "gpt-oss-20b"  # HuggingFace model name
MODEL_MAX_LENGTH = 4096
```

### LoRA Parameters
```python
LORA_CONFIG = {
    "r": 16,                 # LoRA rank (lower = smaller adapter)
    "lora_alpha": 32,        # Scaling factor
    "lora_dropout": 0.05,    # Dropout rate
    # ...
}
```

### Training Parameters
```python
TRAINING_ARGS = {
    "num_train_epochs": 3,
    "learning_rate": 2e-4,
    "per_device_train_batch_size": 1,
    # ...
}
```

## 🎯 Training Details

### QLoRA (4-bit Quantization)

Uses QLoRA for memory-efficient training:
- 4-bit NormalFloat (NF4) quantization
- Double quantization for further compression
- Enables training on consumer GPUs (RTX 3090/4090)

### Memory Requirements

Approximate GPU memory needed:
- **gpt-oss-20b**: ~12-16 GB VRAM with QLoRA
- Per dimension training: 2-4 hours on RTX 4090
- Full 8-dimension training: 16-32 hours

### Dataset Format

Training examples follow instruction-following format:

```
### Instruction:
Analyze the Data Privacy & Compliance dimension based on the following survey data.

### Input:
Survey Metrics:
- Average Score: 7.2/10
- Response Rate: 95%
...

### Response:
[LLM-generated analysis from reports]
```

## 📊 Using Trained Models

### In LM Studio

1. Convert adapter to GGUF (if not done already):
   ```bash
   python scripts/convert_to_gguf.py --dimension privacy_compliance
   ```

2. Copy GGUF file to LM Studio models directory:
   ```bash
   cp models/privacy_compliance_model.Q4_K_M.gguf ~/Documents/LM\ Studio/models/
   ```

3. Load model in LM Studio and use for dimension-specific analysis

### In Python (with transformers)

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("gpt-oss-20b")
tokenizer = AutoTokenizer.from_pretrained("gpt-oss-20b")

# Load LoRA adapter
model = PeftModel.from_pretrained(
    base_model,
    "adapters/privacy_compliance/final"
)

# Generate analysis
prompt = "Analyze the following privacy compliance data..."
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=2048)
response = tokenizer.decode(outputs[0])
```

## 🔧 Troubleshooting

### Out of Memory (OOM)

1. Reduce batch size in `configs/training_config.py`:
   ```python
   "per_device_train_batch_size": 1  # Try reducing to 1
   ```

2. Increase gradient accumulation:
   ```python
   "gradient_accumulation_steps": 16  # Increase to 16 or 32
   ```

3. Enable gradient checkpointing (already enabled by default)

### CUDA Errors

Ensure CUDA-compatible PyTorch is installed:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### llama.cpp Not Found

For GGUF conversion, clone and build llama.cpp:
```bash
git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp
cd ~/llama.cpp
make
```

## 📝 Notes

- **Training Time**: Each dimension takes 2-4 hours on a modern GPU
- **Storage**: Each adapter is ~100-300 MB, GGUF models are 4-8 GB (depending on quantization)
- **Quality**: More training data = better results. Generate multiple customer reports for best performance
- **Overfitting**: With limited data, monitor validation loss. Stop early if it increases

## 🆘 Support

For issues or questions:
1. Check the logs in adapter output directories
2. Review training_info.json for configuration details
3. Adjust hyperparameters in configs/training_config.py

## 📚 References

- [PEFT (LoRA) Documentation](https://huggingface.co/docs/peft)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [llama.cpp GGUF Format](https://github.com/ggerganov/llama.cpp)
- [LM Studio](https://lmstudio.ai/)
