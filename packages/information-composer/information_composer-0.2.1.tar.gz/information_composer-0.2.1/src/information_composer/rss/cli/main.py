"""CLI tool for RSS feed fetcher."""

import asyncio
import json
from pathlib import Path
import sys

import click

from information_composer.rss.config import ConfigManager
from information_composer.rss.fetcher import RSSFetcher
from information_composer.rss.models import FeedConfig


@click.group()
def cli() -> None:
    """RSS Feed Fetcher CLI."""
    pass


@cli.command()
@click.argument("feed_url")
@click.option(
    "--output", "-o", type=click.Choice(["json", "markdown", "text"]), default="json"
)
@click.option("--output-file", "-f", type=click.Path())
@click.option("--cache-dir", type=click.Path())
@click.option("--no-cache", is_flag=True)
@click.option("--limit", "-l", type=int)
@click.option("--llm-optimized", is_flag=True)
def fetch(
    feed_url: str,
    output: str,
    output_file: str | None,
    cache_dir: str | None,
    no_cache: bool,
    limit: int | None,
    llm_optimized: bool,
) -> None:
    """Fetch a single RSS feed."""
    fetcher = RSSFetcher(cache_dir=cache_dir)
    result = fetcher.fetch_single(feed_url, use_cache=not no_cache, max_entries=limit)
    # Format output
    if llm_optimized:
        output_data = result.to_llm_optimized_dict()
    else:
        output_data = result.to_dict()
    if output == "json":
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    elif output == "markdown":
        output_str = _format_markdown(result)
    else:  # text
        output_str = _format_text(result)
    # Output
    if output_file:
        Path(output_file).write_text(output_str, encoding="utf-8")
        click.echo(f"Output written to {output_file}")
    else:
        click.echo(output_str)


@cli.command()
@click.argument("urls_file", type=click.Path(exists=True))
@click.option("--output-dir", "-d", type=click.Path())
@click.option(
    "--output-format", type=click.Choice(["json", "markdown"]), default="json"
)
@click.option("--cache-dir", type=click.Path())
@click.option("--concurrent", "-c", type=int, default=5)
def batch(
    urls_file: str,
    output_dir: str | None,
    output_format: str,
    cache_dir: str | None,
    concurrent: int,
) -> None:
    """Fetch multiple feeds from URL list."""
    # Read URLs
    urls = Path(urls_file).read_text(encoding="utf-8").strip().split("\n")
    urls = [url.strip() for url in urls if url.strip()]
    # Fetch
    fetcher = RSSFetcher(cache_dir=cache_dir)
    results = asyncio.run(fetcher.fetch_batch_async(urls, max_concurrent=concurrent))
    # Output
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for i, result in enumerate(results):
            filename = f"feed_{i + 1}.{output_format}"
            file_path = output_path / filename
            if output_format == "json":
                content = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
            else:
                content = _format_markdown(result)
            file_path.write_text(content, encoding="utf-8")
        click.echo(f"Fetched {len(results)} feeds to {output_dir}")
    else:
        for result in results:
            click.echo(f"\n{'=' * 60}")
            click.echo(f"Feed: {result.feed_url}")
            click.echo(f"Status: {result.status.value}")
            click.echo(f"Entries: {len(result.entries)}")


@cli.group()
def config() -> None:
    """Manage RSS feed configuration."""
    pass


@config.command("init")
@click.option("--config", "-c", type=click.Path())
def config_init(config: str | None) -> None:
    """Initialize default configuration."""
    manager = ConfigManager(config)
    manager.init_default_config()
    click.echo(f"Configuration initialized at {manager.config_path}")


@config.command("list-feeds")
@click.option("--config", "-c", type=click.Path())
@click.option("--format", type=click.Choice(["json", "text"]), default="text")
def config_list_feeds(config: str | None, format: str) -> None:
    """List all configured feeds."""
    manager = ConfigManager(config)
    manager.load_config()
    feeds = manager.get_enabled_feeds()
    if format == "json":
        output = [feed.to_dict() for feed in feeds]
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for feed in feeds:
            status = "✓" if feed.enabled else "✗"
            click.echo(f"{status} {feed.name} - {feed.url}")


@config.command("add-feed")
@click.option("--name", required=True)
@click.option("--url", required=True)
@click.option("--category", default="")
@click.option("--group", default="default")
@click.option("--config", "-c", type=click.Path())
def config_add_feed(
    name: str,
    url: str,
    category: str,
    group: str,
    config: str | None,
) -> None:
    """Add a new feed."""
    manager = ConfigManager(config)
    manager.load_config()
    feed = FeedConfig(name=name, url=url, category=category)
    manager.add_feed(feed, group)
    manager.save_config()
    click.echo(f"Added feed '{name}' to group '{group}'")


@cli.command("fetch-all")
@click.option("--config", "-c", type=click.Path())
@click.option("--group", "-g")
@click.option("--output-dir", "-d", type=click.Path())
@click.option(
    "--output-format", type=click.Choice(["json", "markdown"]), default="json"
)
@click.option("--llm-optimized", is_flag=True)
@click.option("--only-new", is_flag=True)
def fetch_all(
    config: str | None,
    group: str | None,
    output_dir: str | None,
    output_format: str,
    llm_optimized: bool,
    only_new: bool,
) -> None:
    """Fetch all configured feeds."""
    # Load config
    manager = ConfigManager(config)
    manager.load_config()
    if group:
        feeds = manager.get_feeds_by_group(group)
    else:
        feeds = manager.get_enabled_feeds()
    if not feeds:
        click.echo("No feeds configured")
        return
    # Fetch
    fetcher = RSSFetcher()
    urls = [feed.url for feed in feeds]
    results = asyncio.run(fetcher.fetch_batch_async(urls))
    # Output
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for feed, result in zip(feeds, results, strict=False):
            filename = f"{feed.name.replace(' ', '_')}.{output_format}"
            file_path = output_path / filename
            if llm_optimized:
                data = result.to_llm_optimized_dict()
            else:
                data = result.to_dict()
            if output_format == "json":
                content = json.dumps(data, ensure_ascii=False, indent=2)
            else:
                content = _format_markdown(result)
            file_path.write_text(content, encoding="utf-8")
        click.echo(f"Fetched {len(results)} feeds to {output_dir}")
    else:
        # Print summary
        total = len(results)
        success = sum(1 for r in results if r.status.name == "SUCCESS")
        click.echo(f"Fetched {success}/{total} feeds successfully")


def _format_markdown(result) -> str:
    """Format feed result as Markdown."""
    lines = []
    # Title
    if result.metadata:
        lines.append(f"# {result.metadata.title}\n")
        lines.append(f"**来源**: {result.feed_url}")
        lines.append(f"**更新时间**: {result.fetch_time.strftime('%Y-%m-%d %H:%M')}\n")
        if result.metadata.description:
            lines.append(f"**描述**: {result.metadata.description}\n")
    lines.append("---\n")
    lines.append(f"## 文章列表（共 {len(result.entries)} 篇）\n")
    # Entries
    for i, entry in enumerate(result.entries, 1):
        lines.append(f"### {i}. {entry.title}\n")
        lines.append(f"- **链接**: {entry.link}")
        if entry.published:
            lines.append(
                f"- **发布时间**: {entry.published.strftime('%Y-%m-%d %H:%M')}"
            )
        if entry.authors:
            lines.append(f"- **作者**: {', '.join(entry.authors)}")
        if entry.doi:
            lines.append(f"- **DOI**: {entry.doi}")
        if entry.description:
            lines.append(f"\n**摘要**: {entry.description}\n")
        lines.append("---\n")
    return "\n".join(lines)


def _format_text(result) -> str:
    """Format feed result as plain text."""
    lines = []
    if result.metadata:
        lines.append(f"来源: {result.metadata.title} ({result.feed_url})")
        lines.append(f"获取时间: {result.fetch_time.strftime('%Y-%m-%d %H:%M')}\n")
    for i, entry in enumerate(result.entries, 1):
        lines.append(f"文章 {i}:")
        lines.append(f"标题: {entry.title}")
        lines.append(f"链接: {entry.link}")
        if entry.published:
            lines.append(f"发布: {entry.published.strftime('%Y-%m-%d %H:%M')}")
        if entry.authors:
            lines.append(f"作者: {', '.join(entry.authors)}")
        if entry.description:
            lines.append(f"摘要: {entry.description}")
        lines.append("")
    lines.append(f"共 {len(result.entries)} 篇文章")
    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
