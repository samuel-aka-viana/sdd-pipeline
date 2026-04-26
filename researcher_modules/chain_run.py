import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Any


def new_chain_run(
    tool: str,
    foco: str,
    alternative: str,
    queries: list[str],
) -> dict[str, Any]:
    tool_safe = (tool or "unknown").lower().replace(" ", "_")
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    chain_dir = Path("output") / "chains" / tool_safe / run_id
    chain_dir.mkdir(parents=True, exist_ok=True)
    run_data: dict[str, Any] = {
        "tool": tool,
        "tool_safe": tool_safe,
        "foco": foco,
        "alternative": alternative,
        "queries": queries,
        "run_id": run_id,
        "started_at": datetime.now().isoformat(),
        "chain_dir": str(chain_dir),
        "phases": {
            "discovery": [],
            "scrape": [],
            "extract": [],
            "index": [],
            "synthesis_eval": {},
        },
        "files": {},
    }
    return run_data


def write_chain_phase(run_data: dict[str, Any] | None, phase: str, payload: dict[str, Any], memory) -> str:
    if not run_data:
        return ""
    phase_order = {
        "discovery": "01",
        "scrape": "02",
        "extract": "03",
        "index": "04",
        "synthesis_eval": "05",
    }
    prefix = phase_order.get(phase, "99")
    chain_dir = Path(run_data["chain_dir"])
    path = chain_dir / f"{prefix}_{phase}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    run_data["files"][phase] = str(path)
    memory.log_event("chain_phase_saved", {
        "tool": run_data["tool"],
        "phase": phase,
        "path": str(path),
    })
    return str(path)


def finalize_chain_run(
    run_data: dict[str, Any] | None,
    last_scrape_stats: dict,
    memory,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not run_data:
        return None, None

    run_data["finished_at"] = datetime.now().isoformat()
    summary_path = Path(run_data["chain_dir"]) / "00_summary.json"
    summary_payload = {
        "tool": run_data["tool"],
        "foco": run_data["foco"],
        "alternative": run_data["alternative"],
        "run_id": run_data["run_id"],
        "started_at": run_data["started_at"],
        "finished_at": run_data["finished_at"],
        "files": run_data["files"],
        "counts": {
            "discovery": len(run_data["phases"]["discovery"]),
            "scrape": len(run_data["phases"]["scrape"]),
            "extract": len(run_data["phases"]["extract"]),
            "index": len(run_data["phases"]["index"]),
        },
        "scrape_stats": last_scrape_stats,
    }
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    run_data["files"]["summary"] = str(summary_path)
    chain_run_entry = {
        "run_id": run_data["run_id"],
        "chain_dir": run_data["chain_dir"],
        "files": dict(run_data["files"]),
    }
    memory.log_event("chain_run_saved", {
        "tool": run_data["tool"],
        "run_id": run_data["run_id"],
        "chain_dir": run_data["chain_dir"],
    })
    return run_data, chain_run_entry
