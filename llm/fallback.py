import logging

from httpx import TimeoutException

from llm.circuit_breaker import CircuitOpenError

logger = logging.getLogger(__name__)


def try_provider(fn, *, provider_id: str, role: str, errors: list[str] | None = None):
    """Call fn(); catch circuit/runtime/timeout failures, return None on failure."""
    try:
        return fn()
    except CircuitOpenError as exc:
        if errors is not None:
            errors.append(f"{provider_id}: {exc}")
        logger.warning("[LLM] %s circuito aberto role=%s: %s", provider_id, role, exc)
        return None
    except (RuntimeError, TimeoutException) as exc:
        if errors is not None:
            errors.append(f"{provider_id}: {exc}")
        logger.warning("[LLM] %s falhou role=%s: %s", provider_id, role, exc)
        return None
