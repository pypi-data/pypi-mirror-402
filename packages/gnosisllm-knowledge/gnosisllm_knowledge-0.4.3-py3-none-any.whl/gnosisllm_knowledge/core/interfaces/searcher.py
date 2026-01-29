"""Knowledge searcher protocol - Interface Segregation Principle.

Note:
    This library is tenant-agnostic. Multi-tenancy is achieved through index
    isolation (e.g., `knowledge-{account_id}`). Searcher implementations should
    not include tenant filtering logic - callers should use tenant-specific indices.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from gnosisllm_knowledge.core.domain.search import SearchQuery, SearchResult


@runtime_checkable
class IKnowledgeSearcher(Protocol):
    """Protocol for searching documents in a search backend.

    This protocol is tenant-agnostic. Multi-tenancy is achieved through index
    isolation by using tenant-specific index names.

    Knowledge searchers are responsible for:
    - Executing different search modes (semantic, keyword, hybrid)
    - Generating embeddings for queries
    - Filtering and ranking results
    - Handling pagination

    Implementations should follow the Interface Segregation Principle
    and provide focused methods for each search type.
    """

    async def search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute search based on query mode.

        Automatically selects the appropriate search method based
        on the query's mode setting.

        Args:
            query: Search query with filters and options.
            index_name: Target index name.
            **options: Backend-specific options.

        Returns:
            SearchResult with hits and metadata.
        """
        ...

    async def semantic_search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute semantic (vector) search only.

        Uses embedding similarity to find relevant documents.

        Args:
            query: Search query.
            index_name: Target index name.
            **options: Backend-specific options.

        Returns:
            SearchResult with semantically similar documents.
        """
        ...

    async def keyword_search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute keyword (BM25) search only.

        Uses traditional text matching to find relevant documents.

        Args:
            query: Search query.
            index_name: Target index name.
            **options: Backend-specific options.

        Returns:
            SearchResult with keyword-matching documents.
        """
        ...

    async def hybrid_search(
        self,
        query: SearchQuery,
        index_name: str,
        **options: Any,
    ) -> SearchResult:
        """Execute hybrid (semantic + keyword) search.

        Combines vector similarity and text matching for best results.

        Args:
            query: Search query.
            index_name: Target index name.
            **options: Backend-specific options.

        Returns:
            SearchResult with combined ranking.
        """
        ...

    async def get_embedding(
        self,
        text: str,
        **options: Any,
    ) -> list[float]:
        """Get embedding vector for text.

        Args:
            text: Text to embed.
            **options: Embedding model options.

        Returns:
            Embedding vector as list of floats.
        """
        ...

    async def get_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
        **options: Any,
    ) -> list[list[float]]:
        """Get embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed.
            batch_size: Batch size for API calls.
            **options: Embedding model options.

        Returns:
            List of embedding vectors.
        """
        ...

    async def get_similar_documents(
        self,
        doc_id: str,
        index_name: str,
        limit: int = 10,
        **options: Any,
    ) -> SearchResult:
        """Find documents similar to a given document.

        Args:
            doc_id: Document ID to find similar documents for.
            index_name: Target index name.
            limit: Maximum number of results.
            **options: Backend-specific options.

        Returns:
            SearchResult with similar documents.
        """
        ...

    async def multi_search(
        self,
        queries: list[SearchQuery],
        index_name: str,
        **options: Any,
    ) -> list[SearchResult]:
        """Execute multiple searches in a single request.

        More efficient than individual search calls.

        Args:
            queries: List of search queries.
            index_name: Target index name.
            **options: Backend-specific options.

        Returns:
            List of SearchResults in same order as queries.
        """
        ...

    async def count(
        self,
        index_name: str,
        collection_id: str | None = None,
        source_id: str | None = None,
    ) -> int:
        """Count documents in index with optional filters.

        Uses native count API instead of search for efficiency.

        Args:
            index_name: Target index name.
            collection_id: Filter by collection.
            source_id: Filter by source.

        Returns:
            Document count.
        """
        ...
