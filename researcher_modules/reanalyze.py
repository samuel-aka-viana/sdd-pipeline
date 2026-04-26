import json
import re


def reanalyze_urls_for_tips_and_errors(
    tool: str,
    focus_on: str,
    chroma,
    scraped_urls: dict,
    memory,
    prompts,
    llm,
    model: str,
    temp: float,
    ctx_len: int,
    timeout: int,
) -> str:
    scraped_count = 0
    if scraped_urls is not None:
        try:
            scraped_count = len(scraped_urls)
        except TypeError:
            scraped_count = 1
    if chroma is None and scraped_count == 0:
        return "Nenhuma URL foi scrapada para re-análise."

    context_lines = []

    if chroma is not None:
        if focus_on != "errors_only":
            tips_query = f"{tool} dicas otimização tips best practices"
            tips_results = chroma.query_similar(
                tips_query,
                tool=tool,
                k=5,
                distance_threshold=0.25,
            )
            memory.log_event("chroma_query", {
                "tool": tool,
                "query": tips_query,
                "results_count": len(tips_results),
                "query_type": "tips",
            })
            for result in tips_results:
                context_lines.append(f"URL: {result['url']}")
                context_lines.append(result["text"][:1000])
                context_lines.append(f"(Similaridade: {result['similarity']:.2f})")
                context_lines.append("---")

        if focus_on != "tips_only":
            error_query = f"{tool} erros problemas errors troubleshooting solução"
            error_results = chroma.query_similar(
                error_query,
                tool=tool,
                k=5,
                distance_threshold=0.25,
            )
            memory.log_event("chroma_query", {
                "tool": tool,
                "query": error_query,
                "results_count": len(error_results),
                "query_type": "errors",
            })
            for result in error_results:
                context_lines.append(f"URL: {result['url']}")
                context_lines.append(result["text"][:1000])
                context_lines.append(f"(Similaridade: {result['similarity']:.2f})")
                context_lines.append("---")
    else:
        for url, content in list(scraped_urls.items())[:5]:
            context_lines.append(f"URL: {url}")
            context_lines.append(content[:1000])
            context_lines.append("---")

    context = "\n".join(context_lines)

    prompt = prompts.get(
        "research_enricher",
        "reanalyze_cached_content",
        tool=tool,
        focus_on=focus_on,
        cached_context=context,
    )
    if not prompt:
        raise RuntimeError("Prompt template missing: prompts/research_enricher.yaml#reanalyze_cached_content")

    resp = llm.generate(
        role="researcher",
        model=model,
        prompt=prompt,
        temperature=temp,
        num_ctx=ctx_len,
        timeout=timeout,
    )

    parsed = {}
    try:
        parsed = json.loads(resp.response)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", resp.response, flags=re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                parsed = {}

    if isinstance(parsed, dict):
        tips = parsed.get("tips", []) if focus_on != "errors_only" else []
        errors = parsed.get("errors", []) if focus_on != "tips_only" else []
        lines = []
        if tips:
            lines.append("## Dicas Encontradas")
            for tip in tips:
                if isinstance(tip, dict):
                    tip_text = str(tip.get("text", "")).strip()
                    evidence = str(tip.get("evidence", "")).strip()
                    source_url = str(tip.get("source_url", "")).strip()
                    if tip_text:
                        lines.append(f"- {tip_text}")
                        if evidence:
                            lines.append(f"  Evidência: {evidence}")
                        if source_url:
                            lines.append(f"  Fonte: {source_url}")
        if errors:
            lines.append("## Erros Comuns")
            for error in errors:
                if isinstance(error, dict):
                    problem = str(error.get("problem", "")).strip()
                    solution = str(error.get("solution", "")).strip()
                    evidence = str(error.get("evidence", "")).strip()
                    source_url = str(error.get("source_url", "")).strip()
                    if problem:
                        lines.append(f"- **Erro**: {problem}")
                        if solution:
                            lines.append(f"  **Solução**: {solution}")
                        if evidence:
                            lines.append(f"  Evidência: {evidence}")
                        if source_url:
                            lines.append(f"  Fonte: {source_url}")
        if lines:
            return "\n".join(lines)

    return resp.response
