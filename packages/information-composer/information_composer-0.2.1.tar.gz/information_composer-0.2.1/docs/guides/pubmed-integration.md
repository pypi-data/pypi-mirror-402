# PubMed Integration Guide

This guide explains how to integrate and use the PubMed module for searching, retrieving, and processing scientific literature from the PubMed database.

## Overview

The PubMed module provides comprehensive functionality for:
- Searching PubMed database with various query types
- Fetching detailed article information
- Processing Medline format data
- Filtering articles by keywords and impact factors
- Batch processing and caching

## Installation

The PubMed module is part of the Information Composer package. Install it with:

```bash
pip install information-composer
```

### Dependencies

The module requires the following dependencies:
- `biopython` - For PubMed API access
- `pandas` - For data manipulation
- `aiohttp` - For asynchronous HTTP requests
- `tqdm` - For progress bars
- `pubmed-parser` - For baseline data processing

## Basic Usage

### Simple Search

```python
from information_composer.pubmed.pubmed import query_pmid, fetch_pubmed_details_batch_sync

# Search for articles
pmids = query_pmid("cancer immunotherapy", "your-email@example.com", 50)

# Fetch detailed information
details = fetch_pubmed_details_batch_sync(pmids, "your-email@example.com")

# Process results
for article in details:
    print(f"Title: {article['title']}")
    print(f"Authors: {', '.join(article['authors'])}")
    print(f"Journal: {article['journal']}")
    print(f"Abstract: {article['abstract'][:200]}...")
    print("-" * 50)
```

### Date Range Search

```python
from information_composer.pubmed.pubmed import query_pmid_by_date

# Search for articles in specific date range
pmids = query_pmid_by_date(
    "COVID-19 vaccine",
    "your-email@example.com",
    "2020/01/01",
    "2023/12/31",
    6  # 6-month batches
)

print(f"Found {len(pmids)} COVID-19 vaccine articles")
```

### Using the Search Interface

```python
from information_composer.pubmed.core.search import PubMedSearcher

searcher = PubMedSearcher()

# Search with default parameters
results = searcher.search("machine learning healthcare")

# Search with custom parameters
results = searcher.search(
    "cancer immunotherapy",
    "your-email@example.com",
    100
)
```

## Advanced Usage

### Keyword Filtering

```python
from information_composer.pubmed.baseline import load_baseline

# Load and filter articles by keywords
cancer_articles = load_baseline(
    "pubmed_baseline.xml",
    "list",
    keywords=["cancer", "oncology", "tumor"],
    kw_filter="both"  # Search in both title and abstract
)

print(f"Found {len(cancer_articles)} cancer-related articles")
```

### Impact Factor Filtering

```python
# Load high impact factor articles
high_impact_articles = load_baseline(
    "pubmed_baseline.xml",
    "list",
    impact_factor=10.0  # Only journals with IF >= 10
)

print(f"Found {len(high_impact_articles)} high impact articles")
```

### Batch Processing

```python
import asyncio
from information_composer.pubmed.pubmed import fetch_pubmed_details_batch

async def process_large_dataset(pmids, email):
    """Process a large dataset asynchronously."""
    results = await fetch_pubmed_details_batch(pmids, email)
    return results

# Usage
pmids = ["12345678", "23456789", "34567890"]
email = "your-email@example.com"

results = asyncio.run(process_large_dataset(pmids, email))
```

## CLI Usage

The PubMed module includes a comprehensive command-line interface:

### Search Command

```bash
# Basic search
pubmed-cli search "cancer research" -e user@example.com

# Search with date range
pubmed-cli search "cancer research" -e user@example.com -s 2020/01/01 -d 2023/12/31

# Search with results saved to CSV
pubmed-cli search "machine learning" -e user@example.com -o results.csv -f csv

# Search and fetch detailed information
pubmed-cli search "cancer research" -e user@example.com --fetch-details -o results.json
```

### Details Command

```bash
# Get details for specific PMIDs
pubmed-cli details 12345678 23456789 -e user@example.com

# Get details with custom cache directory
pubmed-cli details 12345678 23456789 -e user@example.com --cache-dir ./pubmed_cache
```

### Batch Command

```bash
# Process PMIDs from file
pubmed-cli batch pmids.txt -e user@example.com -o results.json

# Process with CSV output
pubmed-cli batch pmids.txt -e user@example.com -o results.csv -f csv
```

### Cache Management

```bash
# Clean cache files older than 30 days
pubmed-cli cache clean --cache-dir ./pubmed_cache --older-than 30
```

## Integration Examples

### With DOI Downloader

```python
from information_composer.pubmed.pubmed import query_pmid, fetch_pubmed_details_batch_sync
from information_composer.core.doi_downloader import DOIDownloader

# Search for articles
pmids = query_pmid("cancer immunotherapy", "user@example.com", 20)
details = fetch_pubmed_details_batch_sync(pmids, "user@example.com")

# Download full-text articles
downloader = DOIDownloader()
for article in details:
    if article.get('doi'):
        try:
            downloader.download_by_doi(article['doi'], "downloads/")
            print(f"Downloaded: {article['title']}")
        except Exception as e:
            print(f"Failed to download {article['title']}: {e}")
```

### With Markdown Processing

```python
from information_composer.pubmed.pubmed import query_pmid, fetch_pubmed_details_batch_sync
from information_composer.markdown.markdown import MarkdownConverter

# Search and fetch articles
pmids = query_pmid("machine learning", "user@example.com", 10)
details = fetch_pubmed_details_batch_sync(pmids, "user@example.com")

# Convert abstracts to markdown
converter = MarkdownConverter()
for article in details:
    if article.get('abstract'):
        markdown_content = converter.convert_to_markdown(article['abstract'])
        # Save or process markdown content
        print(f"Converted abstract for: {article['title']}")
```

### With LLM Filtering

```python
from information_composer.pubmed.pubmed import query_pmid, fetch_pubmed_details_batch_sync
from information_composer.llm_filter.core.filter import LLMFilter

# Search for articles
pmids = query_pmid("artificial intelligence", "user@example.com", 50)
details = fetch_pubmed_details_batch_sync(pmids, "user@example.com")

# Filter using LLM
filter_config = {
    "model": "qwen-plus",
    "api_key": "your-api-key",
    "criteria": "Articles about medical AI applications"
}

llm_filter = LLMFilter(filter_config)
filtered_articles = llm_filter.filter_articles(details)

print(f"Filtered {len(filtered_articles)} relevant articles from {len(details)} total")
```

### With MCP Server

```python
from information_composer.pubmed.core.search import PubMedSearcher
from information_composer.mcp.server import MCPServer

class PubMedMCPService:
    def __init__(self):
        self.searcher = PubMedSearcher()
    
    async def search_articles(self, query: str, max_results: int = 10):
        """Search for articles via MCP."""
        return self.searcher.search(query, max_results=max_results)
    
    async def get_article_details(self, pmids: list, email: str):
        """Get detailed article information via MCP."""
        from information_composer.pubmed.pubmed import fetch_pubmed_details_batch_sync
        return fetch_pubmed_details_batch_sync(pmids, email)

# Register with MCP server
server = MCPServer()
server.register_service("pubmed", PubMedMCPService())
```

## Configuration

### Environment Variables

Set the following environment variables for optimal performance:

```bash
# NCBI email for tracking (required)
export NCBI_EMAIL="your-email@example.com"

# Cache directory
export PUBMED_CACHE_DIR="./pubmed_cache"

# Rate limiting (requests per second)
export PUBMED_RATE_LIMIT="0.34"

# Chunk size for batch processing
export PUBMED_CHUNK_SIZE="200"
```

### Configuration File

Create a `pubmed_config.yaml` file:

```yaml
email: "your-email@example.com"
cache_dir: "./pubmed_cache"
rate_limit: 0.34
chunk_size: 200
max_retries: 3
delay_between_chunks: 0.34
```

## Performance Optimization

### Caching

Enable caching to avoid repeated requests:

```python
from information_composer.pubmed.pubmed import fetch_pubmed_details_batch_sync

# Use caching
details = fetch_pubmed_details_batch_sync(
    pmids,
    "user@example.com",
    cache_dir="./pubmed_cache"
)
```

### Batch Processing

Process large datasets efficiently:

```python
def process_large_dataset(pmids, email, chunk_size=200):
    """Process large dataset in chunks."""
    all_results = []
    
    for i in range(0, len(pmids), chunk_size):
        chunk = pmids[i:i + chunk_size]
        print(f"Processing chunk {i//chunk_size + 1}/{(len(pmids) + chunk_size - 1)//chunk_size}")
        
        results = fetch_pubmed_details_batch_sync(chunk, email)
        all_results.extend(results)
    
    return all_results
```

### Memory Management

Handle large datasets without memory issues:

```python
import pandas as pd
from information_composer.pubmed.baseline import load_baseline

# Process in chunks to manage memory
def process_baseline_file(filename, chunk_size=1000):
    """Process large baseline file in chunks."""
    # Load as dictionary to avoid memory issues
    articles_dict = load_baseline(filename, "dict")
    
    # Process in chunks
    pmids = list(articles_dict.keys())
    for i in range(0, len(pmids), chunk_size):
        chunk_pmids = pmids[i:i + chunk_size]
        chunk_articles = [articles_dict[pmid] for pmid in chunk_pmids]
        
        # Process chunk
        process_chunk(chunk_articles)
```

## Error Handling

### Network Errors

```python
import time
from information_composer.pubmed.pubmed import query_pmid

def robust_search(query, email, max_retries=3):
    """Search with retry logic."""
    for attempt in range(max_retries):
        try:
            return query_pmid(query, email, 100)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

### Data Validation

```python
def validate_article(article):
    """Validate article data."""
    required_fields = ['pmid', 'title', 'journal']
    
    for field in required_fields:
        if field not in article or not article[field]:
            return False
    
    return True

# Usage
details = fetch_pubmed_details_batch_sync(pmids, email)
valid_articles = [article for article in details if validate_article(article)]
print(f"Valid articles: {len(valid_articles)}/{len(details)}")
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**: NCBI enforces rate limits. Use built-in delays or implement custom rate limiting.

2. **Network Timeouts**: Handle network issues gracefully with retry logic.

3. **Invalid Queries**: Validate query syntax before sending to PubMed.

4. **Memory Issues**: Process large datasets in chunks to avoid memory problems.

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Your PubMed operations
pmids = query_pmid("cancer research", "user@example.com")
```

### Testing

Test your integration with small datasets first:

```python
# Test with small dataset
test_pmids = ["12345678", "23456789"]
test_details = fetch_pubmed_details_batch_sync(test_pmids, "user@example.com")

if len(test_details) == len(test_pmids):
    print("Test successful!")
else:
    print(f"Expected {len(test_pmids)} results, got {len(test_details)}")
```

## Best Practices

1. **Always provide a valid email**: NCBI requires email for tracking purposes.

2. **Use appropriate limits**: Don't request more results than needed.

3. **Implement caching**: Cache results to avoid repeated requests.

4. **Handle errors gracefully**: Implement proper error handling and retry logic.

5. **Respect rate limits**: Don't overwhelm the PubMed API.

6. **Validate data**: Always validate retrieved data before processing.

7. **Use batch processing**: Process large datasets efficiently.

8. **Monitor usage**: Keep track of API usage and costs.

## Examples Repository

For more examples, see the `examples/` directory in the Information Composer package:

- `pubmed_cli_example.py` - CLI usage examples
- `pubmed_details_example.py` - Detailed article retrieval
- `pubmed_batch_example.py` - Batch processing examples
- `pubmed_keywords_filter_example.py` - Keyword filtering examples