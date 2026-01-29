"""
COGNITIVE-CORE: Training Utilities
====================================

Standardized training utilities for cognitive models, including:
- Training configurations
- Trainer wrappers
- Dataset preparation helpers
- Progress tracking

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

import os
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


# ==============================================================================
# CONFIGURATION D'ENTRAÎNEMENT
# ==============================================================================


@dataclass
class CognitiveTrainingConfig:
    """
    Configuration standard pour l'entraînement de modèles cognitifs.
    """

    # Output
    output_dir: str = "./cognitive-output"

    # Training params
    num_epochs: int = 1
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 1e-5
    warmup_steps: int = 100
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0

    # Sequence
    max_seq_len: int = 2048  # IMPORTANT: >= 2048 pour modules cognitifs

    # Precision
    use_fp16: bool = True
    use_bf16: bool = False

    # Logging
    logging_steps: int = 10
    save_steps: int = 200
    save_total_limit: int = 2

    # Hub
    push_to_hub: bool = False
    hub_model_id: Optional[str] = None
    hub_private: bool = True

    # Device
    device: Optional[str] = None  # auto-detected if None

    def __post_init__(self):
        os.makedirs(self.output_dir, exist_ok=True)


# ==============================================================================
# PRÉPARATION DES DONNÉES
# ==============================================================================


def prepare_dataset(
    dataset,
    tokenizer,
    text_column: str = "text",
    max_length: int = 2048,
    num_proc: int = 4,
):
    """
    Prépare un dataset pour l'entraînement d'un modèle cognitif.

    Args:
        dataset: Dataset HuggingFace
        tokenizer: Tokenizer du modèle
        text_column: Nom de la colonne contenant le texte
        max_length: Longueur maximale des séquences
        num_proc: Nombre de processus pour le mapping

    Returns:
        Dataset tokenisé prêt pour l'entraînement
    """

    def tokenize_function(examples):
        texts = examples[text_column]
        if not isinstance(texts, list):
            texts = [texts]

        return tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors=None,
        )

    # Supprimer les colonnes originales
    columns_to_remove = dataset.column_names
    if isinstance(columns_to_remove, dict):
        columns_to_remove = columns_to_remove.get("train", [])

    tokenized = dataset.map(
        tokenize_function,
        batched=True,
        num_proc=num_proc,
        remove_columns=columns_to_remove,
    )

    tokenized.set_format(type="torch")
    return tokenized


def create_instruction_dataset(
    examples: List[Dict[str, str]],
    tokenizer,
    max_length: int = 2048,
    instruction_template: str = "### Instruction:\n{instruction}\n\n### Response:\n{response}",
):
    """
    Crée un dataset d'instructions à partir d'exemples.

    Args:
        examples: Liste de dicts avec 'instruction' et 'response'
        tokenizer: Tokenizer du modèle
        max_length: Longueur maximale
        instruction_template: Template de formatage

    Returns:
        Dataset tokenisé
    """
    from datasets import Dataset

    formatted = []
    for ex in examples:
        text = instruction_template.format(
            instruction=ex.get("instruction", ""), response=ex.get("response", "")
        )
        formatted.append({"text": text})

    dataset = Dataset.from_list(formatted)
    return prepare_dataset(dataset, tokenizer, "text", max_length)


# ==============================================================================
# TRAINER WRAPPER
# ==============================================================================


class CognitiveTrainer:
    """
    Trainer simplifié pour modèles cognitifs.

    Wrapper autour du Trainer HuggingFace avec configuration optimisée
    pour les architectures cognitives.
    """

    def __init__(
        self,
        model,
        tokenizer,
        train_dataset,
        config: CognitiveTrainingConfig,
        eval_dataset=None,
        callbacks: Optional[List] = None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.config = config
        self.callbacks = callbacks or []

        # Configurer tokenizer
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        self._setup_trainer()

    def _setup_trainer(self):
        """Configure le Trainer HuggingFace."""
        from transformers import (
            Trainer,
            TrainingArguments,
            DataCollatorForLanguageModeling,
        )

        # Déterminer device
        if self.config.device:
            device = self.config.device
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

        # Arguments d'entraînement
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            overwrite_output_dir=True,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            weight_decay=self.config.weight_decay,
            max_grad_norm=self.config.max_grad_norm,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            save_total_limit=self.config.save_total_limit,
            fp16=self.config.use_fp16 and device == "cuda",
            bf16=self.config.use_bf16 and device == "cuda",
            push_to_hub=self.config.push_to_hub,
            hub_model_id=self.config.hub_model_id,
            hub_private_repo=self.config.hub_private,
            report_to="none",
            remove_unused_columns=False,
            dataloader_num_workers=0,  # Évite problèmes sur certains environnements
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer, mlm=False
        )

        # Créer le trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
            callbacks=self.callbacks,
        )

    def train(self, resume_from_checkpoint: Optional[str] = None):
        """
        Lance l'entraînement.

        Args:
            resume_from_checkpoint: Chemin pour reprendre l'entraînement

        Returns:
            Résultats de l'entraînement
        """
        print("\n🚀 ENTRAÎNEMENT COGNITIF")
        print("=" * 60)

        try:
            result = self.trainer.train(resume_from_checkpoint=resume_from_checkpoint)
            print("=" * 60)
            print("✅ Entraînement terminé!")
            return result
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback

            traceback.print_exc()
            return None

    def save(self, output_dir: Optional[str] = None):
        """Sauvegarde le modèle et tokenizer."""
        save_dir = output_dir or self.config.output_dir
        self.trainer.save_model(save_dir)
        self.tokenizer.save_pretrained(save_dir)
        print(f"💾 Modèle sauvegardé: {save_dir}")

    def push_to_hub(self, repo_id: Optional[str] = None):
        """Push le modèle vers HuggingFace Hub."""
        if repo_id:
            self.config.hub_model_id = repo_id

        try:
            self.trainer.push_to_hub()
            print(f"📤 Modèle pushé: {self.config.hub_model_id}")
        except Exception as e:
            print(f"⚠️ Erreur push: {e}")


# ==============================================================================
# CALLBACKS PERSONNALISÉS
# ==============================================================================


class CognitiveStateCallback:
    """
    Callback pour monitorer l'état des modules cognitifs pendant l'entraînement.
    """

    def __init__(self, log_every: int = 100):
        self.log_every = log_every
        self.step = 0

    def on_step_end(self, args, state, control, model=None, **kwargs):
        self.step += 1

        if self.step % self.log_every == 0 and model is not None:
            if hasattr(model, "get_cognitive_state"):
                cog_state = model.get_cognitive_state()
                print(f"\n📊 État cognitif (step {self.step}):")
                for name, state_dict in cog_state.items():
                    if state_dict:
                        print(f"   {name}: {len(state_dict)} buffers")


# ==============================================================================
# QUICK TRAIN FUNCTION
# ==============================================================================


def quick_train(
    model,
    tokenizer,
    texts: List[str],
    output_dir: str = "./quick-train-output",
    num_epochs: int = 1,
    max_seq_len: int = 2048,
    learning_rate: float = 1e-5,
    push_to_hub: bool = False,
    hub_model_id: Optional[str] = None,
):
    """
    Entraînement rapide avec configuration minimale.

    Args:
        model: Modèle à entraîner
        tokenizer: Tokenizer
        texts: Liste de textes d'entraînement
        output_dir: Répertoire de sortie
        num_epochs: Nombre d'époques
        max_seq_len: Longueur max des séquences
        learning_rate: Taux d'apprentissage
        push_to_hub: Pusher vers HuggingFace
        hub_model_id: ID du repo HuggingFace

    Returns:
        Résultats de l'entraînement
    """
    from datasets import Dataset

    # Créer dataset
    dataset = Dataset.from_dict({"text": texts})
    tokenized = prepare_dataset(dataset, tokenizer, "text", max_seq_len)

    # Config
    config = CognitiveTrainingConfig(
        output_dir=output_dir,
        num_epochs=num_epochs,
        max_seq_len=max_seq_len,
        learning_rate=learning_rate,
        push_to_hub=push_to_hub,
        hub_model_id=hub_model_id,
    )

    # Trainer
    trainer = CognitiveTrainer(model, tokenizer, tokenized, config)
    result = trainer.train()

    if result:
        trainer.save()

    return result
