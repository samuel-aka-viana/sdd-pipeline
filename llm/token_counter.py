"""Contador de tokens para observabilidade de custo/orçamento.

Usa tiktoken quando o modelo é OpenAI-family. Para outros (Llama, GLM, etc),
cai num encoder genérico (cl100k_base). Como último recurso, heurística chars/4.
"""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


_FALLBACK_ENCODING = "cl100k_base"


@lru_cache(maxsize=8)
def _get_encoder(model: str):
    try:
        import tiktoken
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding(_FALLBACK_ENCODING)
    except Exception as exc:
        logger.debug("[token_counter] tiktoken indisponível (%s) — usando heurística", exc)
        return None


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    if not text:
        return 0
    encoder = _get_encoder(model)
    if encoder is None:
        return max(1, len(text) // 4)
    try:
        return len(encoder.encode(text))
    except Exception:
        return max(1, len(text) // 4)
