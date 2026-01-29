# COGNITIVE-CORES Framework

> 🧠 Universal Standard for Cognitive Architectures by Ame Web Studio

**Cognitive-Cores** is a robust, agnostic framework designed for building advanced cognitive AI models. It provides a standardized interface for integrating Vision, Language, Audio, World Modeling, and Multimodal capabilities into a unified system.

## 🚀 Installation

### Option 1: Via Pip (From PyPI)

```bash
pip install cognitive-cores
```

### Option 2: Via Pip (From GitHub)

```bash
pip install git+https://github.com/Volgat/nexus-standardisation.git@cognitive-core
```

### Option 3: Via HuggingFace

```bash
pip install git+https://huggingface.co/amewebstudio/cognitive-core
```

### Optional Dependencies

```bash
pip install "cognitive-cores[vision]"    # For Vision Models
pip install "cognitive-cores[audio]"     # For Audio Models
pip install "cognitive-cores[training]"  # For Training Tools (WandB, etc.)
pip install "cognitive-cores[all]"       # Full Installation
```

## 🛠️ Usage

### Loading Models regarding Cognitive Finetuning

To finetune a model built with **Cognitive-Cores** (like NEXUS-LPOL) from HuggingFace, use the standard `AutoModel` interface with `trust_remote_code=True`.

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from cognitive_core import CognitiveTrainer, CognitiveTrainingConfig, prepare_dataset

# 1. Configuration
model_id = "amewebstudio/nexus-lpol-v3"  # Example Model

# 2. Load Tokenizer & Model
# trust_remote_code=True is essential to load the custom cognitive architecture
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True, 
    torch_dtype=torch.float16,
    device_map="auto"
)

# 3. Training Setup
config = CognitiveTrainingConfig(
    output_dir="./nexus-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4
)

# 4. Initialize Trainer
trainer = CognitiveTrainer(
    model=model,
    args=config,
    train_dataset=my_dataset, # Prepare your dataset using prepare_dataset helper
)

# 5. Start Finetuning
trainer.train()
```

## 🧩 Core Capabilities

The framework provides a suite of standardized, reusable modules designed for high-performance cognitive modeling.

*   **Advanced Normalization & Encoding**: Optimized implementations for stability and long-context handling.
*   **Attention Mechanisms**: Efficient attention layers supporting extensive context windows and multimodal fusion.
*   **Memory Systems**: sophisticated short-term, long-term, and episodic memory modules.
*   **World Modeling**: Components for simulating and predicting states across physical, social, and abstract domains.
*   **Internal State Management**: Modules for handling agentic internal states, drives, and cohesion.
*   **Multimodal Integration**: Universal latent space mapping for seamless alignment of text, audio, and visual data.
*   **Neurogenesis**: Dynamic architectural adaptation capabilities.

## 📄 License

**PROPRIETARY - ALL RIGHTS RESERVED**
Copyright © 2026 Mike Amega - Ame Web Studio
