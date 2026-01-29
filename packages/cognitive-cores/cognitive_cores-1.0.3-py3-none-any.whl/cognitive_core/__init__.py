"""
COGNITIVE-CORE Framework
========================

Universal template for Ame Web Studio's cognitive AI architectures.
Provides standardized loading, checkpoint management, and utilities
for vision, language, world model, and multimodal cognitive systems.

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

from .cognitive_base import (
    CognitiveConfig,
    CognitiveModule,
    MemoryModule,
    TemporalModule,
    WorldModelModule,
    CognitivePreTrainedModel,
    register_cognitive_model,
)

from .cognitive_checkpoint import (
    remap_checkpoint_keys,
    validate_checkpoint,
    save_cognitive_checkpoint,
    load_cognitive_checkpoint,
)

from .cognitive_utils import (
    setup_environment,
    get_device,
    get_optimal_dtype,
    get_memory_info,
    clear_memory,
    estimate_model_memory,
    print_model_info,
    print_training_progress,
    get_hf_token,
)

from .cognitive_training import (
    CognitiveTrainingConfig,
    CognitiveTrainer,
    prepare_dataset,
    create_instruction_dataset,
    quick_train,
    CognitiveStateCallback,
)

from .cognitive_modules import (
    # Normalization
    RMSNorm,
    # Positional Encoding
    RotaryEmbedding,
    SinusoidalPositionalEncoding,
    # Attention
    GroupedQueryAttention,
    CrossAttention,
    # Feedforward
    SwiGLU,
    MLP,
    # Mixture of Experts
    Expert,
    SparseMoE,
    # Memory Systems
    ContrastiveLPOL,
    MultiScaleMemory,
    EpisodicMemory,
    # World Model
    WorldBuffer,
    MultiWorldBuffer,
    # Internal State
    NonVerbalTension,
    InternalState,
    # Dream & Self-Trace
    DreamPhase,
    SelfTrace,
    # Neurogenesis
    NeurogenesisLayer,
    # EARCP
    EARCPModule,
    # VAE
    VAEEncoder,
    VAEDecoder,
    # Universal Latent Space
    UniversalLatentSpace,
)

__version__ = "1.0.3"
__author__ = "Mike Amega"
__license__ = "Proprietary"

__all__ = [
    # Base classes
    "CognitiveConfig",
    "CognitiveModule",
    "MemoryModule",
    "TemporalModule",
    "WorldModelModule",
    "CognitivePreTrainedModel",
    "register_cognitive_model",
    # Checkpoint
    "remap_checkpoint_keys",
    "validate_checkpoint",
    "save_cognitive_checkpoint",
    "load_cognitive_checkpoint",
    # Utils
    "setup_environment",
    "get_device",
    "get_optimal_dtype",
    "get_memory_info",
    "clear_memory",
    "estimate_model_memory",
    "print_model_info",
    "print_training_progress",
    "get_hf_token",
    # Training
    "CognitiveTrainingConfig",
    "CognitiveTrainer",
    "prepare_dataset",
    "create_instruction_dataset",
    "quick_train",
    "CognitiveStateCallback",
    # Modules - Normalization
    "RMSNorm",
    # Modules - Positional Encoding
    "RotaryEmbedding",
    "SinusoidalPositionalEncoding",
    # Modules - Attention
    "GroupedQueryAttention",
    "CrossAttention",
    # Modules - Feedforward
    "SwiGLU",
    "MLP",
    # Modules - MoE
    "Expert",
    "SparseMoE",
    # Modules - Memory
    "ContrastiveLPOL",
    "MultiScaleMemory",
    "EpisodicMemory",
    # Modules - World Model
    "WorldBuffer",
    "MultiWorldBuffer",
    # Modules - Internal State
    "NonVerbalTension",
    "InternalState",
    # Modules - Dream & Self-Trace
    "DreamPhase",
    "SelfTrace",
    # Modules - Neurogenesis
    "NeurogenesisLayer",
    # Modules - EARCP
    "EARCPModule",
    # Modules - VAE
    "VAEEncoder",
    "VAEDecoder",
    # Modules - Universal Latent Space
    "UniversalLatentSpace",
]
