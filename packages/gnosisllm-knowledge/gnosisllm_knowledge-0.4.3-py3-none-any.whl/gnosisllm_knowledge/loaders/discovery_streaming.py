"""Streaming discovery with bounded memory for large websites.

This module provides streaming URL discovery from websites using the Neo Reader
Discovery API, yielding batches of URLs as they're discovered rather than
waiting for the full discovery to complete. This enables immediate processing
and keeps memory bounded for sites with many URLs (>500).
"""

from __future__ import annotations

import asyncio
import contextlib
import fnmatch
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TYPE_CHECKING, Any

from gnosisllm_knowledge.core.domain.discovery import DiscoveryConfig, DiscoveryProgress
from gnosisllm_knowledge.core.streaming.pipeline import BoundedQueue, PipelineConfig

if TYPE_CHECKING:
    from gnosisllm_knowledge.fetchers.neoreader_discovery import NeoreaderDiscoveryClient


class StreamingDiscoveryDiscoverer:
    """Discovers website URLs in a streaming fashion using Neo Reader Discovery API.

    Instead of collecting all URLs before processing, this yields batches of URLs
    as they're discovered from the polling response. This enables immediate
    processing while discovery continues in the background.

    Key differences from DiscoveryLoader._get_urls():
    - Yields batches instead of returning complete list
    - Uses bounded queue for backpressure
    - Memory usage is O(batch_size) not O(total_urls)
    - Starts yielding URLs while discovery is still running

    Recommended for sites with >500 expected URLs to start content loading
    before full discovery completes.

    Example:
        ```python
        from gnosisllm_knowledge.fetchers.neoreader_discovery import NeoreaderDiscoveryClient
        from gnosisllm_knowledge.loaders.discovery_streaming import StreamingDiscoveryDiscoverer

        client = NeoreaderDiscoveryClient.from_env()
        discoverer = StreamingDiscoveryDiscoverer(discovery_client=client)

        async for url_batch in discoverer.discover_urls_streaming(
            source="https://docs.example.com",
            batch_size=50,
            max_pages=1000,
        ):
            # Process batch immediately - content loading can start
            # while discovery continues
            for url in url_batch:
                await fetch_and_process(url)
        ```
    """

    def __init__(
        self,
        discovery_client: NeoreaderDiscoveryClient,
        config: PipelineConfig | None = None,
    ) -> None:
        """Initialize the streaming discovery discoverer.

        Args:
            discovery_client: Neo Reader Discovery API client.
            config: Pipeline configuration with batch sizes and concurrency.
        """
        self._discovery_client = discovery_client
        self._config = config or PipelineConfig()
        self._logger = logging.getLogger(__name__)

    async def discover_urls_streaming(
        self,
        source: str,
        batch_size: int | None = None,
        max_pages: int = 1000,
        max_depth: int = 3,
        allowed_patterns: list[str] | None = None,
        blocked_patterns: list[str] | None = None,
        poll_interval: float = 2.0,
        discovery_timeout: float = 600.0,
        on_progress: Callable[[DiscoveryProgress], Awaitable[None] | None] | None = None,
        **options: Any,
    ) -> AsyncIterator[list[str]]:
        """Yield batches of URLs as they're discovered.

        Starts a discovery job and polls for new URLs, yielding batches
        as they become available. This allows content fetching to begin
        while discovery is still running.

        Args:
            source: Starting URL for discovery.
            batch_size: URLs per batch (default from config).
            max_pages: Maximum pages to discover.
            max_depth: Maximum crawl depth.
            allowed_patterns: URL patterns to include (glob or regex).
            blocked_patterns: URL patterns to exclude (glob or regex).
            poll_interval: Seconds between status polls.
            discovery_timeout: Maximum time for discovery in seconds.
            on_progress: Optional callback for progress updates (sync or async).
            **options: Additional discovery options passed to DiscoveryConfig.

        Yields:
            Lists of discovered URLs, batch_size at a time.
        """
        batch_size = batch_size or self._config.url_batch_size
        allowed_patterns = allowed_patterns or []
        blocked_patterns = blocked_patterns or []

        # Use bounded queue for discovered URLs
        # Queue size is 2x batch_size to allow producer to stay ahead
        url_queue: BoundedQueue[str] = BoundedQueue(maxsize=batch_size * 2)

        # Tracking state
        seen_urls: set[str] = set()
        last_yielded_count = 0

        # Build discovery config from options
        discovery_config = self._build_discovery_config(
            max_pages=max_pages,
            max_depth=max_depth,
            **options,
        )

        async def poll_and_queue_urls() -> None:
            """Poll discovery job and push new URLs to queue."""
            nonlocal last_yielded_count

            # Create discovery job
            job_id = await self._discovery_client.create_job(source, discovery_config)
            self._logger.info(
                "Started streaming discovery job %s for %s",
                job_id,
                source,
            )

            try:
                loop = asyncio.get_event_loop()
                start_time = loop.time()

                while True:
                    # Get job status with URLs
                    status = await self._discovery_client.get_job_status(
                        job_id,
                        include_urls=True,
                    )

                    # Process any new URLs from this poll
                    if status.urls:
                        new_urls_added = 0
                        for discovered_url in status.urls:
                            url = discovered_url.url

                            if url in seen_urls:
                                continue

                            if not self._should_include_url(
                                url, allowed_patterns, blocked_patterns
                            ):
                                continue

                            seen_urls.add(url)
                            await url_queue.put(url)  # Backpressure if queue full
                            new_urls_added += 1

                        if new_urls_added > 0:
                            self._logger.debug(
                                "Queued %d new URLs (total seen: %d)",
                                new_urls_added,
                                len(seen_urls),
                            )

                    # Check if job is complete
                    if status.is_terminal():
                        if status.status == "completed":
                            self._logger.info(
                                "Discovery completed: %d URLs discovered in %.1fs",
                                len(seen_urls),
                                status.stats.duration_seconds if status.stats else 0.0,
                            )
                        elif status.status == "failed":
                            self._logger.error(
                                "Discovery failed: %s",
                                status.error or "Unknown error",
                            )
                        break

                    # Check timeout
                    elapsed = loop.time() - start_time
                    if elapsed >= discovery_timeout:
                        self._logger.warning(
                            "Discovery timeout after %.1fs, cancelling job %s",
                            elapsed,
                            job_id,
                        )
                        await self._discovery_client.cancel_job(job_id)
                        break

                    # Call progress callback if provided and we have progress
                    if status.progress and on_progress:
                        result = on_progress(status.progress)
                        # Handle async callbacks
                        if asyncio.iscoroutine(result):
                            await result

                    # Log progress
                    if status.progress:
                        self._logger.debug(
                            "Discovery progress: %d%% (%d pages, %d URLs)",
                            status.progress.percent,
                            status.progress.pages_crawled,
                            status.progress.urls_discovered,
                        )

                    # Wait before next poll
                    await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                self._logger.warning("Discovery cancelled, cleaning up job %s", job_id)
                try:
                    await self._discovery_client.cancel_job(job_id)
                except Exception as e:
                    self._logger.error("Failed to cancel job %s: %s", job_id, e)
                raise
            except Exception as e:
                self._logger.error("Discovery error: %s", e)
                try:
                    await self._discovery_client.cancel_job(job_id)
                except Exception as cancel_e:
                    self._logger.error("Failed to cancel job %s: %s", job_id, cancel_e)
                raise
            finally:
                url_queue.close()

        # Start discovery in background task
        discovery_task = asyncio.create_task(poll_and_queue_urls())

        # Yield batches from queue
        batch: list[str] = []
        try:
            async for url in url_queue:
                batch.append(url)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            # Yield remaining URLs
            if batch:
                yield batch

        finally:
            # Ensure discovery task is complete or cancelled
            if not discovery_task.done():
                discovery_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await discovery_task

    def _build_discovery_config(
        self,
        max_pages: int,
        max_depth: int,
        **options: Any,
    ) -> DiscoveryConfig:
        """Build DiscoveryConfig from parameters and options.

        Args:
            max_pages: Maximum pages to crawl.
            max_depth: Maximum crawl depth.
            **options: Additional discovery options.

        Returns:
            Configured DiscoveryConfig instance.
        """
        return DiscoveryConfig(
            max_depth=max_depth,
            max_pages=max_pages,
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

    def _should_include_url(
        self,
        url: str,
        allowed_patterns: list[str],
        blocked_patterns: list[str],
    ) -> bool:
        """Check if a URL should be included based on patterns.

        Args:
            url: The URL to check.
            allowed_patterns: Patterns that must match (if any).
            blocked_patterns: Patterns that must not match.

        Returns:
            True if URL should be included.
        """
        # Check blocked patterns first
        for pattern in blocked_patterns:
            if self._matches_pattern(url, pattern):
                return False

        # If allowed patterns specified, at least one must match
        if allowed_patterns:
            return any(self._matches_pattern(url, p) for p in allowed_patterns)

        return True

    def _matches_pattern(self, url: str, pattern: str) -> bool:
        """Check if URL matches a pattern.

        Supports both glob patterns (with *) and regex patterns.

        Args:
            url: The URL to check.
            pattern: The pattern to match against.

        Returns:
            True if URL matches the pattern.
        """
        # Try fnmatch for glob patterns
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(url, pattern)

        # Try regex
        try:
            return bool(re.search(pattern, url))
        except re.error:
            # Invalid regex, try substring match
            return pattern in url
