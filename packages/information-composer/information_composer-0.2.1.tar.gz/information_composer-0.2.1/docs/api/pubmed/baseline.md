# PubMed Baseline Module API

The PubMed baseline module provides functionality for loading and processing PubMed baseline data from XML files with filtering capabilities based on keywords and impact factors.

## Core Functions

### `load_baseline(xmlfile, output_type="list", **kwargs)`

Load and parse PubMed baseline data from XML file with filtering options.

**Parameters:**
- `xmlfile` (str): Path to the XML file
- `output_type` (str): Output format ('pd', 'dict', 'list')
- `keywords` (List[str], optional): List of keywords for filtering
- `kw_filter` (str, optional): Filter type ('abstract', 'title', 'both')
- `impact_factor` (float, optional): Minimum impact factor threshold
- `log` (bool, optional): Enable logging

**Returns:**
- `Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]`: Parsed data in specified format

**Raises:**
- `FileNotFoundError`: If the specified file doesn't exist
- `ValueError`: If output_type or kw_filter is invalid
- `RuntimeError`: If there's an error parsing the XML file

**Example:**
```python
from information_composer.pubmed.baseline import load_baseline

# Load all articles
articles = load_baseline("pubmed_baseline.xml", "list")

# Filter by keywords in abstract
cancer_articles = load_baseline(
    "pubmed_baseline.xml",
    "list",
    keywords=["cancer", "oncology"],
    kw_filter="abstract"
)

# Filter by high impact factor journals
high_impact = load_baseline(
    "pubmed_baseline.xml",
    "list",
    impact_factor=10.0
)
```

### `keywords_filter(text, keywords)`

Check if text contains any of the specified keywords.

**Parameters:**
- `text` (str): Text to check
- `keywords` (List[str]): List of keywords to search for

**Returns:**
- `bool`: True if any keyword is found, False otherwise

**Example:**
```python
from information_composer.pubmed.baseline import keywords_filter

text = "This article discusses cancer treatment and immunotherapy."
keywords = ["cancer", "immunotherapy"]

if keywords_filter(text, keywords):
    print("Article matches keywords")
```

### `load_dict_from_pickle(filename)`

Load a dictionary from a pickle file.

**Parameters:**
- `filename` (str): Path to the pickle file

**Returns:**
- `Dict[str, Any]`: Dictionary loaded from pickle file

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `pickle.PickleError`: If there's an error unpickling the file

**Example:**
```python
from information_composer.pubmed.baseline import load_dict_from_pickle

# Load impact factor data
impact_factors = load_dict_from_pickle("if2024.pickle")
print(f"Loaded {len(impact_factors)} journal impact factors")
```

## Filtering Options

### Keyword Filtering

The module supports three types of keyword filtering:

1. **Abstract filtering** (`kw_filter="abstract"`): Search keywords in article abstracts
2. **Title filtering** (`kw_filter="title"`): Search keywords in article titles
3. **Both filtering** (`kw_filter="both"`): Search keywords in both abstracts and titles

**Example:**
```python
# Filter by keywords in abstract only
abstract_matches = load_baseline(
    "data.xml",
    keywords=["machine learning", "deep learning"],
    kw_filter="abstract"
)

# Filter by keywords in title only
title_matches = load_baseline(
    "data.xml",
    keywords=["COVID-19", "SARS-CoV-2"],
    kw_filter="title"
)

# Filter by keywords in either abstract or title
any_matches = load_baseline(
    "data.xml",
    keywords=["cancer", "oncology", "tumor"],
    kw_filter="both"
)
```

### Impact Factor Filtering

Filter articles based on journal impact factors:

```python
# Load high impact factor articles only
high_impact = load_baseline(
    "data.xml",
    impact_factor=20.0  # Only journals with IF >= 20
)

# Load medium impact factor articles
medium_impact = load_baseline(
    "data.xml",
    impact_factor=5.0  # Only journals with IF >= 5
)
```

**Note:** Impact factor data must be provided as a pickle file containing a dictionary mapping journal names to impact factors.

## Output Formats

### List Format
Returns a list of article dictionaries:

```python
articles = load_baseline("data.xml", "list")
# Returns: [{"pmid": 12345678, "title": "...", ...}, ...]
```

### Dictionary Format
Returns a dictionary with PMID as key:

```python
articles = load_baseline("data.xml", "dict")
# Returns: {12345678: {"pmid": 12345678, "title": "...", ...}, ...}
```

### Pandas DataFrame Format
Returns a pandas DataFrame:

```python
df = load_baseline("data.xml", "pd")
# Returns: pandas.DataFrame with articles as rows
```

## Data Structure

Each article in the baseline data contains:

```python
{
    "pmid": 12345678,                      # PubMed ID (integer)
    "title": "Article Title",              # Article title
    "abstract": "Article abstract...",     # Article abstract
    "journal": "Journal Name",             # Journal name
    "pubdate": "2023 Jan",                 # Publication date
    "publication_types": ["Journal Article"], # Publication types
    "authors": ["Smith J", "Doe A"],       # Author list
    "doi": "10.1234/example.doi",          # DOI
    "version": "baseline_2023"             # Baseline version
}
```

## Performance Considerations

- **Large files**: Process large XML files in chunks to manage memory usage
- **Filtering**: Apply filters early to reduce memory consumption
- **Caching**: Use pickle files for frequently accessed data like impact factors
- **Logging**: Enable logging for monitoring processing progress

## Examples

### Basic Usage

```python
from information_composer.pubmed.baseline import load_baseline

# Load all articles
articles = load_baseline("pubmed_baseline.xml")
print(f"Loaded {len(articles)} articles")

# Convert to DataFrame for analysis
import pandas as pd
df = pd.DataFrame(articles)
print(f"Articles by journal:\n{df['journal'].value_counts().head()}")
```

### Advanced Filtering

```python
# Complex filtering: cancer articles in high-impact journals
cancer_high_impact = load_baseline(
    "pubmed_baseline.xml",
    "list",
    keywords=["cancer", "oncology", "tumor", "carcinoma"],
    kw_filter="both",
    impact_factor=10.0,
    log=True
)

print(f"Found {len(cancer_high_impact)} high-impact cancer articles")
```

### Batch Processing

```python
import os
from pathlib import Path

# Process multiple baseline files
baseline_dir = Path("baseline_data")
results = []

for xml_file in baseline_dir.glob("*.xml"):
    print(f"Processing {xml_file.name}...")
    
    articles = load_baseline(
        str(xml_file),
        "list",
        keywords=["COVID-19", "pandemic"],
        kw_filter="both"
    )
    
    results.extend(articles)
    print(f"  Found {len(articles)} COVID-19 articles")

print(f"Total COVID-19 articles: {len(results)}")
```

### Impact Factor Analysis

```python
# Load impact factor data
impact_factors = load_dict_from_pickle("if2024.pickle")

# Load articles
articles = load_baseline("data.xml", "list")

# Analyze journal impact factors
journal_ifs = []
for article in articles:
    journal = article['journal'].rstrip().lower()
    if journal in impact_factors:
        journal_ifs.append(impact_factors[journal])

if journal_ifs:
    print(f"Average impact factor: {sum(journal_ifs) / len(journal_ifs):.2f}")
    print(f"Highest impact factor: {max(journal_ifs):.2f}")
    print(f"Lowest impact factor: {min(journal_ifs):.2f}")
```

## Error Handling

The module includes comprehensive error handling:

- **File not found**: Clear error messages for missing files
- **Invalid parameters**: Validation of output_type and kw_filter parameters
- **XML parsing errors**: Graceful handling of malformed XML files
- **Pickle errors**: Proper error handling for corrupted pickle files

## Integration

The baseline module integrates with other Information Composer modules:

- **PubMed module**: Use baseline data with other PubMed functions
- **DOI Downloader**: Download full-text articles for baseline articles
- **LLM Filtering**: Apply AI-based filtering to baseline data
- **MCP Server**: Expose baseline functionality via MCP protocol