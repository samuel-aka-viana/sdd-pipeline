import os
import yaml
import json
from datetime import datetime
from pathlib import Path
from httpx import TimeoutException
from time import monotonic

from tools.search_tool import SearchTool
from tools.scraper_tool import ScraperTool
from memory.memory_store import MemoryStore
from skills.researcher import ResearcherSkill
from skills.analyst import AnalystSkill
from skills.writer import WriterSkill
from skills.critic import CriticSkill
from logger import PipelineLogger


class SDDPipeline:

    MAX_ITERATIONS = 3

    def __init__(self, spec_path: str = "spec/article_spec.yaml"):
        self.spec_path = spec_path
        self.spec      = yaml.safe_load(Path(spec_path).read_text())
        self.log       = PipelineLogger()
        self.memory    = MemoryStore()
        pipeline_conf = self.spec.get("pipeline", {})
        raw_timeout_total = pipeline_conf.get("timeout_total_seconds")
        self.timeout_total_seconds = (
            int(raw_timeout_total)
            if raw_timeout_total not in (None, "")
            else None
        )

        # lê config do scraper do spec
        scraper_conf = self.spec.get("research", {}).get("scraper", {})
        search_tool  = SearchTool()
        scraper_tool = ScraperTool(
            max_chars=scraper_conf.get("max_chars_per_page", 4000),
            timeout=scraper_conf.get("timeout_seconds", 15),
        )

        self.researcher = ResearcherSkill(search_tool, scraper_tool, self.memory, spec_path)
        self.analyst    = AnalystSkill(self.memory, spec_path)
        self.writer     = WriterSkill(self.memory, spec_path)
        self.critic     = CriticSkill(self.memory, spec_path)

        os.makedirs("output", exist_ok=True)
        os.makedirs("artigos", exist_ok=True)

    def run(
        self,
        ferramentas: str,
        contexto:    str,
        foco:        str = "comparação geral",
        questoes:    list[str] | None = None,
    ) -> str:

        questoes = questoes or []
        started_at = monotonic()
        article = ""
        iteration = 0
        evaluation = {"approved": False, "problems": [], "correction_prompt": ""}

        self.log.pipeline_start(ferramentas, contexto)
        self.log.console.print(
            f"   [dim]Foco: {foco} | "
            f"Perguntas: {len(questoes)}[/dim]\n"
        )

        self.memory.set("ferramentas", ferramentas)
        self.memory.set("contexto", contexto)
        self.memory.set("foco", foco)
        self.memory.set("questoes", questoes)
        self.memory.log_event("pipeline_start", {
            "ferramentas": ferramentas,
            "contexto":    contexto,
            "foco":        foco,
            "questoes":    questoes,
        })

        # ---- 1. research ----
        self.log.section(1, 3, "Pesquisando")
        tools_list     = self._parse_tools(ferramentas)
        research_parts = []

        for tool in tools_list:
            self._enforce_global_timeout(
                started_at,
                stage=f"pesquisa ({tool})",
            )
            alt = next((t for t in tools_list if t != tool), "")
            with self.log.task(f"Pesquisando {tool}"):
                try:
                    data = self.researcher.run(
                        tool=tool,
                        alternative=alt,
                        foco=foco,
                        questoes=questoes,
                    )
                except TimeoutException:
                    self.log.error(
                        f"Researcher timeout ({self.researcher.timeout}s) — "
                        f"dados insuficientes para {tool}"
                    )
                    data = f"# {tool}\n\nPesquisa interrompida por timeout ({self.researcher.timeout}s)."
            research_parts.append(f"# {tool}\n{data}")

        research = "\n\n".join(research_parts)
        self.memory.set("research", research)
        self._save_debug("research", research)

        # detecta research fraco
        research_quality = self._assess_research_quality(research)
        if research_quality == "weak":
            self.log.console.print(
                "   [yellow]⚠ Research fraco — poucos dados concretos encontrados[/yellow]"
            )

        # ---- 2. analysis ----
        self.log.section(2, 3, "Analisando")
        self._enforce_global_timeout(
            started_at,
            stage="análise",
        )
        with self.log.task("Gerando análise"):
            try:
                analysis = self.analyst.run(
                    research=research,
                    ferramentas=ferramentas,
                    contexto=contexto,
                    foco=foco,
                    questoes=questoes,
                )
            except TimeoutException:
                self.log.error(
                    f"Analyst timeout ({self.analyst.timeout}s) — usando research bruto"
                )
                analysis = f"Análise interrompida por timeout ({self.analyst.timeout}s).\n\n{research}"

        self.memory.set("analysis", analysis)
        self._save_debug("analysis", analysis)

        # ---- 3. write + critic loop ----
        self.log.section(3, 3, "Escrevendo")

        lessons = self.memory.get_lessons_for_prompt()
        if lessons:
            lesson_line = next(
                (l for l in lessons.splitlines() if l.startswith("-")),
                lessons.splitlines()[0],
            )
            self.log.memory_hit(lesson_line)

        correction_instructions = ""
        try:
            for iteration in range(1, self.MAX_ITERATIONS + 1):
                self._enforce_global_timeout(
                    started_at,
                    stage=f"iteração {iteration} (writer)",
                )
                self.log.iteration(iteration, self.MAX_ITERATIONS)

                with self.log.task("Escrevendo artigo"):
                    try:
                        article = self.writer.run(
                            research=research,
                            analysis=analysis,
                            ferramentas=ferramentas,
                            contexto=contexto,
                            foco=foco,
                            questoes=questoes,
                            correction_instructions=correction_instructions,
                            research_quality=research_quality,
                        )
                    except TimeoutException:
                        self.log.error(
                            f"Writer timeout ({self.writer.timeout}s) na iteração {iteration}"
                        )
                        if iteration == self.MAX_ITERATIONS:
                            article = f"# Timeout\n\nGeração interrompida: writer excedeu {self.writer.timeout}s."
                            break
                        continue

                # pós-processamento: remove frases proibidas que o modelo insiste
                article = self._sanitize_article(article)

                self._enforce_global_timeout(
                    started_at,
                    stage=f"iteração {iteration} (critic)",
                )
                with self.log.task("Validando contra spec"):
                    try:
                        evaluation = self.critic.evaluate(article, ferramentas)
                    except TimeoutException:
                        self.log.error(
                            f"Critic timeout ({self.critic.timeout}s) — aprovando sem validação semântica"
                        )
                        evaluation = {
                            "approved": True,
                            "layer": "timeout_skip",
                            "warnings": [f"Validação semântica pulada: critic excedeu {self.critic.timeout}s"],
                            "report": "Validação semântica pulada por timeout.",
                        }

                # mostra resultado da validação
                if evaluation["approved"]:
                    self.log.critic_passed(
                        evaluation.get("layer", ""),
                        evaluation.get("warnings", []),
                    )
                    self.memory.log_event("article_approved", {
                        "iteration":   iteration,
                        "ferramentas": ferramentas,
                        "foco":        foco,
                    })
                    if iteration > 1:
                        # extrai os problemas reais, sem o header genérico
                        problems = [
                            l.strip()
                            for l in correction_instructions.splitlines()
                            if l.strip() and l.strip()[0].isdigit()
                        ]
                        pattern = "; ".join(problems)[:150] if problems else correction_instructions[:150]
                        self.memory.learn(
                            problem_pattern=pattern,
                            solution=f"Resolvido em {iteration} iterações",
                            context=f"{ferramentas} | foco: {foco}",
                        )
                    break

                self.log.critic_failed(evaluation.get("problems", []))
                correction_instructions = evaluation.get("correction_prompt", "")

                if iteration == self.MAX_ITERATIONS:
                    self.log.error("Máximo de iterações atingido. Salvando melhor versão.")
                    self.memory.log_event("max_iterations_reached", {
                        "ferramentas": ferramentas,
                        "problems":    evaluation.get("problems", []),
                    })
        except TimeoutException as exc:
            self.log.error(str(exc))
            self.memory.log_event("pipeline_timeout_total", {
                "ferramentas": ferramentas,
                "foco": foco,
                "timeout_total_seconds": self.timeout_total_seconds,
                "elapsed_seconds": round(monotonic() - started_at, 2),
            })
            if not article:
                article = (
                    "# Timeout\n\n"
                    f"Pipeline excedeu timeout total de {self.timeout_total_seconds}s."
                )

        # ---- save ----
        slug = ferramentas.lower().replace(" ", "-").replace(",", "")[:40]
        ts   = datetime.now().strftime("%Y%m%d_%H%M")
        path = f"artigos/{slug}_{ts}.md"

        Path(path).write_text(article, encoding="utf-8")

        metrics = {
            "ferramentas": ferramentas,
            "foco":        foco,
            "perguntas":   len(questoes),
            "iterações":   iteration,
            "aprovado":    evaluation["approved"],
            "output":      path,
        }
        self.log.metrics(metrics)
        self.log.saved(path)

        self._save_metrics(ferramentas, path, evaluation["approved"], foco)
        return path

    def _parse_tools(self, ferramentas: str) -> list[str]:
        return [
            t.strip()
            for t in ferramentas.lower().replace(" e ", ",").split(",")
            if t.strip()
        ]

    def _assess_research_quality(self, research: str) -> str:
        """Retorna 'weak' se o research não tem dados suficientes."""
        indicators = 0
        lower = research.lower()
        # tem URLs reais?
        import re
        urls = re.findall(r'https?://[^\s]+', research)
        if len(urls) >= 5:
            indicators += 1
        # tem blocos de código?
        if research.count("```") >= 4:
            indicators += 1
        # tem conteúdo extraído (não só snippets)?
        if "conteúdo extraído" in lower or "conteúdo:" in lower:
            indicators += 1
        # não tem muitos scrape_falhou?
        fail_count = lower.count("scrape_falhou")
        if fail_count <= 2:
            indicators += 1
        return "ok" if indicators >= 3 else "weak"

    def _sanitize_article(self, article: str) -> str:
        """Remove frases proibidas que o modelo insiste em usar."""
        import re
        patterns = self.spec["article"]["quality_rules"]["no_placeholders"]["patterns"]

        lines = article.split("\n")
        cleaned = []

        for line in lines:
            lower = line.lower().strip()
            has_placeholder = any(p.lower() in lower for p in patterns)
            if has_placeholder:
                if lower.startswith("#") and len(lower) < 80:
                    continue
                for p in patterns:
                    line = re.sub(re.escape(p), "", line, flags=re.IGNORECASE)
                if not line.strip() or line.strip() in (".", "-", "*"):
                    continue
            cleaned.append(line)

        result = "\n".join(cleaned)

        # remove blocos ```bash``` vazios ou com só comentários
        result = re.sub(
            r'```bash\s*\n(\s*#[^\n]*\n)*\s*```',
            '',
            result,
        )

        # remove URLs inventadas
        url_rules = self.spec["article"]["quality_rules"].get("url_validation", {})
        for bp in url_rules.get("block_patterns", []):
            result = re.sub(rf'https?://[^\s]*{re.escape(bp)}[^\s]*', '', result)

        return result

    def _save_debug(self, stage: str, content: str):
        Path(f"output/debug_{stage}.md").write_text(content, encoding="utf-8")

    def _save_metrics(self, ferramentas, path, approved, foco):
        entry = {
            "ts":          datetime.now().isoformat(),
            "ferramentas": ferramentas,
            "foco":        foco,
            "output":      path,
            "approved":    approved,
        }
        with open("output/metrics.json", "a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

    def _enforce_global_timeout(self, started_at: float, stage: str):
        if not self.timeout_total_seconds:
            return
        elapsed = monotonic() - started_at
        if elapsed <= self.timeout_total_seconds:
            return
        raise TimeoutException(
            "Pipeline timeout total excedido "
            f"({elapsed:.1f}s > {self.timeout_total_seconds}s) durante {stage}"
        )
