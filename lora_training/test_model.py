#!/usr/bin/env python3
"""
Test the fine-tuned Privacy Compliance model
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def test_model_simple():
    """Test the model with a simple prompt"""

    print("="*80)
    print("TESTING PRIVACY COMPLIANCE MODEL")
    print("="*80)

    # Use the merged model (adapter already integrated)
    model_path = "models/privacy_compliance_merged"

    print(f"\nLoading model from: {model_path}")
    print("This may take a minute...\n")

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    print("✓ Model loaded successfully!\n")

    # Test prompt (similar to training format)
    prompt = """### Instruction:
Analyze the Data Privacy & Compliance dimension based on the following survey data.

### Input:
Survey Metrics:
- Average Score: 6.8/10
- Response Rate: 92%
- Total Respondents: 45

Key Findings:
- GDPR compliance documentation exists but needs updating
- Data retention policies are 2 years old
- Access controls are implemented
- Privacy training completion rate: 78%
- No recent privacy audits conducted

Score Distribution:
- Excellent (9-10): 15%
- Good (7-8): 45%
- Fair (5-6): 30%
- Poor (1-4): 10%

### Response:
"""

    print("Generating analysis...")
    print("-"*80)

    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Generate response
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode and print
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract just the response part (after "### Response:")
    response_part = full_response.split("### Response:")[-1].strip()

    print("\n" + "="*80)
    print("MODEL OUTPUT:")
    print("="*80)
    print(response_part)
    print("="*80)

    return response_part


def test_model_comparison():
    """Compare base model vs fine-tuned model"""

    print("\n" + "="*80)
    print("COMPARISON TEST: Base vs Fine-tuned")
    print("="*80)

    prompt = """Analyze privacy compliance for this organization:
- GDPR documentation incomplete
- No data retention policy
- Access controls need improvement

Provide recommendations."""

    print("\nPrompt:", prompt)
    print("\n" + "-"*80)

    # Test with fine-tuned model
    model_path = "models/privacy_compliance_merged"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print("\nFINE-TUNED MODEL OUTPUT:")
    print("-"*80)
    print(response)
    print("="*80)


if __name__ == "__main__":
    import sys

    # Check if merged model exists
    import os
    if not os.path.exists("models/privacy_compliance_merged"):
        print("ERROR: Merged model not found!")
        print("The model was cleaned up during GGUF conversion.")
        print("\nOptions:")
        print("1. Re-run conversion without cleanup:")
        print("   python3 scripts/convert_to_gguf.py --dimension privacy_compliance --keep-merged")
        print("\n2. Test the GGUF model in LM Studio instead")
        print("\n3. Load the adapter manually (see test_with_adapter.py)")
        sys.exit(1)

    print("\nTest 1: Simple Analysis")
    print("="*80)
    test_model_simple()

    print("\n\nTest 2: Comparison Test")
    print("="*80)
    test_model_comparison()

    print("\n\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
