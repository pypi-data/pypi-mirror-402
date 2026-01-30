"""Basic RSS feed fetcher example.

This example demonstrates:
1. Fetching a single RSS feed (Molecular Plant journal)
2. Parsing feed metadata and entries
3. Extracting academic metadata (DOI, authors, journal info)
4. Outputting in LLM-optimized format for MCP integration
"""

import json

from information_composer.rss import RSSFetcher


def main() -> None:
    """Run basic RSS fetch example."""
    # Initialize fetcher
    fetcher = RSSFetcher()

    # Fetch Molecular Plant RSS feed
    feed_url = "http://www.cell.com/molecular-plant/inpress.rss"
    print(f"Fetching feed from: {feed_url}\n")

    result = fetcher.fetch_single(feed_url, max_entries=5)

    # Check status
    if result.status.name != "SUCCESS":
        print(f"Failed to fetch feed: {result.error}")
        return

    # Print feed metadata
    if result.metadata:
        print("=" * 60)
        print("FEED METADATA")
        print("=" * 60)
        print(f"Title: {result.metadata.title}")
        print(f"Description: {result.metadata.description}")
        print(f"Link: {result.metadata.link}")
        print(f"Language: {result.metadata.language}")
        print(f"Format: {result.metadata.format.value}")
        print(f"Total Entries: {len(result.entries)}\n")

    # Print entries
    print("=" * 60)
    print("ARTICLES")
    print("=" * 60)

    for i, entry in enumerate(result.entries[:5], 1):
        print(f"\n{i}. {entry.title}")
        print(f"   Link: {entry.link}")

        if entry.published:
            print(f"   Published: {entry.published.strftime('%Y-%m-%d %H:%M')}")

        if entry.authors:
            print(f"   Authors: {', '.join(entry.authors)}")

        if entry.doi:
            print(f"   DOI: {entry.doi}")

        if entry.journal_name:
            print(f"   Journal: {entry.journal_name}")

        if entry.description:
            # Truncate long descriptions
            desc = entry.description
            if len(desc) > 200:
                desc = desc[:200] + "..."
            print(f"   Summary: {desc}")

        print("-" * 60)

    # Export to LLM-optimized JSON format
    print("\n" + "=" * 60)
    print("LLM-OPTIMIZED OUTPUT")
    print("=" * 60)

    llm_data = result.to_llm_optimized_dict(
        max_summary_length=300, max_content_length=1000
    )

    # Save to file
    output_file = "molecular_plant_feed_llm.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(llm_data, f, ensure_ascii=False, indent=2)

    print(f"\nLLM-optimized output saved to: {output_file}")
    print("\nThis JSON can be passed to LLM via MCP for:")
    print("- 分析最新的学术进展")
    print("- 提取关键研究发现")
    print("- 生成文献综述")

    # Show sample of LLM context
    print("\nLLM Context Info:")
    llm_context = llm_data["result"]["llm_context"]
    print(f"  Description: {llm_context['description']}")
    print("  Suggested Actions:")
    for action in llm_context["suggested_actions"]:
        print(f"    - {action}")


if __name__ == "__main__":
    main()
