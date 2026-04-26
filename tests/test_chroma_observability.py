import json
from contextlib import contextmanager
from types import SimpleNamespace

from enrichment.coordinator import EnrichmentCoordinator
from logger import EventLog
from researcher_modules.cached_search import search_cached_content


class DummyMemory:
    def __init__(self):
        self.events = []
        self.values = {"research": "pesquisa atual"}

    def log_event(self, event, details):
        self.events.append({"event": event, "details": details})

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


def read_events(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_cached_search_writes_chroma_query_to_event_log(tmp_path):
    class DummyChroma:
        def query_similar(self, *_args, **_kwargs):
            return [
                {
                    "url": "https://cli.datacontract.com/",
                    "text": "datacontract test datacontract.yaml --output-format junit",
                    "source_quality": "official",
                    "similarity": 0.91,
                }
            ]

    event_path = tmp_path / "events.jsonl"
    event_log = EventLog(str(event_path))
    memory = DummyMemory()

    results = search_cached_content(
        query="datacontract test junit",
        tool="datacontract cli",
        k=3,
        chroma=DummyChroma(),
        memory=memory,
        logger=SimpleNamespace(warning=lambda *_args, **_kwargs: None),
        event_log=event_log,
    )

    assert results
    events = read_events(event_path)
    assert events[-1]["type"] == "chroma_query"
    assert events[-1]["tool"] == "datacontract cli"
    assert events[-1]["results_count"] == 1
    assert events[-1]["urls"] == ["https://cli.datacontract.com/"]


def test_enrichment_logs_each_chroma_recovery_query(tmp_path):
    event_path = tmp_path / "events.jsonl"
    event_log = EventLog(str(event_path))

    @contextmanager
    def task(_description):
        yield None

    class DummyResearcher:
        def search_cached_content(self, query, tool, k):
            return [
                {
                    "url": "https://cli.datacontract.com/",
                    "text": f"evidencia para {query}",
                    "similarity": 0.88,
                }
            ]

    pipeline = SimpleNamespace(
        log=SimpleNamespace(
            console=SimpleNamespace(print=lambda *_args, **_kwargs: None),
            task=task,
            event_log=event_log,
        ),
        memory=DummyMemory(),
        researcher=DummyResearcher(),
        build_targeted_research_questions=lambda _evaluation: ["como corrigir junit?"],
        parse_tools=lambda _ferramentas: ["datacontract cli"],
        enforce_global_timeout=lambda *_args, **_kwargs: None,
        save_debug=lambda *_args, **_kwargs: None,
        run_analysis_stage=lambda **_kwargs: "analysis",
        assess_research_quality=lambda _research: "ok",
    )

    coordinator = EnrichmentCoordinator(pipeline)
    coordinator.build_targeted_research_questions = lambda _evaluation: ["como corrigir junit?"]

    result = coordinator._enrich_via_chroma_cache(
        ferramentas="datacontract cli",
        contexto="data mesh",
        foco="integração",
        questoes=[],
        started_at=0,
        evaluation={"problems": ["falta --input"], "warnings": [], "correction_prompt": ""},
    )

    assert result is not None
    events = read_events(event_path)
    query_events = [event for event in events if event["type"] == "chroma_recovery_query"]
    assert query_events
    assert query_events[0]["tool"] == "datacontract cli"
    assert query_events[0]["results_count"] == 1
    assert query_events[0]["urls"] == ["https://cli.datacontract.com/"]
