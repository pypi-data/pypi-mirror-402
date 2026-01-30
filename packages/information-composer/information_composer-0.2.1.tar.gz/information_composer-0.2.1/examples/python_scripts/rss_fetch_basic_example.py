"""Basic RSS fetcher example.

This example demonstrates how to:
1. Parse local RSS/Atom feed files
2. Extract article metadata
3. Display feed content
"""

from pathlib import Path

from information_composer.rss.parser import RSSParser


def main():
    """Run basic RSS fetcher example."""
    # Initialize parser
    parser = RSSParser()

    # Path to test data
    test_data_dir = Path(__file__).parent.parent.parent / "tests" / "test_data" / "rss"

    # Example 1: Parse RSS 2.0 feed
    print("=" * 60)
    print("Example 1: Parsing RSS 2.0 Feed")
    print("=" * 60)

    rss_file = test_data_dir / "sample_rss_2.0.xml"
    with open(rss_file) as f:
        rss_content = f.read()

    metadata, entries = parser.parse(rss_content, str(rss_file))

    if metadata is None:
        print("Failed to parse feed metadata")
        return

    print(f"\nFeed Title: {metadata.title}")
    print(f"Feed Description: {metadata.description}")
    print(f"Feed Format: {metadata.format.value}")
    print(f"\nTotal Entries: {len(entries)}")

    for idx, entry in enumerate(entries, 1):
        print(f"\n--- Article {idx} ---")
        print(f"Title: {entry.title}")
        print(f"Link: {entry.link}")
        print(f"Published: {entry.published}")
        print(f"Authors: {', '.join(entry.authors) if entry.authors else entry.author}")
        print(f"Categories: {', '.join(entry.categories)}")
        print(f"Description: {entry.description[:100]}...")

    # Example 2: Parse Atom feed
    print("\n" + "=" * 60)
    print("Example 2: Parsing Atom Feed")
    print("=" * 60)

    atom_file = test_data_dir / "sample_atom_1.0.xml"
    with open(atom_file) as f:
        atom_content = f.read()

    metadata, entries = parser.parse(atom_content, str(atom_file))

    if metadata is None:
        print("Failed to parse feed metadata")
        return

    print(f"\nFeed Title: {metadata.title}")
    print(f"Feed Format: {metadata.format.value}")
    print(f"\nTotal Entries: {len(entries)}")

    for idx, entry in enumerate(entries, 1):
        print(f"\n--- Entry {idx} ---")
        print(f"Title: {entry.title}")
        print(f"Link: {entry.link}")
        print(f"Summary: {entry.description}")

    # Example 3: Parse academic journal feed
    print("\n" + "=" * 60)
    print("Example 3: Parsing Academic Journal Feed")
    print("=" * 60)

    academic_file = test_data_dir / "sample_academic_rss.xml"
    with open(academic_file) as f:
        academic_content = f.read()

    metadata, entries = parser.parse(academic_content, str(academic_file))

    if metadata is None:
        print("Failed to parse feed metadata")
        return

    print(f"\nJournal Feed: {metadata.title}")
    print(f"Total Articles: {len(entries)}")

    for idx, entry in enumerate(entries, 1):
        print(f"\n--- Article {idx} ---")
        print(f"Title: {entry.title}")
        print(f"Authors: {', '.join(entry.authors)}")
        print(f"DOI: {entry.doi}")
        print(f"Journal: {entry.journal_name}")
        if entry.volume:
            print(f"Volume/Issue: {entry.volume}/{entry.issue}")
        print(f"Article Type: {entry.article_type if entry.article_type else 'N/A'}")
        print(f"Link: {entry.link}")

    # Example 4: LLM-optimized output
    print("\n" + "=" * 60)
    print("Example 4: LLM-Optimized JSON Output")
    print("=" * 60)

    from datetime import datetime

    from information_composer.rss.models import FeedResult, FeedStatus

    # Create FeedResult for LLM integration
    result = FeedResult(
        feed_url=str(academic_file),
        metadata=metadata,
        entries=entries[:2],  # Limit to 2 entries for demo
        fetch_time=datetime.now(),
        status=FeedStatus.SUCCESS,
    )

    # Get LLM-optimized dictionary
    llm_data = result.to_llm_optimized_dict(max_summary_length=200)

    print("\nLLM Context:")
    print(f"Description: {llm_data['result']['llm_context']['description']}")
    print("Suggested Actions:")
    for action in llm_data["result"]["llm_context"]["suggested_actions"]:
        print(f"  - {action}")

    print("\nSummary:")
    summary = llm_data["result"]["summary"]
    print(f"Feed: {summary['feed_title']}")
    print(f"Total Entries: {summary['total_entries']}")

    print("\nFirst Entry (truncated for LLM):")
    first_entry = llm_data["result"]["data"]["entries"][0]
    print(f"Title: {first_entry['title']}")
    print(f"Summary: {first_entry['summary']}")
    print(f"DOI: {first_entry['metadata']['doi']}")


if __name__ == "__main__":
    main()
