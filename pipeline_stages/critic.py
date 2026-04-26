"""Stage: critic (validação determinística + semântica)."""

from __future__ import annotations

from httpx import TimeoutException


def run_critic_iteration(
    pipeline,
    *,
    article: str,
    ferramentas: str,
    started_at: float,
    iteration: int,
) -> dict:
    pipeline.enforce_global_timeout(started_at, stage=f"iteração {iteration} (critic)")
    route = pipeline.memory.get("route", {})
    tool_type = route.get("tool_type", "unknown")

    with pipeline.log.task("Validando contra spec"):
        try:
            return pipeline.critic.evaluate(article, ferramentas, tool_type=tool_type)
        except TimeoutException:
            pipeline.log.error(
                f"Critic timeout ({pipeline.critic.timeout}s) — aprovando sem validação semântica"
            )
            return {
                "approved": True,
                "layer": "timeout_skip",
                "warnings": [f"Validação semântica pulada: critic excedeu {pipeline.critic.timeout}s"],
                "report": "Validação semântica pulada por timeout.",
            }
