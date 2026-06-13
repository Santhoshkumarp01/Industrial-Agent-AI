"""
Upload the proper adapter_config.json to HuggingFace.
This fixes the 'peft_type' KeyError when loading the adapter.
"""

from huggingface_hub import HfApi, upload_file
import json

# Create PEFT-compatible adapter_config.json
adapter_config = {
    "base_model_name_or_path": "microsoft/Phi-3.5-mini-instruct",
    "bias": "none",
    "fan_in_fan_out": False,
    "inference_mode": True,
    "init_lora_weights": True,
    "layers_pattern": None,
    "layers_to_transform": None,
    "lora_alpha": 16,
    "lora_dropout": 0.0,
    "modules_to_save": None,
    "peft_type": "LORA",
    "r": 8,
    "revision": None,
    "target_modules": [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj"
    ],
    "task_type": "CAUSAL_LM"
}

# Save locally
with open("adapter_config.json", "w") as f:
    json.dump(adapter_config, f, indent=2)

print("✓ Created adapter_config.json locally")

# Upload to HuggingFace
try:
    api = HfApi()
    api.upload_file(
        path_or_fileobj="adapter_config.json",
        path_in_repo="adapter_config.json",
        repo_id="Santhoshkumarp/phi35-maintenance-wizard-lora",
        repo_type="model",
    )
    print("✓ Uploaded adapter_config.json to HuggingFace")
    print("  Repository: https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora")
except Exception as e:
    print(f"✗ Upload failed: {e}")
    print("\nManual upload instructions:")
    print("1. Go to: https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora")
    print("2. Click 'Files and versions' tab")
    print("3. Click 'Add file' → 'Upload files'")
    print("4. Upload the 'adapter_config.json' file created in this directory")
