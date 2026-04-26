"""Stage: evidence builder (replaces relevance_filter)."""

from __future__ import annotations

from pathlib import Path

from skills.schemas import EvidencePack


def run_evidence_stage(
    pipeline,
    *,
    research: str,
    ferramentas: str,
    foco: str,
    started_at: float,
) -> EvidencePack:
    pipeline.enforce_global_timeout(started_at, stage="evidence")
    pack = pipeline.evidence_builder.build(research, ferramentas, foco)

    Path("output").mkdir(exist_ok=True)
    Path("output/evidence_pack.json").write_text(
        pack.model_dump_json(indent=2), encoding="utf-8"
    )

    pipeline.memory.log_event("evidence_pack_built", {
        "ferramentas": ferramentas,
        "total_urls_found": pack.total_urls_found,
        "retained_urls": len(pack.retained_urls),
        "items": len(pack.items),
        "gaps": len(pack.gaps),
    })
    return pack
