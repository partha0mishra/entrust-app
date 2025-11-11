#!/bin/bash

echo "=========================================="
echo "LoRA Training Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create directory structure
echo ""
echo "Creating directory structure..."
mkdir -p data
mkdir -p adapters
mkdir -p models

# Generate dimension-specific training scripts
echo ""
echo "Generating dimension-specific training scripts..."
python3 scripts/generate_dimension_scripts.py

# Check for llama.cpp (for GGUF conversion)
echo ""
echo "Checking for llama.cpp..."
if [ -d "$HOME/llama.cpp" ]; then
    echo "✓ llama.cpp found at $HOME/llama.cpp"
else
    echo "⚠ llama.cpp not found"
    echo "  To enable GGUF conversion, run:"
    echo "    git clone https://github.com/ggerganov/llama.cpp $HOME/llama.cpp"
    echo "    cd $HOME/llama.cpp && make"
fi

# Check for reports
echo ""
echo "Checking for training data..."
reports_path="$HOME/entrust/report_json"
if [ -d "$reports_path" ]; then
    report_count=$(find "$reports_path" -name "*.json" -type f | wc -l)
    echo "✓ Found $report_count report files in $reports_path"
else
    echo "⚠ Reports directory not found: $reports_path"
    echo "  Generate some reports first from the main application"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Prepare training data:"
echo "     python3 scripts/prepare_training_data.py"
echo ""
echo "  2. Train a specific dimension:"
echo "     python3 scripts/train_lora_privacy_compliance.py"
echo ""
echo "  3. Or train all dimensions:"
echo "     python3 scripts/train_lora_all.py"
echo ""
echo "  4. Convert to GGUF for LM Studio:"
echo "     python3 scripts/convert_to_gguf.py"
echo ""
