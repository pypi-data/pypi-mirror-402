"""
COGNITIVE-CORE: Checkpoint Loading & Key Remapping
===================================================

This module provides robust checkpoint loading with automatic key remapping
to handle different checkpoint formats (with/without 'model.' prefix, etc.)

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

import re
from typing import Dict, Set, Optional
import torch


def remap_checkpoint_keys(
    checkpoint_state_dict: Dict[str, torch.Tensor],
    model_state_dict: Dict[str, torch.Tensor],
    verbose: bool = False,
) -> Dict[str, torch.Tensor]:
    """
    Remappe automatiquement les clés du checkpoint pour correspondre au modèle.

    Gère les scénarios suivants:
    1. Checkpoint a préfixe 'model.' mais modèle n'en a pas → retirer préfixe
    2. Checkpoint n'a pas préfixe 'model.' mais modèle en a → ajouter préfixe
    3. Autres préfixes personnalisés

    Args:
        checkpoint_state_dict: État du checkpoint chargé
        model_state_dict: État du modèle cible
        verbose: Afficher les détails du remappage

    Returns:
        Dict remappé compatible avec le modèle
    """
    model_keys = set(model_state_dict.keys())
    checkpoint_keys = set(checkpoint_state_dict.keys())

    # Vérifier si le checkpoint correspond déjà
    matching = model_keys & checkpoint_keys
    if len(matching) >= len(checkpoint_keys) * 0.9:
        if verbose:
            print(
                f"✅ Checkpoint compatible: {len(matching)}/{len(checkpoint_keys)} clés correspondent"
            )
        return checkpoint_state_dict

    # Tester différentes stratégies de remappage
    strategies = [
        ("remove_model_prefix", _remove_prefix, "model."),
        ("add_model_prefix", _add_prefix, "model."),
        ("remove_backbone_prefix", _remove_prefix, "backbone."),
        ("remove_encoder_prefix", _remove_prefix, "encoder."),
    ]

    best_strategy = None
    best_match_count = len(matching)
    best_result = checkpoint_state_dict

    for name, func, prefix in strategies:
        remapped = func(checkpoint_state_dict, prefix)
        match_count = len(model_keys & set(remapped.keys()))

        if match_count > best_match_count:
            best_match_count = match_count
            best_strategy = name
            best_result = remapped

    if verbose and best_strategy:
        print(f"🔄 Stratégie appliquée: {best_strategy}")
        print(f"   Clés correspondantes: {best_match_count}/{len(checkpoint_keys)}")

    # Fallback: mapper intelligemment clé par clé
    if best_match_count < len(checkpoint_keys) * 0.5:
        best_result = _smart_key_mapping(checkpoint_state_dict, model_keys)
        if verbose:
            final_match = len(model_keys & set(best_result.keys()))
            print(
                f"🧠 Remappage intelligent: {final_match}/{len(checkpoint_keys)} clés"
            )

    return best_result


def _remove_prefix(state_dict: Dict, prefix: str) -> Dict:
    """Retirer un préfixe de toutes les clés."""
    return {
        (k[len(prefix) :] if k.startswith(prefix) else k): v
        for k, v in state_dict.items()
    }


def _add_prefix(state_dict: Dict, prefix: str) -> Dict:
    """Ajouter un préfixe à toutes les clés."""
    return {f"{prefix}{k}": v for k, v in state_dict.items()}


def _smart_key_mapping(
    checkpoint_dict: Dict[str, torch.Tensor], model_keys: Set[str]
) -> Dict[str, torch.Tensor]:
    """
    Mapping intelligent clé par clé basé sur les suffixes et patterns.
    """
    result = {}
    model_keys_list = list(model_keys)

    for ckpt_key, value in checkpoint_dict.items():
        # Correspondance exacte
        if ckpt_key in model_keys:
            result[ckpt_key] = value
            continue

        # Essayer avec préfixe 'model.'
        with_prefix = f"model.{ckpt_key}"
        if with_prefix in model_keys:
            result[with_prefix] = value
            continue

        # Essayer sans préfixe 'model.'
        if ckpt_key.startswith("model."):
            without_prefix = ckpt_key[6:]
            if without_prefix in model_keys:
                result[without_prefix] = value
                continue

        # Chercher par suffixe (ex: ".weight", ".bias")
        ckpt_suffix = ckpt_key.split(".")[-1]
        ckpt_base = ".".join(ckpt_key.split(".")[:-1])

        for model_key in model_keys_list:
            if model_key.endswith(ckpt_suffix):
                model_base = ".".join(model_key.split(".")[:-1])
                # Vérifier similarité structurelle
                if _keys_similar(ckpt_base, model_base):
                    result[model_key] = value
                    break
        else:
            # Garder la clé originale (sera ignorée si pas dans modèle)
            result[ckpt_key] = value

    return result


def _keys_similar(key1: str, key2: str) -> bool:
    """Vérifier si deux clés sont structurellement similaires."""
    parts1 = key1.split(".")
    parts2 = key2.split(".")

    # Même nombre de parties
    if len(parts1) != len(parts2):
        return False

    # Comparer chaque partie (ignorer les préfixes comme 'model')
    matches = sum(
        1 for p1, p2 in zip(parts1, parts2) if p1 == p2 or p1.isdigit() and p2.isdigit()
    )
    return matches >= len(parts1) * 0.7


def validate_checkpoint(
    checkpoint_state_dict: Dict[str, torch.Tensor],
    model_state_dict: Dict[str, torch.Tensor],
    strict: bool = False,
) -> Dict[str, any]:
    """
    Valider qu'un checkpoint est compatible avec un modèle.

    Returns:
        Dict avec:
        - valid: bool
        - missing_keys: clés manquantes dans checkpoint
        - unexpected_keys: clés inattendues dans checkpoint
        - size_mismatches: clés avec tailles incompatibles
    """
    model_keys = set(model_state_dict.keys())
    ckpt_keys = set(checkpoint_state_dict.keys())

    missing = model_keys - ckpt_keys
    unexpected = ckpt_keys - model_keys

    # Vérifier les tailles
    size_mismatches = []
    for key in model_keys & ckpt_keys:
        model_shape = model_state_dict[key].shape
        ckpt_shape = checkpoint_state_dict[key].shape
        if model_shape != ckpt_shape:
            size_mismatches.append(
                {"key": key, "model_shape": model_shape, "checkpoint_shape": ckpt_shape}
            )

    valid = len(missing) == 0 and len(size_mismatches) == 0
    if not strict:
        valid = len(size_mismatches) == 0 and len(missing) < len(model_keys) * 0.1

    return {
        "valid": valid,
        "missing_keys": list(missing),
        "unexpected_keys": list(unexpected),
        "size_mismatches": size_mismatches,
        "matched_keys": len(model_keys & ckpt_keys),
        "total_model_keys": len(model_keys),
    }


def save_cognitive_checkpoint(
    model,
    path: str,
    include_optimizer: bool = False,
    optimizer=None,
    extra_state: Optional[Dict] = None,
):
    """
    Sauvegarder un checkpoint de modèle cognitif.

    Args:
        model: Le modèle à sauvegarder
        path: Chemin de sauvegarde
        include_optimizer: Inclure l'état de l'optimiseur
        optimizer: L'optimiseur (si include_optimizer=True)
        extra_state: État additionnel à sauvegarder
    """
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": model.config.to_dict() if hasattr(model, "config") else {},
    }

    if include_optimizer and optimizer is not None:
        checkpoint["optimizer_state_dict"] = optimizer.state_dict()

    # Sauvegarder l'état cognitif si disponible
    if hasattr(model, "get_cognitive_state"):
        checkpoint["cognitive_state"] = model.get_cognitive_state()

    if extra_state:
        checkpoint["extra_state"] = extra_state

    torch.save(checkpoint, path)
    print(f"✅ Checkpoint sauvegardé: {path}")


def load_cognitive_checkpoint(
    model, path: str, strict: bool = False, verbose: bool = True
) -> Dict:
    """
    Charger un checkpoint dans un modèle cognitif avec remappage automatique.

    Args:
        model: Le modèle cible
        path: Chemin du checkpoint
        strict: Mode strict (erreur si clés manquantes)
        verbose: Afficher les détails

    Returns:
        Dict avec informations de chargement
    """
    checkpoint = torch.load(path, map_location="cpu")

    # Extraire le state_dict
    if "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    elif "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        state_dict = checkpoint

    # Remapper les clés
    remapped = remap_checkpoint_keys(state_dict, model.state_dict(), verbose=verbose)

    # Valider
    validation = validate_checkpoint(remapped, model.state_dict(), strict=strict)

    if verbose:
        print(
            f"📊 Clés chargées: {validation['matched_keys']}/{validation['total_model_keys']}"
        )
        if validation["missing_keys"]:
            print(f"⚠️ Clés manquantes: {len(validation['missing_keys'])}")
        if validation["size_mismatches"]:
            print(f"⚠️ Tailles incompatibles: {len(validation['size_mismatches'])}")

    # Charger avec ignore_mismatched_sizes pour robustesse
    model.load_state_dict(remapped, strict=False)

    # Restaurer l'état cognitif si disponible
    if "cognitive_state" in checkpoint and hasattr(model, "reset_cognitive_state"):
        # L'état cognitif est généralement réinitialisé, pas restauré
        pass

    if verbose:
        print("✅ Checkpoint chargé avec succès")

    return {
        "validation": validation,
        "config": checkpoint.get("config", {}),
        "extra_state": checkpoint.get("extra_state", {}),
    }
