import os
import yaml
import json
from datetime import datetime
from pathlib import Path

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
            alt = next((t for t in tools_list if t != tool), "")
            with self.log.task(f"Pesquisando {tool}"):
                data = self.researcher.run(
                    tool=tool,
                    alternative=alt,
                    foco=foco,
                    questoes=questoes,
                )
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
        with self.log.task("Gerando análise"):
            analysis = self.analyst.run(
                research=research,
                ferramentas=ferramentas,
                contexto=contexto,
                foco=foco,
                questoes=questoes,
            )

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
        article    = ""
        evaluation = {"approved": False, "problems": [], "correction_prompt": ""}

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            self.log.iteration(iteration, self.MAX_ITERATIONS)

            with self.log.task("Escrevendo artigo"):
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

            # pós-processamento: remove frases proibidas que o modelo insiste
            article = self._sanitize_article(article)

            with self.log.task("Validando contra spec"):
                evaluation = self.critic.evaluate(article, ferramentas)

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