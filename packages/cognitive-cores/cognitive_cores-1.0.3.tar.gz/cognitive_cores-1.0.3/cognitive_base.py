"""
COGNITIVE-CORE: Base Classes for Cognitive Architectures
=========================================================

This module provides the foundational classes for building cognitive AI models
that follow the Ame Web Studio standard. All cognitive models (vision, language,
world model, multimodal) should inherit from these base classes.

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod

from transformers import PreTrainedModel, PretrainedConfig


# ==============================================================================
# CONFIGURATION DE BASE
# ==============================================================================


class CognitiveConfig(PretrainedConfig):
    """
    Configuration de base pour tous les modèles cognitifs.

    Tous les modèles cognitifs (vision, language, world, multimodal) doivent
    hériter de cette configuration pour garantir la compatibilité.
    """

    model_type = "cognitive"

    def __init__(
        self,
        # Dimensions de base
        d_model: int = 512,
        d_ff: int = 2048,
        n_layers: int = 12,
        n_heads: int = 8,
        dropout: float = 0.1,
        # Modules cognitifs (peuvent être activés/désactivés)
        use_memory: bool = True,
        use_temporal: bool = True,
        use_synaptic: bool = True,
        use_dream: bool = True,
        use_world_model: bool = True,
        use_neurogenesis: bool = True,
        # Mémoire
        memory_size: int = 8192,
        short_term_dim: int = 512,
        long_term_dim: int = 256,
        # États internes
        internal_state_dim: int = 128,
        latent_state_dim: int = 768,
        # Meta
        version: str = "1.0",
        author: str = "Mike Amega",
        license: str = "Proprietary",
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Dimensions
        self.d_model = d_model
        self.hidden_size = d_model  # Alias HuggingFace
        self.d_ff = d_ff
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.dropout = dropout

        # Modules cognitifs
        self.use_memory = use_memory
        self.use_temporal = use_temporal
        self.use_synaptic = use_synaptic
        self.use_dream = use_dream
        self.use_world_model = use_world_model
        self.use_neurogenesis = use_neurogenesis

        # Mémoire
        self.memory_size = memory_size
        self.short_term_dim = short_term_dim
        self.long_term_dim = long_term_dim

        # États
        self.internal_state_dim = internal_state_dim
        self.latent_state_dim = latent_state_dim

        # Meta
        self.version = version
        self.author = author
        self.license = license

    @property
    def head_dim(self) -> int:
        return self.d_model // self.n_heads


# ==============================================================================
# MODULES COGNITIFS ABSTRAITS
# ==============================================================================


class CognitiveModule(nn.Module, ABC):
    """
    Classe de base abstraite pour tous les modules cognitifs.

    Chaque module cognitif doit implémenter:
    - forward(): traitement principal
    - reset_state(): réinitialisation des états internes
    - get_state(): récupérer l'état courant
    """

    def __init__(self, config: CognitiveConfig):
        super().__init__()
        self.config = config

    @abstractmethod
    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        """Traitement principal du module."""
        pass

    @abstractmethod
    def reset_state(self):
        """Réinitialiser les états internes du module."""
        pass

    def get_state(self) -> Dict[str, torch.Tensor]:
        """Récupérer l'état courant (pour sauvegarde/debug)."""
        return {}


class MemoryModule(CognitiveModule):
    """Interface pour les modules de mémoire."""

    @abstractmethod
    def store(self, key: torch.Tensor, value: torch.Tensor):
        """Stocker une information en mémoire."""
        pass

    @abstractmethod
    def retrieve(self, query: torch.Tensor, k: int = 1) -> torch.Tensor:
        """Récupérer les k informations les plus pertinentes."""
        pass


class TemporalModule(CognitiveModule):
    """Interface pour les modules temporels/prédictifs."""

    @abstractmethod
    def predict(self, state: torch.Tensor, horizon: int = 1) -> torch.Tensor:
        """Prédire l'état futur à l'horizon donné."""
        pass


class WorldModelModule(CognitiveModule):
    """Interface pour les modèles du monde."""

    @abstractmethod
    def update(self, observation: torch.Tensor) -> Dict[str, float]:
        """Mettre à jour le modèle du monde avec une observation."""
        pass

    @abstractmethod
    def imagine(self, action: torch.Tensor) -> torch.Tensor:
        """Imaginer l'effet d'une action."""
        pass


# ==============================================================================
# MODÈLE COGNITIF DE BASE
# ==============================================================================


class CognitivePreTrainedModel(PreTrainedModel):
    """
    Classe de base pour tous les modèles cognitifs HuggingFace-compatibles.

    Fournit:
    - Remappage automatique des clés de checkpoint
    - Gestion des modules cognitifs optionnels
    - Méthodes d'initialisation standardisées
    """

    config_class = CognitiveConfig
    base_model_prefix = "cognitive"
    supports_gradient_checkpointing = False  # Incompatible avec architecture cognitive

    # Clés à ignorer lors du chargement (buffers dynamiques)
    _keys_to_ignore_on_load_missing = [
        r".*\.state$",
        r".*\.history$",
        r".*\.buffer$",
        r".*rope\..*_cache",
        r".*rope\.inv_freq",
    ]

    def _init_weights(self, module):
        """Initialisation standard des poids."""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def _load_from_state_dict(
        self,
        state_dict,
        prefix,
        local_metadata,
        strict,
        missing_keys,
        unexpected_keys,
        error_msgs,
    ):
        """
        Remappage automatique des clés de checkpoint.

        Gère les différences de préfixes entre formats de checkpoint
        (ex: avec/sans 'model.' prefix).
        """
        from .cognitive_checkpoint import remap_checkpoint_keys

        # Remapper les clés si nécessaire
        remapped = remap_checkpoint_keys(state_dict, self.state_dict())

        # Appeler l'implémentation parent
        super()._load_from_state_dict(
            remapped,
            prefix,
            local_metadata,
            strict,
            missing_keys,
            unexpected_keys,
            error_msgs,
        )

    def get_cognitive_state(self) -> Dict[str, Any]:
        """Récupérer l'état de tous les modules cognitifs."""
        state = {}
        for name, module in self.named_modules():
            if isinstance(module, CognitiveModule):
                state[name] = module.get_state()
        return state

    def reset_cognitive_state(self):
        """Réinitialiser l'état de tous les modules cognitifs."""
        for module in self.modules():
            if isinstance(module, CognitiveModule):
                module.reset_state()


# ==============================================================================
# UTILITAIRES D'ENREGISTREMENT AUTO
# ==============================================================================


def register_cognitive_model(config_class, model_class):
    """
    Enregistrer un modèle cognitif pour utilisation avec AutoModel.

    Usage:
        register_cognitive_model(MyConfig, MyModel)
        # Puis: AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)
    """
    from transformers import AutoConfig, AutoModel

    AutoConfig.register(config_class.model_type, config_class)
    AutoModel.register(config_class, model_class)
