"""Structured outputs com validação Pydantic + retry de reparação.

Em vez do padrão atual (texto → regex/parser frágil), as skills declaram
um schema Pydantic e recebem uma instância validada. Se o LLM responder
JSON inválido, fazemos UM retry com a mensagem de erro como hint.
"""

from __future__ import annotations

import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from utils import extract_json_object

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(RuntimeError):
    """Falha ao obter JSON válido após retries."""


def build_schema_hint(schema: type[BaseModel]) -> str:
    """Schema JSON resumido para colar no prompt."""
    json_schema = schema.model_json_schema()
    return json.dumps(json_schema, ensure_ascii=False, indent=2)


def parse_response(raw_text: str, schema: type[T]) -> T:
    parsed = extract_json_object(raw_text)
    if not isinstance(parsed, dict):
        raise StructuredOutputError(f"resposta sem objeto JSON: {raw_text[:200]!r}")
    try:
        return schema.model_validate(parsed)
    except ValidationError as exc:
        raise StructuredOutputError(f"schema inválido: {exc}") from exc


def build_repair_prompt(original_prompt: str, raw_response: str, error: str) -> str:
    return (
        f"{original_prompt}\n\n"
        "---\n"
        "ERRO NA RESPOSTA ANTERIOR (não repita):\n"
        f"{error}\n\n"
        f"Resposta anterior (truncada):\n{raw_response[:600]}\n\n"
        "Responda APENAS com o JSON válido conforme o schema acima. Sem texto antes ou depois."
    )
