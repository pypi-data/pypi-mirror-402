"""
COGNITIVE-CORE: Utility Functions
==================================

Common utilities for cognitive model development, including:
- Environment setup for Kaggle/Colab
- Device detection
- Memory optimization helpers
- Logging utilities

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

import os
import sys
import torch
import warnings
from typing import Optional, Dict, Any


# ==============================================================================
# ENVIRONNEMENT & CACHE
# ==============================================================================


def setup_environment(cache_dir: Optional[str] = None) -> str:
    """
    Configure l'environnement pour Kaggle/Colab/Local.

    Résout les problèmes de:
    - Read-only file system sur Kaggle
    - Chemins de cache HuggingFace

    Args:
        cache_dir: Répertoire cache personnalisé (optionnel)

    Returns:
        Chemin du répertoire cache configuré
    """
    if cache_dir is None:
        # Détecter l'environnement
        if os.path.exists("/kaggle"):
            cache_dir = "/kaggle/working/.cache"
        elif os.path.exists("/content"):  # Colab
            cache_dir = "/content/.cache"
        else:
            cache_dir = os.path.expanduser("~/.cache/cognitive")

    # Créer le répertoire
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(os.path.join(cache_dir, "datasets"), exist_ok=True)

    # Configurer les variables d'environnement
    os.environ["HF_HOME"] = cache_dir
    os.environ["TRANSFORMERS_CACHE"] = cache_dir
    os.environ["HF_DATASETS_CACHE"] = os.path.join(cache_dir, "datasets")

    # Désactiver les warnings non critiques
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

    return cache_dir


def get_device(prefer_gpu: bool = True) -> torch.device:
    """
    Détecte et retourne le meilleur device disponible.

    Args:
        prefer_gpu: Préférer GPU si disponible

    Returns:
        torch.device configuré
    """
    if prefer_gpu and torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"🔧 GPU: {gpu_name} ({gpu_mem:.1f} GB)")
    elif (
        prefer_gpu
        and hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        device = torch.device("mps")
        print("🔧 Apple MPS")
    else:
        device = torch.device("cpu")
        print("🔧 CPU")

    return device


def get_optimal_dtype(device: torch.device) -> torch.dtype:
    """
    Retourne le dtype optimal pour le device.

    Args:
        device: Le device cible

    Returns:
        torch.dtype optimal (float16 pour GPU, float32 pour CPU)
    """
    if device.type == "cuda":
        # Vérifier support BF16
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    return torch.float32


# ==============================================================================
# MÉMOIRE & OPTIMISATION
# ==============================================================================


def get_memory_info() -> Dict[str, float]:
    """
    Retourne les informations mémoire (GPU si disponible).

    Returns:
        Dict avec allocated, reserved, free en GB
    """
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        reserved = torch.cuda.memory_reserved() / 1e9
        total = torch.cuda.get_device_properties(0).total_memory / 1e9
        return {
            "allocated_gb": allocated,
            "reserved_gb": reserved,
            "free_gb": total - allocated,
            "total_gb": total,
        }
    return {"allocated_gb": 0, "reserved_gb": 0, "free_gb": 0, "total_gb": 0}


def clear_memory():
    """Libère la mémoire GPU si possible."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def estimate_model_memory(model, dtype: torch.dtype = torch.float32) -> float:
    """
    Estime la mémoire nécessaire pour un modèle.

    Args:
        model: Le modèle PyTorch
        dtype: Le dtype utilisé

    Returns:
        Estimation en GB
    """
    param_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_bytes = sum(b.numel() * b.element_size() for b in model.buffers())

    # Facteur pour activations (estimation: 2x les paramètres)
    activation_factor = 2.0

    total_bytes = (param_bytes + buffer_bytes) * activation_factor

    # Ajuster selon dtype
    if dtype in (torch.float16, torch.bfloat16):
        total_bytes *= 0.5

    return total_bytes / 1e9


# ==============================================================================
# LOGGING & AFFICHAGE
# ==============================================================================


def print_model_info(model, show_params: bool = True):
    """
    Affiche les informations du modèle.

    Args:
        model: Le modèle à analyser
        show_params: Afficher le détail des paramètres
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"\n📊 MODÈLE: {model.__class__.__name__}")
    print(f"   Total paramètres: {total_params:,}")
    print(f"   Paramètres entraînables: {trainable_params:,}")
    print(f"   Mémoire estimée: {estimate_model_memory(model):.2f} GB")

    if show_params and hasattr(model, "config"):
        print(f"\n   Configuration:")
        for key in ["d_model", "n_layers", "n_heads", "vocab_size"]:
            if hasattr(model.config, key):
                print(f"   - {key}: {getattr(model.config, key)}")


def print_training_progress(
    step: int,
    total_steps: int,
    loss: float,
    lr: Optional[float] = None,
    extras: Optional[Dict[str, float]] = None,
):
    """
    Affiche la progression d'entraînement.

    Args:
        step: Étape actuelle
        total_steps: Nombre total d'étapes
        loss: Valeur de la loss
        lr: Learning rate actuel
        extras: Métriques additionnelles
    """
    progress = step / total_steps * 100
    msg = f"[{step:>6}/{total_steps}] ({progress:>5.1f}%) | Loss: {loss:.4f}"

    if lr is not None:
        msg += f" | LR: {lr:.2e}"

    if extras:
        for key, val in extras.items():
            msg += f" | {key}: {val:.4f}"

    print(msg)


# ==============================================================================
# TOKEN HUGGINGFACE
# ==============================================================================


def get_hf_token() -> Optional[str]:
    """
    Récupère le token HuggingFace depuis différentes sources.

    Ordre de recherche:
    1. Variable d'environnement HF_TOKEN
    2. Secrets Kaggle
    3. Secrets Colab
    4. Token local HuggingFace CLI

    Returns:
        Token ou None si non trouvé
    """
    # Env var
    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    # Kaggle
    try:
        from kaggle_secrets import UserSecretsClient

        token = UserSecretsClient().get_secret("HF_TOKEN")
        if token:
            return token
    except Exception:
        pass

    # Colab
    try:
        from google.colab import userdata

        token = userdata.get("HF_TOKEN")
        if token:
            return token
    except Exception:
        pass

    # Local HuggingFace CLI
    try:
        from huggingface_hub import HfFolder

        token = HfFolder.get_token()
        if token:
            return token
    except Exception:
        pass

    return None
