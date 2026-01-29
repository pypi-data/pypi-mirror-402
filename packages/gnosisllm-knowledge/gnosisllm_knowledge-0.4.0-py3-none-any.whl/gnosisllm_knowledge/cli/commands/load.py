"""Load command for indexing content from URLs or sitemaps.

Fetches content, chunks it for optimal embedding, and indexes
into OpenSearch with automatic embedding generation via ingest pipeline.

Note:
    This library is tenant-agnostic. Multi-tenancy is achieved through index
    isolation - each tenant should use a separate index (e.g., "knowledge-{account_id}").
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from opensearchpy import AsyncOpenSearch
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from gnosisllm_knowledge.backends.opensearch.config import OpenSearchConfig
from gnosisllm_knowledge.backends.opensearch.indexer import OpenSearchIndexer
from gnosisllm_knowledge.chunking.sentence import SentenceChunker
from gnosisllm_knowledge.cli.display.service import RichDisplayService
from gnosisllm_knowledge.cli.utils.config import CliConfig
from gnosisllm_knowledge.core.domain.document import Document, DocumentStatus
from gnosisllm_knowledge.core.events.emitter import EventEmitter
from gnosisllm_knowledge.core.events.types import (
    DiscoveryCompletedEvent,
    DiscoveryFailedEvent,
    DiscoveryProgressEvent,
    DiscoveryStartedEvent,
    EventType,
)
from gnosisllm_knowledge.fetchers.config import NeoreaderConfig
from gnosisllm_knowledge.fetchers.neoreader import NeoreaderContentFetcher
from gnosisllm_knowledge.loaders.factory import LoaderFactory

if TYPE_CHECKING:
    pass


async def load_command(
    display: RichDisplayService,
    source: str,
    source_type: str | None = None,
    index_name: str = "knowledge",
    collection_id: str | None = None,
    source_id: str | None = None,
    batch_size: int = 100,
    max_urls: int = 1000,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    discovery: bool = False,
    max_depth: int = 3,
    max_pages: int = 100,
    same_domain: bool = True,
) -> None:
    """Execute the load command.

    Note:
        Multi-tenancy is achieved through index isolation. Use tenant-specific
        index names instead (e.g., --index knowledge-tenant-123).

    Args:
        display: Display service for output.
        source: URL or sitemap to load content from.
        source_type: Source type (website, sitemap, discovery) or auto-detect.
        index_name: Target index name (use tenant-specific name for isolation).
        collection_id: Collection grouping ID.
        source_id: Source identifier (defaults to URL).
        batch_size: Documents per indexing batch.
        max_urls: Maximum URLs to process from sitemap.
        force: Delete existing source documents first.
        dry_run: Preview without indexing.
        verbose: Show per-document progress.
        discovery: Use discovery loader (website crawling) instead of single URL.
        max_depth: Maximum crawl depth for discovery (default: 3).
        max_pages: Maximum pages to discover (default: 100).
        same_domain: Only crawl URLs on the same domain (default: True).
    """
    # Load configuration
    cli_config = CliConfig.from_env()

    # Auto-detect source type
    detected_type = source_type
    if not detected_type:
        if discovery:
            detected_type = "discovery"
        elif "sitemap" in source.lower() or source.endswith(".xml"):
            detected_type = "sitemap"
        else:
            detected_type = "website"
    elif discovery and detected_type != "discovery":
        # --discovery flag overrides explicit type for website URLs
        display.warning(
            f"Using discovery loader (--discovery flag overrides --type {detected_type})"
        )
        detected_type = "discovery"

    # Default source_id to URL
    final_source_id = source_id or source

    # Display header
    display.header(
        "GnosisLLM Knowledge Loader",
        f"Loading from: {source[:60]}{'...' if len(source) > 60 else ''}",
    )

    # Show configuration
    is_auto_detected = not source_type and not discovery
    type_suffix = " (auto-detected)" if is_auto_detected else ""
    config_rows = [
        ("Source", source[:50] + "..." if len(source) > 50 else source),
        ("Type", f"{detected_type}{type_suffix}"),
        ("Target Index", index_name),
        ("Batch Size", str(batch_size)),
    ]

    # Add type-specific configuration
    if detected_type == "sitemap":
        config_rows.append(("Max URLs", str(max_urls)))
    elif detected_type == "discovery":
        config_rows.append(("Max Depth", str(max_depth)))
        config_rows.append(("Max Pages", str(max_pages)))
        config_rows.append(("Same Domain", "Yes" if same_domain else "No"))

    config_rows.extend([
        ("Neoreader", cli_config.neoreader_host),
        ("OpenSearch", f"{cli_config.opensearch_host}:{cli_config.opensearch_port}"),
    ])

    if collection_id:
        config_rows.append(("Collection ID", collection_id))
    if force:
        config_rows.append(("Force Reload", "Yes"))
    if dry_run:
        config_rows.append(("Dry Run", "Yes (no indexing)"))

    display.table("Configuration", config_rows)
    display.newline()

    # Create fetcher
    neoreader_config = NeoreaderConfig(host=cli_config.neoreader_host)
    fetcher = NeoreaderContentFetcher(neoreader_config)

    # Check Neoreader health
    display.info("Checking Neoreader connection...")
    if await fetcher.health_check():
        display.success("Neoreader connected")
    else:
        display.warning(f"Cannot connect to Neoreader at {cli_config.neoreader_host}")
        display.info("Continuing with fallback HTTP fetcher...")

    # Create event emitter for discovery progress tracking
    event_emitter = EventEmitter()

    # Create loader
    chunker = SentenceChunker()
    loader_factory = LoaderFactory(
        fetcher=fetcher,
        chunker=chunker,
        event_emitter=event_emitter,
    )

    try:
        loader = loader_factory.create(detected_type)
    except ValueError as e:
        display.format_error_with_suggestion(
            error=f"Invalid source: {e}",
            suggestion="Check the URL format or specify --type explicitly.",
            command="gnosisllm-knowledge load <url> --type sitemap",
        )
        sys.exit(1)

    # Configure sitemap loader if applicable
    if detected_type == "sitemap":
        loader.max_urls = max_urls

    display.newline()

    # Discover URLs
    display.info("Discovering URLs...")
    with display.loading_spinner("Discovering..."):
        validation = await loader.validate_source(source)

    if not validation.valid:
        display.format_error_with_suggestion(
            error=f"Source validation failed: {validation.message}",
            suggestion="Check that the URL is accessible.",
        )
        sys.exit(1)

    # Build loader options for discovery
    loader_options: dict = {}
    if detected_type == "discovery":
        loader_options = {
            "max_depth": max_depth,
            "max_pages": max_pages,
            "same_domain": same_domain,
        }

    # Load documents with discovery progress display
    documents: list[Document] = []
    url_count = 0
    discovery_state: dict = {"started": False, "completed": False, "job_id": None}

    # Register discovery event handlers for Rich display
    def _on_discovery_started(event: DiscoveryStartedEvent) -> None:
        discovery_state["started"] = True
        discovery_state["job_id"] = event.job_id

    def _on_discovery_progress(event: DiscoveryProgressEvent) -> None:
        # Update will be handled in the progress context
        discovery_state["percent"] = event.percent
        discovery_state["pages_crawled"] = event.pages_crawled
        discovery_state["urls_discovered"] = event.urls_discovered
        discovery_state["current_depth"] = event.current_depth
        discovery_state["message"] = event.message

    def _on_discovery_completed(event: DiscoveryCompletedEvent) -> None:
        discovery_state["completed"] = True
        discovery_state["urls_count"] = event.urls_count
        discovery_state["duration_seconds"] = event.duration_seconds

    def _on_discovery_failed(event: DiscoveryFailedEvent) -> None:
        discovery_state["failed"] = True
        discovery_state["error"] = event.error

    # Register discovery event handlers
    if detected_type == "discovery":
        event_emitter.add_handler(EventType.DISCOVERY_STARTED, _on_discovery_started)
        event_emitter.add_handler(EventType.DISCOVERY_PROGRESS, _on_discovery_progress)
        event_emitter.add_handler(EventType.DISCOVERY_COMPLETED, _on_discovery_completed)
        event_emitter.add_handler(EventType.DISCOVERY_FAILED, _on_discovery_failed)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=display.console,
    ) as progress:
        # Add task for discovery phase (if applicable)
        if detected_type == "discovery":
            discovery_task = progress.add_task(
                "Discovering URLs...",
                total=max_pages,
            )

        load_task = progress.add_task("Loading content...", total=None, visible=False)

        async for doc in loader.load_streaming(source, **loader_options):
            # Update discovery progress if available
            if detected_type == "discovery":
                if discovery_state.get("started") and not discovery_state.get("completed"):
                    pages = discovery_state.get("pages_crawled", 0)
                    urls = discovery_state.get("urls_discovered", 0)
                    depth = discovery_state.get("current_depth", 0)
                    progress.update(
                        discovery_task,
                        completed=pages,
                        description=f"Discovering... (depth {depth}, {urls} URLs found)",
                    )
                elif discovery_state.get("completed"):
                    # Hide discovery task and show load task
                    progress.update(discovery_task, visible=False)
                    progress.update(load_task, visible=True)

            documents.append(doc)
            url_count += 1
            progress.update(load_task, advance=1, description=f"Loading... ({url_count} docs)")

            if url_count >= max_urls and detected_type == "sitemap":
                break

        progress.update(load_task, completed=url_count)

    # Show discovery summary if applicable
    if detected_type == "discovery" and discovery_state.get("completed"):
        display.success(
            f"Discovered {discovery_state.get('urls_count', 0)} URLs "
            f"in {discovery_state.get('duration_seconds', 0):.1f}s"
        )

    display.success(f"Loaded {len(documents)} documents")

    if not documents:
        display.warning("No documents found. Check the source URL.")
        sys.exit(0)

    # Dry run - stop here
    if dry_run:
        display.newline()
        display.panel(
            f"Documents found: {len(documents)}\n\n"
            "Sample URLs:\n"
            + "\n".join(f"  • {d.url}" for d in documents[:5])
            + (f"\n  ... and {len(documents) - 5} more" if len(documents) > 5 else ""),
            title="Dry Run Complete",
            style="info",
        )
        return

    # Chunk documents
    display.newline()
    display.info("Chunking documents for optimal embedding...")

    chunker = SentenceChunker()
    chunked_documents: list[Document] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=display.console,
    ) as progress:
        chunk_task = progress.add_task("Chunking...", total=len(documents))

        for doc in documents:
            chunks = chunker.chunk(doc.content)

            if len(chunks) == 1:
                # Single chunk - use original document
                chunked_doc = Document(
                    content=doc.content,
                    url=doc.url,
                    title=doc.title,
                    source=final_source_id,
                    collection_id=collection_id,
                    source_id=final_source_id,
                    metadata=doc.metadata,
                    status=DocumentStatus.PENDING,
                )
                chunked_documents.append(chunked_doc)
            else:
                # Multiple chunks - create chunk documents
                for i, chunk in enumerate(chunks):
                    chunk_doc = Document(
                        content=chunk.content,
                        url=doc.url,
                        title=doc.title,
                        source=final_source_id,
                        collection_id=collection_id,
                        source_id=final_source_id,
                        chunk_index=i,
                        total_chunks=len(chunks),
                        parent_doc_id=doc.doc_id,
                        metadata={**(doc.metadata or {}), "chunk_start": chunk.start_position},
                        status=DocumentStatus.PENDING,
                    )
                    chunked_documents.append(chunk_doc)

            progress.update(chunk_task, advance=1)

    display.success(f"Created {len(chunked_documents)} chunks from {len(documents)} documents")

    # Create OpenSearch client
    http_auth = None
    if cli_config.opensearch_username and cli_config.opensearch_password:
        http_auth = (cli_config.opensearch_username, cli_config.opensearch_password)

    client = AsyncOpenSearch(
        hosts=[{"host": cli_config.opensearch_host, "port": cli_config.opensearch_port}],
        http_auth=http_auth,
        use_ssl=cli_config.opensearch_use_ssl,
        verify_certs=cli_config.opensearch_verify_certs,
        ssl_show_warn=False,
    )

    try:
        # Create indexer config from environment, preserving k-NN and other settings
        # This ensures proper vector mappings are used when creating indices
        base_config = OpenSearchConfig.from_env()
        opensearch_config = OpenSearchConfig(
            # CLI/CliConfig overrides
            host=cli_config.opensearch_host,
            port=cli_config.opensearch_port,
            username=cli_config.opensearch_username,
            password=cli_config.opensearch_password,
            use_ssl=cli_config.opensearch_use_ssl,
            verify_certs=cli_config.opensearch_verify_certs,
            model_id=cli_config.opensearch_model_id,
            ingest_pipeline_name=cli_config.opensearch_ingest_pipeline_name,
            # Preserve env-based k-NN settings for proper index mappings
            embedding_model=base_config.embedding_model,
            embedding_dimension=base_config.embedding_dimension,
            embedding_field=base_config.embedding_field,
            knn_engine=base_config.knn_engine,
            knn_space_type=base_config.knn_space_type,
            knn_algo_param_ef_search=base_config.knn_algo_param_ef_search,
            knn_algo_param_ef_construction=base_config.knn_algo_param_ef_construction,
            knn_algo_param_m=base_config.knn_algo_param_m,
            # Preserve other settings
            index_prefix=base_config.index_prefix,
            number_of_shards=base_config.number_of_shards,
            number_of_replicas=base_config.number_of_replicas,
            search_pipeline_name=base_config.search_pipeline_name,
        )

        indexer = OpenSearchIndexer(client, opensearch_config)

        # Ensure index exists
        display.newline()
        display.info(f"Ensuring index '{index_name}' exists...")

        try:
            created = await indexer.ensure_index(index_name)
            if created:
                display.success(f"Created index: {index_name}")
            else:
                display.info(f"Index already exists: {index_name}")
        except Exception as e:
            display.format_error_with_suggestion(
                error=f"Failed to ensure index: {e}",
                suggestion="Run 'gnosisllm-knowledge setup' first to configure OpenSearch.",
            )
            sys.exit(1)

        # Force delete existing if requested
        if force:
            display.info(f"Deleting existing documents from source: {final_source_id}")
            deleted = await indexer.delete_by_query(
                {"query": {"term": {"source_id": final_source_id}}},
                index_name,
            )
            if deleted > 0:
                display.info(f"Deleted {deleted} existing documents")

        # Index documents
        display.newline()
        display.info("Indexing documents...")

        indexed_count = 0
        failed_count = 0
        all_errors: list[dict] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=display.console,
        ) as progress:
            index_task = progress.add_task("Indexing...", total=len(chunked_documents))

            # Index in batches
            for i in range(0, len(chunked_documents), batch_size):
                batch = chunked_documents[i : i + batch_size]

                result = await indexer.bulk_index(batch, index_name, batch_size=batch_size)
                indexed_count += result.indexed_count
                failed_count += result.failed_count
                if result.errors:
                    all_errors.extend(result.errors)

                progress.update(index_task, advance=len(batch))

        # Refresh index to make documents searchable
        await indexer.refresh_index(index_name)

        display.newline()

        # Display results
        if failed_count == 0:
            display.panel(
                f"Documents Loaded:     [cyan]{len(documents)}[/cyan]\n"
                f"Chunks Created:       [cyan]{len(chunked_documents)}[/cyan]\n"
                f"Documents Indexed:    [green]{indexed_count}[/green]\n"
                f"Index:                [cyan]{index_name}[/cyan]\n\n"
                f"Verify with:\n"
                f'  [dim]gnosisllm-knowledge search "your query" --index {index_name}[/dim]',
                title="Loading Complete",
                style="success",
            )
        else:
            # Build error details section
            error_details = ""
            if all_errors:
                error_details = "\n\n[bold red]Error Details:[/bold red]\n"
                for i, err in enumerate(all_errors[:5], 1):  # Show first 5 errors
                    if isinstance(err, dict):
                        error_type = err.get("error", {}).get("type", "unknown") if isinstance(err.get("error"), dict) else str(err.get("error", "unknown"))
                        error_reason = err.get("error", {}).get("reason", "No reason provided") if isinstance(err.get("error"), dict) else str(err.get("error", "No details"))
                        doc_id = err.get("_id", "unknown")
                        error_details += f"  {i}. [dim]Doc {doc_id}:[/dim] {error_type} - {error_reason}\n"
                    else:
                        error_details += f"  {i}. {err}\n"
                if len(all_errors) > 5:
                    error_details += f"  ... and {len(all_errors) - 5} more errors\n"

            display.panel(
                f"Documents Loaded:     [cyan]{len(documents)}[/cyan]\n"
                f"Chunks Created:       [cyan]{len(chunked_documents)}[/cyan]\n"
                f"Documents Indexed:    [green]{indexed_count}[/green]\n"
                f"Documents Failed:     [red]{failed_count}[/red]\n"
                f"Index:                [cyan]{index_name}[/cyan]"
                f"{error_details}",
                title="Loading Complete (with errors)",
                style="warning",
            )
            sys.exit(1)

    finally:
        await client.close()
