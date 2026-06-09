"""
Verify Phi-3.5 Mini layer names before fine-tuning.
Run this once to confirm the exact MLP layer names.

Run: python ml/check_layers.py
"""

import torch
from transformers import AutoModelForCausalLM

print("=" * 60)
print("PHI-3.5 MINI LAYER NAME VERIFICATION")
print("=" * 60)

print("\n→ Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    "ml/base_models/phi35_mini",
    torch_dtype=torch.float32,
    device_map={"": "mps"},
    trust_remote_code=True
)

print("✓ Model loaded\n")
print("=== Phi-3.5 Mini Layer Names ===")

mlp_layers = set()
for name, _ in model.named_modules():
    # Show only leaf projection layers
    if any(x in name for x in ["proj", "fc", "gate", "up", "down", "mlp"]):
        parts = name.split(".")
        mlp_layers.add(parts[-1])   # last part = layer type name

print("\nAttention & MLP projection layers found:")
for layer in sorted(mlp_layers):
    print(f"  • {layer}")

print("\n" + "=" * 60)
print("RECOMMENDED LORA TARGET_MODULES:")
print("=" * 60)

if "fc1" in mlp_layers and "fc2" in mlp_layers:
    print("""
target_modules=[
    "q_proj",    # attention query
    "k_proj",    # attention key
    "v_proj",    # attention value
    "o_proj",    # attention output
    "fc1",       # MLP up projection
    "fc2",       # MLP down projection
]
""")
    print("✓ Use fc1/fc2 (confirmed present in model)")
elif "gate_up_proj" in mlp_layers and "down_proj" in mlp_layers:
    print("""
target_modules=[
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_up_proj",
    "down_proj",
]
""")
    print("⚠ Use gate_up_proj/down_proj (different architecture)")
else:
    print("\n⚠ Unexpected layer names found!")
    print("Check the full list above and update target_modules manually.")

print("\n" + "=" * 60)
print("You can now run: python ml/finetune_phi35.py")
print("=" * 60)
