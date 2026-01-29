"""
COGNITIVE-CORE: Universal Cognitive Architecture Framework
===========================================================

A robust, agnostic framework for building cognitive AI models.
Supports vision, language, world model, audio, and multimodal architectures.

Installation:
    pip install cognitive-core

Or from HuggingFace:
    pip install git+https://huggingface.co/amewebstudio/cognitive-core

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

from setuptools import setup, find_packages

# Read README relative to this file
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cognitive-cores",
    version="1.0.3",
    author="Mike Amega",
    author_email="contact@amewebstudio.com",
    description="Universal Cognitive Architecture Framework for AI Models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Volgat/nexus-standardisation",
    project_urls={
        "HuggingFace": "https://huggingface.co/amewebstudio/cognitive-core",
        "Documentation": "https://github.com/Volgat/nexus-standardisation#readme",
        "Bug Tracker": "https://github.com/Volgat/nexus-standardisation/issues",
    },
    packages=["cognitive_core"],
    package_dir={"cognitive_core": "."},
    py_modules=["cognitive_core"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "datasets>=2.14.0",
        "huggingface_hub>=0.19.0",
        "accelerate>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "training": [
            "wandb>=0.15.0",
            "tensorboard>=2.14.0",
        ],
        "vision": [
            "torchvision>=0.15.0",
            "pillow>=9.0.0",
        ],
        "audio": [
            "torchaudio>=2.0.0",
            "librosa>=0.10.0",
        ],
        "all": [
            "wandb>=0.15.0",
            "tensorboard>=2.14.0",
            "torchvision>=0.15.0",
            "pillow>=9.0.0",
            "torchaudio>=2.0.0",
            "librosa>=0.10.0",
        ],
    },
    keywords=[
        "cognitive-ai",
        "neural-network",
        "transformer",
        "llm",
        "world-model",
        "multimodal",
        "huggingface",
        "pytorch",
        "deep-learning",
        "neurogenesis",
        "memory-system",
    ],
    include_package_data=True,
    zip_safe=False,
)
