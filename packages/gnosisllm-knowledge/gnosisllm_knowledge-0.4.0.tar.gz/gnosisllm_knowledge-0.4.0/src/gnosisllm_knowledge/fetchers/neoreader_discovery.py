"""Neo Reader Discovery API client for website crawling and URL discovery."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from gnosisllm_knowledge.core.domain.discovery import (
    DiscoveredURL,
    DiscoveryConfig,
    DiscoveryJobStatus,
    DiscoveryProgress,
    DiscoveryStats,
)
from gnosisllm_knowledge.core.exceptions import (
    ConnectionError,
    DiscoveryJobFailedError,
    DiscoveryTimeoutError,
    FetchError,
)
from gnosisllm_knowledge.fetchers.config import NeoreaderConfig


class NeoreaderDiscoveryClient:
    """Client for Neo Reader Discovery API.

    Handles the lifecycle of discovery jobs: creating jobs, polling for status
    with exponential backoff, and cancellation. Uses httpx.AsyncClient internally
    for efficient async HTTP operations.

    Example:
        ```python
        config = NeoreaderConfig.from_env()
        client = NeoreaderDiscoveryClient(config)

        # Create a discovery job
        job_id = await client.create_job(
            "https://docs.example.com",
            DiscoveryConfig(max_depth=3, max_pages=100)
        )

        # Wait for completion with progress callback
        result = await client.wait_for_completion(
            job_id,
            on_progress=lambda p: print(f"Progress: {p.percent}%")
        )

        # Get discovered URLs
        for url in result.urls:
            print(url.url)

        await client.close()
        ```
    """

    def __init__(self, config: NeoreaderConfig) -> None:
        """Initialize the discovery client.

        Args:
            config: Neo Reader configuration with host, API key, etc.
        """
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def from_env(cls) -> NeoreaderDiscoveryClient:
        """Create client from environment variables.

        Uses NeoreaderConfig.from_env() to load configuration from:
        - NEOREADER_HOST
        - NEOREADER_API_KEY
        - NEOREADER_TIMEOUT

        Returns:
            NeoreaderDiscoveryClient configured from environment.
        """
        return cls(NeoreaderConfig.from_env())

    @property
    def config(self) -> NeoreaderConfig:
        """Get the Neo Reader configuration.

        Returns:
            The configuration used by this client.
        """
        return self._config

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Creates a reusable httpx.AsyncClient with base URL, timeout,
        and authentication headers configured.

        Returns:
            Configured httpx.AsyncClient instance.
        """
        if self._client is None:
            headers: dict[str, str] = {}
            if self._config.api_key:
                headers["Authorization"] = f"Bearer {self._config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self._config.host,
                timeout=self._config.timeout,
                headers=headers,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client and release resources.

        Should be called when done with the client to properly
        close connections. Safe to call multiple times.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> NeoreaderDiscoveryClient:
        """Enter async context manager.

        Returns:
            Self for use in async with statement.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager and close client."""
        await self.close()

    async def create_job(
        self,
        url: str,
        discovery_config: DiscoveryConfig | None = None,
    ) -> str:
        """Create a discovery job for the given URL.

        Initiates an async discovery crawl starting from the specified URL.
        The job runs in the background on the Neo Reader server.

        Args:
            url: The starting URL for discovery.
            discovery_config: Configuration for the crawl. Uses defaults if None.

        Returns:
            The job ID for tracking the discovery job.

        Raises:
            ConnectionError: If unable to connect to Neo Reader.
            FetchError: If the API returns an error response.
        """
        config = discovery_config or DiscoveryConfig()
        client = await self._get_client()

        # Use the DiscoveryConfig.to_headers() method for clean conversion
        headers = config.to_headers()

        self._logger.debug(
            "Creating discovery job for %s with config: max_depth=%d, max_pages=%d",
            url,
            config.max_depth,
            config.max_pages,
        )

        try:
            response = await client.post(
                f"/discover/{url}",
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            job_id = data["job_id"]

            self._logger.info("Created discovery job %s for %s", job_id, url)
            return job_id

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to Neo Reader at {self._config.host}",
                host=self._config.host,
                cause=e,
            ) from e
        except httpx.HTTPStatusError as e:
            raise FetchError(
                f"Failed to create discovery job: HTTP {e.response.status_code}",
                source=url,
                status_code=e.response.status_code,
                cause=e,
            ) from e

    async def get_job_status(
        self,
        job_id: str,
        include_urls: bool = True,
    ) -> DiscoveryJobStatus:
        """Get the current status of a discovery job.

        Fetches the job status, progress, stats, and optionally the
        discovered URLs from the Neo Reader API.

        Args:
            job_id: The discovery job ID.
            include_urls: Whether to include discovered URLs in the response.

        Returns:
            DiscoveryJobStatus with current job state.

        Raises:
            ConnectionError: If unable to connect to Neo Reader.
            FetchError: If the API returns an error response.
        """
        client = await self._get_client()

        params = {"include_urls": str(include_urls).lower()}

        try:
            response = await client.get(
                f"/discover/jobs/{job_id}",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            return self._parse_job_status(data)

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to Neo Reader at {self._config.host}",
                host=self._config.host,
                cause=e,
            ) from e
        except httpx.HTTPStatusError as e:
            raise FetchError(
                f"Failed to get job status: HTTP {e.response.status_code}",
                source=job_id,
                status_code=e.response.status_code,
                cause=e,
            ) from e

    async def wait_for_completion(
        self,
        job_id: str,
        *,
        initial_interval: float = 1.0,
        max_interval: float = 10.0,
        backoff_factor: float = 1.5,
        timeout: float = 600.0,
        on_progress: Callable[[DiscoveryProgress], Awaitable[None] | None]
        | None = None,
    ) -> DiscoveryJobStatus:
        """Poll until job completes or fails with exponential backoff.

        Continuously polls the job status with exponential backoff between
        requests. Calls the optional progress callback on each update.
        Raises an exception if the job times out or fails.

        Args:
            job_id: The discovery job ID to wait for.
            initial_interval: Initial polling interval in seconds.
            max_interval: Maximum polling interval in seconds.
            backoff_factor: Multiplier for interval increase (e.g., 1.5 = 50% increase).
            timeout: Maximum time to wait for completion in seconds.
            on_progress: Optional async or sync callback for progress updates.

        Returns:
            DiscoveryJobStatus with completed/failed/cancelled state.

        Raises:
            DiscoveryTimeoutError: If the job doesn't complete within timeout.
            ConnectionError: If unable to connect to Neo Reader.
            FetchError: If the API returns an error response.
        """
        loop = asyncio.get_event_loop()
        start_time = loop.time()
        interval = initial_interval

        self._logger.info(
            "Waiting for job %s to complete (timeout: %.0fs)",
            job_id,
            timeout,
        )

        while True:
            status = await self.get_job_status(job_id)

            # Call progress callback if provided and we have progress
            if status.progress and on_progress:
                result = on_progress(status.progress)
                # Handle async callbacks
                if asyncio.iscoroutine(result):
                    await result

            # Check if job is in terminal state
            if status.is_terminal():
                self._logger.info(
                    "Job %s completed with status: %s",
                    job_id,
                    status.status,
                )
                return status

            # Check timeout
            elapsed = loop.time() - start_time
            if elapsed >= timeout:
                self._logger.warning(
                    "Job %s timed out after %.1fs",
                    job_id,
                    elapsed,
                )
                raise DiscoveryTimeoutError(
                    f"Discovery job {job_id} timed out after {elapsed:.1f}s",
                    job_id=job_id,
                    elapsed=elapsed,
                    timeout=timeout,
                )

            # Wait with exponential backoff
            self._logger.debug(
                "Job %s still running, waiting %.1fs before next poll",
                job_id,
                interval,
            )
            await asyncio.sleep(interval)
            interval = min(interval * backoff_factor, max_interval)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running discovery job.

        Sends a cancellation request to stop the job. The job will
        transition to 'cancelled' status.

        Args:
            job_id: The discovery job ID to cancel.

        Returns:
            True if cancellation was successful, False if job was
            already in a terminal state.

        Raises:
            ConnectionError: If unable to connect to Neo Reader.
            FetchError: If the API returns an error response.
        """
        client = await self._get_client()

        self._logger.info("Cancelling discovery job %s", job_id)

        try:
            response = await client.delete(f"/discover/jobs/{job_id}")
            response.raise_for_status()

            self._logger.info("Successfully cancelled job %s", job_id)
            return True

        except httpx.HTTPStatusError as e:
            # 404 or similar might mean job is already completed/cancelled
            if e.response.status_code == 404:
                self._logger.warning(
                    "Job %s not found (may already be completed)",
                    job_id,
                )
                return False
            raise FetchError(
                f"Failed to cancel job: HTTP {e.response.status_code}",
                source=job_id,
                status_code=e.response.status_code,
                cause=e,
            ) from e
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to Neo Reader at {self._config.host}",
                host=self._config.host,
                cause=e,
            ) from e

    async def discover(
        self,
        url: str,
        discovery_config: DiscoveryConfig | None = None,
        *,
        timeout: float = 600.0,
        on_progress: Callable[[DiscoveryProgress], Awaitable[None] | None]
        | None = None,
    ) -> list[str]:
        """Convenience method to discover all URLs from a website.

        Creates a job, waits for completion, and returns the discovered URLs.
        Handles job cancellation on errors or interruption.

        Args:
            url: The starting URL for discovery.
            discovery_config: Configuration for the crawl. Uses defaults if None.
            timeout: Maximum time to wait for completion in seconds.
            on_progress: Optional callback for progress updates.

        Returns:
            List of discovered URL strings.

        Raises:
            DiscoveryTimeoutError: If the job doesn't complete within timeout.
            DiscoveryJobFailedError: If the job fails or is cancelled.
            ConnectionError: If unable to connect to Neo Reader.
            FetchError: If the API returns an error response.
        """
        job_id = await self.create_job(url, discovery_config)

        try:
            status = await self.wait_for_completion(
                job_id,
                timeout=timeout,
                on_progress=on_progress,
            )

            if status.status != "completed":
                raise DiscoveryJobFailedError(
                    f"Discovery job {job_id} failed with status: {status.status}",
                    job_id=job_id,
                    status=status.status,
                    source=url,
                )

            return [u.url for u in status.urls]

        except (asyncio.CancelledError, Exception) as e:
            # Attempt to cancel the job on any error
            self._logger.warning(
                "Cancelling job %s due to error: %s",
                job_id,
                e,
            )
            try:
                await self.cancel_job(job_id)
            except Exception as cancel_err:
                self._logger.error(
                    "Failed to cancel job %s: %s",
                    job_id,
                    cancel_err,
                )
            raise

    def _parse_job_status(self, data: dict[str, Any]) -> DiscoveryJobStatus:
        """Parse API response into DiscoveryJobStatus.

        Args:
            data: Raw JSON response from the API.

        Returns:
            Parsed DiscoveryJobStatus instance.
        """
        # Parse progress if present
        progress = None
        if data.get("progress"):
            progress = DiscoveryProgress(
                percent=data["progress"].get("percent", 0),
                pages_crawled=data["progress"].get("pages_crawled", 0),
                urls_discovered=data["progress"].get("urls_discovered", 0),
                current_depth=data["progress"].get("current_depth", 0),
                message=data["progress"].get("message", ""),
            )

        # Parse stats if present
        stats = None
        if data.get("stats"):
            stats = DiscoveryStats(
                pages_crawled=data["stats"].get("pages_crawled", 0),
                urls_found=data["stats"].get("urls_found", 0),
                urls_returned=data["stats"].get("urls_returned", 0),
                urls_filtered=data["stats"].get("urls_filtered", 0),
                errors=data["stats"].get("errors", 0),
                duration_seconds=data["stats"].get("duration_seconds", 0.0),
            )

        # Parse URLs if present
        urls: list[DiscoveredURL] = []
        if data.get("urls"):
            for u in data["urls"]:
                urls.append(
                    DiscoveredURL(
                        url=u["url"],
                        depth=u.get("depth", 0),
                        title=u.get("title"),
                        is_internal=u.get("is_internal", True),
                    )
                )

        return DiscoveryJobStatus(
            job_id=data["job_id"],
            status=data["status"],
            start_url=data["start_url"],
            progress=progress,
            stats=stats,
            urls=urls,
            error=data.get("error"),
        )
