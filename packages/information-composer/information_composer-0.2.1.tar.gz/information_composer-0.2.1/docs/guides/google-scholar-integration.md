# Google Scholar Integration Guide

This guide explains how to use the Google Scholar integration module for searching and retrieving academic papers from Google Scholar.

## Overview

The Google Scholar integration provides comprehensive functionality for:
- Searching Google Scholar with various query types
- Retrieving detailed paper information including citations, abstracts, and metadata
- Supporting multiple search strategies (requests, selenium, scholarly)
- Caching results for improved performance
- Rate limiting and error handling

## Installation

The Google Scholar module is part of the Information Composer package. Install it with:

```bash
pip install information-composer
```

### Optional Dependencies

For full functionality, install optional dependencies:

```bash
# For Selenium-based search strategy
pip install selenium

# For Scholarly-based search strategy  
pip install scholarly
```

## Basic Usage

### Simple Search

```python
from information_composer.sites.google_scholar.models import SearchConfig, SearchStrategy
from information_composer.sites.google_scholar.crawler import GoogleScholarCrawler

# Create search configuration
config = SearchConfig(
    max_results=10,
    search_strategy=SearchStrategy.REQUESTS,
    include_abstracts=True,
    include_citations=True
)

# Initialize crawler
crawler = GoogleScholarCrawler(config)

# Perform search
results = crawler.search("machine learning artificial intelligence")

# Access results
for paper in results.papers:
    print(f"Title: {paper.title}")
    print(f"Authors: {', '.join(paper.authors)}")
    print(f"Journal: {paper.journal}")
    print(f"Year: {paper.year}")
    print(f"Citations: {paper.citation_count}")
    print(f"DOI: {paper.doi}")
    print("---")
```

### Advanced Search with Filters

```python
from information_composer.sites.google_scholar.models import SearchConfig

# Advanced configuration
config = SearchConfig(
    max_results=50,
    year_range=(2020, 2024),
    language="en",
    include_abstracts=True,
    include_citations=True,
    include_patents=False,
    sort_by="date",  # or "relevance"
    rate_limit=2.0,  # 2 seconds between requests
    max_retries=3,
    timeout=30.0,
    cache_dir="./cache",
    cache_ttl_days=7,
    resolve_dois=True,
    link_pubmed=True
)

crawler = GoogleScholarCrawler(config)
results = crawler.search("deep learning neural networks")
```

## Search Strategies

### 1. Requests Strategy (Default)

Uses HTTP requests directly. Fastest but may be blocked by Google.

```python
config = SearchConfig(search_strategy=SearchStrategy.REQUESTS)
crawler = GoogleScholarCrawler(config)
```

### 2. Selenium Strategy

Uses browser automation. More reliable but slower.

```python
config = SearchConfig(
    search_strategy=SearchStrategy.SELENIUM,
    use_selenium_fallback=True  # Fallback to requests if selenium fails
)
crawler = GoogleScholarCrawler(config)
```

### 3. Scholarly Strategy

Uses the scholarly library. Good balance of speed and reliability.

```python
config = SearchConfig(
    search_strategy=SearchStrategy.SCHOLARLY,
    use_selenium_fallback=True
)
crawler = GoogleScholarCrawler(config)
```

## Data Models

### SearchConfig

Configuration class for search parameters:

```python
from information_composer.sites.google_scholar.models import SearchConfig

config = SearchConfig(
    # Basic search parameters
    max_results=100,
    year_range=(2020, 2024),
    language="en",
    
    # Search behavior
    include_citations=True,
    include_abstracts=True,
    include_patents=False,
    sort_by="relevance",
    
    # Rate limiting and performance
    rate_limit=2.0,
    max_retries=3,
    timeout=30.0,
    
    # Strategy selection
    search_strategy=SearchStrategy.REQUESTS,
    use_selenium_fallback=True,
    
    # Caching
    cache_dir="./cache",
    cache_ttl_days=30,
    
    # Data enhancement
    resolve_dois=True,
    link_pubmed=True,
    fetch_abstracts=True
)
```

### GoogleScholarPaper

Data model for individual papers:

```python
from information_composer.sites.google_scholar.models import GoogleScholarPaper

paper = GoogleScholarPaper(
    google_scholar_id="12345",
    title="Machine Learning in Practice",
    authors=["John Doe", "Jane Smith"],
    journal="Nature Machine Intelligence",
    year=2023,
    abstract="This paper presents...",
    doi="10.1038/s42256-023-00123-4",
    citation_count=150,
    search_rank=1,
    confidence_score=0.95
)

# Access paper information
print(paper.title)
print(paper.get_primary_author())
print(paper.get_citation_display())
print(f"Valid: {paper.is_valid()}")
```

### SearchResult

Container for search results:

```python
from information_composer.sites.google_scholar.models import SearchResult

result = SearchResult(
    papers=[paper1, paper2, paper3],
    query="machine learning",
    total_results=1000,
    search_time=5.2,
    strategy_used=SearchStrategy.REQUESTS,
    cached=False
)

# Update statistics
result.update_statistics()
print(f"Valid papers: {result.valid_papers}")
print(f"Papers with DOI: {result.papers_with_doi}")

# Get top papers
top_papers = result.get_top_papers(10)

# Filter by year
recent_papers = result.filter_by_year(2023, 2024)
```

## Advanced Usage

### Batch Processing

```python
queries = [
    "machine learning",
    "artificial intelligence", 
    "deep learning",
    "neural networks"
]

all_results = []
for query in queries:
    print(f"Searching: {query}")
    results = crawler.search(query)
    all_results.append(results)
    
    # Add delay between searches
    time.sleep(2)

# Combine results
combined_papers = []
for result in all_results:
    combined_papers.extend(result.papers)
```

### Caching

```python
# Enable caching
config = SearchConfig(
    cache_dir="./google_scholar_cache",
    cache_ttl_days=7
)

crawler = GoogleScholarCrawler(config)

# First search - will be cached
results1 = crawler.search("machine learning")

# Second search - will use cache if within TTL
results2 = crawler.search("machine learning")
```

### Error Handling

```python
try:
    results = crawler.search("machine learning")
    if results.cached:
        print("Results loaded from cache")
    else:
        print(f"Found {len(results.papers)} papers")
        
except Exception as e:
    print(f"Search failed: {e}")
    # Handle error appropriately
```

### Custom User Agents

```python
config = SearchConfig(
    user_agent_rotation=True,  # Enable user agent rotation
    rate_limit=3.0  # Slower rate to avoid detection
)

crawler = GoogleScholarCrawler(config)
```

## Data Export

### Export to JSON

```python
import json

# Search and get results
results = crawler.search("machine learning")

# Export to JSON
with open("results.json", "w") as f:
    json.dump(results.to_dict(), f, indent=2)
```

### Export to CSV

```python
import pandas as pd

# Convert to DataFrame
papers_data = [paper.to_dict() for paper in results.papers]
df = pd.DataFrame(papers_data)

# Export to CSV
df.to_csv("papers.csv", index=False)
```

### Export Citations

```python
# Generate citation list
citations = []
for paper in results.papers:
    citations.append(paper.get_citation_display())

# Save to file
with open("citations.txt", "w") as f:
    f.write("\n".join(citations))
```

## Performance Optimization

### Rate Limiting

```python
# Conservative rate limiting
config = SearchConfig(
    rate_limit=3.0,  # 3 seconds between requests
    max_retries=5,
    timeout=60.0
)
```

### Caching Strategy

```python
# Long-term caching for stable queries
config = SearchConfig(
    cache_dir="./long_term_cache",
    cache_ttl_days=30
)

# Short-term caching for dynamic queries
config = SearchConfig(
    cache_dir="./short_term_cache", 
    cache_ttl_days=1
)
```

### Memory Management

```python
# Process results in batches
batch_size = 100
for i in range(0, len(results.papers), batch_size):
    batch = results.papers[i:i + batch_size]
    # Process batch
    process_batch(batch)
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**: If you get blocked, increase `rate_limit` and `max_retries`
2. **Timeout Errors**: Increase `timeout` value
3. **Empty Results**: Check your query and try different search strategies
4. **Selenium Issues**: Ensure Chrome/Chromium is installed for Selenium strategy

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Search with debug information
results = crawler.search("machine learning")
```

### Strategy Fallback

```python
# Enable automatic fallback
config = SearchConfig(
    search_strategy=SearchStrategy.SELENIUM,
    use_selenium_fallback=True  # Falls back to requests if selenium fails
)
```

## Best Practices

1. **Respect Rate Limits**: Use appropriate delays between requests
2. **Use Caching**: Enable caching for repeated searches
3. **Handle Errors**: Implement proper error handling
4. **Validate Results**: Check paper validity before processing
5. **Monitor Usage**: Track API usage and performance
6. **Update Regularly**: Keep dependencies updated

## Example Script

Here's a complete example script:

```python
#!/usr/bin/env python3
"""
Google Scholar Search Example
"""

import json
from information_composer.sites.google_scholar.models import SearchConfig, SearchStrategy
from information_composer.sites.google_scholar.crawler import GoogleScholarCrawler

def main():
    # Configuration
    config = SearchConfig(
        max_results=20,
        year_range=(2020, 2024),
        include_abstracts=True,
        include_citations=True,
        search_strategy=SearchStrategy.REQUESTS,
        cache_dir="./cache",
        rate_limit=2.0
    )
    
    # Initialize crawler
    crawler = GoogleScholarCrawler(config)
    
    # Search query
    query = "machine learning artificial intelligence"
    
    try:
        print(f"Searching Google Scholar for: {query}")
        results = crawler.search(query)
        
        print(f"Found {len(results.papers)} papers")
        print(f"Search time: {results.search_time:.2f} seconds")
        print(f"Strategy used: {results.strategy_used.value}")
        print(f"Cached: {results.cached}")
        
        # Display results
        for i, paper in enumerate(results.papers[:5], 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            print(f"   Journal: {paper.journal}")
            print(f"   Year: {paper.year}")
            print(f"   Citations: {paper.citation_count}")
            print(f"   DOI: {paper.doi}")
        
        # Save results
        with open("search_results.json", "w") as f:
            json.dump(results.to_dict(), f, indent=2)
        
        print(f"\nResults saved to search_results.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

This guide provides comprehensive information for using the Google Scholar integration effectively. The module is designed to be robust and handle various search scenarios while providing detailed paper information for further analysis.