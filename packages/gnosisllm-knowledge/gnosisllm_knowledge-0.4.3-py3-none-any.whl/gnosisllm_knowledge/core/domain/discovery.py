"""Domain models for website discovery."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiscoveryConfig:
    """Configuration for website discovery crawl.

    Controls how the Neo Reader Discovery API crawls and discovers URLs.

    Attributes:
        max_depth: Maximum crawl depth from start URL.
        max_pages: Maximum number of pages to crawl.
        same_domain: Only crawl URLs on the same domain.
        include_subdomains: Include subdomains when same_domain is True.
        respect_robots: Respect robots.txt rules.
        parse_sitemap: Also parse sitemap if available.
        with_metadata: Include page metadata (title, etc.) in results.
        crawl_timeout: Overall timeout for the crawl in seconds.
        concurrent_requests: Number of concurrent crawl requests.
        request_delay: Delay between requests in milliseconds.
        include_pattern: Regex pattern for URLs to include.
        exclude_pattern: Regex pattern for URLs to exclude.
        path_prefix: Only crawl URLs with this path prefix.
    """

    max_depth: int = 3
    max_pages: int = 100
    same_domain: bool = True
    include_subdomains: bool = True
    respect_robots: bool = True
    parse_sitemap: bool = False
    with_metadata: bool = True
    crawl_timeout: int = 300
    concurrent_requests: int = 5
    request_delay: int = 100
    include_pattern: str | None = None
    exclude_pattern: str | None = None
    path_prefix: str | None = None

    def to_headers(self) -> dict[str, str]:
        """Convert config to HTTP headers for Neo Reader API.

        Returns:
            Dictionary of header name to value.
        """
        headers = {
            "X-Max-Depth": str(self.max_depth),
            "X-Max-Pages": str(self.max_pages),
            "X-Same-Domain": str(self.same_domain).lower(),
            "X-Include-Subdomains": str(self.include_subdomains).lower(),
            "X-Respect-Robots": str(self.respect_robots).lower(),
            "X-Parse-Sitemap": str(self.parse_sitemap).lower(),
            "X-With-Metadata": str(self.with_metadata).lower(),
            "X-Crawl-Timeout": str(self.crawl_timeout),
            "X-Concurrent-Requests": str(self.concurrent_requests),
            "X-Request-Delay": str(self.request_delay),
        }
        if self.include_pattern:
            headers["X-Include-Pattern"] = self.include_pattern
        if self.exclude_pattern:
            headers["X-Exclude-Pattern"] = self.exclude_pattern
        if self.path_prefix:
            headers["X-Path-Prefix"] = self.path_prefix
        return headers


@dataclass
class DiscoveryProgress:
    """Progress information for a running discovery job.

    Attributes:
        percent: Completion percentage (0-100).
        pages_crawled: Number of pages crawled so far.
        urls_discovered: Number of URLs discovered so far.
        current_depth: Current crawl depth.
        message: Human-readable progress message.
    """

    percent: int = 0
    pages_crawled: int = 0
    urls_discovered: int = 0
    current_depth: int = 0
    message: str = ""


@dataclass
class DiscoveryStats:
    """Statistics for a completed discovery job.

    Attributes:
        pages_crawled: Total pages crawled.
        urls_found: Total URLs found during crawl.
        urls_returned: URLs returned in results (after filtering).
        urls_filtered: URLs excluded by filters.
        errors: Number of errors during crawl.
        duration_seconds: Total crawl duration.
    """

    pages_crawled: int = 0
    urls_found: int = 0
    urls_returned: int = 0
    urls_filtered: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


@dataclass
class DiscoveredURL:
    """A URL discovered during crawl.

    Attributes:
        url: The discovered URL.
        depth: Crawl depth at which URL was found.
        title: Page title if available.
        is_internal: Whether URL is internal to the domain.
    """

    url: str
    depth: int = 0
    title: str | None = None
    is_internal: bool = True


@dataclass
class DiscoveryJobStatus:
    """Status of a discovery job.

    Represents the current state of an async discovery job.

    Attributes:
        job_id: Unique job identifier.
        status: Job status (pending, queued, running, completed, failed, cancelled).
        start_url: The URL that started the discovery.
        progress: Progress information if job is running.
        stats: Statistics if job is completed.
        urls: Discovered URLs if job is completed.
        error: Error message if job failed.
    """

    job_id: str
    status: str
    start_url: str
    progress: DiscoveryProgress | None = None
    stats: DiscoveryStats | None = None
    urls: list[DiscoveredURL] = field(default_factory=list)
    error: str | None = None

    def is_terminal(self) -> bool:
        """Check if job is in a terminal state.

        Returns:
            True if job is completed, failed, or cancelled.
        """
        return self.status in ("completed", "failed", "cancelled")

    def is_running(self) -> bool:
        """Check if job is currently running.

        Returns:
            True if job is pending, queued, or running.
        """
        return self.status in ("pending", "queued", "running")
