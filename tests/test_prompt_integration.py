from types import SimpleNamespace
from pathlib import Path

from memory.memory_store import MemoryStore
from pipeline import SDDPipeline
from skills.critic import CriticSkill
from skills.researcher import ResearcherSkill


def test_build_targeted_research_questions_uses_prompt_llm(monkeypatch):
    pipeline = SDDPipeline(verbose=False, verbosity="quiet")
    pipeline.memory.set("ferramentas", "docker e podman")
    pipeline.memory.set("foco", "comparação geral")

    def fake_generate(**_kwargs):
        return SimpleNamespace(
            response='{"questions":["q1 benchmark","q2 requisitos","q3 erros"]}'
        )

    monkeypatch.setattr(pipeline.llm, "generate", fake_generate)
    questions = pipeline.build_targeted_research_questions(
        {"problems": ["falta benchmark"], "warnings": [], "report": "x"}
    )
    assert questions == ["q1 benchmark", "q2 requisitos", "q3 erros"]


def test_decide_retry_or_finalize_uses_orchestrator_prompt(monkeypatch):
    pipeline = SDDPipeline(verbose=False, verbosity="quiet")

    def fake_generate(**_kwargs):
        return SimpleNamespace(
            response='{"action":"ENRICH_RESEARCH","reason":"missing evidence","priority_fixes":["add benchmarks"]}'
        )

    monkeypatch.setattr(pipeline.llm, "generate", fake_generate)
    decision = pipeline.decide_retry_or_finalize(
        ferramentas="docker e podman",
        foco="performance / throughput",
        iteration=1,
        research_enrichment_count=0,
        stagnant_iterations=0,
        evaluation={"approved": False, "layer": "semantic", "problems": ["sem benchmark"], "warnings": []},
    )
    assert decision["action"] == "ENRICH_RESEARCH"
    assert "priority_fixes" in decision


def test_critic_semantic_check_uses_fact_checker_prompt_json(monkeypatch):
    critic = CriticSkill(memory=MemoryStore(), spec_path="spec/article_spec.yaml")

    def fake_generate(**_kwargs):
        return SimpleNamespace(
            response=(
                '{"issues":[{"excerpt":"docker run --bad-flag","problem":"flag inexistente","severity":"high"}]}'
            )
        )

    monkeypatch.setattr(critic.llm, "generate", fake_generate)
    article = "Use: docker run --bad-flag image"
    issues = critic.semantic_check(article, "docker", "containers")
    assert len(issues) == 1
    assert "flag inexistente" in issues[0]


def test_researcher_reanalyze_uses_prompt_and_formats_json(monkeypatch):
    class DummySearch:
        def search_multi(self, *args, **kwargs):
            return {}

        def save_urls(self, *args, **kwargs):
            return None

    class DummyScraper:
        def extract_text(self, *_args, **_kwargs):
            return {"status": "ok", "text": "x"}

    researcher = ResearcherSkill(
        search_tool=DummySearch(),
        scraper_tool=DummyScraper(),
        memory=MemoryStore(),
        spec_path="spec/article_spec.yaml",
    )
    researcher._scraped_urls = {"https://example.com": "docker rootless tip and error troubleshooting"}
    researcher.chroma = None

    def fake_generate(**_kwargs):
        return SimpleNamespace(
            response=(
                '{"tips":[{"text":"Use rootless mode","evidence":"rootless reduces risk","source_url":"https://example.com"}],'
                '"errors":[{"problem":"permission denied","solution":"add user to group","evidence":"docker group","source_url":"https://example.com"}]}'
            )
        )

    monkeypatch.setattr(researcher.llm, "generate", fake_generate)
    out = researcher.reanalyze_urls_for_tips_and_errors("docker", focus_on="tips_and_errors")
    assert "## Dicas Encontradas" in out
    assert "## Erros Comuns" in out


def test_no_hardcoded_prompt_fstrings_in_active_skills():
    monitored_files = [
        "skills/researcher.py",
        "skills/analyst.py",
        "skills/writer.py",
        "skills/critic.py",
        "pipeline.py",
    ]
    for path in monitored_files:
        content = Path(path).read_text(encoding="utf-8")
        assert 'prompt = f"""' not in content


def test_spec_has_langgraph_orchestration_and_context_by_role():
    pipeline = SDDPipeline(verbose=False, verbosity="quiet")
    spec = pipeline.spec
    assert spec["pipeline"]["orchestration"]["backend"] == "langgraph"
    ctx = spec["llm"]["context_length"]
    assert ctx["researcher"] >= 16000
    assert ctx["analyst"] >= 16000
    assert ctx["writer"] >= 16000
    assert ctx["critic"] >= 16000
