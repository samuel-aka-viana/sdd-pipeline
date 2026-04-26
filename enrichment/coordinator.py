import re
from time import monotonic


class EnrichmentCoordinator:

    def __init__(self, pipeline):
        self._p = pipeline

    # --- public interface (called by pipeline delegates) ---

    def enrich_analysis_with_tips(self, analysis: str, ferramentas: str, foco: str) -> str:
        p = self._p
        has_dicas = bool(
            re.search(r"^#{2,3}\s+(dicas|otimiza[çc][õo]es)\b", analysis, re.IGNORECASE | re.MULTILINE)
        )
        if has_dicas:
            p.log.console.print("[green]✓[/green] Análise já contém dicas/otimizações")
            return analysis

        p.log.console.print("[yellow]⚠[/yellow] Buscando dicas no Chroma...")
        try:
            query = f"{ferramentas} dicas tips otimizações best practices {foco}"
            tool_names = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
            primary_tool = tool_names[0] if tool_names else None
            tips_results = p.chroma.query_similar(query, tool=primary_tool, k=5)

            if not tips_results:
                p.log.console.print("[dim]Sem dicas encontradas no Chroma[/dim]")
                p.memory.log_event("analysis_enrich_failed", {"ferramentas": ferramentas, "reason": "no_chroma_tips"})
                return analysis

            tips_block = "\n## OTIMIZAÇÕES\n"
            tips_count = 0
            for result in tips_results[:5]:
                text = result.get("text", "")
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                for line in lines:
                    if any(kw in line.lower() for kw in ["comando", "config", "flag", "opção", "--", "cmd", "export"]):
                        tips_block += f"- {line}\n"
                        tips_count += 1
                        if tips_count >= 3:
                            break
                if tips_count >= 3:
                    break

            if tips_count > 0:
                p.log.console.print(f"[green]✓[/green] Enriquecido com {tips_count} dicas do Chroma")
                p.memory.log_event("analysis_enriched_with_tips", {"ferramentas": ferramentas, "tips_count": tips_count})
                return analysis + tips_block

            p.log.console.print("[dim]Sem dicas extraíveis encontradas[/dim]")
            return analysis

        except Exception as e:
            p.log.console.print(f"[dim]Erro ao enriquecer análise: {e}[/dim]")
            p.memory.log_event("analysis_enrich_error", {"ferramentas": ferramentas, "error": str(e)})
            return analysis

    def should_enrich_research_after_critic_failure(self, evaluation: dict, research_quality: str) -> bool:
        evidence_chunks = []
        evidence_chunks.extend(evaluation.get("problems", []))
        evidence_chunks.extend(evaluation.get("warnings", []))
        evidence_chunks.append(evaluation.get("correction_prompt", ""))
        combined_feedback = " ".join(str(c) for c in evidence_chunks).lower()

        enrichment_markers = (
            "referências insuficientes",
            "sem dados",
            "dados insuficientes",
            "não foram encontrados dados",
            "nao foram encontrados dados",
            "falta evidência",
            "falta evidencia",
            "dados mensuráveis",
            "dados measuráveis",
            "perguntas do contexto",
            "métricas mensuráveis",
            "metricas mensuraveis",
            "benchmark",
        )
        # NOTE: Removed "insuficiente" and "p95"/"throughput" because they match
        # structural issues like "Dicas insuficientes" or "Poucos erros documentados"
        # which are Writer problems, not Research problems.
        if any(marker in combined_feedback for marker in enrichment_markers):
            return True
        return research_quality == "weak"

    def enrich_research_and_analysis_for_critic(
        self,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        started_at: float,
        enrichment_number: int,
        evaluation: dict,
    ) -> tuple[str, str, str]:
        p = self._p
        p.memory.log_event("research_enrichment_started", {
            "ferramentas": ferramentas,
            "foco": foco,
            "enrichment_number": enrichment_number,
        })

        problems_text = " ".join(evaluation.get("problems", [])).lower()

        if "dicas insuficientes" in problems_text or "poucos erro" in problems_text:
            return self._enrich_via_reanalysis(ferramentas, contexto, foco, questoes, evaluation)

        cached_enrichment = self._enrich_via_chroma_cache(
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
            evaluation=evaluation,
        )
        if cached_enrichment is not None:
            return cached_enrichment

        p.log.console.print(
            "   [yellow]↻ Sem novos hits no Chroma; reutilizando pesquisa atual (sem busca web)[/yellow]"
        )
        return self._reuse_current_research_without_web(
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
        )

    def build_targeted_research_questions(self, evaluation: dict) -> list[str]:
        p = self._p
        prompt = p.prompts.get(
            "research_enricher",
            "targeted_research_questions",
            ferramentas=p.memory.get("ferramentas", ""),
            foco=p.memory.get("foco", ""),
            evaluation_report=evaluation.get("report", ""),
            problems=evaluation.get("problems", []),
            warnings=evaluation.get("warnings", []),
        )
        if prompt:
            try:
                from skills.schemas import TargetedQuestionsResult
                parsed = p.llm.generate_structured(
                    role="researcher",
                    model=p.llm.model_for_role("researcher"),
                    prompt=prompt,
                    schema=TargetedQuestionsResult,
                    temperature=p.spec.get("llm", {}).get("temperature", {}).get("researcher", 0.1),
                    num_ctx=p.spec.get("llm", {}).get("context_length", {}).get("researcher", 8192),
                    timeout=p.spec.get("llm", {}).get("timeout", {}).get("researcher", 300),
                )
                cleaned_questions = [q.strip() for q in parsed.questions if q.strip()]
                if cleaned_questions:
                    p.memory.log_event("targeted_questions_llm", {"count": len(cleaned_questions)})
                    return cleaned_questions[:8]
            except Exception as exc:
                p.memory.log_event("targeted_questions_llm_failed", {"error": str(exc)})

        return self._build_targeted_research_questions_fallback(evaluation)

    # --- private helpers ---

    def _reuse_current_research_without_web(
        self,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        started_at: float,
    ) -> tuple[str, str, str]:
        p = self._p
        current_research = p.memory.get("research", "")
        p.memory.log_event("research_reuse_without_web", {
            "ferramentas": ferramentas,
            "research_chars": len(current_research),
        })
        enriched_analysis = p.run_analysis_stage(
            research=current_research,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
        )
        enriched_analysis = self.enrich_analysis_with_tips(
            analysis=enriched_analysis,
            ferramentas=ferramentas,
            foco=foco,
        )
        enriched_quality = p.assess_research_quality(current_research)
        return current_research, enriched_analysis, enriched_quality

    def _enrich_via_chroma_cache(
        self,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        started_at: float,
        evaluation: dict,
    ) -> tuple[str, str, str] | None:
        p = self._p
        p.log.console.print(
            "   [yellow]♻ Reutilizando evidências do Chroma (sem nova busca web)[/yellow]"
        )

        targeted_questions = self.build_targeted_research_questions(evaluation)
        first_problem = str((evaluation.get("problems") or [""])[0]).strip()
        fallback_query = f"dados concretos para validar: {first_problem[:120]}" if first_problem else ""
        critic_feedback = " ".join(
            str(chunk).strip()
            for chunk in (
                list(evaluation.get("problems", []))
                + list(evaluation.get("warnings", []))
                + [evaluation.get("correction_prompt", "")]
            )
            if str(chunk).strip()
        )

        tools_list = p.parse_tools(ferramentas)
        enrichment_parts: list[str] = []
        total_hits = 0

        for tool in tools_list:
            p.enforce_global_timeout(started_at, stage=f"enriquecimento via Chroma ({tool})")
            queries = self._build_chroma_enrichment_queries(
                tool=tool,
                foco=foco,
                targeted_questions=targeted_questions,
                fallback_query=fallback_query,
                critic_feedback=critic_feedback,
            )

            seen_signatures: set[tuple[str, str]] = set()
            seen_urls: set[str] = set()
            tool_hits: list[dict] = []
            with p.log.task(f"Consultando cache semântico ({tool})"):
                for query in queries:
                    results = p.researcher.search_cached_content(query=query, tool=tool, k=8)
                    self._log_chroma_recovery_query(tool=tool, query=query, results=results)
                    self._append_unique_chroma_hits(
                        results=results,
                        seen_signatures=seen_signatures,
                        seen_urls=seen_urls,
                        tool_hits=tool_hits,
                    )
                    if len(tool_hits) >= 12 and len(seen_urls) >= 4:
                        break

            if not tool_hits:
                enrichment_parts.append(
                    f"## Evidências semânticas para correção ({tool})\n"
                    "- Sem resultados relevantes no Chroma."
                )
                continue

            total_hits += len(tool_hits)
            lines = [f"## Evidências semânticas para correção ({tool})"]
            for result in tool_hits[:12]:
                url = str(result.get("url", "")).strip()
                similarity = result.get("similarity", None)
                snippet = str(result.get("text", "")).replace("\n", " ").strip()[:350]
                if isinstance(similarity, (int, float)):
                    lines.append(f"- URL: {url} | Similaridade: {float(similarity):.2f}")
                else:
                    lines.append(f"- URL: {url}")
                lines.append(f"  Trecho: {snippet}")
            enrichment_parts.append("\n".join(lines))

        if total_hits == 0:
            p.memory.log_event("enrichment_via_chroma", {"ferramentas": ferramentas, "hits": 0, "used": False})
            return None

        enrichment_text = "\n\n".join(enrichment_parts)
        current_research = p.memory.get("research", "")
        enriched_research = f"{current_research}\n\n## EVIDÊNCIAS RECUPERADAS DO CHROMA\n{enrichment_text}"

        p.memory.set("research", enriched_research)
        p.save_debug("research_chroma_enriched", enrichment_text)
        p.memory.log_event("enrichment_via_chroma", {"ferramentas": ferramentas, "hits": total_hits, "used": True})

        enriched_analysis = p.run_analysis_stage(
            research=enriched_research,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
        )
        enriched_analysis = self.enrich_analysis_with_tips(
            analysis=enriched_analysis,
            ferramentas=ferramentas,
            foco=foco,
        )
        enriched_quality = p.assess_research_quality(enriched_research)
        return enriched_research, enriched_analysis, enriched_quality

    def _build_chroma_enrichment_queries(
        self,
        tool: str,
        foco: str,
        targeted_questions: list[str],
        fallback_query: str,
        critic_feedback: str,
    ) -> list[str]:
        queries: list[str] = []
        for question in (targeted_questions or [])[:8]:
            clean = str(question).strip()
            if clean:
                queries.append(f"{tool} {clean}")

        feedback = critic_feedback.lower()
        if any(term in feedback for term in ("referências insuficientes", "fontes", "urls")):
            queries.extend([
                f"{tool} documentação oficial referência",
                f"{tool} github release notes migration guide",
                f"{tool} example tutorial with source links",
            ])
        if any(term in feedback for term in ("erro", "problema", "troubleshoot", "falha")):
            queries.extend([
                f"{tool} common errors troubleshooting",
                f"{tool} known issue solution",
            ])
        if any(term in feedback for term in ("benchmark", "latência", "throughput", "performance", "métrica")):
            queries.extend([
                f"{tool} benchmark throughput p95 latency",
                f"{tool} performance numbers methodology",
            ])

        if foco.strip():
            queries.append(f"{tool} {foco} dados técnicos")
        if fallback_query:
            queries.append(f"{tool} {fallback_query}")
        queries.append(f"{tool} evidências técnicas oficiais")

        deduped: list[str] = []
        seen: set[str] = set()
        for query in queries:
            clean = " ".join(str(query).split()).strip()
            if not clean:
                continue
            key = clean.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(clean)
        return deduped[:12]

    def _log_chroma_recovery_query(self, tool: str, query: str, results: list[dict]) -> None:
        event_log = getattr(getattr(self._p, "log", None), "event_log", None)
        if event_log is None:
            return
        event_log.log_event("chroma_recovery_query", {
            "tool": tool,
            "query": query,
            "results_count": len(results),
            "urls": self._unique_result_urls(results),
        })

    @staticmethod
    def _append_unique_chroma_hits(
        results: list[dict],
        seen_signatures: set[tuple[str, str]],
        seen_urls: set[str],
        tool_hits: list[dict],
    ) -> None:
        for result in results:
            url = str(result.get("url", "")).strip()
            text = str(result.get("text", "")).strip()
            if not text:
                continue
            signature = (url, text[:160])
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            if url:
                seen_urls.add(url)
            tool_hits.append(result)
            if len(tool_hits) >= 12 and len(seen_urls) >= 4:
                return

    @staticmethod
    def _unique_result_urls(results: list[dict]) -> list[str]:
        urls: list[str] = []
        seen_urls: set[str] = set()
        for result in results:
            url = str(result.get("url", "")).strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            urls.append(url)
        return urls

    def _enrich_via_reanalysis(
        self,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        evaluation: dict,
    ) -> tuple[str, str, str]:
        p = self._p
        p.log.console.print(
            "   [yellow]♻ Re-analisando URLs já coletadas para extrair dicas/erros[/yellow]"
        )

        problems_text = " ".join(evaluation.get("problems", [])).lower()
        focus_on = "tips_and_errors"
        if "dicas insuficientes" in problems_text and "poucos erro" not in problems_text:
            focus_on = "tips_only"
        elif "poucos erro" in problems_text and "dicas insuficientes" not in problems_text:
            focus_on = "errors_only"

        tools_list = p.parse_tools(ferramentas)
        enrichment_parts = []

        for tool in tools_list:
            try:
                with p.log.task(f"Re-analisando conteúdo em cache ({tool})"):
                    tips_and_errors = p.researcher.reanalyze_urls_for_tips_and_errors(
                        tool=tool,
                        focus_on=focus_on,
                    )
                tips_count = len(re.findall(r"(?:^|\n)\s*-\s+", tips_and_errors))
                p.log.console.print(f"   [green]✓[/green] Reanálise {tool}: ~{tips_count} itens extraídos")
                p.memory.log_event("reanalysis_tool_done", {
                    "tool": tool,
                    "focus_on": focus_on,
                    "items_count": tips_count,
                })
                enrichment_parts.append(f"# {tool}\n{tips_and_errors}")
            except Exception as e:
                p.log.error(f"Reanalysis failed for {tool}: {e}")
                enrichment_parts.append(f"# {tool}\n(Re-análise falhou)")

        enrichment_text = "\n\n".join(enrichment_parts)
        current_research = p.memory.get("research", "")
        enriched_research = f"{current_research}\n\n## ANÁLISE DE URLS JÁ COLETADAS\n{enrichment_text}"

        p.memory.set("research", enriched_research)
        p.save_debug("research_reanalyzed", enrichment_text)

        enriched_analysis = p.run_analysis_stage(
            research=enriched_research,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=monotonic(),
        )
        enriched_analysis = self.enrich_analysis_with_tips(
            analysis=enriched_analysis,
            ferramentas=ferramentas,
            foco=foco,
        )
        enriched_quality = p.assess_research_quality(enriched_research)
        return enriched_research, enriched_analysis, enriched_quality

    def _build_targeted_research_questions_fallback(self, evaluation: dict) -> list[str]:
        feedback_chunks = []
        feedback_chunks.extend(evaluation.get("problems", []))
        feedback_chunks.extend(evaluation.get("warnings", []))
        feedback_chunks.append(evaluation.get("correction_prompt", ""))
        feedback_text = " ".join(str(c) for c in feedback_chunks).lower()

        questions = []
        if any(term in feedback_text for term in ("referências insuficientes", "fontes", "urls")):
            questions.append("fontes oficiais e comunitárias confiáveis para este tópico")
        if any(term in feedback_text for term in ("erro", "armadilha", "troubleshoot")):
            questions.append("erros comuns reais com causa e solução validada")
        if any(term in feedback_text for term in ("instala", "comando", "endpoint-url", "curl")):
            questions.append("comandos de instalação e verificação com sintaxe exata")
        if any(term in feedback_text for term in ("requisito", "hardware", "ram", "cpu")):
            questions.append("requisitos mínimos de hardware com números concretos")
        if any(term in feedback_text for term in ("benchmark", "latência", "throughput", "performance")):
            questions.append("benchmarks e métricas de performance com metodologia")

        if not questions and evaluation.get("problems"):
            first_problem = str(evaluation["problems"][0]).strip()
            if first_problem:
                questions.append(f"dados concretos para corrigir: {first_problem[:120]}")

        return questions[:4]
