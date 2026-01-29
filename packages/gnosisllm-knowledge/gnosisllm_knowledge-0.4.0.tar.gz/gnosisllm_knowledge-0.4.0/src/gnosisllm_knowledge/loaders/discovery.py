"""Discovery loader using Neo Reader Discovery API for website crawling."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from gnosisllm_knowledge.core.domain.discovery import DiscoveryConfig, DiscoveryProgress
from gnosisllm_knowledge.core.events.types import (
    DiscoveryCompletedEvent,
    DiscoveryFailedEvent,
    DiscoveryProgressEvent,
    DiscoveryStartedEvent,
)
from gnosisllm_knowledge.core.exceptions import DiscoveryError
from gnosisllm_knowledge.loaders.base import BaseLoader

if TYPE_CHECKING:
    from gnosisllm_knowledge.core.events.emitter import EventEmitter
    from gnosisllm_knowledge.core.interfaces.chunker import ITextChunker
    from gnosisllm_knowledge.core.interfaces.fetcher import IContentFetcher
    from gnosisllm_knowledge.fetchers.neoreader_discovery import NeoreaderDiscoveryClient


class DiscoveryLoader(BaseLoader):
    """Loader that discovers all URLs from a website using Neo Reader Discovery API.

    Similar to SitemapLoader but uses Neo Reader's crawler instead of sitemap XML.
    Supports full website crawling with configurable depth, filters, and limits.

    The loader follows the Template Method Pattern from BaseLoader:
    1. _get_urls() performs URL discovery via Neo Reader Discovery API
    2. Returns all discovered URLs
    3. BaseLoader handles parallel fetching of each URL's content

    Features:
    - Async website crawling via Neo Reader Discovery API
    - Configurable crawl depth, page limits, and domain restrictions
    - URL filtering with include/exclude patterns
    - Progress events during discovery
    - Job cancellation on interruption
    - Partial failure handling (logs warnings, continues with available URLs)

    Example:
        ```python
        from gnosisllm_knowledge.fetchers import NeoreaderContentFetcher
        from gnosisllm_knowledge.fetchers.neoreader_discovery import NeoreaderDiscoveryClient
        from gnosisllm_knowledge.chunking import SentenceChunker

        fetcher = NeoreaderContentFetcher.from_env()
        discovery_client = NeoreaderDiscoveryClient.from_env()
        chunker = SentenceChunker()

        loader = DiscoveryLoader(
            fetcher=fetcher,
            chunker=chunker,
            discovery_client=discovery_client,
        )

        result = await loader.load(
            "https://docs.example.com",
            max_depth=3,
            max_pages=100,
        )
        ```
    """

    def __init__(
        self,
        fetcher: IContentFetcher,
        chunker: ITextChunker,
        discovery_client: NeoreaderDiscoveryClient,
        config: dict[str, Any] | None = None,
        event_emitter: EventEmitter | None = None,
    ) -> None:
        """Initialize the discovery loader.

        Args:
            fetcher: Content fetcher for retrieving URL content.
            chunker: Text chunker for splitting content into documents.
            discovery_client: Neo Reader Discovery API client for URL discovery.
            config: Optional configuration dictionary.
            event_emitter: Optional event emitter for progress events.
        """
        super().__init__(fetcher, chunker, config, event_emitter)
        self._discovery_client = discovery_client
        self._discovery_logger = logging.getLogger(f"{__name__}.DiscoveryLoader")

    @property
    def name(self) -> str:
        """Return the loader name for registry identification.

        Returns:
            The string "discovery" for factory registration.
        """
        return "discovery"

    def supports(self, source: str) -> bool:
        """Check if this loader supports the given source.

        Supports any HTTP/HTTPS URL that is not a sitemap. Sitemap URLs
        should be handled by SitemapLoader instead.

        Args:
            source: The source URL.

        Returns:
            True if source is HTTP/HTTPS and not a sitemap URL.
        """
        source_lower = source.lower()
        is_http = source_lower.startswith(("http://", "https://"))
        is_sitemap = "sitemap" in source_lower or source_lower.endswith(".xml")
        return is_http and not is_sitemap

    async def _get_urls(self, source: str, **options: Any) -> list[str]:
        """Discover URLs using Neo Reader Discovery API.

        Creates a discovery job, polls for completion with progress updates,
        and returns the discovered URLs. Handles job cancellation if
        interrupted.

        Args:
            source: The starting URL for discovery.
            **options: Discovery options:
                - max_depth: Maximum crawl depth (default: 3)
                - max_pages: Maximum pages to crawl (default: 100)
                - same_domain: Only crawl same domain (default: True)
                - include_subdomains: Include subdomains (default: True)
                - respect_robots: Respect robots.txt (default: True)
                - parse_sitemap: Also parse sitemap if found (default: False)
                - with_metadata: Include page metadata (default: True)
                - crawl_timeout: Crawl timeout in seconds (default: 300)
                - concurrent_requests: Concurrent crawl requests (default: 5)
                - request_delay: Delay between requests in ms (default: 100)
                - include_pattern: Regex pattern for URLs to include
                - exclude_pattern: Regex pattern for URLs to exclude
                - path_prefix: Only crawl URLs with this path prefix

        Returns:
            List of discovered URL strings.

        Raises:
            DiscoveryError: If discovery fails.
        """
        discovery_config = self._build_discovery_config(options)
        job_id = await self._discovery_client.create_job(source, discovery_config)

        self._emit_discovery_started(source, job_id, discovery_config)

        try:
            result = await self._wait_for_job_completion(job_id)
        except (asyncio.CancelledError, Exception) as e:
            await self._handle_job_cancellation(job_id, e)
            raise

        return self._process_discovery_result(job_id, result, source)

    def _build_discovery_config(self, options: dict[str, Any]) -> DiscoveryConfig:
        """Build DiscoveryConfig from options dictionary.

        Args:
            options: Discovery options passed to _get_urls.

        Returns:
            Configured DiscoveryConfig instance.
        """
        return DiscoveryConfig(
            max_depth=options.get("max_depth", 3),
            max_pages=options.get("max_pages", 100),
            same_domain=options.get("same_domain", True),
            include_subdomains=options.get("include_subdomains", True),
            respect_robots=options.get("respect_robots", True),
            parse_sitemap=options.get("parse_sitemap", False),
            with_metadata=options.get("with_metadata", True),
            crawl_timeout=options.get("crawl_timeout", 300),
            concurrent_requests=options.get("concurrent_requests", 5),
            request_delay=options.get("request_delay", 100),
            include_pattern=options.get("include_pattern"),
            exclude_pattern=options.get("exclude_pattern"),
            path_prefix=options.get("path_prefix"),
        )

    def _emit_discovery_started(
        self,
        source: str,
        job_id: str,
        discovery_config: DiscoveryConfig,
    ) -> None:
        """Emit discovery started event.

        Args:
            source: The starting URL.
            job_id: The discovery job ID.
            discovery_config: The discovery configuration.
        """
        self._events.emit(
            DiscoveryStartedEvent(
                url=source,
                job_id=job_id,
                config={
                    "max_depth": discovery_config.max_depth,
                    "max_pages": discovery_config.max_pages,
                    "same_domain": discovery_config.same_domain,
                    "include_subdomains": discovery_config.include_subdomains,
                    "respect_robots": discovery_config.respect_robots,
                    "parse_sitemap": discovery_config.parse_sitemap,
                },
            )
        )
        self._discovery_logger.info(
            "Started discovery job %s for %s (max_depth=%d, max_pages=%d)",
            job_id,
            source,
            discovery_config.max_depth,
            discovery_config.max_pages,
        )

    async def _wait_for_job_completion(self, job_id: str) -> Any:
        """Wait for discovery job to complete with progress updates.

        Args:
            job_id: The discovery job ID.

        Returns:
            The final DiscoveryJobStatus.
        """

        async def on_progress(progress: DiscoveryProgress) -> None:
            """Emit progress event for each update."""
            self._events.emit(
                DiscoveryProgressEvent(
                    job_id=job_id,
                    percent=progress.percent,
                    pages_crawled=progress.pages_crawled,
                    urls_discovered=progress.urls_discovered,
                    current_depth=progress.current_depth,
                    message=progress.message,
                )
            )
            self._discovery_logger.debug(
                "Discovery progress: %d%% (%d pages, %d URLs)",
                progress.percent,
                progress.pages_crawled,
                progress.urls_discovered,
            )

        return await self._discovery_client.wait_for_completion(
            job_id,
            on_progress=on_progress,
        )

    async def _handle_job_cancellation(self, job_id: str, error: Exception) -> None:
        """Handle job cancellation on error or interruption.

        Args:
            job_id: The discovery job ID to cancel.
            error: The exception that caused cancellation.
        """
        self._discovery_logger.warning(
            "Cancelling discovery job %s due to: %s",
            job_id,
            error,
        )
        try:
            await self._discovery_client.cancel_job(job_id)
            self._discovery_logger.info("Successfully cancelled job %s", job_id)
        except Exception as cancel_err:
            self._discovery_logger.error(
                "Failed to cancel job %s: %s",
                job_id,
                cancel_err,
            )

    def _process_discovery_result(
        self,
        job_id: str,
        result: Any,
        source: str,
    ) -> list[str]:
        """Process discovery result and extract URLs.

        Handles completed, failed, and partial failure cases.

        Args:
            job_id: The discovery job ID.
            result: The DiscoveryJobStatus from wait_for_completion.
            source: The original source URL.

        Returns:
            List of discovered URL strings.

        Raises:
            DiscoveryError: If the job failed or was cancelled.
        """
        if result.status != "completed":
            error_msg = result.error or "Unknown error"
            self._events.emit(
                DiscoveryFailedEvent(
                    job_id=job_id,
                    error=error_msg,
                )
            )
            raise DiscoveryError(
                f"Discovery failed: {error_msg}",
                job_id=job_id,
                source=source,
            )

        # Handle partial failures (log warning if errors occurred)
        if result.stats and result.stats.errors > 0:
            self._discovery_logger.warning(
                "Discovery completed with %d errors (%d URLs returned)",
                result.stats.errors,
                result.stats.urls_returned,
            )

        # Extract URLs
        urls = [u.url for u in (result.urls or [])]

        # Emit completion event
        self._events.emit(
            DiscoveryCompletedEvent(
                job_id=job_id,
                urls_count=len(urls),
                pages_crawled=result.stats.pages_crawled if result.stats else 0,
                duration_seconds=result.stats.duration_seconds if result.stats else 0.0,
                errors=result.stats.errors if result.stats else 0,
            )
        )

        self._discovery_logger.info(
            "Discovery completed: %d URLs discovered in %.1fs",
            len(urls),
            result.stats.duration_seconds if result.stats else 0.0,
        )

        return urls
