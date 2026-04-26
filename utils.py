import json
import logging
import re


def extract_json_object(raw_text: str) -> dict:
    text = (raw_text or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def compact_text_block(
    text: str,
    max_chars: int,
    label: str,
    memory=None,
    logger: logging.Logger | None = None,
) -> str:
    content = (text or "").strip()
    if len(content) <= max_chars:
        return content

    original_len = len(content)
    head_size = int(max_chars * 0.7)
    tail_size = max_chars - head_size
    compacted = (
        f"{content[:head_size]}\n\n"
        f"[... {label} truncado para caber no contexto ...]\n\n"
        f"{content[-tail_size:]}"
    )

    lost = original_len - len(compacted)
    loss_pct = (lost / original_len) * 100
    if logger:
        logger.warning(
            f"⚠️  TRUNCATION [{label}]: {original_len:,} → {len(compacted):,} chars "
            f"({loss_pct:.1f}% lost) | limit={max_chars:,}"
        )
    if memory:
        memory.log_event("writer_truncation", {
            "label": label,
            "original": original_len,
            "final": len(compacted),
            "lost": lost,
            "loss_pct": f"{loss_pct:.1f}%",
        })
    return compacted
