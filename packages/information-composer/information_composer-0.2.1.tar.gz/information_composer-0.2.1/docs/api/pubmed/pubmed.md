# PubMed Module API

The PubMed module provides comprehensive functionality for querying the PubMed database, fetching article details, and processing Medline format data.

## Core Functions

### `query_pmid(query, email, retmax=9999)`

Query PubMed database and return a list of PMIDs matching the search query.

**Parameters:**
- `query` (str): PubMed search query string
- `email` (str): Email address for NCBI's tracking purposes
- `retmax` (int): Maximum number of results to return (default: 9999)

**Returns:**
- `List[str]`: List of PMIDs matching the query

**Raises:**
- `RuntimeError`: If there's an error querying PubMed

**Example:**
```python
from information_composer.pubmed.pubmed import query_pmid

pmids = query_pmid("cancer research", "user@example.com", 100)
print(f"Found {len(pmids)} articles")
```

### `query_pmid_by_date(query, email, start_date=None, end_date=None, batch_months=12)`

Query PubMed database with date ranges to get all unique PMIDs matching the search query.

**Parameters:**
- `query` (str): PubMed search query string
- `email` (str): Email address for NCBI's tracking purposes
- `start_date` (str, optional): Start date in format 'YYYY/MM/DD' (defaults to earliest possible)
- `end_date` (str, optional): End date in format 'YYYY/MM/DD' (defaults to today)
- `batch_months` (int): Number of months per batch (default: 12)

**Returns:**
- `List[str]`: List of unique PMIDs matching the query

**Raises:**
- `RuntimeError`: If there's an error querying PubMed or too many results

**Example:**
```python
from information_composer.pubmed.pubmed import query_pmid_by_date

pmids = query_pmid_by_date(
    "machine learning",
    "user@example.com",
    "2020/01/01",
    "2023/12/31",
    6
)
print(f"Found {len(pmids)} articles in date range")
```

### `fetch_pubmed_details_batch_sync(pmids, email, cache_dir=None, chunk_size=200, delay_between_chunks=0.34, max_retries=3)`

Fetch detailed information for a list of PMIDs synchronously.

**Parameters:**
- `pmids` (List[str]): List of PMIDs to fetch details for
- `email` (str): Email address for NCBI's tracking purposes
- `cache_dir` (str, optional): Directory to cache results
- `chunk_size` (int): Number of PMIDs to process in each chunk
- `delay_between_chunks` (float): Delay between chunks in seconds
- `max_retries` (int): Maximum number of retry attempts

**Returns:**
- `List[Dict[str, Any]]`: List of detailed article information

**Example:**
```python
from information_composer.pubmed.pubmed import fetch_pubmed_details_batch_sync

pmids = ["12345678", "23456789"]
details = fetch_pubmed_details_batch_sync(pmids, "user@example.com")
for article in details:
    print(f"Title: {article.get('title', 'N/A')}")
    print(f"Abstract: {article.get('abstract', 'N/A')[:100]}...")
```

### `load_pubmed_file(filename, output_type="list")`

Load and parse PubMed Medline file.

**Parameters:**
- `filename` (str): Path to Medline format file
- `output_type` (str): Output format ('pd', 'dict', 'list')

**Returns:**
- `Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]`: Parsed data in specified format

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If output_type is invalid
- `RuntimeError`: If there's an error parsing the file

**Example:**
```python
from information_composer.pubmed.pubmed import load_pubmed_file

# Load as list of dictionaries
articles = load_pubmed_file("pubmed_data.txt", "list")

# Load as pandas DataFrame
df = load_pubmed_file("pubmed_data.txt", "pd")

# Load as dictionary with PMID as key
articles_dict = load_pubmed_file("pubmed_data.txt", "dict")
```

## Data Structures

### Article Information

Each article returned by the functions contains the following fields:

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
    "version": "baseline_2023"             # Baseline version (for baseline data)
}
```

## Error Handling

All functions in the PubMed module include comprehensive error handling:

- **Network errors**: Retry logic with exponential backoff
- **Rate limiting**: Automatic delays between requests
- **Invalid data**: Graceful handling of malformed responses
- **File errors**: Clear error messages for file operations

## Performance Considerations

- **Batch processing**: Use `fetch_pubmed_details_batch_sync` for multiple PMIDs
- **Caching**: Enable caching to avoid repeated requests
- **Rate limiting**: Respect NCBI's rate limits (0.34 seconds between requests)
- **Memory usage**: Process large datasets in chunks

## Examples

### Basic Search and Fetch

```python
from information_composer.pubmed.pubmed import query_pmid, fetch_pubmed_details_batch_sync

# Search for articles
pmids = query_pmid("cancer immunotherapy", "user@example.com", 50)

# Fetch detailed information
details = fetch_pubmed_details_batch_sync(pmids, "user@example.com")

# Process results
for article in details:
    print(f"PMID: {article['pmid']}")
    print(f"Title: {article['title']}")
    print(f"Journal: {article['journal']}")
    print(f"Authors: {', '.join(article['authors'])}")
    print("-" * 50)
```

### Date Range Search

```python
from information_composer.pubmed.pubmed import query_pmid_by_date

# Search for articles in specific date range
pmids = query_pmid_by_date(
    "COVID-19 vaccine",
    "user@example.com",
    "2020/01/01",
    "2023/12/31",
    3  # 3-month batches
)

print(f"Found {len(pmids)} COVID-19 vaccine articles")
```

### Load and Process Medline File

```python
from information_composer.pubmed.pubmed import load_pubmed_file
import pandas as pd

# Load Medline file
articles = load_pubmed_file("pubmed_baseline.txt", "list")

# Convert to DataFrame for analysis
df = pd.DataFrame(articles)

# Filter by journal
nature_articles = df[df['journal'].str.contains('Nature', case=False)]

# Filter by publication year
recent_articles = df[df['pubdate'].str.contains('2023')]

print(f"Nature articles: {len(nature_articles)}")
print(f"2023 articles: {len(recent_articles)}")
```

## Integration with Other Modules

The PubMed module integrates seamlessly with other Information Composer modules:

- **DOI Downloader**: Use PMIDs to download full-text articles
- **Markdown Processing**: Convert abstracts to markdown format
- **LLM Filtering**: Filter articles based on AI analysis
- **MCP Server**: Expose PubMed functionality via MCP protocol