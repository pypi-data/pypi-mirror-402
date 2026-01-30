#!/usr/bin/env python3
"""
Google Scholar batch processing example.
Demonstrates large-scale data collection.
"""

import asyncio
import json
from pathlib import Path
import time

from information_composer.sites.google_scholar import (
    GoogleScholarCrawler,
    SearchConfig,
    SearchStrategy,
)


async def batch_processing_example():
    """Demonstrate batch processing capabilities."""
    print("🔄 Google Scholar Batch Processing Example")
    print("=" * 60)

    # Research topics for batch processing
    research_topics = [
        "artificial intelligence machine learning",
        "natural language processing transformers",
        "computer vision deep learning",
        "reinforcement learning robotics",
        "neural networks optimization",
        "data mining big data analytics",
        "blockchain technology security",
        "quantum computing algorithms",
        "bioinformatics computational biology",
        "human-computer interaction usability",
    ]

    # Configure for batch processing
    config = SearchConfig(
        max_results=25,  # Moderate number per query
        year_range=(2020, 2023),
        rate_limit=3.0,  # Conservative rate limiting
        search_strategy=SearchStrategy.REQUESTS,
        use_selenium_fallback=True,
        cache_dir="./cache/batch_processing",
        cache_ttl_days=14,
        resolve_dois=False,  # Skip for faster processing
        link_pubmed=False,  # Skip for faster processing
    )

    async with GoogleScholarCrawler(config=config) as crawler:
        print(f"Processing {len(research_topics)} research topics...")
        print(f"Rate limit: {config.rate_limit}s between requests")
        print(f"Max results per topic: {config.max_results}")
        print()

        start_time = time.time()

        # Process batch
        batch_results = await crawler.search_batch(
            research_topics,
            max_results_per_query=config.max_results,
            delay_between_queries=config.rate_limit,
        )

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        print("📊 Batch Processing Results")
        print("-" * 40)

        total_papers = 0
        successful_queries = 0
        failed_queries = 0

        for topic, result in batch_results.items():
            paper_count = len(result.papers)
            total_papers += paper_count

            if paper_count > 0:
                successful_queries += 1
                status = "✅"
            else:
                failed_queries += 1
                status = "❌"

            print(f"{status} {topic[:40]:<40} {paper_count:>3} papers")

        print("-" * 40)
        print(f"Total processing time: {total_time:.1f} seconds")
        print(
            f"Average time per query: {total_time / len(research_topics):.1f} seconds"
        )
        print(f"Successful queries: {successful_queries}/{len(research_topics)}")
        print(f"Total papers collected: {total_papers}")
        print(f"Average papers per topic: {total_papers / len(research_topics):.1f}")
        print()

        # Generate comprehensive analysis
        await generate_batch_analysis(batch_results, "batch_analysis_report.json")

        # Export results in multiple formats
        await export_batch_data(crawler, batch_results)

        return batch_results


async def generate_batch_analysis(batch_results, output_file):
    """Generate comprehensive analysis of batch results."""
    print("📈 Generating Batch Analysis")
    print("-" * 30)

    analysis = {
        "summary": {
            "total_queries": len(batch_results),
            "total_papers": sum(
                len(result.papers) for result in batch_results.values()
            ),
            "successful_queries": sum(
                1 for result in batch_results.values() if result.papers
            ),
            "timestamp": time.time(),
        },
        "query_results": {},
        "overall_statistics": {},
        "top_papers": [],
        "research_trends": {},
    }

    # Analyze each query
    all_papers = []
    for query, result in batch_results.items():
        query_analysis = {
            "paper_count": len(result.papers),
            "search_time": result.search_time,
            "strategy_used": result.strategy_used.value,
            "valid_papers": result.valid_papers,
            "papers_with_doi": result.papers_with_doi,
            "avg_citation_count": sum(p.citation_count for p in result.papers)
            / len(result.papers)
            if result.papers
            else 0,
            "year_distribution": {},
        }

        # Year distribution for this query
        for paper in result.papers:
            if paper.year:
                year = paper.year
                query_analysis["year_distribution"][year] = (
                    query_analysis["year_distribution"].get(year, 0) + 1
                )

        analysis["query_results"][query] = query_analysis
        all_papers.extend(result.papers)

    # Overall statistics
    if all_papers:
        analysis["overall_statistics"] = {
            "total_papers": len(all_papers),
            "avg_citation_count": sum(p.citation_count for p in all_papers)
            / len(all_papers),
            "papers_with_doi": sum(1 for p in all_papers if p.doi),
            "papers_with_abstract": sum(1 for p in all_papers if p.abstract),
            "unique_journals": len({p.journal for p in all_papers if p.journal}),
            "year_range": {
                "earliest": min(p.year for p in all_papers if p.year),
                "latest": max(p.year for p in all_papers if p.year),
            }
            if any(p.year for p in all_papers)
            else None,
        }

        # Top papers by citation count
        top_papers = sorted(all_papers, key=lambda p: p.citation_count, reverse=True)[
            :20
        ]
        analysis["top_papers"] = [
            {
                "title": paper.title,
                "authors": paper.authors[:3],
                "journal": paper.journal,
                "year": paper.year,
                "citation_count": paper.citation_count,
                "doi": paper.doi,
            }
            for paper in top_papers
        ]

        # Research trends by year
        year_counts = {}
        for paper in all_papers:
            if paper.year:
                year_counts[paper.year] = year_counts.get(paper.year, 0) + 1

        analysis["research_trends"]["publications_by_year"] = dict(
            sorted(year_counts.items())
        )

        # Top journals
        journal_counts = {}
        for paper in all_papers:
            if paper.journal:
                journal_counts[paper.journal] = journal_counts.get(paper.journal, 0) + 1

        top_journals = sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]
        analysis["research_trends"]["top_journals"] = [
            {"journal": journal, "paper_count": count}
            for journal, count in top_journals
        ]

    # Save analysis
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Analysis saved to: {output_file}")
    print(f"   📊 Analyzed {len(all_papers)} total papers")
    print(
        f"   🏆 Top paper: {analysis['top_papers'][0]['title'][:50]}..."
        if analysis["top_papers"]
        else "   No papers found"
    )


async def export_batch_data(crawler, batch_results):
    """Export batch data in multiple formats."""
    print("💾 Exporting Batch Data")
    print("-" * 25)

    # Combine all papers
    all_papers = []
    for result in batch_results.values():
        all_papers.extend(result.papers)

    if not all_papers:
        print("   ⚠️  No papers to export")
        return

    # Export to JSON
    await crawler.export_results(all_papers, "batch_all_papers.json", "json")
    print(f"   ✅ JSON: batch_all_papers.json ({len(all_papers)} papers)")

    # Export to CSV
    await crawler.export_results(all_papers, "batch_all_papers.csv", "csv")
    print(f"   ✅ CSV: batch_all_papers.csv ({len(all_papers)} papers)")

    # Export high-impact papers to BibTeX
    high_impact_papers = [p for p in all_papers if p.citation_count >= 20]
    if high_impact_papers:
        await crawler.export_results(
            high_impact_papers, "batch_high_impact.bib", "bibtex"
        )
        print(
            "   ✅ BibTeX: batch_high_impact.bib "
            f"({len(high_impact_papers)} high-impact papers)"
        )

    # Create query-specific exports
    for query, result in batch_results.items():
        if result.papers:
            safe_filename = "".join(
                c for c in query[:30] if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_filename = safe_filename.replace(" ", "_")

            await crawler.export_results(
                result.papers, f"query_{safe_filename}.json", "json"
            )

    print("   ✅ Individual query files created")


async def demonstrate_error_handling():
    """Demonstrate error handling and recovery in batch processing."""
    print("\n🛡️  Error Handling Demonstration")
    print("=" * 50)

    # Include some problematic queries
    test_queries = [
        "valid machine learning query",
        "",  # Empty query
        "a" * 1000,  # Very long query
        "normal deep learning query",
        "another valid query about AI",
    ]

    config = SearchConfig(
        max_results=5, rate_limit=1.0, cache_dir="./cache/error_handling"
    )

    async with GoogleScholarCrawler(config=config) as crawler:
        print(f"Testing error handling with {len(test_queries)} queries...")

        results = await crawler.search_batch(test_queries, max_results_per_query=5)

        print("\n📊 Error Handling Results:")
        for query, result in results.items():
            query_display = query[:30] + "..." if len(query) > 30 else query
            query_display = query_display or "[empty query]"

            if result.papers:
                print(f"   ✅ {query_display}: {len(result.papers)} papers")
            else:
                print(f"   ❌ {query_display}: No results")


if __name__ == "__main__":

    async def main():
        # Run batch processing example
        # batch_results = await batch_processing_example()
        await batch_processing_example()

        # Demonstrate error handling
        await demonstrate_error_handling()

        print("\n🎉 Batch processing example completed!")
        print("Check the generated files:")
        print("   - batch_analysis_report.json")
        print("   - batch_all_papers.json")
        print("   - batch_all_papers.csv")
        print("   - batch_high_impact.bib")
        print("   - query_*.json (individual query results)")

    asyncio.run(main())
