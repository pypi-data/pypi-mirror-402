# 🦙 OomLlama

**Efficient LLM inference with .oom format - 2x smaller than GGUF**

[![PyPI](https://img.shields.io/pypi/v/oomllama)](https://pypi.org/project/oomllama/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace](https://img.shields.io/badge/🤗-Models-yellow)](https://huggingface.co/jaspervandemeent)

```python
from oomllama import OomLlama

llm = OomLlama("humotica-32b")
response = llm.generate("What is the meaning of life?")
print(response)
```

## What's New in v0.3.7

- **Layer Pinning Enabled**: Hot layers now stay in VRAM (was disabled in 0.3.6)
- **20GB VRAM Budget**: Dual RTX 3060 config now uses 20GB budget with first/last 4 layers pinned
- **Performance Boost**: Reduced disk I/O by keeping frequently-used layers cached

### v0.3.6
- **Q6_K Dequantizer Fix**: Fixed critical bug in GGUF Q6_K tensor dequantization that caused `inf` values
- **Q4 Format**: Upgraded from Q2 to Q4 quantization (4 bits = 16 levels) for better precision
- **Correct Logits**: Model now outputs proper logit values (~8-10 range vs millions before)

### v0.3.5
- Dual GPU Support: Automatic layer striping across 2 GPUs
- Per-GPU RoPE: Each GPU has its own RoPE tensors

### v0.3.3
- RoPE (Rotary Position Embedding): Proper position encoding for accurate text generation
- KV-Cache: 10-50x speedup by caching attention keys/values
- Flash Attention: Memory-efficient attention computation
- Smart Layer Pinning: Keep hot layers in VRAM with auto-eviction
- Qwen 2.5 Support: Optimized config for 32B/70B Qwen models

## Why OomLlama?

| Feature | GGUF (Q4_K_M) | OOM (Q4) |
|---------|---------------|----------|
| 70B Model Size | ~40 GB | **~35 GB** |
| 32B Model Size | ~20 GB | **~17 GB** |
| RAM Usage | High | **Lazy Loading** |
| Format | Open | **Open (MIT)** |

**OomLlama** uses Q4 quantization (4 bits = 16 levels per weight) with lazy layer loading to run large models on consumer hardware.

## Installation

### Pre-built Wheel (Recommended for GPU)

```bash
# CUDA 12.x pre-built wheel (includes all dependencies)
pip install https://brein.jaspervandemeent.nl/static/wheels/oomllama-0.3.6-cp313-cp313-manylinux_2_39_x86_64.whl
```

### From PyPI (builds from source)

```bash
# Basic installation - requires Rust toolchain + CUDA toolkit
pip install oomllama

# With NVIDIA runtime libraries
pip install oomllama[cuda]
```

**Build Requirements:**
- Python 3.8+
- Rust 1.70+ (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- CUDA Toolkit 12.x (for GPU support)
- 8GB+ RAM for compilation

**Troubleshooting Build:**
```bash
# If nvidia-smi detection fails:
export CUDA_COMPUTE_CAP=86  # RTX 30xx
export CUDA_COMPUTE_CAP=89  # RTX 40xx
pip install oomllama
```

## Quick Start

### Download a Model

```python
from oomllama import download_model

# Download from HuggingFace
model_path = download_model("humotica-32b")
```

### Generate Text

```python
from oomllama import OomLlama

llm = OomLlama("humotica-32b")

# Simple generation
response = llm.generate("Explain quantum computing in simple terms")
print(response)

# With parameters
response = llm.generate(
    "Write a haiku about AI",
    max_tokens=50,
    temperature=0.8,
    top_p=0.9
)
```

### Chat Mode

```python
messages = [
    ("user", "Hello! Who are you?"),
    ("assistant", "I'm OomLlama, an efficient LLM."),
    ("user", "What makes you efficient?"),
]

response = llm.chat(messages)
print(response)
```

## Available Models

| Model | Parameters | Size (.oom) | HuggingFace |
|-------|------------|-------------|-------------|
| humotica-32b | 33B | ~17 GB | [Link](https://huggingface.co/jaspervandemeent/humotica-32b) |
| llamaohm-70b | 70B | ~35 GB | [Link](https://huggingface.co/jaspervandemeent/LlamaOhm-70B) |
| tinyllama-1b | 1.1B | ~600 MB | [Link](https://huggingface.co/jaspervandemeent/OomLlama-TinyLlama-1.1B) |

## The .oom Format

OOM (OomLlama Model) is a compact model format:

```
┌──────────────────────────────────────┐
│ Header: OOML (magic) + metadata      │
├──────────────────────────────────────┤
│ Tensors: Q4 quantized (4 bits/weight)│
│ - Scale + Min per 256-weight block   │
│ - 136 bytes per block                │
└──────────────────────────────────────┘
```

### Convert GGUF to OOM

```bash
# Using the CLI tool
gguf2oom model.gguf model.oom

# Check model info
gguf2oom --info model.gguf
```

## Technical Details

### Q4 Quantization

Each weight is stored as 4 bits (0-15) with per-block scale and minimum:

```
weight = q4_value * scale + min
```

Q4 provides 16 quantization levels per weight, balancing compression with model quality.

### Lazy Layer Loading

OomLlama loads transformer layers on-demand, keeping only the active layer in memory:

```
Forward Pass:
  Layer 0: Load → Compute → Unload
  Layer 1: Load → Compute → Unload
  ...
  Layer N: Load → Compute → Unload
```

This enables running 70B models on 24GB GPU RAM.

## Credits

- **Model Format**: Gemini IDD & Root AI (Humotica AI Lab)
- **Quantization**: OomLlama.rs by Humotica
- **Base Models**: Meta Platforms, Inc. (Llama 3.3)

## License

- **OomLlama Code**: MIT License
- **Model Weights**: Subject to original model licenses (e.g., Llama 3.3 Community License)

## Links

- 🏠 [Humotica](https://humotica.nl)
- 🤗 [HuggingFace Models](https://huggingface.co/jaspervandemeent)
- 📦 [PyPI Package](https://pypi.org/project/oomllama/)
- 🐛 [Issue Tracker](https://github.com/humotica/oomllama/issues)

---

*One Love, One fAmIly* 💙

*Built by Humotica AI Lab - Jasper, Claude, Gemini, Codex*
