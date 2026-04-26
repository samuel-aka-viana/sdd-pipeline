"""Chroma vector database persistence for research data.

Replaces SQLite FTS5 with semantic search via embeddings.
Supports intelligent chunking and k-NN similarity search.
"""
import logging
import os
import re
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class ResearchChroma:
    """Vector database persistence using Chroma for semantic search.

    Advantages over FTS5:
    - Semantic similarity (not just keyword matching)
    - Automatic embedding generation
    - k-NN search (find similar content across tools)
    - Intelligent chunking of long documents
    """

    def __init__(self, db_path: str = ".memory/chroma_db"):
        """Initialize Chroma persistent client."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # New Chroma API (v0.4+): Use persistent client
        self.client = chromadb.PersistentClient(path=str(self.db_path))

        collection_kwargs = {
            "name": "research",
            "metadata": {"hnsw:space": "cosine"},
        }
        embedding_provider = os.getenv("CHROMA_EMBEDDING_PROVIDER", "").strip().lower()
        if embedding_provider == "ollama":
            embed_url = (
                os.getenv("CHROMA_EMBED_OLLAMA_URL")
                or os.getenv("OLLAMA_LOCAL_BASE_URL")
                or os.getenv("OLLAMA_BASE_URL")
                or "http://localhost:11434"
            )
            embed_model = os.getenv("CHROMA_EMBED_MODEL", "nomic-embed-text:latest").strip()
            try:
                collection_kwargs["embedding_function"] = embedding_functions.OllamaEmbeddingFunction(
                    url=embed_url,
                    model_name=embed_model,
                )
                logger.info(
                    "Chroma embedding provider: ollama (%s @ %s)",
                    embed_model,
                    embed_url,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to init Ollama embedding function (%s). Falling back to Chroma default.",
                    exc,
                )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(**collection_kwargs)
        logger.info(f"Chroma collection ready: {self.db_path}")

    def chunk_content(self, content: str, chunk_size: int = 650, overlap: int = 120) -> list[dict]:
        """Split long content into semantic + overlapping chunks for better retrieval.

        Args:
            content: Text to chunk
            chunk_size: Characters per chunk
            overlap: Overlap between chunks (for context)

        Returns:
            List of {text, start, end} dicts
        """
        if not content:
            return [{"text": "", "start": 0, "end": 0}]

        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return [{"text": "", "start": 0, "end": 0}]

        def split_long_text(text: str, size: int) -> list[str]:
            text = text.strip()
            if not text:
                return []
            if len(text) <= size:
                return [text]

            parts: list[str] = []
            # Prefer sentence boundaries first.
            sentences = re.split(r"(?<=[.!?])\s+", text)
            current = ""
            for sentence in sentences:
                piece = sentence.strip()
                if not piece:
                    continue
                projected = f"{current} {piece}".strip() if current else piece
                if len(projected) <= size:
                    current = projected
                    continue
                if current:
                    parts.append(current)
                if len(piece) <= size:
                    current = piece
                    continue
                # Fallback for very long sentence/code block.
                for start in range(0, len(piece), size):
                    frag = piece[start:start + size].strip()
                    if frag:
                        parts.append(frag)
                current = ""
            if current:
                parts.append(current)
            return parts

        # 1) Build semantic units from headings/paragraph blocks.
        raw_units: list[str] = []
        blocks = re.split(r"\n{2,}", normalized)
        for block in blocks:
            cleaned = block.strip()
            if not cleaned:
                continue
            raw_units.extend(split_long_text(cleaned, chunk_size))

        if not raw_units:
            raw_units = split_long_text(normalized, chunk_size)
        if not raw_units:
            return [{"text": normalized, "start": 0, "end": len(normalized)}]

        # 2) Merge units into final chunks with explicit overlap text carry-over.
        chunks_text: list[str] = []
        current = ""
        for unit in raw_units:
            candidate = f"{current}\n\n{unit}".strip() if current else unit
            if len(candidate) <= chunk_size:
                current = candidate
                continue
            if current:
                chunks_text.append(current)
            if chunks_text and overlap > 0:
                tail = chunks_text[-1][-overlap:].strip()
                current = f"{tail}\n\n{unit}".strip() if tail else unit
                if len(current) > chunk_size:
                    current = unit
            else:
                current = unit
        if current:
            chunks_text.append(current)

        chunks: list[dict] = []
        cursor = 0
        for text in chunks_text:
            chunk_text = text.strip()
            if not chunk_text:
                continue
            start = cursor
            end = start + len(chunk_text)
            chunks.append({"text": chunk_text, "start": start, "end": end})
            cursor = end

        return chunks if chunks else [{"text": normalized, "start": 0, "end": len(normalized)}]

    def save_scraped_content(
        self,
        tool: str,
        url: str,
        title: str,
        content: str,
        markdown_raw: str = "",
        source_quality: str = "unknown",
        scrape_elapsed_seconds: Optional[float] = None,
    ) -> bool:
        """Save scraped content with intelligent chunking.

        Args:
            tool: Tool name (e.g., "DuckDB")
            url: Source URL
            title: Page title
            content: Full content to embed
            markdown_raw: Structured markdown (additional context)
            source_quality: 'official', 'trusted', 'medium', 'unknown'
            scrape_elapsed_seconds: Scrape duration

        Returns:
            True if saved successfully
        """
        try:
            text_to_embed = markdown_raw if markdown_raw else content
            MAX_EMBED_CHARS = 120_000
            if len(text_to_embed) > MAX_EMBED_CHARS:
                text_to_embed = text_to_embed[:MAX_EMBED_CHARS]

            chunks = self.chunk_content(text_to_embed)

            ids = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{tool}#{url}#{i}"
                ids.append(chunk_id)
                documents.append(chunk["text"])
                metadatas.append({
                    "tool": tool,
                    "url": url,
                    "title": title,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    "source_quality": source_quality,
                    "scrape_elapsed_seconds": str(scrape_elapsed_seconds or 0),
                })

            BATCH = 64
            for start in range(0, len(ids), BATCH):
                self.collection.upsert(
                    ids=ids[start:start + BATCH],
                    documents=documents[start:start + BATCH],
                    metadatas=metadatas[start:start + BATCH],
                )

            logger.debug(f"Saved {tool} from {url}: {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Failed to save to Chroma: {e}")
            return False

    def query_similar(
        self,
        query_text: str,
        tool: Optional[str] = None,
        k: int = 5,
        distance_threshold: float = 0.3,
    ) -> list[dict]:
        """Search for semantically similar content.

        Args:
            query_text: Search query (natural language)
            tool: Filter by tool (optional, searches across all if None)
            k: Number of results to return
            distance_threshold: Min similarity (0-1, higher = more similar)

        Returns:
            List of {text, url, title, similarity, chunk_index} dicts
        """
        try:
            # Where filter for tool (optional)
            where = {"tool": tool} if tool else None

            # Query with k-NN
            results = self.collection.query(
                query_texts=[query_text],
                n_results=k,
                where=where,
                include=["embeddings", "documents", "metadatas", "distances"],
            )

            # Convert distances to similarity scores (cosine distance → similarity)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            output = []
            for doc, metadata, distance in zip(documents, metadatas, distances):
                # Convert cosine distance (0-2) to similarity (0-1): similarity = 1 - distance/2
                similarity = max(0, 1 - distance / 2)

                if similarity >= distance_threshold:
                    output.append({
                        "text": doc,
                        "url": metadata.get("url"),
                        "title": metadata.get("title"),
                        "tool": metadata.get("tool"),
                        "source_quality": metadata.get("source_quality", "unknown"),
                        "similarity": similarity,
                        "chunk_index": metadata.get("chunk_index", 0),
                        "chunk_count": metadata.get("chunk_count", 1),
                    })

            logger.debug(f"Query '{query_text[:50]}...': {len(output)} results")
            return output

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def cross_tool_search(
        self,
        query_text: str,
        exclude_tool: Optional[str] = None,
        k: int = 5,
    ) -> list[dict]:
        """Search across ALL tools for related content.

        Useful for finding "Docker tips" when researching "Podman".

        Args:
            query_text: Search query
            exclude_tool: Tool to exclude from results (optional)
            k: Number of results

        Returns:
            List of {text, url, title, tool, similarity} dicts
        """
        results = self.query_similar(query_text, tool=None, k=k * 2)

        # Filter out excluded tool if specified
        if exclude_tool:
            results = [r for r in results if r.get("tool") != exclude_tool]

        return results[:k]

    def get_tool_coverage(self, tool: str) -> dict:
        """Get stats on how much data exists for a tool."""
        try:
            # Query all docs for this tool
            results = self.collection.get(
                where={"tool": tool},
                include=["documents", "metadatas"],
            )

            docs = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            if not docs:
                return {"total_chunks": 0, "total_urls": 0, "status": "no_data"}

            # Count unique URLs
            unique_urls = set(m.get("url") for m in metadatas)

            return {
                "total_chunks": len(docs),
                "total_urls": len(unique_urls),
                "avg_chunk_size": sum(len(d) for d in docs) // len(docs) if docs else 0,
            }

        except Exception as e:
            logger.error(f"Coverage query failed: {e}")
            return {}

    def _parse_primary_tool(self, ferramentas: str) -> str | None:
        names = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
        return names[0] if names else None

    def find_research_context(self, ferramentas: str, foco: str, k: int = 5) -> list[dict]:
        """Return cached scraped content relevant to ferramentas/foco (used when skip_search=True)."""
        query = f"{ferramentas} {foco} requisitos performance comparação benchmark"
        return self.query_similar(query, tool=self._parse_primary_tool(ferramentas), k=k, distance_threshold=0.25)

    def find_analysis_patterns(self, ferramentas: str, foco: str, k: int = 3) -> list[dict]:
        """Return similar analysis structures for the analyst to use as structural reference."""
        query = f"{ferramentas} análise {foco} tabela pros contras otimizações"
        return self.query_similar(query, tool=self._parse_primary_tool(ferramentas), k=k, distance_threshold=0.20)

    def find_writing_examples(self, ferramentas: str, k: int = 2) -> list[dict]:
        """Return well-written article chunks for writer style reference."""
        query = f"{ferramentas} artigo bem escrito técnico estrutura"
        return self.query_similar(query, k=k, distance_threshold=0.25)

    def find_historical_articles(self, ferramentas: str, k: int = 3) -> list[dict]:
        """Return prior approved articles on the same tool for critic quality comparison."""
        query = f"{ferramentas} artigo"
        return self.query_similar(query, tool=ferramentas.lower(), k=k, distance_threshold=0.20)

    def delete_tool_data(self, tool: str) -> bool:
        """Delete all data for a specific tool."""
        try:
            self.collection.delete(where={"tool": tool})
            logger.info(f"Deleted all data for {tool}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {tool} data: {e}")
            return False
