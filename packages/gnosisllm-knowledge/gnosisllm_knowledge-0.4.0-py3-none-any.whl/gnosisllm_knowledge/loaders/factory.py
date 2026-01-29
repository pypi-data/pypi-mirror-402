"""Loader factory with registry pattern."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from gnosisllm_knowledge.core.events.emitter import EventEmitter
from gnosisllm_knowledge.core.interfaces.chunker import ITextChunker
from gnosisllm_knowledge.core.interfaces.fetcher import IContentFetcher
from gnosisllm_knowledge.fetchers.config import NeoreaderConfig
from gnosisllm_knowledge.fetchers.neoreader import NeoreaderContentFetcher
from gnosisllm_knowledge.fetchers.neoreader_discovery import NeoreaderDiscoveryClient
from gnosisllm_knowledge.loaders.base import BaseLoader
from gnosisllm_knowledge.loaders.discovery import DiscoveryLoader
from gnosisllm_knowledge.loaders.sitemap import SitemapLoader
from gnosisllm_knowledge.loaders.website import WebsiteLoader

# Type for loader factory functions
LoaderCreator = Callable[
    [IContentFetcher, ITextChunker, dict[str, Any] | None, EventEmitter | None],
    BaseLoader,
]


def _create_discovery_loader(
    fetcher: IContentFetcher,
    chunker: ITextChunker,
    config: dict[str, Any] | None,
    event_emitter: EventEmitter | None,
) -> DiscoveryLoader:
    """Factory function for creating DiscoveryLoader instances.

    Creates a DiscoveryLoader with a NeoreaderDiscoveryClient. If the fetcher
    is a NeoreaderContentFetcher, reuses its config to ensure consistency.
    Otherwise, creates config from environment variables.

    Args:
        fetcher: Content fetcher for retrieving URL content.
        chunker: Text chunker for splitting content.
        config: Optional configuration dictionary.
        event_emitter: Optional event emitter for progress events.

    Returns:
        Configured DiscoveryLoader instance.
    """
    # Get config from fetcher if it's NeoreaderContentFetcher, otherwise use env
    if isinstance(fetcher, NeoreaderContentFetcher):
        neoreader_config = fetcher.config
    else:
        neoreader_config = NeoreaderConfig.from_env()

    discovery_client = NeoreaderDiscoveryClient(neoreader_config)
    return DiscoveryLoader(
        fetcher=fetcher,
        chunker=chunker,
        discovery_client=discovery_client,
        config=config,
        event_emitter=event_emitter,
    )


class LoaderFactory:
    """Factory for creating content loaders (Registry Pattern).

    The factory maintains a registry of loader types and can create
    the appropriate loader based on source URL or explicit type.

    Built-in loaders:
    - website: Single URL loading
    - sitemap: Sitemap XML with recursive discovery
    - discovery: Website crawling via Neo Reader Discovery API

    Example:
        ```python
        factory = LoaderFactory(fetcher, chunker)

        # Auto-detect source type
        loader = factory.create_for_source("https://example.com/sitemap.xml")

        # Explicit type
        loader = factory.create("sitemap", config={"max_urls": 500})

        # Discovery loader for full website crawling
        loader = factory.create("discovery", config={"max_depth": 3, "max_pages": 100})

        # Register custom loader
        factory.register("custom", MyCustomLoader)
        ```
    """

    def __init__(
        self,
        fetcher: IContentFetcher,
        chunker: ITextChunker,
        default_config: dict[str, Any] | None = None,
        event_emitter: EventEmitter | None = None,
    ) -> None:
        """Initialize the factory with dependencies.

        Args:
            fetcher: Content fetcher for all loaders.
            chunker: Text chunker for all loaders.
            default_config: Default configuration for all loaders.
            event_emitter: Event emitter for all loaders.
        """
        self._fetcher = fetcher
        self._chunker = chunker
        self._default_config = default_config or {}
        self._events = event_emitter or EventEmitter()
        self._logger = logging.getLogger(__name__)

        # Registry of loader creators
        self._registry: dict[str, LoaderCreator] = {}

        # Register built-in loaders
        self._register_builtin_loaders()

    def _register_builtin_loaders(self) -> None:
        """Register built-in loader types."""
        self.register("website", lambda f, c, cfg, e: WebsiteLoader(f, c, cfg, e))
        self.register("sitemap", lambda f, c, cfg, e: SitemapLoader(f, c, cfg, e))
        self.register("discovery", _create_discovery_loader)

    def register(self, name: str, creator: LoaderCreator) -> None:
        """Register a loader type.

        Args:
            name: Loader type name.
            creator: Factory function that creates the loader.

        Example:
            ```python
            factory.register("custom", lambda f, c, cfg, e: MyLoader(f, c, cfg, e))
            ```
        """
        self._registry[name.lower()] = creator
        self._logger.debug(f"Registered loader type: {name}")

    def unregister(self, name: str) -> bool:
        """Unregister a loader type.

        Args:
            name: Loader type name to remove.

        Returns:
            True if removed, False if not found.
        """
        name = name.lower()
        if name in self._registry:
            del self._registry[name]
            return True
        return False

    def list_types(self) -> list[str]:
        """List all registered loader types.

        Returns:
            List of loader type names.
        """
        return list(self._registry.keys())

    def create(
        self,
        loader_type: str,
        config: dict[str, Any] | None = None,
    ) -> BaseLoader:
        """Create a loader by type name.

        Args:
            loader_type: Type of loader to create.
            config: Optional configuration (merged with defaults).

        Returns:
            Configured loader instance.

        Raises:
            ValueError: If loader type is not registered.
        """
        loader_type = loader_type.lower()

        if loader_type not in self._registry:
            available = ", ".join(self._registry.keys())
            raise ValueError(
                f"Unknown loader type: {loader_type}. Available: {available}"
            )

        # Merge default config with provided config
        merged_config = {**self._default_config, **(config or {})}

        creator = self._registry[loader_type]
        return creator(self._fetcher, self._chunker, merged_config, self._events)

    def create_for_source(
        self,
        source: str,
        config: dict[str, Any] | None = None,
    ) -> BaseLoader:
        """Create the appropriate loader for a source URL.

        Auto-detects the loader type based on the source URL.

        Args:
            source: The source URL or path.
            config: Optional configuration.

        Returns:
            Loader that supports the source.

        Raises:
            ValueError: If no loader supports the source.
        """
        # Check each registered loader
        for loader_type, creator in self._registry.items():
            merged_config = {**self._default_config, **(config or {})}
            loader = creator(self._fetcher, self._chunker, merged_config, self._events)
            if loader.supports(source):
                self._logger.debug(f"Auto-selected loader type '{loader_type}' for {source}")
                return loader

        raise ValueError(f"No loader supports source: {source}")

    def detect_type(self, source: str) -> str | None:
        """Detect the loader type for a source URL.

        Args:
            source: The source URL or path.

        Returns:
            Loader type name or None if not detected.
        """
        for loader_type, creator in self._registry.items():
            loader = creator(self._fetcher, self._chunker, {}, None)
            if loader.supports(source):
                return loader_type
        return None

    def supports(self, source: str) -> bool:
        """Check if any loader supports the source.

        Args:
            source: The source URL or path.

        Returns:
            True if at least one loader supports it.
        """
        return self.detect_type(source) is not None
