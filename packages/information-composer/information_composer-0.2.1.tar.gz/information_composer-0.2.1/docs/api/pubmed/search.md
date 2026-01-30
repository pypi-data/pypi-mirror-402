# PubMed Search Module API

The PubMed search module provides a clean interface for PubMed search operations with proper type annotations and error handling.

## PubMedSearcher Class

### `PubMedSearcher()`

A simple wrapper for PubMed search functionality.

**Example:**
```python
from information_composer.pubmed.core.search import PubMedSearcher

searcher = PubMedSearcher()
```

### `search(query, email="mcp@information-composer.org", max_results=10)`

Search PubMed database and return detailed results.

**Parameters:**
- `query` (str): PubMed search query string
- `email` (str): Email address for NCBI's tracking purposes (default: "mcp@information-composer.org")
- `max_results` (int): Maximum number of results to return (default: 10)

**Returns:**
- `List[Dict[str, Any]]`: List of dictionaries containing detailed PubMed records

**Raises:**
- `RuntimeError`: If there's an error searching PubMed

**Example:**
```python
from information_composer.pubmed.core.search import PubMedSearcher

searcher = PubMedSearcher()

# Basic search
results = searcher.search("cancer research", "user@example.com", 20)

# Search with default parameters
results = searcher.search("machine learning")

# Process results
for article in results:
    print(f"PMID: {article['pmid']}")
    print(f"Title: {article['title']}")
    print(f"Journal: {article['journal']}")
    print("-" * 50)
```

## Search Query Examples

### Basic Queries

```python
# Simple keyword search
results = searcher.search("cancer immunotherapy")

# Phrase search
results = searcher.search('"machine learning" AND "deep learning"')

# Author search
results = searcher.search("Smith JA[Author]")

# Journal search
results = searcher.search("Nature[Journal]")
```

### Advanced Queries

```python
# Date range search
results = searcher.search("COVID-19 AND 2020[DP]")

# MeSH term search
results = searcher.search("Neoplasms[Mesh]")

# Boolean operators
results = searcher.search("(cancer OR tumor) AND (treatment OR therapy)")

# Field-specific search
results = searcher.search("cancer[Title] AND immunotherapy[Abstract]")
```

### Complex Queries

```python
# Multi-field search
query = """
(cancer OR tumor OR neoplasm) AND 
(immunotherapy OR "immune therapy") AND 
2020:2023[DP] AND 
"clinical trial"[Publication Type]
"""
results = searcher.search(query, max_results=50)
```

## Error Handling

The search module includes comprehensive error handling:

```python
from information_composer.pubmed.core.search import PubMedSearcher

searcher = PubMedSearcher()

try:
    results = searcher.search("invalid query with special chars !@#$%")
except RuntimeError as e:
    print(f"Search error: {e}")
    # Handle error appropriately
```

## Performance Considerations

- **Result limits**: Use appropriate `max_results` to avoid overwhelming responses
- **Query complexity**: Complex queries may take longer to process
- **Rate limiting**: Respect NCBI's rate limits (built into the underlying functions)
- **Caching**: Results are automatically cached when using the full PubMed module

## Integration Examples

### With MCP Server

```python
from information_composer.pubmed.core.search import PubMedSearcher

class PubMedMCPService:
    def __init__(self):
        self.searcher = PubMedSearcher()
    
    def search_articles(self, query: str, max_results: int = 10):
        """Search for articles via MCP."""
        return self.searcher.search(query, max_results=max_results)
```

### With Other Modules

```python
from information_composer.pubmed.core.search import PubMedSearcher
from information_composer.pubmed.pubmed import fetch_pubmed_details_batch_sync

def search_and_analyze(query: str, email: str):
    """Search and perform detailed analysis."""
    searcher = PubMedSearcher()
    
    # Get basic results
    results = searcher.search(query, email, 100)
    
    # Extract PMIDs for detailed analysis
    pmids = [article['pmid'] for article in results]
    
    # Get detailed information
    details = fetch_pubmed_details_batch_sync(pmids, email)
    
    return details
```

### Batch Processing

```python
def batch_search(queries: list, email: str):
    """Process multiple search queries."""
    searcher = PubMedSearcher()
    all_results = []
    
    for query in queries:
        print(f"Searching: {query}")
        results = searcher.search(query, email, 50)
        all_results.extend(results)
        print(f"  Found {len(results)} articles")
    
    return all_results

# Usage
queries = [
    "cancer immunotherapy",
    "machine learning healthcare",
    "COVID-19 vaccine"
]

results = batch_search(queries, "user@example.com")
print(f"Total articles found: {len(results)}")
```

## Data Structure

Search results contain the following fields:

```python
{
    "pmid": "12345678",                    # PubMed ID
    "title": "Article Title",              # Article title
    "abstract": "Article abstract...",     # Article abstract
    "journal": "Journal Name",             # Journal name
    "pubdate": "2023 Jan",                 # Publication date
    "publication_types": ["Journal Article"], # Publication types
    "authors": ["Smith J", "Doe A"],       # Author list
    "doi": "10.1234/example.doi",          # DOI
    "keywords": ["keyword1", "keyword2"],  # MeSH keywords
    "mesh_terms": ["D000123", "D000456"],  # MeSH term IDs
    "pmc": "PMC1234567",                   # PubMed Central ID (if available)
    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"  # Article URL
}
```

## Best Practices

### Query Construction

1. **Use specific terms**: More specific queries yield better results
2. **Combine keywords**: Use Boolean operators effectively
3. **Field-specific searches**: Target specific fields when appropriate
4. **Date ranges**: Use date filters to limit results to relevant time periods

### Result Processing

1. **Check for empty results**: Always handle cases where no results are found
2. **Validate data**: Check for missing or incomplete fields
3. **Handle errors**: Implement proper error handling for network issues
4. **Limit results**: Use appropriate limits to avoid overwhelming responses

### Performance Optimization

1. **Batch processing**: Process multiple queries efficiently
2. **Caching**: Leverage built-in caching mechanisms
3. **Rate limiting**: Respect API rate limits
4. **Memory management**: Process large result sets in chunks

## Troubleshooting

### Common Issues

1. **No results found**: Check query syntax and spelling
2. **Network errors**: Verify internet connection and try again
3. **Rate limiting**: Wait before retrying requests
4. **Invalid email**: Ensure email address is valid for NCBI tracking

### Debug Tips

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test with simple queries first
searcher = PubMedSearcher()
results = searcher.search("cancer", max_results=1)
print(f"Test search returned {len(results)} results")

# Check query syntax
query = "cancer AND immunotherapy"
print(f"Query: {query}")
results = searcher.search(query)
```