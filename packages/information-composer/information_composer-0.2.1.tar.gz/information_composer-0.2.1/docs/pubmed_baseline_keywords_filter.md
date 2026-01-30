# PubMed Keywords Filter

A tool for filtering PubMed XML data based on keywords and generating statistical analysis.

## Features

- Filter PubMed XML data using multiple keywords
- Search in both titles and abstracts
- Generate keyword occurrence statistics
- Export filtered results to CSV
- Clean text formatting for better readability
- Support for impact factor filtering
- Multiple output formats (DataFrame, dict, list)

## Installation

The tool is part of the information-composer package. Install it using pip:

```bash
pip install information-composer
```

## Code Structure

### Core Module (baseline.py)

The core functionality is implemented in `src/information_composer/pubmed/baseline.py`:

```python
def load_baseline(xmlfile: str, *args, **kwargs) -> Union[pd.DataFrame, dict, list]:
    """
    Load and filter PubMed baseline data from XML file.
    
    Args:
        xmlfile (str): Path to PubMed XML file
        **kwargs: Optional parameters
            - output_type (str): Output format ('pd', 'dict', 'list')
            - keywords (list): Keywords to filter by
            - kw_filter (str): Filter type ('abstract', 'title', 'both')
            - impact_factor (float): Minimum impact factor
            - log (bool): Enable logging
    
    Returns:
        Union[pd.DataFrame, dict, list]: Filtered data in specified format
    """
```

Helper functions:

```python
def _should_keep_entry(entry: dict, keywords: list, kw_filter: str, 
                      impact_factor: float, impact_factor_dict: dict) -> bool:
    """Determine if an entry should be kept based on filters"""

def _create_entry_dict(entry: dict, version: str) -> dict:
    """Create standardized entry dictionary"""

def keywords_filter(text: str, keywords: list) -> bool:
    """Check if text contains any keywords"""

def load_dict_from_pickle(filename):
    """Load dictionary from pickle file"""
```

### Example data download

```bash
   wget ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed24n1219.xml.gz
```

Then save it to the `data/pubmedbaseline/` directory.

### Example Script

The example implementation in `examples/pubmed_keywords_filter_example.py` shows how to use the module:

```python
def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    if pd.isna(text):
        return ""
    return " ".join(str(text).split())

def main():
    # Set up paths
    current_dir = Path(__file__).parent
    data_dir = (current_dir / ".." / "data" / "pubmedbaseline").resolve()
    xml_file = data_dir / "pubmed24n1219.xml.gz"
    
    # Define keywords
    keywords = [
        "promoter",
        "cis-regulatory",
        "cis-element",
        "enhancer",
        "silencer",
        "operator",
    ]
    
    # Load and process data
    df = load_baseline(
        str(xml_file),
        output_type='pd',
        keywords=keywords,
        kw_filter='both',
        log=True
    )
```

## Usage Examples

### Basic Filtering

```python
from information_composer.pubmed.baseline import load_baseline

# Simple keyword filtering
df = load_baseline(
    "pubmed24n1219.xml.gz",
    output_type='pd',
    keywords=["promoter", "enhancer"],
    kw_filter='both'
)
```

### With Impact Factor Filter

```python
# Filter with minimum impact factor
df = load_baseline(
    "pubmed24n1219.xml.gz",
    output_type='pd',
    keywords=["promoter"],
    impact_factor=2.5
)
```

### Different Output Formats

```python
# Get results as dictionary
results_dict = load_baseline(
    "pubmed24n1219.xml.gz",
    output_type='dict',
    keywords=["promoter"]
)

# Get results as list
results_list = load_baseline(
    "pubmed24n1219.xml.gz",
    output_type='list',
    keywords=["promoter"]
)
```

## Input/Output Specifications

### Input XML Format

The tool expects PubMed XML files in the standard MEDLINE format:

```xml
<PubmedArticle>
    <MedlineCitation>
        <PMID>...</PMID>
        <Article>
            <ArticleTitle>...</ArticleTitle>
            <Abstract>...</Abstract>
            ...
        </Article>
    </MedlineCitation>
</PubmedArticle>
```

### Output CSV Format

The filtered results CSV contains the following columns:

- pmid: PubMed ID (integer)
- title: Article title (string)
- abstract: Article abstract (string)
- journal: Journal name (string)
- pubdate: Publication date (string)
- publication_types: Type of publication (string)
- authors: Author list (string)
- doi: Digital Object Identifier (string)
- version: PubMed version (string)

## Error Handling

The module includes comprehensive error handling:

1. File Validation:

```python
if not isfile(xmlfile):
    raise FileNotFoundError(f"The specified file {xmlfile} does not exist.")
```

2. Parameter Validation:

```python
if output_type not in ['list', 'dict', 'pd']:
    raise ValueError('output_type must be "pd", "list" or "dict"')
```

3. XML Parsing Errors:

```python
try:
    path_xml = pp.parse_medline_xml(xmlfile)
except Exception as e:
    raise RuntimeError(f"Error parsing XML file {xmlfile}") from e
```

## Dependencies

Required packages:
- pandas >= 2.2.0
- pubmed-parser >= 0.5.0
- requests >= 2.28.0
- beautifulsoup4 >= 4.11.0
- habanero >= 1.2.0

## Project Structure

```
information-composer/
├── src/
│   └── information_composer/
│       └── pubmed/
│           └── baseline.py
├── data/
│   └── pubmedbaseline/
│       ├── pubmed24n1219.xml.gz
│       └── pubmed_filtered_results.csv
├── examples/
│   └── pubmed_keywords_filter_example.py
└── docs/
    └── pubmed_keywords_filter.md
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 