# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Architecture: 4-Stage Pipeline

**SDD Tech Writer** is a specialized system that generates technical articles through a multi-stage LLM pipeline:

```
INPUT (CLI)
  ↓
[Research]  ← Search the web + scrape URLs + extract context
  ↓
[Analysis]  ← Structure research into tables/pros/cons/recommendations
  ↓
[Writing]   ← Generate complete article from analysis + research context
  ↓
[Critic]    ← Validate article against spec rules; if fails, loop back to Writer with corrections
  ↓
OUTPUT (Markdown article)
```

**Key architectural fact:** Each stage is a separate LLM call with its own model/temperature/timeout config from `spec/article_spec.yaml`. The pipeline chains them together via `pipeline.py` with a retry loop on critic rejection.

---

## Scraping & Persistence Layer

### Unified Scraper: Crawl4AI

**Status:** ✅ **Integrated & Working**

Crawl4AI replaces the previous multi-dependency chain (playwright + curl_cffi + trafilatura). It handles:
- JavaScript rendering (CloudFlare challenges, dynamic content)
- Native markdown extraction (`result.markdown_v2.raw_markdown`)
- Automatic encoding detection
- Domain-specific context management (per-domain browser contexts)

**Key files:**
- `tools/scraper_crawl4ai.py` — Main Crawl4AI wrapper with async batch processing
- `tools/scraper_factory.py` — Automatic provider selection + fallback logic
- `tools/scraper_tool.py` — Fallback scraper (Playwright + curl_cffi) for edge cases

**Optimization: Async Batching**

Researcher uses ThreadPoolExecutor to scrape 10+ URLs in parallel:
```python
# In skills/researcher.py
results = []
with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(scraper.extract_text, url): url for url in urls}
    for future in as_completed(futures):
        results.append(future.result())
```
**Gain:** ~60% faster scraping for multi-URL research.

**Fallback Logic**

If Crawl4AI fails 3+ consecutive times on a domain:
1. Switch to ScraperTool (playwright + curl_cffi) for that domain
2. Log: `"Fallback to ScraperTool after 3 Crawl4AI failures for {domain}"`
3. Continue without breaking the run

---

### Vector Database: Chroma (Semantic Search)

**Status:** ✅ **Integrated & Working**

Chroma provides semantic similarity search across all previously scraped content. This enables **cross-tool knowledge transfer** (e.g., finding Docker tips when researching Podman).

**Key files:**
- `memory/research_chroma.py` — Chroma PersistentClient wrapper
- Integrated in `skills/researcher.py` for reanalysis and smart enrichment

**Database:** `.memory/chroma_db/` (parquet format, persistent across runs)

**Key methods:**

```python
# Save scraped content with intelligent chunking
chroma.save_scraped_content(
    tool="Docker",
    url="https://docs.docker.com/...",
    title="Docker Security Best Practices",
    content=raw_content,
    markdown_raw=structured_markdown,  # From Crawl4AI
    source_quality="official",  # or "trusted", "medium", "unknown"
)

# Semantic search (k-NN with cosine similarity)
results = chroma.query_similar(
    query_text="docker rootless performance optimization",
    tool=None,  # Search across all tools if None
    k=5,
    distance_threshold=0.3,  # Min similarity (0-1)
)

# Cross-tool knowledge transfer
results = chroma.cross_tool_search(
    query_text="kubernetes deployment strategies",
    exclude_tool="Kubernetes",  # Don't return results from this tool
    k=5,
)
```

**Intelligent Chunking:**
- Splits long documents into 1000-char chunks with 200-char overlap
- Preserves context at chunk boundaries
- Each chunk stored with metadata (URL, title, tool, quality)

---

### Smart Enrichment vs Re-search

**Problem:** When critic says "Insufficient tips", old system re-ran entire 10-minute search. New system uses **semantic reanalysis**.

**Smart Enrichment Flow (NEW):**

```python
# In pipeline.py._enrich_via_reanalysis()
if "tips" in feedback.lower() or "dicas" in feedback.lower():
    # Query Chroma for semantically similar content
    results = chroma.query_similar(
        query_text=f"{tool} tips best practices optimization",
        k=10,
        distance_threshold=0.25,
    )
    # Re-analyze the found content without new search
    reanalysis = researcher.reanalyze_urls_for_tips_and_errors(
        urls=results,
        focus_on="tips_only",
    )
    # Merge into research block for Writer
    enriched_research = research + "\n\n## ANÁLISE DE URLS JÁ COLETADAS\n" + reanalysis
```

**Result:** Insufficient tips → 5-second reanalysis (vs 10-minute re-search)

---

## Critical Problem: Context Loss

⚠️ **STATUS:** Addressed with Chroma vector database + smart enrichment

The pipeline still truncates data at each stage:
- Researcher scrapes ~40KB from 10 URLs
- Writer receives max 24KB of research
- Writer receives max 10KB of analysis
- Article output: ~2-3KB

**Mitigation strategies in place:**
1. **Chroma semantic search** — Find most relevant content for reanalysis (no truncation loss)
2. **Smart enrichment** — Use cached content instead of new search
3. **Chroma vector storage** — Persist all content with embeddings for cross-session reuse
4. **Markdown caching** — Store structured markdown from Crawl4AI (preserves headers/structure)

**When modifying writer.py, analyst.py, or researcher.py:**
- Check `spec/article_spec.yaml` → `llm.writer_input` section for truncation limits
- If truncating data, log it: `logger.warning(f"TRUNCATED {label}: {loss} chars")`
- Consider using Chroma for semantic filtering instead of raw truncation
- See `CONTEXT_ANALYSIS.md` for deeper analysis

---

## Common Commands

### Run
```bash
# Interactive CLI (collects tools, context, focus, questions)
python main.py

# Force refresh of search cache (ignore 24h TTL)
python main.py --refresh-search

# Monitor pipeline events in real-time
python watch_events.py --watch

# View debug outputs from last run
python watch_events.py --tail=30
```

### Test
```bash
# Run all tests
uv run pytest -q

# Run one test suite
uv run pytest tests/test_skills.py -v

# Run one test
uv run pytest tests/test_pipeline.py::test_run_research_stage -v

# Coverage report
uv run pytest --cov=skills --cov=pipeline tests/ --cov-report=term-missing
```

### Lint
```bash
# Check for unused imports/variables/arguments (the important stuff)
uv run ruff check . --select ARG,F401,F841

# Full ruff suite
uv run ruff check .

# Fix style issues
uv run ruff format .
```

### Setup
```bash
# Virtual environment
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies
uv sync

# Optional: Playwright fallback (for edge cases)
uv add playwright
playwright install chromium

# Optional: Crawl4AI (for improved scraping)
uv add crawl4ai

# Optional: Chroma (for semantic search persistence)
uv add chromadb
```

---

## Configuration

### Two sources of config:

**1. `spec/article_spec.yaml`** — Rules, limits, and pipeline behavior
- `llm.temperature.{role}` — LLM creativity per role (researcher/analyst/writer/critic)
- `llm.timeout.{role}` — Request timeout per role
- `llm.context_length.{role}` — Context window hint per role
- `llm.writer_input.max_research_chars` — **Truncation limit for research** (default 24000)
- `llm.writer_input.max_analysis_chars` — **Truncation limit for analysis** (default 10000)
- `research.scraper.max_chars_per_page` — Truncation at scrape time (default 4000)
- `research.search_cache.ttl_seconds` — How long to cache search results (default 86400 = 24h)
- `pipeline.max_iterations` — Retry loop limit for critic rejections
- `pipeline.max_research_enrichments` — When critic flags missing data, how many times to re-run research

**2. `.env`** — Runtime provider and model selection
```env
LLM_PROVIDER=openrouter_free  # or ollama_local, ollama_cloud
LLM_MODEL_RESEARCHER=...
LLM_MODEL_ANALYST=...
LLM_MODEL_WRITER=...
LLM_MODEL_CRITIC=...
# Optional fallback models
LLM_MODEL_FALLBACK_CLOUD=glm5.1:cloud
LLM_MODEL_FALLBACK_LOCAL=llama2:latest
```

**Validation:** `pipeline.py` loads and validates spec against `spec/schema.json` at startup.

---

## Error Handling & Resilience

### Minimal Logging Strategy

All scrapers now use **minimal, structured logging** to avoid context spam:
- No stack traces (only `error_type`)
- No verbose messages (only URL prefix + error summary)
- Debug-level logging for investigation, warning-level for important issues

**Example:**
```python
# Old: 5 lines per error
except Exception as e:
    log.error(f"Failed to scrape {url}: {e}")
    log.error(traceback.format_exc())

# New: 1 line, actionable
except Exception as e:
    error_type = type(e).__name__
    log.debug(f"trafilatura [{error_type}]: {url[:60]}")
```

**In tools/scraper_tool.py:**
- `cffi_fetch()` — logs `cffi [ErrorType] attempt N: {url_prefix}`
- `trafilatura_extract()` — logs `trafilatura [ErrorType]: {url_prefix}`
- `playwright_extract()` — detects threading errors (greenlet) and silent-fallbacks them

### Threading Error Handling ✅ **FIXED**

**Problem:** Playwright sync_api in ThreadPoolExecutor throws `greenlet.error: Cannot switch to a different thread`.

**Solution:** Use async Playwright (async_api) instead. Each thread gets its own event loop:

```python
# In scraper_tool.py
def playwright_extract(self, url: str) -> dict:
    """Sync wrapper that creates own event loop per call."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(self._playwright_extract_async(url))
    return result

async def _playwright_extract_async(self, url: str) -> dict:
    """Async implementation using async_playwright context manager."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # ... rest of async extraction
```

**Why it works:**
- Each thread gets own `asyncio.new_event_loop()` → no greenlet conflicts
- Async context manager properly manages browser lifecycle
- No persistent browser objects shared across threads

**Result:** Zero threading errors; Playwright works reliably in ThreadPoolExecutor.

### Fallback Chain (in scraper_factory.py)

```
Crawl4AI success
  ↓ (failure)
Crawl4AI retry #1, #2
  ↓ (3+ failures)
ScraperTool (Playwright + curl_cffi)
  ↓ (if available)
Log error, return empty content
```

Fallback is automatic and silent (users don't see error details).

---

## Memory and Persistence

### Three-layer memory (`memory/memory_store.py`):
1. **working** — in-RAM session state, lost at exit
2. **episodic** — `.memory/episodic.json`, log of all events (50 events max, rotated)
3. **procedural** — `.memory/procedural.json`, learned fixes (pattern → solution)

**Used by:** Writer calls `memory.get_lessons_for_prompt()` to inject top 3 learned patterns into LLM prompt.

### Chroma Vector Database (`memory/research_chroma.py`) ✅ **Primary Storage**

**Database:** `.memory/chroma_db/` with HNSW indexing for semantic similarity

**Purpose:** Unified persistence layer for all scraped research content. Replaces SQLite FTS with semantic embeddings.

**Key features:**
- Semantic search (find concepts similar to "docker container isolation")
- Intelligent chunking (1000 chars with 200-char overlap for context)
- Automatic embedding generation
- Cross-tool knowledge transfer (find Docker tips when researching Podman)

**Integration in researcher.py:**
```python
# Save scraped content automatically (semantic chunks)
self.chroma.save_scraped_content(
    tool="Docker",
    url="https://...",
    title="...",
    content=raw_text,
    markdown_raw=structured_markdown,  # From Crawl4AI
    source_quality="official",
)

# Semantic reanalysis (smart enrichment)
if "tips insuficientes" in critic_feedback:
    similar = chroma.query_similar(
        query_text=f"{tool} tips best practices",
        k=10,
        distance_threshold=0.25,
    )

# Cross-tool knowledge transfer
results = chroma.cross_tool_search(
    query_text="rootless containers",
    exclude_tool="Podman",
    k=5,
)
```

**Advantages over previous SQLite FTS:**
- Semantic understanding (similar concepts, not just keywords)
- Automatic embeddings (no separate indexing step)
- Chunking for better context preservation
- Single unified storage (no sync issues)

---

## Agentic Improvements (Stage 3)

This section documents the 5-part upgrade from Stage 2 (sequential multi-agent) to Stage 3 (smarter, parallel, adaptive).

### 1. Critic Improvements (skills/critic.py)

**Problem:** Critic couldn't detect issues in the bottom half of articles due to 4000-char truncation.

**Solution:**
- Expanded semantic window from 4000 → 12000 chars (configurable: `self.semantic_window`)
- Added **tool-aware false positive filtering** (e.g., "rootless" is valid for containers, not an error)
- Separated problems into severity levels: `{"blocking": [...], "warnings": [...]}`
- Implemented `validate_min_tips()` to count ## Dicas headers + list items

**Files:**
- `skills/critic.py` — See `semantic_check()` and `filter_known_false_positives()`
- `validators/spec_validator.py` — See `validate_min_tips()`

---

### 2. Tool-Type Router (skills/router.py)

**Purpose:** Classify tool pair + focus → optimal pipeline configuration

**Method:** `router.classify(ferramentas, foco)` returns:
```python
{
    "tool_type": "containers|orchestration|databases_olap|...",
    "research_boost_queries": ["docker rootless", "..."],
    "skip_sections": [],  # Sections irrelevant for this combo
    "rule_profile": "containers",  # Used by RulesEngine
    "can_parallelize_analysis": True|False,
    "analysis_aspects": ["core", "performance", "security"],  # For parallel run
}
```

**Classification:**
- Docker, Podman, containerd → `containers`
- Kubernetes, K3s, kind → `orchestration`
- PostgreSQL, MySQL → `databases_oltp`
- DuckDB, ClickHouse → `databases_olap` (requires benchmarks)
- Ollama, LM Studio → `llm_tools`
- Python, Go, Rust → `languages`
- (and more in `skills/router.py:TOOL_MAP`)

**Used by:** `pipeline.py` injects router results into all stages for optimized behavior.

---

### 3. Adaptive Rules Engine (validators/rules_engine.py)

**Purpose:** Override quality rule thresholds based on tool_type and focus

**Profiles:**
```python
PROFILES = {
    "containers": {
        "min_references": 5,
        "min_errors": 2,
        "min_tips": 3,
        "require_benchmark": False,
    },
    "databases_olap": {
        "min_references": 4,
        "min_errors": 2,
        "min_tips": 2,
        "require_benchmark": True,  # ← Performance comparison needed
    },
    "llm_tools": {
        "min_references": 3,
        "min_errors": 2,
        "min_tips": 2,
        "require_benchmark": True,
    },
    # ... + default profile
}
```

**Dynamic adjustment:**
- `foco="performance / throughput"` → `require_benchmark = True`
- `foco="segurança"` → `min_errors = max(profile['min_errors'], 3)`

**Used by:** `spec_validator.py` uses profile thresholds instead of hardcoded spec values.

**In pipeline.py:**
```python
route = self.router.classify(ferramentas, foco)
profile = self.rules_engine.get_profile(route["tool_type"], foco)
self.validator.validate(artigo, profile=profile)
```

---

### 4. Prompt Versioning (prompts/manager.py + YAML files)

**Purpose:** Extract prompts to YAML for version tracking and metric logging

**New directory structure:**
```
prompts/
├── manager.py           # PromptManager class
├── researcher.yaml      # Prompt templates for researcher role
├── analyst.yaml
├── writer.yaml
└── critic.yaml
```

**Usage:**
```python
manager = PromptManager(memory, prompts_dir="prompts")
prompt = manager.get(
    role="researcher",
    template_key="main_search",
    tool="Docker",
    foco="performance",
)
# Automatically logs: role, template_key, version, rendered_chars
```

**Benefits:**
- Version tracked in YAML (can do A/B testing on different prompt versions)
- Metrics logged: `memory.log_event("prompt_used", {...})`
- Future: analyze which prompts give best results per tool_type

---

### 5. Parallel Analysis (pipeline.py)

**Problem:** Analyst ran once with all research + analysis at once (serial).

**Solution:** Run analyst in parallel per aspect:

```python
# In pipeline.run_analysis_stage()
aspects = route.get("analysis_aspects", ["core"])

if len(aspects) > 1:
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(self.analyst.run, research, ferramentas, aspect, questoes): aspect
            for aspect in aspects
        }
        # Collect results as they complete
        results = {aspect: future.result() for future, aspect in futures.items()}
        
    # Merge into single block
    merged = "\n\n---\n\n".join(
        f"## Analysis: {asp}\n{results[asp]}"
        for asp in aspects
    )
```

**Safe:** `analyst.run()` is stateless (no shared mutable state), so ThreadPoolExecutor is safe.

**Result:** For Docker vs Podman with 3 aspects, analyst runs in ~1/3 the time.

---

## Testing Strategy

- **Unit tests** (`test_skills.py`, `test_skills_mocked.py`): Individual skill logic with mocked LLM
- **Integration** (`test_pipeline.py`): Full pipeline with mocked LLM (fast, deterministic)
- **E2E** (`test_pipeline_e2e.py`): Real LLM calls (slow, use sparingly, requires `.env` config)
- **Schema** (`test_spec_schema.py`): Validates `spec/article_spec.yaml` structure
- **Validation** (`test_spec_validator.py`): Critic rules enforcement

**Current coverage:** 142 tests passing. Aim to keep it green when modifying pipeline or skills.

### Chroma Data Verification

For interactive testing of Chroma queries and data isolation:

```bash
# Interactive Chroma tester
python test_chroma_queries.py

# Options:
# 1 - Chroma statistics (chunks per tool, URLs)
# 2 - Tool isolation verification (no data mixing)
# 3 - Interactive semantic search
# 4 - Cross-tool knowledge transfer
# 5 - Data integrity check
```

See `CHROMA_TESTING.md` for detailed testing guide.

---

## Key Decision Points

### Q: Should I add a new skill?
**A:** Skills are LLM-based stages that transform inputs into outputs. Examples: researcher, analyst, writer, critic.
- Create `skills/new_skill.py` with a class that has a `run()` method
- Call it from appropriate `pipeline.run_*_stage()` method
- Log events via `memory.log_event()`
- See `docs/extending-with-new-skill.md`

### Q: Should I change LLM timeouts/temps?
**A:** Edit `spec/article_spec.yaml`, not the skill files. Allows runtime config without code changes.

### Q: Should I change truncation limits?
**A:** Edit `spec/article_spec.yaml` → `llm.writer_input.max_research_chars|max_analysis_chars`. But first:
- Check `CONTEXT_ANALYSIS.md` to understand why we're losing data
- Add loss logging in `skills/writer.py:compact_text_block()` so we see truncations happen
- Consider using Chroma semantic filtering instead of raw truncation (already implemented for smart enrichment)

### Q: Should I fix something in the researcher/analyst/writer/critic?
**A:** Check `AGENTS.md` for exact file paths and method signatures before editing. Also check `spec/article_spec.yaml` for related config that might need changing.

### Q: The article is too short/generic/wrong — what do I debug?
**A:** Check in order:
1. Research quality: Does `output/debug_research.md` have enough real data?
2. Analysis quality: Does `output/debug_analysis.md` have structured tables/pros/cons?
3. Data truncation: Did `max_research_chars` or `max_analysis_chars` truncate important sections? (Check logs)
4. Critic rules: Did critic reject it? Check `output/pipeline_events.jsonl` for critic feedback

---

## Project File Reference

**Always check `AGENTS.md`** before modifying code. It has:
- Exact file paths with responsibilities
- Method signatures and data flow
- Which files import which
- Config locations for each module
- Checklist before modifying

**Core Scraping & Persistence:**
- `tools/scraper_crawl4ai.py` — Main Crawl4AI wrapper (async batching, markdown extraction)
- `tools/scraper_factory.py` — Provider selection + fallback logic (Crawl4AI → ScraperTool)
- `tools/scraper_tool.py` — Fallback scraper (async Playwright + curl_cffi with minimal error logging)
- `memory/research_chroma.py` — Chroma vector database (semantic search, chunking, primary storage)

**Skills & Pipeline:**
- `skills/researcher.py` — Integrates Crawl4AI + Chroma + async scraping + smart enrichment
- `skills/critic.py` — Expanded semantic window + tool-aware FP filtering + severity levels
- `pipeline.py` — Injects router + rules engine + parallel analysis

**Agentic Improvements:**
- `skills/router.py` — Tool-type classification + aspect detection
- `validators/rules_engine.py` — Adaptive thresholds per tool_type
- `prompts/manager.py` — YAML template loading + metric logging
- `prompts/*.yaml` — Extracted prompt templates (researcher, analyst, writer, critic)

**Validation & Configuration:**
- `validators/spec_validator.py` — Rule enforcement + `validate_min_tips()` implementation
- `spec/article_spec.yaml` — Limits, thresholds, pipeline config

**Documentation:**
- `CONTEXT_ANALYSIS.md` — Deep dive into context loss problem + roadmap
- `CHROMA_DATA_SEPARATION.md` — Chroma indexing & tool-based filtering to prevent data mixing
- `RESEARCH_REUSE_GUIDE.md` — Research history, reuse patterns, performance gains
- `README.md` — Setup, quickstart, examples
- `examples.md` — Curated examples of good prompts for each topic
- `MONITORING.md` — Event logging and observability
- `AGENTS.md` — **ALWAYS READ THIS** before modifying code

---

## Output Locations

- `artigos/{tool}_{timestamp}.md` — Final article
- `output/debug_research.md` — Raw research report from researcher
- `output/debug_analysis.md` — Analysis output from analyst
- `output/metrics.json` — Stats per execution (time, tokens, etc.)
- `.memory/episodic.json` — Log of events
- `.memory/procedural.json` — Learned fixes
- `.memory/search_cache.json` — Cached search results

---

## Common Integration Patterns

### Using Crawl4AI in Researcher

```python
# Import and instantiate (automatic detection)
from tools.scraper_factory import ScraperFactory
scraper = ScraperFactory.create("auto")  # Uses Crawl4AI if available

# Extract with structured markdown
for url in urls:
    result = scraper.extract_text(url)
    if result["status"] == "ok":
        # result["text"] = extracted content
        # result["source"] = "crawl4ai" or "original"
        # Markdown is automatically extracted if available
```

### Querying Chroma for Smart Enrichment

```python
from memory.research_chroma import ResearchChroma

chroma = ResearchChroma()

# Find semantically similar content (without new search)
similar = chroma.query_similar(
    query_text=f"{tool} tips optimization best practices",
    k=10,
    distance_threshold=0.25,
)

# Cross-tool knowledge transfer
related = chroma.cross_tool_search(
    query_text="container orchestration",
    exclude_tool="Kubernetes",
    k=5,
)
```

### Using Router for Aspect Detection

```python
from skills.router import ToolTypeRouter

router = ToolTypeRouter()
route = router.classify(ferramentas="Docker e Podman", foco="performance")

# route["tool_type"] = "containers"
# route["analysis_aspects"] = ["core", "performance"]
# route["can_parallelize_analysis"] = True
```

### Applying Adaptive Rules

```python
from validators.rules_engine import AdaptiveRulesEngine

rules = AdaptiveRulesEngine()
profile = rules.get_profile(tool_type="databases_olap", foco="performance")

# profile["require_benchmark"] = True (automatically set for OLAP + perf focus)
# profile["min_tips"] = 2
# Pass to validator: spec_validator.validate(artigo, profile=profile)
```

---

## When Making Changes

1. **Read AGENTS.md** — Understand file structure and dependencies
2. **Check spec/article_spec.yaml** — Any config that needs updating?
3. **Review CONTEXT_ANALYSIS.md** — Is this change affected by the truncation problem?
4. **Run tests** — `uv run pytest tests/ -q` before committing
5. **Test manually** — Run `python main.py` with a small example to verify behavior
6. **Update AGENTS.md** — If you added/renamed files or changed key responsibilities
7. **Update CLAUDE.md** — If you added/modified major components, document them here

---

## Monitoring & Verification

### View Pipeline Events
```bash
# Monitor in real-time (watches pipeline_events.jsonl)
python watch_events.py --watch

# Show last 30 events
python watch_events.py --tail=30

# Check for smart enrichment happening
grep -i "reanalyze\|smart" .memory/episodic.json

# Verify Chroma is being used
grep -i "chroma\|semantic" .memory/episodic.json

# Check scraper fallback logs
grep -i "fallback\|crawl4ai" .memory/episodic.json
```

### Verify Integration Points

**Crawl4AI is used:**
```bash
grep -r "crawl4ai\|Crawl4AI" skills/researcher.py tools/scraper_*.py
```

**Chroma is saving data:**
```bash
ls -lah .memory/chroma_db/
# Should have: index, uuid_to_data_uuid.parquet, data_level_0.parquet, etc
```

**Router classifying tools:**
```bash
grep -i "tool_type\|analysis_aspects" .memory/episodic.json | head -5
```

**Parallel analysis is running:**
```bash
grep -i "parallel\|threadpool\|aspect" .memory/episodic.json
```

### Metrics to Monitor

After running `python main.py`:
- Check `output/metrics.json` for:
  - `total_urls_scraped` (should be >= 3)
  - `scraper_source` (should be "crawl4ai" mostly)
  - `analysis_aspects` (should be > 1 if parallel analysis is enabled)
  - `pipeline_iterations` (1 = article passed on first try)
- Check `.memory/episodic.json` for:
  - `prompt_used` events (should log version, template_key)
  - `reanalyze_urls` events (if smart enrichment triggered)
  - `semantic_search` events (Chroma queries)

---

## Quick Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "429 Too Many Requests" | OpenRouter rate limit | Try `--refresh-search` (uses cache), or switch `LLM_PROVIDER=ollama_local` |
| Article has placeholders like "[TODO]" | Critic rules not enforced | Check `spec/article_spec.yaml` quality_rules; critic failed to catch it |
| Article is too generic | Research quality weak | Check `output/debug_research.md`; if empty, search queries didn't return results |
| "timeout" error | LLM call took too long | Increase `llm.timeout.{role}` in spec, or use faster model |
| Search results not changing | Cache not refreshed | Use `python main.py --refresh-search` to bypass TTL |
| Tests failing | Code changes broke skill logic | Run single test with `-v` to see assertion; check skill input/output contract |
| "Crawl4AI failed" in logs | Network issue or invalid URL | Check `tools/scraper_factory.py` fallback chain; will auto-switch to ScraperTool |
| ~~"playwright threading error"~~ | ~~ThreadPoolExecutor + sync_api~~  | ✅ **FIXED:** Now uses async_playwright with per-thread event loops (no more threading errors) |
| "Insufficient tips" feedback loop | Critic keeps rejecting articles | Use `--refresh-search` or check Chroma cache isn't stale; smart enrichment should trigger instead of re-search |
| Chroma queries return nothing | Vector database empty | Run one scrape first to populate `.memory/chroma_db/`; subsequent runs will use semantic search |

---

## LLM Provider Fallback Chain

The system tries providers in this order (configurable in `llm/client.py`):
1. **OpenRouter** (from `.env` LLM_PROVIDER) — Usually fastest, has free tier
2. **Ollama Cloud** — Fallback if OpenRouter fails (needs account)
3. **Ollama Local** — Last resort if both above fail (requires Ollama running locally)

If all fail, the skill raises an exception and pipeline halts with error. Crawl4AI failures → automatic silent fallback to ScraperTool.

---

## Implementation Checklist (Stage 2 → Stage 3)

### ✅ Completed
- [x] Crawl4AI unified scraper (replaces playwright + curl_cffi + trafilatura)
- [x] Async batch scraping with ThreadPoolExecutor (3 workers)
- [x] Chroma vector database for semantic search and primary storage
- [x] Smart enrichment (reanalyze vs re-search for insufficient tips)
- [x] Minimal error logging (no stack traces, error_type + URL only)
- [x] Threading error detection & silent fallback (greenlet handling)
- [x] Critic semantic window expansion (4000 → 12000 chars)
- [x] Tool-aware false positive filtering in critic
- [x] `validate_min_tips()` implementation in spec_validator
- [x] Router (tool-type classification + aspect detection)
- [x] Rules engine (adaptive thresholds per tool_type + foco)
- [x] Prompt versioning (YAML templates + manager)
- [x] Parallel analysis (ThreadPoolExecutor per aspect)

### 📋 Future Work

**Short-term:**
- Chroma to Docker Compose (separate persistent service for production)
- Source attribution (track which URL each claim comes from in article)
- Markdown structure preservation in Writer (preserve ## headers from research)

**Medium-term:**
- Autonomous re-research trigger (if Critic rejects 3x, suggest human review)
- A/B testing on prompt versions via metrics in memory.episodic
- Cross-tool knowledge indexing (build knowledge graph: Docker → Podman → containerd)

**Long-term:**
- Multimodal scraping (images, diagrams, code samples)
- Real-time web monitoring (alert if new Docker features appear)
- Federated learning on article quality (learn from community feedback)

---

## Summary: Stage 2 → Stage 3 Evolution

This document describes the **multi-layered upgrade** from a basic multi-agent pipeline (Stage 2) to an intelligent, adaptive system (Stage 3). The key changes:

1. **Unified Scraping** — Crawl4AI replaces 3 competing dependencies (playwright + curl_cffi + trafilatura), with graceful fallback for edge cases
2. **Semantic Persistence** — Chroma + SQLite enable smart enrichment (reuse cached content instead of re-searching) and cross-tool knowledge transfer
3. **Intelligent Routing** — Tool-type classification automatically optimizes research, analysis, and validation per tool category
4. **Adaptive Rules** — Quality thresholds adjust based on tool type (e.g., benchmarks mandatory for OLAP, optional for containers)
5. **Parallel Analysis** — Multiple aspects analyzed simultaneously via ThreadPoolExecutor, with no race conditions (stateless design)
6. **Prompt Versioning** — YAML templates with metric logging enable continuous improvement of prompt quality
7. **Better Error Handling** — Minimal, structured logging with automatic fallback makes failures transparent and non-blocking

**When working with this codebase:** Always refer back to this document. It's designed to be your single source of truth — no need to search the project for "where is Crawl4AI integrated?" or "how does smart enrichment work?" — **it's all here**.

**Key principle:** Every stage of the pipeline is optimized for its tool type and focus area. A Docker vs Podman comparison gets different research queries, different analysis aspects, and different quality thresholds than a DuckDB benchmark. This adaptation happens automatically based on the router's classification.
