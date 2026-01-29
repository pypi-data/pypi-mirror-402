```markdown
# Wesamoyo SDK

**Official SDK for Wesamoyo-293M-MoE Transformer Model**  
Professional SDK for loading and training the 293M parameter Mixture-of-Experts transformer.

## Overview
SDK for seamless integration with **Wesamoyo-293M-MoE** transformer model. Developed and maintained by **Houndtid Labs**.

## Features
- **Model Loading**: Load the complete 293M parameter MoE transformer
- **Weight Compatibility**: Works with the 591MB model.safetensors file
- **Hugging Face Native**: Integrated with transformers ecosystem
- **Training Ready**: Ready for training from scratch or fine-tuning
- **African Innovation**: Developed in Uganda by Houndtid Labs

## Installation
```bash
pip install wesamoyo
```

## Quick Start
```python
import wesamoyo

# Load the Wesamoyo-293M-MoE model
model = wesamoyo.load_wesamoyo_293m()

# Or use Hugging Face AutoModel
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    "HoundtidLabs/wesamoyo-293M-MoE",
    trust_remote_code=True
)
```

## Model Specifications
- **Parameters**: 293 Million total
- **Architecture**: Mixture-of-Experts (64 experts, 6 activated)
- **Context Length**: 16,384 tokens
- **File Size**: 591MB (complete weights)
- **Precision**: BF16 optimized
```