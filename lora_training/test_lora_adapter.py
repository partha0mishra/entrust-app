#!/usr/bin/env python3
"""
Test the Privacy Compliance LoRA adapter
This loads the base model + adapter separately
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def test_lora_adapter(prompt: str = None):
    """Test the LoRA adapter with a privacy compliance prompt"""

    print("="*80)
    print("TESTING PRIVACY COMPLIANCE LORA ADAPTER")
    print("="*80)

    # Paths
    base_model_name = "mistralai/Mistral-7B-v0.1"
    adapter_path = "adapters/privacy_compliance/final"

    print(f"\nBase model: {base_model_name}")
    print(f"Adapter: {adapter_path}")
    print("\nLoading model (this may take a minute)...")

    # Load base model
    print("  Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    # Load adapter
    print("  Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, adapter_path)

    print("✓ Model and adapter loaded successfully!\n")

    # Default test prompt if none provided
    if prompt is None:
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

    print("Prompt:")
    print("-"*80)
    print(prompt)
    print("-"*80)

    print("\nGenerating analysis...\n")

    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # Decode
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract response part
    if "### Response:" in full_response:
        response = full_response.split("### Response:")[-1].strip()
    else:
        response = full_response

    print("="*80)
    print("FINE-TUNED MODEL OUTPUT:")
    print("="*80)
    print(response)
    print("="*80)

    return response


def quick_test():
    """Quick test with a short prompt"""

    print("="*80)
    print("QUICK TEST")
    print("="*80)

    prompt = """Analyze privacy compliance: GDPR documentation is incomplete, no data retention policy, and access controls need improvement. Provide recommendations."""

    # Load model
    base_model_name = "mistralai/Mistral-7B-v0.1"
    adapter_path = "adapters/privacy_compliance/final"

    print(f"\nLoading model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    model = PeftModel.from_pretrained(base_model, adapter_path)

    print(f"✓ Loaded\n")
    print(f"Prompt: {prompt}\n")
    print("Generating response...")

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

    print("\n" + "="*80)
    print("OUTPUT:")
    print("="*80)
    print(response)
    print("="*80)


if __name__ == "__main__":
    import sys
    import os

    # Check if adapter exists
    if not os.path.exists("adapters/privacy_compliance/final"):
        print("ERROR: LoRA adapter not found!")
        print("Expected location: adapters/privacy_compliance/final")
        print("\nMake sure you're in the lora_training directory and have trained the model.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        test_lora_adapter()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\nTips:")
    print("- For a quicker test, run: python3 test_lora_adapter.py --quick")
    print("- Test in LM Studio for interactive use")
    print("- Compare with base model to see improvement")
