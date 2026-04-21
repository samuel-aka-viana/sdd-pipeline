"""Chroma vector database persistence for research data.

Replaces SQLite FTS5 with semantic search via embeddings.
Supports intelligent chunking and k-NN similarity search.
"""
import logging
from pathlib import Path
from typing import Optional
import chromadb

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

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="research",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Chroma collection ready: {self.db_path}")

    def chunk_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
        """Split long content into overlapping chunks for better embeddings.

        Args:
            content: Text to chunk
            chunk_size: Characters per chunk
            overlap: Overlap between chunks (for context)

        Returns:
            List of {text, start, end} dicts
        """
        chunks = []
        start = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk_text = content[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start": start,
                    "end": end,
                })

            # Move start position (with overlap)
            start = end - overlap if end < len(content) else end

        return chunks if chunks else [{"text": content, "start": 0, "end": len(content)}]

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
            # Use markdown if available (richer), else content
            text_to_embed = markdown_raw if markdown_raw else content

            # Intelligent chunking
            chunks = self.chunk_content(text_to_embed, chunk_size=1000, overlap=200)

            # Prepare batch insert
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

            # Add to collection (Chroma auto-embeds)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
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

    def delete_tool_data(self, tool: str) -> bool:
        """Delete all data for a specific tool."""
        try:
            self.collection.delete(where={"tool": tool})
            logger.info(f"Deleted all data for {tool}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {tool} data: {e}")
            return False

