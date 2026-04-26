"""Circuit breaker para o fallback chain de LLM.

Detecta 429/503/timeouts e abre o circuito por cooldown, evitando que cada
falha consuma o timeout completo antes de cair pro próximo provider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from time import monotonic

logger = logging.getLogger(__name__)


# Cooldowns (segundos) por tipo de falha. Conservador: 429 cai fundo porque
# o rate limit normalmente persiste por um minuto inteiro.
COOLDOWNS = {
    "rate_limited": 60.0,   # HTTP 429
    "unavailable": 30.0,    # HTTP 503 / 502
    "timeout": 20.0,        # leitura/conexão
    "error": 10.0,          # outros (5xx, payload inválido)
}

CONSECUTIVE_THRESHOLD = 3
CONSECUTIVE_WINDOW = 120.0


class CircuitOpenError(RuntimeError):
    """Sinaliza que o circuito está aberto — pular pro próximo provider sem tentar."""


@dataclass
class ProviderHealth:
    provider_id: str
    opened_until: float = 0.0
    last_kind: str = ""
    consecutive_failures: int = 0
    last_failure_at: float = 0.0

    def is_open(self, now: float) -> bool:
        return now < self.opened_until


@dataclass
class CircuitBreakerRegistry:
    health: dict[str, ProviderHealth] = field(default_factory=dict)

    def check(self, provider_id: str) -> None:
        health = self.health.get(provider_id)
        if health is None:
            return
        now = monotonic()
        if health.is_open(now):
            remaining = round(health.opened_until - now, 1)
            raise CircuitOpenError(
                f"circuit_open(provider={provider_id} kind={health.last_kind} "
                f"cooldown_remaining={remaining}s)"
            )

    def record_failure(self, provider_id: str, kind: str) -> None:
        now = monotonic()
        cooldown = COOLDOWNS.get(kind, COOLDOWNS["error"])
        health = self.health.setdefault(provider_id, ProviderHealth(provider_id=provider_id))

        within_window = (now - health.last_failure_at) <= CONSECUTIVE_WINDOW
        health.consecutive_failures = (health.consecutive_failures + 1) if within_window else 1
        health.last_failure_at = now
        health.last_kind = kind

        if health.consecutive_failures >= CONSECUTIVE_THRESHOLD:
            cooldown = max(cooldown, COOLDOWNS["rate_limited"])

        health.opened_until = max(health.opened_until, now + cooldown)
        logger.warning(
            "[circuit_breaker] provider=%s kind=%s consecutive=%d cooldown=%.1fs",
            provider_id, kind, health.consecutive_failures, cooldown,
        )

    def record_success(self, provider_id: str) -> None:
        health = self.health.get(provider_id)
        if health is None:
            return
        if health.consecutive_failures or health.opened_until:
            logger.info("[circuit_breaker] provider=%s recuperado", provider_id)
        health.consecutive_failures = 0
        health.opened_until = 0.0
        health.last_kind = ""


def classify_http_failure(status_code: int | None, exception_name: str = "") -> str:
    if status_code == 429:
        return "rate_limited"
    if status_code in (502, 503, 504):
        return "unavailable"
    if "Timeout" in exception_name:
        return "timeout"
    return "error"
