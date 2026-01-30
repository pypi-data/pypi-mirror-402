#!/usr/bin/env python3
"""
Advanced example demonstrating Google Scholar crawler capabilities.
"""

import asyncio
from pathlib import Path

from information_composer.sites.google_scholar import (
    GoogleScholarCrawler,
    SearchConfig,
    SearchStrategy,
)


async def advanced_search_example():
    """Demonstrate advanced Google Scholar search functionality."""
    print("🔍 Google Scholar Advanced Search Example")
    print("=" * 60)

    # Configure search with advanced parameters
    config = SearchConfig(
        max_results=50,
        year_range=(2018, 2023),
        language="en",
        include_citations=True,
        include_abstracts=True,
        include_patents=False,
        sort_by="relevance",
        rate_limit=2.5,
        search_strategy=SearchStrategy.REQUESTS,
        use_selenium_fallback=True,
        cache_dir="./cache/google_scholar_advanced",
        resolve_dois=True,
        link_pubmed=True,
    )

    async with GoogleScholarCrawler(config=config) as crawler:
        # Example 1: Advanced structured search
        print("1️⃣ Advanced Structured Search")
        print("-" * 30)

        result1 = await crawler.advanced_search(
            title_keywords=["neural networks", "deep learning"],
            author_names=["Hinton", "LeCun"],
            exclude_terms=["survey", "review"],
        )

        print(f"   Found {len(result1.papers)} papers with structured search")
        print(f"   Search time: {result1.search_time:.2f}s")

        if result1.papers:
            print(f"   Top result: {result1.papers[0].title}")
            print(f"   Authors: {', '.join(result1.papers[0].authors[:3])}")
        print()

        # Example 2: Batch search with multiple queries
        print("2️⃣ Batch Search")
        print("-" * 30)

        queries = [
            "transformer neural networks attention mechanism",
            "BERT language model natural language processing",
            "GPT generative pre-trained transformer",
            "computer vision convolutional neural networks",
        ]

        batch_results = await crawler.search_batch(
            queries, max_results_per_query=20, delay_between_queries=3.0
        )

        print(f"   Processed {len(batch_results)} queries")
        total_papers = sum(len(result.papers) for result in batch_results.values())
        print(f"   Total papers from batch search: {total_papers}")

        # Display batch results summary
        for query, result in batch_results.items():
            print(f"   '{query[:40]}...': {len(result.papers)} papers")
        print()

        # Example 3: Search with specific year and journal focus
        print("3️⃣ Targeted Journal Search")
        print("-" * 30)

        result3 = await crawler.search(
            "artificial intelligence ethics fairness",
            max_results=30,
            year_range=(2021, 2023),
        )

        # Identify high-impact papers (≥50 citations)
        high_impact_papers = [p for p in result3.papers if p.citation_count >= 50]
        print(f"   High-impact papers (≥50 citations): {len(high_impact_papers)}")

        if high_impact_papers:
            print(f"   Most cited: {high_impact_papers[0].title}")
            print(f"   Citations: {high_impact_papers[0].citation_count}")
        print()

        # Example 4: Export results in different formats
        print("4️⃣ Export Results")
        print("-" * 30)

        # Export to JSON
        await crawler.export_results(result1, "advanced_search_structured.json", "json")
        print("   ✅ Exported structured search to JSON")

        # Export to CSV
        await crawler.export_results(result3, "ai_ethics_papers.csv", "csv")
        print("   ✅ Exported AI ethics papers to CSV")

        # Export to BibTeX
        await crawler.export_results(
            high_impact_papers, "high_impact_papers.bib", "bibtex"
        )
        print("   ✅ Exported high-impact papers to BibTeX")

        # Export batch results
        all_batch_papers = []
        for result in batch_results.values():
            all_batch_papers.extend(result.papers)

        await crawler.export_results(
            all_batch_papers, "batch_search_results.json", "json"
        )
        print("   ✅ Exported batch results to JSON")
        print()

        # Example 5: Demonstrate data composition
        print("5️⃣ Data Analysis")
        print("-" * 30)

        # Compose data from all sources
        composed_data = await crawler.compose_data(
            {
                "structured_search": result1,
                "batch_results": batch_results,
                "targeted_search": result3,
                "high_impact_papers": high_impact_papers,
            }
        )

        # Export composed data
        await crawler.export_results(
            composed_data, "advanced_search_composed.json", "json"
        )
        await crawler.export_results(result1, "advanced_search_structured.json", "json")

        # Display summary statistics
        print("   Summary statistics:")
        avg_citation = composed_data["statistics"]["avg_citation_count"]
        print(f"   - Average citation count: {avg_citation:.1f}")

        year_dist = dict(
            list(composed_data["statistics"]["year_distribution"].items())[:3]
        )
        print(f"   - Year distribution: {year_dist}")

        top_journals = [
            j["journal"] for j in composed_data["statistics"]["top_journals"][:3]
        ]
        print(f"   - Top journals: {top_journals}")

        return {
            "structured_search": result1,
            "batch_results": batch_results,
            "targeted_search": result3,
            "high_impact_papers": high_impact_papers,
            "composed_data": composed_data,
        }


# Separate the function definitions properly
async def integration_example():
    """Demonstrate integration with other information-composer modules."""
    print("\n🔗 Integration with Information Composer Modules")
    print("=" * 60)

    # Comment out unused imports
    # from information_composer.core.doi_downloader import DOIDownloader
    # from information_composer.pubmed.pubmed import query_pmid

    config = SearchConfig(max_results=10, resolve_dois=True, link_pubmed=True)

    async with GoogleScholarCrawler(config=config) as crawler:
        # Search for papers
        result = await crawler.search("COVID-19 vaccine efficacy")

        print(f"Found {len(result.papers)} papers on COVID-19 vaccines")

        # Demonstrate DOI integration
        papers_with_doi = [p for p in result.papers if p.doi]
        print(f"Papers with DOI: {len(papers_with_doi)}")

        if papers_with_doi:
            # Try to download PDF for first paper with DOI
            # doi_downloader = DOIDownloader()
            first_paper = papers_with_doi[0]

            print(f"\nTrying to download PDF for: {first_paper.title[:50]}...")
            print(f"DOI: {first_paper.doi}")

            # Note: This would actually attempt to download
            # result = doi_downloader.download_single(
            #     first_paper.doi, "downloads"
            # )
            print("   (PDF download skipped in example)")

        # Demonstrate PubMed integration
        papers_with_pubmed = [p for p in result.papers if p.pubmed_id]
        print(f"\nPapers linked to PubMed: {len(papers_with_pubmed)}")

        if papers_with_pubmed:
            first_pubmed_paper = papers_with_pubmed[0]
            print(f"PubMed ID: {first_pubmed_paper.pubmed_id}")

            # Could fetch additional data from PubMed here
            print("   (PubMed data fetch skipped in example)")

        print("\n✅ Integration example completed")


if __name__ == "__main__":

    async def main():
        # results = await advanced_search_example()
        await advanced_search_example()
        await integration_example()

        print("\n🎉 Advanced example completed!")
        print("Check the output files in the current directory for exported results.")

    asyncio.run(main())
