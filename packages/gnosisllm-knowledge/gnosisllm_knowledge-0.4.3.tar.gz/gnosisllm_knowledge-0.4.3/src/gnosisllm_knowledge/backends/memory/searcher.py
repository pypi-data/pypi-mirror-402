"""In-memory document searcher for testing.

Note: This module is tenant-agnostic. Multi-tenancy should be handled
at the API layer by using separate indices per account (e.g.,
gnosisllm-{account_id}-knowledge) rather than filtering by account_id.
"""

from __future__ import annotations

import math
import re
import time
import warnings
from typing import Any, Callable

from gnosisllm_knowledge.backends.memory.indexer import MemoryIndexer
from gnosisllm_knowledge.core.domain.search import (
    SearchMode,
    SearchQuery,
    SearchResult,
    SearchResultItem,
)


class MemorySearcher:
    """In-memory document searcher for testing.

    Provides basic search functionality using simple text matching
    and optional cosine similarity for vector search.

    Example:
        ```python
        indexer = MemoryIndexer()
        searcher = MemorySearcher(indexer)

        query = SearchQuery(text="hello world")
        results = await searcher.search(query, "test-index")
        ```
    """

    def __init__(
        self,
        indexer: MemoryIndexer,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        """Initialize the memory searcher.

        Args:
            indexer: Memory indexer with stored documents.
            embedding_fn: Optional function to generate embeddings.
        """
        self._indexer = indexer
        self._embedding_fn = embedding_fn

    async def search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute search using the specified mode.

        Args:
            query: Search query.
            index_name: Index to search.
            **options: Additional options.

        Returns:
            Search results.
        """
        mode = query.mode

        if mode == SearchMode.SEMANTIC:
            return await self.semantic_search(query, index_name, **options)
        elif mode == SearchMode.KEYWORD:
            return await self.keyword_search(query, index_name, **options)
        else:
            return await self.hybrid_search(query, index_name, **options)

    async def semantic_search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute semantic (vector) search.

        Args:
            query: Search query.
            index_name: Index to search.
            **options: Additional options.

        Returns:
            Search results.
        """
        start_time = time.perf_counter()

        if not self._embedding_fn:
            # Fall back to keyword search if no embedding function
            return await self.keyword_search(query, index_name, **options)

        query_embedding = self._embedding_fn(query.text)
        documents = self._indexer.get_all(index_name)

        # Apply filters
        filtered_docs = self._apply_filters(documents, query)

        # Score by cosine similarity
        scored_docs = []
        for doc in filtered_docs:
            doc_embedding = doc.get("embedding")
            if doc_embedding:
                score = self._cosine_similarity(query_embedding, doc_embedding)
                scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Apply pagination
        paginated = scored_docs[query.offset : query.offset + query.limit]

        duration_ms = (time.perf_counter() - start_time) * 1000
        return self._build_result(query, paginated, len(scored_docs), duration_ms)

    async def keyword_search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute keyword search.

        Uses simple term frequency scoring.

        Args:
            query: Search query.
            index_name: Index to search.
            **options: Additional options.

        Returns:
            Search results.
        """
        start_time = time.perf_counter()

        documents = self._indexer.get_all(index_name)

        # Apply filters
        filtered_docs = self._apply_filters(documents, query)

        # Score by keyword matching
        query_terms = self._tokenize(query.text.lower())
        scored_docs = []

        for doc in filtered_docs:
            content = doc.get("content", "").lower()
            title = (doc.get("title") or "").lower()

            # Simple TF scoring
            content_score = sum(
                content.count(term) for term in query_terms
            )
            title_score = sum(
                title.count(term) for term in query_terms
            ) * 2  # Boost title matches

            total_score = content_score + title_score
            if total_score > 0:
                scored_docs.append((doc, float(total_score)))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Apply min_score filter
        if query.min_score:
            scored_docs = [(d, s) for d, s in scored_docs if s >= query.min_score]

        # Apply pagination
        paginated = scored_docs[query.offset : query.offset + query.limit]

        duration_ms = (time.perf_counter() - start_time) * 1000
        return self._build_result(query, paginated, len(scored_docs), duration_ms)

    async def hybrid_search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute hybrid search (semantic + keyword).

        Args:
            query: Search query.
            index_name: Index to search.
            **options: Weights for combining scores.

        Returns:
            Search results.
        """
        start_time = time.perf_counter()

        semantic_weight = options.get("semantic_weight", 0.7)
        keyword_weight = options.get("keyword_weight", 0.3)

        documents = self._indexer.get_all(index_name)
        filtered_docs = self._apply_filters(documents, query)

        # Get embeddings if available
        query_embedding = None
        if self._embedding_fn:
            query_embedding = self._embedding_fn(query.text)

        query_terms = self._tokenize(query.text.lower())
        scored_docs = []

        for doc in filtered_docs:
            # Keyword score
            content = doc.get("content", "").lower()
            title = (doc.get("title") or "").lower()
            keyword_score = sum(content.count(term) for term in query_terms)
            keyword_score += sum(title.count(term) for term in query_terms) * 2

            # Normalize keyword score
            if keyword_score > 0:
                keyword_score = min(keyword_score / 10.0, 1.0)

            # Semantic score
            semantic_score = 0.0
            if query_embedding:
                doc_embedding = doc.get("embedding")
                if doc_embedding:
                    semantic_score = self._cosine_similarity(query_embedding, doc_embedding)
                    # Normalize to 0-1 range
                    semantic_score = (semantic_score + 1) / 2

            # Combine scores
            total_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)

            if total_score > 0:
                scored_docs.append((doc, total_score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Apply pagination
        paginated = scored_docs[query.offset : query.offset + query.limit]

        duration_ms = (time.perf_counter() - start_time) * 1000
        return self._build_result(query, paginated, len(scored_docs), duration_ms)

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.

        Raises:
            ValueError: If no embedding function configured.
        """
        if not self._embedding_fn:
            raise ValueError("Embedding function not configured")
        return self._embedding_fn(text)

    async def get_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """Get embeddings for multiple texts.

        Args:
            texts: Texts to embed.
            batch_size: Ignored.

        Returns:
            List of embedding vectors.
        """
        if not self._embedding_fn:
            return [[] for _ in texts]
        return [self._embedding_fn(text) for text in texts]

    async def get_similar_documents(
        self,
        doc_id: str,
        index_name: str,
        limit: int = 10,
    ) -> SearchResult:
        """Find documents similar to a given document.

        Args:
            doc_id: Document ID.
            index_name: Index to search.
            limit: Maximum results.

        Returns:
            Search results.
        """
        start_time = time.perf_counter()

        source_doc = self._indexer.get_by_id(doc_id, index_name)
        if not source_doc:
            return SearchResult(
                query="",
                mode=SearchMode.SEMANTIC,
                items=[],
                total_hits=0,
                duration_ms=0,
            )

        source_embedding = source_doc.get("embedding")
        if not source_embedding:
            # Fall back to content similarity
            query = SearchQuery(text=source_doc.get("content", "")[:500], limit=limit)
            return await self.keyword_search(query, index_name)

        documents = self._indexer.get_all(index_name)
        scored_docs = []

        for doc in documents:
            if doc.get("id") == doc_id:
                continue

            doc_embedding = doc.get("embedding")
            if doc_embedding:
                score = self._cosine_similarity(source_embedding, doc_embedding)
                scored_docs.append((doc, score))

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        paginated = scored_docs[:limit]

        duration_ms = (time.perf_counter() - start_time) * 1000
        query = SearchQuery(text="", limit=limit)
        return self._build_result(query, paginated, len(scored_docs), duration_ms)

    async def multi_search(
        self,
        queries: list[SearchQuery],
        index_name: str,
    ) -> list[SearchResult]:
        """Execute multiple searches.

        Args:
            queries: List of search queries.
            index_name: Index to search.

        Returns:
            List of search results.
        """
        results = []
        for query in queries:
            result = await self.search(query, index_name)
            results.append(result)
        return results

    async def list_documents(
        self,
        index_name: str,
        *,
        source_id: str | None = None,
        collection_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List documents with optional filters.

        Args:
            index_name: Index to query.
            source_id: Optional source ID filter.
            collection_id: Optional collection ID filter.
            limit: Maximum documents to return.
            offset: Number of documents to skip.

        Returns:
            Dictionary with documents, total, limit, offset.
        """
        documents = self._indexer.get_all(index_name)

        # Apply filters
        if source_id:
            documents = [d for d in documents if d.get("source_id") == source_id]
        if collection_id:
            documents = [d for d in documents if d.get("collection_id") == collection_id]

        total = len(documents)

        # Apply pagination
        paginated = documents[offset : offset + limit]

        return {
            "documents": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def count(
        self,
        index_name: str,
        collection_id: str | None = None,
        source_id: str | None = None,
    ) -> int:
        """Count documents in index with optional filters.

        Args:
            index_name: Index to count.
            collection_id: Filter by collection.
            source_id: Filter by source.

        Returns:
            Document count.
        """
        # Use efficient O(1) count when no filters
        if not collection_id and not source_id:
            return self._indexer.count(index_name)

        # With filters, iterate over index values (memory backend is for testing only)
        index_data = self._indexer._indices.get(index_name, {})
        count = 0
        for doc in index_data.values():
            if collection_id and doc.get("collection_id") != collection_id:
                continue
            if source_id and doc.get("source_id") != source_id:
                continue
            count += 1

        return count

    async def get_collections(self, index_name: str) -> list[dict[str, Any]]:
        """Get unique collections with document counts.

        Args:
            index_name: Index to query.

        Returns:
            List of collections with id, name, and document_count.
        """
        documents = self._indexer.get_all(index_name)
        collections: dict[str, dict[str, Any]] = {}

        for doc in documents:
            col_id = doc.get("collection_id")
            if not col_id:
                continue

            if col_id not in collections:
                collections[col_id] = {
                    "id": col_id,
                    "name": doc.get("collection_name") or col_id,
                    "document_count": 0,
                }
            collections[col_id]["document_count"] += 1

        return list(collections.values())

    async def get_stats(self, index_name: str) -> dict[str, Any]:
        """Get index statistics.

        Args:
            index_name: Index to query.

        Returns:
            Dictionary with document_count and index info.
        """
        count = self._indexer.count(index_name)
        return {
            "document_count": count,
            "index_name": index_name,
            "exists": count > 0 or index_name in self._indexer._indices,
        }

    def _apply_filters(
        self,
        documents: list[dict[str, Any]],
        query: SearchQuery,
    ) -> list[dict[str, Any]]:
        """Apply query filters to documents.

        Note:
            This method is tenant-agnostic. Multi-tenancy should be handled
            at the API layer by using separate indices per account.

        Args:
            documents: Documents to filter.
            query: Query with filter parameters.

        Returns:
            Filtered documents.
        """
        filtered = documents

        # Collection filter
        if query.collection_ids:
            filtered = [
                d for d in filtered if d.get("collection_id") in query.collection_ids
            ]

        # Source filter
        if query.source_ids:
            filtered = [d for d in filtered if d.get("source_id") in query.source_ids]

        # Custom metadata filters
        if query.metadata_filters:
            for field, value in query.metadata_filters.items():
                if isinstance(value, list):
                    filtered = [d for d in filtered if d.get(field) in value]
                else:
                    filtered = [d for d in filtered if d.get(field) == value]

        return filtered

    def _build_result(
        self,
        query: SearchQuery,
        scored_docs: list[tuple[dict[str, Any], float]],
        total_hits: int,
        duration_ms: float,
    ) -> SearchResult:
        """Build search result from scored documents.

        Args:
            query: Original query.
            scored_docs: List of (document, score) tuples.
            total_hits: Total matching documents.
            duration_ms: Search duration.

        Returns:
            Search result.
        """
        items = []
        max_score = None

        for doc, score in scored_docs:
            if max_score is None or score > max_score:
                max_score = score

            # Generate simple highlights
            highlights = self._generate_highlights(doc.get("content", ""), query.text)

            item = SearchResultItem(
                doc_id=doc.get("id", ""),
                content=doc.get("content", ""),
                score=score,
                title=doc.get("title"),
                url=doc.get("url"),
                source=doc.get("source"),
                collection_id=doc.get("collection_id"),
                highlights=highlights if highlights else None,
                metadata=doc.get("metadata"),
                chunk_index=doc.get("chunk_index"),
                total_chunks=doc.get("total_chunks"),
            )
            items.append(item)

        return SearchResult(
            query=query.text,
            mode=query.mode,
            items=items,
            total_hits=total_hits,
            duration_ms=duration_ms,
            max_score=max_score,
            has_more=total_hits > query.offset + len(items),
        )

    def _generate_highlights(
        self,
        content: str,
        query_text: str,
        fragment_size: int = 150,
    ) -> list[str]:
        """Generate simple highlights for search results.

        Args:
            content: Document content.
            query_text: Query text.
            fragment_size: Size of highlight fragments.

        Returns:
            List of highlighted fragments.
        """
        highlights = []
        query_terms = self._tokenize(query_text.lower())

        for term in query_terms:
            # Find term in content
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(content):
                start = max(0, match.start() - fragment_size // 2)
                end = min(len(content), match.end() + fragment_size // 2)
                fragment = content[start:end]

                # Add emphasis
                highlighted = pattern.sub(f"<em>{match.group()}</em>", fragment)
                if highlighted not in highlights:
                    highlights.append(highlighted)

                if len(highlights) >= 3:
                    return highlights

        return highlights

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenizer.

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens.
        """
        return [t for t in re.split(r"\W+", text) if t]

    def _cosine_similarity(
        self,
        vec1: list[float],
        vec2: list[float],
    ) -> float:
        """Calculate cosine similarity between vectors.

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Cosine similarity (-1 to 1).
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
