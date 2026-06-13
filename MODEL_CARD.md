---
license: mit
base_model: microsoft/Phi-3.5-mini-instruct
tags:
  - industrial
  - maintenance
  - steel-plant
  - lora
  - phi-3.5
  - fine-tuned
language:
  - en
pipeline_tag: text-generation
---

# 🏭 Phi-3.5 Mini — Industrial Maintenance Wizard

Fine-tuned LoRA adapter for **Phi-3.5 Mini Instruct** specialized in steel plant maintenance diagnostics, safety procedures, and equipment fault analysis.

## 📊 Model Details

| Property | Value |
|----------|-------|
| **Base Model** | [microsoft/Phi-3.5-mini-instruct](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) |
| **Parameters** | 3.8B (base) + 24MB (LoRA adapter) |
| **Fine-tuning Method** | LoRA (Low-Rank Adaptation) |
| **LoRA Rank** | 8 |
| **LoRA Alpha** | 16 |
| **Target Modules** | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| **Training Data** | 2,027 industrial maintenance Q&A pairs |
| **Training Hardware** | Apple M3 Max (MLX framework) |
| **License** | MIT |

## 🎯 Specialization

This model is fine-tuned on real-world industrial maintenance scenarios for:

- **Equipment Types**: Rolling Mills, Blast Furnace Blowers, Compressors, Conveyor Motors
- **Failure Analysis**: Bearing wear, thermal overload, electrical faults, pressure system failures
- **Maintenance Procedures**: Step-by-step repair instructions with safety protocols
- **Technical Specifications**: Torque values, part numbers, measurement standards

## 🚀 Quick Start

### Installation

```bash
pip install transformers torch peft
```

### Usage (Cross-Platform)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Phi-3.5-mini-instruct",
    torch_dtype="auto",
    device_map="auto"
)

# Load fine-tuned adapter
model = PeftModel.from_pretrained(
    base_model,
    "Santhoshkumarp/phi35-maintenance-wizard-lora"
)

tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3.5-mini-instruct")

# Generate maintenance guidance
prompt = """<|system|>
You are an expert AI maintenance engineer specializing in steel plant equipment.
<|end|>
<|user|>
Rolling Mill RM1 shows excessive vibration (12.5 mm/s) and high temperature (95°C). 
What could be the root cause and recommended actions?
<|end|>
<|assistant|>
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=500, temperature=0.7)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)
```

### Apple Silicon (MLX - Faster)

```bash
pip install mlx-lm
```

```python
from mlx_lm import load, generate

model, tokenizer = load(
    "microsoft/Phi-3.5-mini-instruct",
    adapter_path="Santhoshkumarp/phi35-maintenance-wizard-lora"
)

prompt = """<|system|>
You are an expert AI maintenance engineer specializing in steel plant equipment.
<|end|>
<|user|>
Rolling Mill RM1 shows excessive vibration (12.5 mm/s) and high temperature (95°C). 
What could be the root cause and recommended actions?
<|end|>
<|assistant|>
"""

response = generate(model, tokenizer, prompt=prompt, max_tokens=500, verbose=False)
print(response)
```

## 📈 Training Details

### Dataset

- **Size**: 2,027 maintenance Q&A pairs
- **Sources**:
  - Historical incident reports
  - Standard Operating Procedures (SOPs)
  - Equipment maintenance manuals
  - Sensor data analysis scenarios
  
### Training Configuration

```yaml
Model: microsoft/Phi-3.5-mini-instruct
Method: LoRA fine-tuning
Rank: 8
Alpha: 16
Dropout: 0.05
Learning Rate: 2e-4
Batch Size: 4
Gradient Accumulation: 4
Epochs: 3
Optimizer: AdamW
Scheduler: Cosine with warmup
Warmup Steps: 100
Max Sequence Length: 2048
```

### Hardware

- **Training**: Apple M3 Max (MLX framework)
- **Training Time**: ~45 minutes
- **Memory**: ~12GB RAM

## 💡 Example Outputs

**Query**: *"Blast furnace blower shows high current (65A) and unusual noise. Diagnose the issue."*

**Base Phi-3.5**:
> "High current in a blower could indicate several issues. Check the motor, bearings, and ensure proper maintenance."

**Fine-tuned Model**:
> "**Root Cause**: Motor overload due to bearing degradation or misalignment.
> 
> **Immediate Actions**:
> 1. STOP blower operation immediately (safety-critical equipment)
> 2. Lock out / Tag out (LOTO) - ensure zero energy state
> 3. Monitor for smoke or excessive heating
> 
> **Diagnostic Steps**:
> 1. Check bearing condition using vibration analysis
> 2. Measure motor winding resistance (megger test)
> 3. Inspect coupling alignment
> 4. Verify voltage balance across all phases
> 
> **Parts Required**: Bearing assembly (Part: BF-BRG-001), Motor contactor if damaged
> 
> **Repair Procedure**: Follow SOP-BF-003 for bearing replacement. Torque coupling bolts to 85 Nm."

## ⚠️ Limitations

- **Domain-Specific**: Optimized for steel plant equipment, may not generalize to other industries
- **Safety-Critical**: Always verify recommendations with qualified maintenance personnel
- **English Only**: Trained on English-language maintenance documentation
- **Sensor Data**: Best performance with specific numerical values (vibration, temperature, current, pressure)

## 🔧 System Architecture

This model is used in the **Industrial Agent AI** system:

```
User Query
    ↓
Equipment Sensor Data + Historical Context
    ↓
RAG Retrieval (Qdrant Vector DB)
    ↓
Fine-tuned Phi-3.5 Mini (this model)
    ↓
Multi-Agent Analysis
    ↓
Actionable Maintenance Plan + Citations
```

## 📄 Citation

```bibtex
@misc{phi35-maintenance-wizard-2024,
  title  = {Phi-3.5 Mini Industrial Maintenance Wizard LoRA Adapter},
  author = {Santhosh Kumar P},
  year   = {2024},
  url    = {https://huggingface.co/Santhoshkumarp/phi35-maintenance-wizard-lora}
}
```

## 📜 License

MIT License - Adapter weights only. Base model license: [MIT](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)

---

**Built for the Industrial AI Hackathon** • [GitHub Repository](https://github.com/Santhoshkumarp01/Industrial-Agent-AI)
