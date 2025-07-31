# Private AI Pipeline: Building Secure, Fast, and Smart AI Systems

**PyCon 2025 Workshop Materials**

Learn how to build private AI systems that keep your data secure while delivering good enough performance. This hands-on workshop takes you from basic local AI deployment to a domain specific Retrieval-Augmented Generation (RAG) systems.

<img src="no-cloud.jpeg" width="500" style="display: block; margin: 0 auto;">

## What You'll Learn

Transform from cloud-dependent AI usage to running powerful, private AI systems that:
- **Keep your data secure** - Everything runs on your hardware
- **Deliver fast responses** - 2-5x performance improvements through optimization
- **Understand your business** - Custom knowledge integration via RAG

## Workshop Structure

### Chapter 1: Building Your First Private AI Assistant

Learn why organizations choose private AI and get hands-on experience running a production-ready Large Language Model locally.

**Key Topics:**
- Cloud vs. local AI trade-offs
- Hardware requirements and cost analysis
- Real-world use cases (Healthcare, Legal, Finance, R&D)
- Setting up your first local LLM

**Deliverable:** Working AI assistant running on your laptop

---

### Chapter 2: Supercharging Your AI with Hardware Optimization

Transform your slow baseline into a lightning-fast AI system using hardware-specific optimizations across different platforms.

**Key Topics:**
- Intel OpenVINO optimization (2-4x speed improvement)
- NVIDIA TensorRT acceleration (3-6x faster)
- AMD ROCm support for AMD GPUs
- Apple Silicon Metal Performance Shaders
- CPU-only optimization with ONNX Runtime

**Deliverable:** Optimized AI system with sub-5-second response times

---

### Chapter 3: Teaching Your AI About Your Business

Build a Retrieval-Augmented Generation (RAG) system that gives your AI access to domain specific knowledge.

**Key Topics:**
- RAG architecture and components
- Vector databases and semantic search

**Deliverable:** Complete private AI system with access to buisness knowledge

## Hardware Requirements

### Minimum Requirements (Development)
- **RAM:** 16GB (32GB recommended)
- **Storage:** 20GB free space
- **CPU:** Modern multi-core (Intel i5/i7 8th gen+, AMD Ryzen 5/7)
- **OS:** Linux, macOS, or Windows

### Recommended Setup
- **RAM:** 32GB+
- **GPU:** NVIDIA RTX 3060+ (12GB VRAM) or Apple M1/M2/M3 with 16GB+ unified memory
- **Storage:** NVMe SSD for faster model loading

### Enterprise/Team Server
- **RAM:** 64-128GB DDR4/DDR5
- **GPU:** NVIDIA RTX 4090 (24GB) or A100/H100 for production
- **Network:** 10Gbps+ for multi-user access

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yaacov/pycon-2025.git
cd pycon-2025
```

### 2. Set Up Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install base requirements
pip install jupyter transformers torch accelerate
```

### 3. Launch Notebooks
```bash
jupyter lab
```

### 4. Follow Along
Start with `ch_1.ipynb` and work through each chapter sequentially.

## Installation by Platform

### Intel Systems (Most Common)
```bash
pip install optimum[openvino] transformers torch accelerate
```

### NVIDIA GPU Systems
```bash
pip install transformers torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install optimum[nvidia]
```

### AMD GPU Systems
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
```

### Apple Silicon (M1/M2/M3)
```bash
pip install transformers torch accelerate
# MPS (Metal) support is built into PyTorch for Apple Silicon
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
