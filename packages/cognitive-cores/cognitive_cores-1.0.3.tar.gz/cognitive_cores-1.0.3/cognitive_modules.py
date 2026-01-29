"""
COGNITIVE-CORE: Reusable Cognitive Modules
===========================================

Complete library of cognitive modules that can be composed to build
any cognitive model: vision, language, world model, multimodal, etc.

All modules are agnostic and can be configured for different use cases.

Copyright © 2026 Mike Amega (Logo) - Ame Web Studio
License: Proprietary - All Rights Reserved
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from abc import ABC, abstractmethod

from .cognitive_base import CognitiveConfig, CognitiveModule


# ==============================================================================
# SECTION 1: NORMALIZATION LAYERS
# ==============================================================================


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization - More efficient than LayerNorm."""

    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        rms = torch.sqrt(torch.mean(x**2, dim=-1, keepdim=True) + self.eps)
        return x / rms * self.weight


# ==============================================================================
# SECTION 2: POSITIONAL ENCODINGS
# ==============================================================================


class RotaryEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE) with scaling support."""

    def __init__(
        self, dim: int, max_seq_len: int = 4096, base: int = 10000, scaling: float = 1.0
    ):
        super().__init__()
        self.dim = dim
        self.scaling = scaling

        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)

        t = torch.arange(max_seq_len).float() / scaling
        freqs = torch.einsum("i,j->ij", t, inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer("cos_cache", emb.cos()[None, None, :, :])
        self.register_buffer("sin_cache", emb.sin()[None, None, :, :])

    def forward(
        self, q: torch.Tensor, k: torch.Tensor, seq_len: int, offset: int = 0
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        cos = self.cos_cache[:, :, offset : offset + seq_len, :].to(q.dtype)
        sin = self.sin_cache[:, :, offset : offset + seq_len, :].to(q.dtype)
        q_rot = (q * cos) + (self._rotate_half(q) * sin)
        k_rot = (k * cos) + (self._rotate_half(k) * sin)
        return q_rot, k_rot

    def _rotate_half(self, x: torch.Tensor) -> torch.Tensor:
        x1, x2 = x[..., : x.shape[-1] // 2], x[..., x.shape[-1] // 2 :]
        return torch.cat([-x2, x1], dim=-1)


class SinusoidalPositionalEncoding(nn.Module):
    """Classical sinusoidal positional encoding."""

    def __init__(self, d_model: int, max_seq_len: int = 4096, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        pe = torch.zeros(max_seq_len, d_model)
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1)]
        return self.dropout(x)


# ==============================================================================
# SECTION 3: ATTENTION MECHANISMS
# ==============================================================================


class GroupedQueryAttention(nn.Module):
    """Grouped Query Attention (GQA) with RoPE and KV-Cache support."""

    def __init__(
        self,
        d_model: int,
        n_heads: int = 8,
        n_kv_heads: int = 4,
        max_seq_len: int = 4096,
        dropout: float = 0.1,
        use_rope: bool = True,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = d_model // n_heads
        self.n_rep = n_heads // n_kv_heads
        self.scale = self.head_dim**-0.5

        self.q_proj = nn.Linear(d_model, n_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(n_heads * self.head_dim, d_model, bias=False)

        self.dropout = nn.Dropout(dropout)
        self.rope = RotaryEmbedding(self.head_dim, max_seq_len) if use_rope else None

    def _repeat_kv(self, x: torch.Tensor) -> torch.Tensor:
        if self.n_rep == 1:
            return x
        B, n_kv, T, D = x.shape
        return (
            x[:, :, None, :, :]
            .expand(B, n_kv, self.n_rep, T, D)
            .reshape(B, self.n_heads, T, D)
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple]]:
        B, T, C = x.shape

        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1, 2)

        offset = 0
        if kv_cache is not None:
            k_cache, v_cache = kv_cache
            offset = k_cache.size(2)
            k = torch.cat([k_cache, k], dim=2)
            v = torch.cat([v_cache, v], dim=2)

        if self.rope is not None:
            q, _ = self.rope(q, q, T, offset)
            _, k = self.rope(k, k, k.size(2), 0)

        k = self._repeat_kv(k)
        v = self._repeat_kv(v)

        attn = (q @ k.transpose(-2, -1)) * self.scale
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))

        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        out = (attn @ v).transpose(1, 2).reshape(B, T, -1)
        out = self.o_proj(out)

        new_cache = None
        if use_cache:
            k_to_cache = (
                self.k_proj(x)
                .view(B, T, self.n_kv_heads, self.head_dim)
                .transpose(1, 2)
            )
            v_to_cache = (
                self.v_proj(x)
                .view(B, T, self.n_kv_heads, self.head_dim)
                .transpose(1, 2)
            )
            if kv_cache is not None:
                k_to_cache = torch.cat([kv_cache[0], k_to_cache], dim=2)
                v_to_cache = torch.cat([kv_cache[1], v_to_cache], dim=2)
            new_cache = (k_to_cache, v_to_cache)

        return out, new_cache


class CrossAttention(nn.Module):
    """Cross-attention for multimodal fusion."""

    def __init__(self, d_model: int, n_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.scale = self.head_dim**-0.5

        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.o_proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,
        key_value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        B, T, C = query.shape
        _, S, _ = key_value.shape

        q = self.q_proj(query).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = (
            self.k_proj(key_value)
            .view(B, S, self.n_heads, self.head_dim)
            .transpose(1, 2)
        )
        v = (
            self.v_proj(key_value)
            .view(B, S, self.n_heads, self.head_dim)
            .transpose(1, 2)
        )

        attn = (q @ k.transpose(-2, -1)) * self.scale
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))

        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        out = (attn @ v).transpose(1, 2).reshape(B, T, -1)
        return self.o_proj(out)


# ==============================================================================
# SECTION 4: FEEDFORWARD NETWORKS
# ==============================================================================


class SwiGLU(nn.Module):
    """SwiGLU activation - better than GELU for transformers."""

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        hidden = int(d_ff * 2 / 3)
        hidden = ((hidden + 63) // 64) * 64  # Align to 64

        self.w1 = nn.Linear(d_model, hidden, bias=False)
        self.w2 = nn.Linear(hidden, d_model, bias=False)
        self.w3 = nn.Linear(d_model, hidden, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.w2(F.silu(self.w1(x)) * self.w3(x)))


class MLP(nn.Module):
    """Standard MLP with GELU activation."""

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ==============================================================================
# SECTION 5: SPARSE MIXTURE OF EXPERTS
# ==============================================================================


class Expert(nn.Module):
    """Single expert module."""

    def __init__(self, d_model: int, d_ff: int, expert_type: str = "general"):
        super().__init__()
        self.expert_type = expert_type
        self.ffn = SwiGLU(d_model, d_ff)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.ffn(x)


class SparseMoE(nn.Module):
    """Sparse Mixture of Experts with Top-K routing."""

    def __init__(
        self,
        d_model: int,
        d_ff: int,
        num_experts: int = 8,
        top_k: int = 2,
        expert_types: Optional[List[str]] = None,
        aux_loss_weight: float = 0.01,
    ):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.aux_loss_weight = aux_loss_weight

        if expert_types is None:
            expert_types = ["general"]

        self.router = nn.Linear(d_model, num_experts, bias=False)
        self.experts = nn.ModuleList(
            [
                Expert(d_model, d_ff, expert_types[i % len(expert_types)])
                for i in range(num_experts)
            ]
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, C = x.shape
        x_flat = x.view(-1, C)

        router_logits = self.router(x_flat)
        topk_weights, topk_indices = torch.topk(
            F.softmax(router_logits, dim=-1), self.top_k, dim=-1
        )
        topk_weights = topk_weights / topk_weights.sum(dim=-1, keepdim=True)

        output = torch.zeros_like(x_flat)

        for i, expert in enumerate(self.experts):
            mask = (topk_indices == i).any(dim=-1)
            if not mask.any():
                continue
            expert_weight = torch.where(
                topk_indices == i, topk_weights, torch.zeros_like(topk_weights)
            ).sum(dim=-1)
            expert_out = expert(x_flat[mask])
            output[mask] += expert_out * expert_weight[mask].unsqueeze(-1)

        # Auxiliary load balancing loss
        router_probs = F.softmax(router_logits, dim=-1)
        expert_usage = router_probs.mean(dim=0)
        aux_loss = (
            self.num_experts
            * (expert_usage * expert_usage).sum()
            * self.aux_loss_weight
        )

        return output.view(B, T, C), aux_loss


# ==============================================================================
# SECTION 6: MEMORY SYSTEMS
# ==============================================================================


class ContrastiveLPOL(CognitiveModule):
    """
    LPOL Memory System with configurable knowledge domains.
    Uses contrastive learning for memory retrieval.
    """

    def __init__(
        self,
        d_model: int,
        config: CognitiveConfig,
        domains: Optional[List[str]] = None,
        slots_per_domain: int = 512,
        retrieval_k: int = 8,
    ):
        super().__init__(config)

        if domains is None:
            domains = [
                "semantic",
                "episodic",
                "procedural",
                "spatial",
                "temporal",
                "causal",
                "social",
                "emotional",
                "conceptual",
            ]

        self.domains = domains
        self.k = retrieval_k

        self.memories = nn.ParameterDict(
            {
                domain: nn.Parameter(torch.randn(slots_per_domain, d_model) * 0.01)
                for domain in domains
            }
        )

        self.domain_clf = nn.Sequential(
            nn.Linear(d_model, len(domains) * 2),
            nn.GELU(),
            nn.Linear(len(domains) * 2, len(domains)),
        )

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model * 2, d_model)

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        B, T, C = x.shape

        domain_probs = F.softmax(self.domain_clf(x.mean(dim=1)), dim=-1)
        all_mem = torch.cat([self.memories[d] for d in self.domains], dim=0)

        q = self.q_proj(x)
        k = self.k_proj(all_mem)
        v = self.v_proj(all_mem)

        sim = torch.matmul(q, k.T) / math.sqrt(C)
        topk_sim, topk_idx = torch.topk(sim, min(self.k, all_mem.size(0)), dim=-1)
        weights = F.softmax(topk_sim, dim=-1)
        retrieved = (weights.unsqueeze(-1) * v[topk_idx]).sum(dim=2)
        output = self.out_proj(torch.cat([x, retrieved], dim=-1))

        return {
            "output": output,
            "domain_probs": domain_probs,
            "retrieval_weights": weights,
        }

    def reset_state(self):
        pass

    def update_memory(self, x: torch.Tensor, domain: str, lr: float = 0.01):
        """Online memory update."""
        if domain in self.memories:
            with torch.no_grad():
                mem = self.memories[domain]
                sim = F.cosine_similarity(
                    x.mean(dim=1, keepdim=True), mem.unsqueeze(0), dim=-1
                )
                _, idx = sim.min(dim=-1)
                mem[idx] = (1 - lr) * mem[idx] + lr * x.mean(dim=1)


class MultiScaleMemory(CognitiveModule):
    """Short-term and long-term memory with consolidation."""

    def __init__(
        self,
        d_model: int,
        config: CognitiveConfig,
        short_term_dim: int = 512,
        long_term_dim: int = 256,
        st_decay: float = 0.95,
        lt_decay: float = 0.99,
        consolidation_threshold: float = 0.7,
    ):
        super().__init__(config)

        self.st_decay = st_decay
        self.lt_decay = lt_decay
        self.consolidation_threshold = consolidation_threshold

        # Short-term memory
        self.st_compress = nn.Sequential(
            nn.Linear(d_model, short_term_dim),
            nn.GELU(),
            nn.Linear(short_term_dim, short_term_dim),
        )
        self.st_gate = nn.GRUCell(short_term_dim, short_term_dim)

        # Long-term memory
        self.consolidation = nn.Sequential(
            nn.Linear(short_term_dim + long_term_dim, 256),
            nn.SiLU(),
            nn.Linear(256, 1),
            nn.Sigmoid(),
        )
        self.st_to_lt = nn.Linear(short_term_dim, long_term_dim)
        self.lt_gate = nn.GRUCell(long_term_dim, long_term_dim)

        # Fusion
        self.fusion = nn.Sequential(
            nn.Linear(short_term_dim + long_term_dim, d_model), nn.Tanh()
        )

        # State buffers
        self.register_buffer("st_state", torch.zeros(1, short_term_dim))
        self.register_buffer("lt_state", torch.zeros(1, long_term_dim))

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        B = x.size(0)
        h_compressed = self.st_compress(x.mean(dim=1))

        st_prev = self.st_state.expand(B, -1)
        st_new = self.st_decay * st_prev + (1 - self.st_decay) * self.st_gate(
            h_compressed, st_prev
        )

        lt_prev = self.lt_state.expand(B, -1)
        consolidation_score = self.consolidation(torch.cat([st_new, lt_prev], dim=-1))

        if (consolidation_score > self.consolidation_threshold).any():
            lt_input = self.st_to_lt(st_new)
            lt_new = self.lt_decay * lt_prev + (1 - self.lt_decay) * self.lt_gate(
                lt_input, lt_prev
            )
        else:
            lt_new = lt_prev

        self.st_state = st_new[:1].detach()
        self.lt_state = lt_new[:1].detach()

        fused = self.fusion(torch.cat([st_new, lt_new], dim=-1))

        return {
            "st": st_new,
            "lt": lt_new,
            "fused": fused,
            "consolidation_score": consolidation_score.mean().item(),
        }

    def reset_state(self):
        self.st_state.zero_()
        self.lt_state.zero_()


class EpisodicMemory(CognitiveModule):
    """Episodic memory for experience storage and retrieval."""

    def __init__(self, d_model: int, config: CognitiveConfig, max_episodes: int = 1000):
        super().__init__(config)

        self.encoder = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Linear(d_model // 2, d_model),
        )

        self.register_buffer("episodes", torch.zeros(max_episodes, d_model))
        self.register_buffer("count", torch.tensor(0))
        self.max = max_episodes

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        encoded = self.encoder(x)
        return {"encoded": encoded}

    def store(self, x: torch.Tensor):
        """Store an experience."""
        with torch.no_grad():
            idx = self.count.item() % self.max
            self.episodes[idx] = x.mean(dim=(0, 1)) if x.dim() == 3 else x.mean(dim=0)
            self.count += 1

    def retrieve(self, query: torch.Tensor, k: int = 5) -> torch.Tensor:
        """Retrieve k most similar episodes."""
        n = min(self.count.item(), self.max)
        if n == 0:
            return torch.zeros_like(query)

        episodes = self.episodes[:n]
        sim = F.cosine_similarity(query.unsqueeze(1), episodes.unsqueeze(0), dim=-1)
        _, indices = sim.topk(min(k, n), dim=-1)
        return episodes[indices].mean(dim=1)

    def reset_state(self):
        self.count.zero_()


# ==============================================================================
# SECTION 7: WORLD MODEL COMPONENTS
# ==============================================================================


class WorldBuffer(CognitiveModule):
    """Single domain world buffer with state prediction."""

    def __init__(self, d_model: int, config: CognitiveConfig, domain: str = "physical"):
        super().__init__(config)
        self.domain = domain

        state_dim = getattr(config, "world_state_dim", 256)

        self.encoder = nn.Sequential(
            nn.Linear(d_model, state_dim), nn.GELU(), nn.Linear(state_dim, state_dim)
        )

        self.dynamics = nn.GRUCell(state_dim, state_dim)

        self.predictor = nn.Sequential(
            nn.Linear(state_dim, state_dim), nn.Tanh(), nn.Linear(state_dim, state_dim)
        )

        self.register_buffer("state", torch.zeros(1, state_dim))
        self.register_buffer("prediction", torch.zeros(1, state_dim))
        self.register_buffer("surprise", torch.tensor(0.0))

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        if x.dim() == 3:
            x = x.mean(dim=1)

        encoded = self.encoder(x)

        # Compute surprise
        if self.prediction.norm() > 0:
            surprise = F.mse_loss(
                encoded, self.prediction.expand(encoded.size(0), -1)
            ).item()
        else:
            surprise = 0.0

        self.surprise = torch.tensor(surprise)

        # Update state
        new_state = self.dynamics(encoded, self.state.expand(encoded.size(0), -1))
        update_rate = getattr(self.config, "world_update_rate", 0.1)
        self.state = (
            update_rate * new_state[:1] + (1 - update_rate) * self.state
        ).detach()
        self.prediction = self.predictor(self.state).detach()

        return {"surprise": surprise, "state": new_state}

    def reset_state(self):
        self.state.zero_()
        self.prediction.zero_()
        self.surprise.zero_()


class MultiWorldBuffer(CognitiveModule):
    """Multi-domain world model buffers."""

    def __init__(
        self, d_model: int, config: CognitiveConfig, domains: Optional[List[str]] = None
    ):
        super().__init__(config)

        if domains is None:
            domains = ["physical", "social", "abstract", "temporal"]

        self.world_buffers = nn.ModuleDict(
            {d: WorldBuffer(d_model, config, d) for d in domains}
        )
        self.register_buffer("aggregate_surprise", torch.tensor(0.0))

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        results = {}
        total_surprise = 0.0

        for domain, buffer in self.world_buffers.items():
            result = buffer(x)
            results[domain] = result
            total_surprise += result["surprise"]

        self.aggregate_surprise = torch.tensor(total_surprise / len(self.world_buffers))

        return {
            "domain_results": results,
            "aggregate_surprise": self.aggregate_surprise.item(),
        }

    def reset_state(self):
        for buffer in self.world_buffers.values():
            buffer.reset_state()


# ==============================================================================
# SECTION 8: INTERNAL STATE SYSTEMS
# ==============================================================================


class NonVerbalTension(nn.Module):
    """Tracks prediction error as internal tension signal."""

    def __init__(self, integration_rate: float = 0.1, buffer_size: int = 100):
        super().__init__()
        self.integration_rate = integration_rate
        self.register_buffer("prediction_errors", torch.zeros(buffer_size))
        self.register_buffer("error_idx", torch.tensor(0))
        self.register_buffer("integrated_tension", torch.tensor(0.0))

    def update(self, pred: torch.Tensor, actual: torch.Tensor):
        with torch.no_grad():
            error = F.mse_loss(pred.float(), actual.float()).item()
            idx = self.error_idx.item() % len(self.prediction_errors)
            self.prediction_errors[idx] = error
            self.error_idx += 1

    def integrate(self) -> float:
        n = min(self.error_idx.item(), len(self.prediction_errors))
        if n > 0:
            raw = self.prediction_errors[:n].mean().item()
            self.integrated_tension = (
                1 - self.integration_rate
            ) * self.integrated_tension + self.integration_rate * raw
        return self.integrated_tension.item()


class InternalState(CognitiveModule):
    """Complete internal cognitive state tracker."""

    def __init__(self, d_model: int, config: CognitiveConfig):
        super().__init__(config)

        internal_dim = getattr(config, "internal_state_dim", 128)
        latent_dim = getattr(config, "latent_state_dim", 768)

        self.tension = NonVerbalTension()

        self.encoder = nn.Sequential(nn.Linear(latent_dim, internal_dim), nn.Tanh())

        self.register_buffer("discomfort", torch.zeros(1, internal_dim))

    def forward(
        self,
        fused: torch.Tensor,
        pred: Optional[torch.Tensor] = None,
        actual: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if pred is not None and actual is not None:
            self.tension.update(pred, actual)

        tension = self.tension.integrate()

        encoded = self.encoder(fused)
        if encoded.dim() == 3:
            encoded = encoded.mean(dim=1)

        self.discomfort = 0.9 * self.discomfort + 0.1 * encoded[:1].detach()

        return {
            "tension": tension,
            "discomfort": self.discomfort,
            "encoded_state": encoded,
        }

    def reset_state(self):
        self.discomfort.zero_()


# ==============================================================================
# SECTION 9: DREAM & SELF-TRACE
# ==============================================================================


class DreamPhase(CognitiveModule):
    """Dream phase for memory consolidation."""

    def __init__(
        self,
        d_model: int,
        config: CognitiveConfig,
        buffer_size: int = 256,
        dream_threshold: float = 0.7,
    ):
        super().__init__(config)

        internal_dim = getattr(config, "internal_state_dim", 128)

        self.buffer = deque(maxlen=buffer_size)
        self.is_dreaming = False
        self.dream_steps = 0
        self.dream_threshold = dream_threshold
        self.total_dreams = 0

        self.consolidator = nn.Sequential(
            nn.Linear(internal_dim, internal_dim),
            nn.GELU(),
            nn.Linear(internal_dim, internal_dim),
            nn.Tanh(),
        )

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        return {"is_dreaming": self.is_dreaming, "dream_steps": self.dream_steps}

    def record(self, state: torch.Tensor, tension: float):
        """Record state for potential dream consolidation."""
        self.buffer.append((state.detach().cpu(), tension))

    def should_dream(self) -> bool:
        if len(self.buffer) < 10:
            return False
        recent = [t for _, t in list(self.buffer)[-10:]]
        return sum(recent) / len(recent) > self.dream_threshold

    def enter_dream(self):
        self.is_dreaming = True
        self.dream_steps = 0
        self.total_dreams += 1

    def dream_step(self, identity: torch.Tensor) -> Optional[torch.Tensor]:
        """Execute one dream consolidation step."""
        if not self.is_dreaming or len(self.buffer) == 0:
            return None

        self.dream_steps += 1

        # Sample from buffer
        idx = torch.randint(0, len(self.buffer), (1,)).item()
        state, _ = self.buffer[idx]
        state = state.to(identity.device)

        # Consolidate
        consolidated = self.consolidator(state)

        # Exit dream after some steps
        if self.dream_steps > 50:
            self.is_dreaming = False

        return consolidated

    def reset_state(self):
        self.buffer.clear()
        self.is_dreaming = False
        self.dream_steps = 0


class SelfTrace(CognitiveModule):
    """Identity tracking across time."""

    def __init__(self, d_model: int, config: CognitiveConfig):
        super().__init__(config)

        internal_dim = getattr(config, "internal_state_dim", 128)

        self.register_buffer("identity", torch.zeros(1, internal_dim))
        self.register_buffer("n_traces", torch.tensor(0))

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        return {"identity": self.identity, "n_traces": self.n_traces.item()}

    def record(self, state: torch.Tensor, tension: float):
        """Update identity based on state and tension."""
        with torch.no_grad():
            if state.dim() > 2:
                state = state.mean(dim=1)

            # Weight by tension (high tension = more salient)
            weight = min(0.1, 0.01 * max(1.0, tension))
            self.identity = (1 - weight) * self.identity + weight * state[:1]
            self.n_traces += 1

    def get_identity(self) -> torch.Tensor:
        return self.identity

    def reset_state(self):
        self.identity.zero_()
        self.n_traces.zero_()


# ==============================================================================
# SECTION 10: NEUROGENESIS
# ==============================================================================


class NeurogenesisLayer(CognitiveModule):
    """Layer with dynamic neuron birth/death based on usage."""

    def __init__(
        self,
        input_dim: int,
        n_neurons: int,
        config: CognitiveConfig,
        max_neurons: int = 256,
        usage_decay: float = 0.99,
        birth_threshold: float = 0.8,
        death_threshold: float = 0.01,
    ):
        super().__init__(config)

        self.input_dim = input_dim
        self.max_neurons = max_neurons
        self.usage_decay = usage_decay
        self.birth_threshold = birth_threshold
        self.death_threshold = death_threshold

        self.weights = nn.Parameter(torch.randn(max_neurons, input_dim) * 0.02)
        self.bias = nn.Parameter(torch.zeros(max_neurons))

        self.register_buffer("n_neurons", torch.tensor(n_neurons))
        self.register_buffer("usage", torch.ones(max_neurons))
        self.register_buffer("lifetime", torch.zeros(max_neurons))
        self.register_buffer("births", torch.tensor(0))
        self.register_buffer("deaths", torch.tensor(0))

    def forward(self, x: torch.Tensor, **kwargs) -> Dict[str, Any]:
        n = self.n_neurons.item()
        out = torch.tanh(F.linear(x, self.weights[:n], self.bias[:n]))

        with torch.no_grad():
            activation = out.abs().mean(dim=0) if out.dim() > 1 else out.abs()
            if activation.size(-1) >= n:
                self.usage[:n] = (
                    self.usage_decay * self.usage[:n]
                    + (1 - self.usage_decay) * activation[..., :n].mean(dim=0)
                    if activation.dim() > 1
                    else activation[:n]
                )
            self.lifetime[:n] += 1

        return {
            "output": out,
            "n_neurons": n,
            "avg_usage": self.usage[:n].mean().item(),
        }

    def maybe_birth(self, coherence: float) -> bool:
        """Try to add a neuron if coherence is high."""
        n = self.n_neurons.item()
        if coherence > self.birth_threshold and n < self.max_neurons:
            with torch.no_grad():
                nn.init.normal_(self.weights[n], std=0.02)
                self.bias[n] = 0
                self.usage[n] = 1.0
                self.lifetime[n] = 0
                self.n_neurons += 1
                self.births += 1
            return True
        return False

    def maybe_death(self) -> int:
        """Remove underused neurons."""
        n = self.n_neurons.item()
        if n <= 8:
            return 0

        dead = 0
        with torch.no_grad():
            for i in range(n - 1, 7, -1):
                if self.usage[i] < self.death_threshold and self.lifetime[i] > 100:
                    # Swap with last active
                    last = self.n_neurons.item() - 1
                    if i < last:
                        self.weights.data[i] = self.weights.data[last]
                        self.bias.data[i] = self.bias.data[last]
                        self.usage[i] = self.usage[last]
                        self.lifetime[i] = self.lifetime[last]
                    self.n_neurons -= 1
                    self.deaths += 1
                    dead += 1
        return dead

    def get_stats(self) -> Dict[str, Any]:
        n = self.n_neurons.item()
        return {
            "total_neurons": n,
            "births": self.births.item(),
            "deaths": self.deaths.item(),
            "avg_usage": self.usage[:n].mean().item() if n > 0 else 0,
        }

    def reset_state(self):
        pass


# ==============================================================================
# SECTION 11: EARCP MODULE
# ==============================================================================


class EARCPModule(CognitiveModule):
    """
    Ensemble Auto-Regulated Coherence Protocol.
    Compresses hidden states and regulates information flow.
    """

    def __init__(self, d_model: int, config: CognitiveConfig):
        super().__init__(config)

        latent_dim = getattr(config, "latent_state_dim", 768)
        d_ff = getattr(config, "d_ff", 2048)

        self.compress = nn.Sequential(
            nn.Linear(d_model, (d_model + latent_dim) // 2),
            nn.SiLU(),
            nn.Linear((d_model + latent_dim) // 2, latent_dim),
        )

        self.state_gate = nn.Linear(latent_dim * 2, latent_dim)

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(latent_dim, d_model)
        self.v_proj = nn.Linear(latent_dim, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.coherence_proc = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.SiLU(), nn.Linear(d_ff, d_model)
        )

        # Initialize small for residual
        nn.init.zeros_(self.out_proj.weight)
        nn.init.zeros_(self.coherence_proc[-1].weight)

    def forward(self, h: torch.Tensor, fused: torch.Tensor, **kwargs) -> Dict[str, Any]:
        h_compressed = self.compress(h.mean(dim=1))

        gate = torch.sigmoid(self.state_gate(torch.cat([h_compressed, fused], dim=-1)))
        state = (1 - gate) * fused + gate * h_compressed

        q = self.q_proj(h)
        k = self.k_proj(state).unsqueeze(1)
        v = self.v_proj(state).unsqueeze(1)

        attn = F.softmax(q @ k.transpose(-2, -1) / math.sqrt(h.size(-1)), dim=-1)
        h = h + 0.02 * self.out_proj(attn @ v)
        h = h + 0.1 * self.coherence_proc(h)

        coherence = torch.sigmoid(h.mean()).item()

        return {"hidden": h, "state": state, "coherence": coherence}

    def reset_state(self):
        pass


# ==============================================================================
# SECTION 12: VAE COMPONENTS (for World Models / Vision)
# ==============================================================================


class VAEEncoder(nn.Module):
    """Convolutional VAE Encoder for visual inputs."""

    def __init__(
        self, in_channels: int = 3, latent_dim: int = 256, channels: List[int] = None
    ):
        super().__init__()

        if channels is None:
            channels = [32, 64, 128, 256]

        layers = []
        prev_c = in_channels

        for c in channels:
            layers.extend(
                [
                    nn.Conv2d(prev_c, c, 4, 2, 1),
                    nn.BatchNorm2d(c),
                    nn.LeakyReLU(0.2, inplace=True),
                ]
            )
            prev_c = c

        self.encoder = nn.Sequential(*layers)

        # Calculate flattened size (assumes 64x64 input)
        self.flat_size = channels[-1] * 4 * 4

        self.fc_mu = nn.Linear(self.flat_size, latent_dim)
        self.fc_logvar = nn.Linear(self.flat_size, latent_dim)

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.encoder(x)
        h = h.view(h.size(0), -1)

        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)

        # Reparameterization
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mu + eps * std

        return z, mu, logvar


class VAEDecoder(nn.Module):
    """Convolutional VAE Decoder for visual outputs."""

    def __init__(
        self, latent_dim: int = 256, out_channels: int = 3, channels: List[int] = None
    ):
        super().__init__()

        if channels is None:
            channels = [256, 128, 64, 32]

        self.fc = nn.Linear(latent_dim, channels[0] * 4 * 4)
        self.init_channels = channels[0]

        layers = []
        for i in range(len(channels) - 1):
            layers.extend(
                [
                    nn.ConvTranspose2d(channels[i], channels[i + 1], 4, 2, 1),
                    nn.BatchNorm2d(channels[i + 1]),
                    nn.ReLU(inplace=True),
                ]
            )

        # Final layer
        layers.extend(
            [nn.ConvTranspose2d(channels[-1], out_channels, 4, 2, 1), nn.Sigmoid()]
        )

        self.decoder = nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        h = self.fc(z)
        h = h.view(h.size(0), self.init_channels, 4, 4)
        return self.decoder(h)


# ==============================================================================
# SECTION 13: UNIVERSAL LATENT SPACE
# ==============================================================================


class UniversalLatentSpace(CognitiveModule):
    """Universal Latent Space for cross-modal alignment."""

    def __init__(
        self,
        d_model: int,
        config: CognitiveConfig,
        uls_dim: int = 1024,
        n_anchors: int = 64,
    ):
        super().__init__(config)

        self.uls_dim = uls_dim

        self.anchors = nn.Parameter(torch.randn(n_anchors, uls_dim) * 0.02)

        # Modality projections
        self.text_to_uls = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, uls_dim),
            RMSNorm(uls_dim),
        )

        self.vision_to_uls = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, uls_dim),
            RMSNorm(uls_dim),
        )

        self.audio_to_uls = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, uls_dim),
            RMSNorm(uls_dim),
        )

        self.uls_to_model = nn.Sequential(
            nn.Linear(uls_dim, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
            RMSNorm(d_model),
        )

        self.anchor_attn = nn.MultiheadAttention(uls_dim, num_heads=4, batch_first=True)

    def forward(self, features: Dict[str, torch.Tensor], **kwargs) -> Dict[str, Any]:
        unified_features = []

        if "text" in features and features["text"] is not None:
            unified_features.append(self.text_to_uls(features["text"]))

        if "vision" in features and features["vision"] is not None:
            unified_features.append(self.vision_to_uls(features["vision"]))

        if "audio" in features and features["audio"] is not None:
            unified_features.append(self.audio_to_uls(features["audio"]))

        if not unified_features:
            B = 1
            device = self.anchors.device
            unified = torch.zeros(B, 1, self.uls_dim, device=device)
        else:
            # Average all modalities
            unified = torch.stack(unified_features, dim=0).mean(dim=0)

        # Anchor attention
        anchors_expanded = self.anchors.unsqueeze(0).expand(unified.size(0), -1, -1)
        enhanced, _ = self.anchor_attn(unified, anchors_expanded, anchors_expanded)
        enhanced = unified + 0.1 * enhanced

        output = self.uls_to_model(enhanced)

        return {"unified": unified, "enhanced": enhanced, "output": output}

    def reset_state(self):
        pass
