#!/bin/bash
# Test the GGUF model with llama.cpp

echo "========================================================================"
echo "TESTING PRIVACY COMPLIANCE GGUF MODEL"
echo "========================================================================"

# Paths
MODEL_PATH="models/privacy_compliance_model.f16.gguf"
LLAMA_CPP="$HOME/llama.cpp"

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: Model not found at $MODEL_PATH"
    exit 1
fi

# Check if llama.cpp exists
if [ ! -d "$LLAMA_CPP" ]; then
    echo "ERROR: llama.cpp not found at $LLAMA_CPP"
    exit 1
fi

# Check if llama-cli exists
if [ ! -f "$LLAMA_CPP/llama-cli" ]; then
    echo "llama-cli not found, building it..."
    cd "$LLAMA_CPP" && make llama-cli
    cd - > /dev/null
fi

echo ""
echo "Model: $MODEL_PATH"
echo "Size: $(du -h "$MODEL_PATH" | cut -f1)"
echo ""

# Test prompt
PROMPT="Analyze the Data Privacy & Compliance dimension:

Survey Results:
- Average Score: 6.8/10
- Response Rate: 92%
- Total Respondents: 45

Key Findings:
- GDPR compliance documentation exists but needs updating
- Data retention policies are 2 years old
- Access controls are implemented
- Privacy training completion rate: 78%
- No recent privacy audits conducted

Provide a detailed analysis with recommendations."

echo "Prompt:"
echo "------------------------------------------------------------------------"
echo "$PROMPT"
echo "------------------------------------------------------------------------"
echo ""
echo "Generating response..."
echo "========================================================================"
echo ""

# Run llama.cpp
"$LLAMA_CPP/llama-cli" \
    -m "$MODEL_PATH" \
    -p "$PROMPT" \
    -n 512 \
    --temp 0.7 \
    --top-p 0.9 \
    --ctx-size 4096 \
    --threads 8

echo ""
echo "========================================================================"
echo "TESTING COMPLETE"
echo "========================================================================"
