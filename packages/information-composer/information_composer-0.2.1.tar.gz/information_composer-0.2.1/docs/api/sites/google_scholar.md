# Google Scholar Models API

## SearchStrategy

Enumeration for search strategies.

```python
class SearchStrategy(Enum):
    REQUESTS = "requests"
    SELENIUM = "selenium"
    SCHOLARLY = "scholarly"
```

## SearchConfig

Configuration for Google Scholar search.

### Constructor

```python
SearchConfig(
    max_results: int = 100,
    year_range: Optional[Tuple[int, int]] = None,
    language: str = "en",
    include_citations: bool = True,
    include_abstracts: bool = True,
    include_patents: bool = False,
    sort_by: str = "relevance",
    rate_limit: float = 2.0,
    max_retries: int = 3,
    timeout: float = 30.0,
    search_strategy: SearchStrategy = SearchStrategy.REQUESTS,
    use_selenium_fallback: bool = True,
    cache_dir: Optional[str] = None,
    cache_ttl_days: int = 30,
    user_agent_rotation: bool = True,
    session_persistence: bool = True,
    resolve_dois: bool = True,
    link_pubmed: bool = True,
    fetch_abstracts: bool = True
) -> None
```

### Parameters

**Basic Search Parameters:**
- `max_results` (int): Maximum number of results to return (default: 100)
- `year_range` (Optional[Tuple[int, int]]): Year range for filtering results
- `language` (str): Language for search results (default: "en")

**Search Behavior:**
- `include_citations` (bool): Include citation counts (default: True)
- `include_abstracts` (bool): Include abstracts (default: True)
- `include_patents` (bool): Include patents (default: False)
- `sort_by` (str): Sort order - "relevance" or "date" (default: "relevance")

**Rate Limiting and Performance:**
- `rate_limit` (float): Seconds between requests (default: 2.0)
- `max_retries` (int): Maximum retry attempts (default: 3)
- `timeout` (float): Request timeout in seconds (default: 30.0)

**Strategy Selection:**
- `search_strategy` (SearchStrategy): Search strategy to use (default: REQUESTS)
- `use_selenium_fallback` (bool): Fallback to requests if selenium unavailable (default: True)

**Caching:**
- `cache_dir` (Optional[str]): Directory for caching results
- `cache_ttl_days` (int): Cache time-to-live in days (default: 30)

**Data Enhancement:**
- `resolve_dois` (bool): Resolve DOI information (default: True)
- `link_pubmed` (bool): Link to PubMed (default: True)
- `fetch_abstracts` (bool): Fetch full abstracts (default: True)

### Methods

#### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Convert configuration to dictionary for serialization.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the configuration

#### from_dict()

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> SearchConfig
```

Create instance from dictionary.

**Parameters:**
- `data` (Dict[str, Any]): Dictionary containing configuration data

**Returns:**
- `SearchConfig`: SearchConfig instance

## GoogleScholarPaper

Data model for a Google Scholar paper.

### Constructor

```python
GoogleScholarPaper(
    google_scholar_id: str,
    title: str,
    authors: List[str] = field(default_factory=list),
    author_affiliations: List[str] = field(default_factory=list),
    journal: Optional[str] = None,
    conference: Optional[str] = None,
    year: Optional[int] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    pages: Optional[str] = None,
    publisher: Optional[str] = None,
    abstract: Optional[str] = None,
    pdf_url: Optional[str] = None,
    doi: Optional[str] = None,
    pubmed_id: Optional[str] = None,
    arxiv_id: Optional[str] = None,
    isbn: Optional[str] = None,
    citation_count: int = 0,
    search_rank: int = 0,
    confidence_score: float = 0.0,
    google_scholar_url: Optional[str] = None,
    source_url: Optional[str] = None,
    language: str = "en",
    search_query: str = "",
    extracted_date: datetime = field(default_factory=datetime.now),
    publication_date: Optional[datetime] = None,
    keywords: List[str] = field(default_factory=list),
    abstract_snippet: Optional[str] = None,
    venue_type: Optional[str] = None,
    open_access: Optional[bool] = None
) -> None
```

### Methods

#### is_valid()

```python
def is_valid(self) -> bool
```

Check if the paper has minimum required information.

**Returns:**
- `bool`: True if paper has required information, False otherwise

#### get_primary_author()

```python
def get_primary_author(self) -> Optional[str]
```

Get the first author if available.

**Returns:**
- `Optional[str]`: First author name or None

#### get_citation_display()

```python
def get_citation_display(self) -> str
```

Get formatted citation for display.

**Returns:**
- `str`: Formatted citation string

#### update_confidence_score()

```python
def update_confidence_score(self) -> None
```

Calculate and update confidence score based on available data.

#### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Convert to dictionary for JSON serialization.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the paper

#### from_dict()

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> GoogleScholarPaper
```

Create instance from dictionary.

**Parameters:**
- `data` (Dict[str, Any]): Dictionary containing paper data

**Returns:**
- `GoogleScholarPaper`: GoogleScholarPaper instance

## SearchResult

Container for search results with metadata.

### Constructor

```python
SearchResult(
    papers: List[GoogleScholarPaper] = field(default_factory=list),
    query: str = "",
    total_results: int = 0,
    search_time: float = 0.0,
    strategy_used: SearchStrategy = SearchStrategy.REQUESTS,
    cached: bool = False,
    search_config: Optional[SearchConfig] = None,
    valid_papers: int = 0,
    papers_with_doi: int = 0,
    papers_with_abstract: int = 0
) -> None
```

### Methods

#### update_statistics()

```python
def update_statistics(self) -> None
```

Update result statistics.

#### get_top_papers()

```python
def get_top_papers(self, n: int = 10) -> List[GoogleScholarPaper]
```

Get top N papers by search rank.

**Parameters:**
- `n` (int): Number of top papers to return

**Returns:**
- `List[GoogleScholarPaper]`: List of top N papers

#### filter_by_year()

```python
def filter_by_year(self, start_year: int, end_year: int) -> SearchResult
```

Filter papers by year range.

**Parameters:**
- `start_year` (int): Start year for filtering
- `end_year` (int): End year for filtering

**Returns:**
- `SearchResult`: New SearchResult with filtered papers

#### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Convert to dictionary for serialization.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the search results

### Example Usage

```python
from information_composer.sites.google_scholar.models import (
    SearchConfig,
    GoogleScholarPaper,
    SearchResult,
    SearchStrategy
)

# Create search configuration
config = SearchConfig(
    max_results=50,
    year_range=(2020, 2023),
    search_strategy=SearchStrategy.REQUESTS,
    include_abstracts=True,
    resolve_dois=True
)

# Create a paper
paper = GoogleScholarPaper(
    google_scholar_id="123456",
    title="Machine Learning in Bioinformatics",
    authors=["John Doe", "Jane Smith"],
    journal="Nature Methods",
    year=2023,
    doi="10.1038/s41592-023-01234-5",
    citation_count=25
)

# Update confidence score
paper.update_confidence_score()

# Create search result
result = SearchResult(
    papers=[paper],
    query="machine learning bioinformatics",
    total_results=1,
    search_time=2.5,
    search_config=config
)

# Update statistics
result.update_statistics()

# Get top papers
top_papers = result.get_top_papers(5)

# Filter by year
recent_papers = result.filter_by_year(2022, 2023)

# Convert to dictionary
result_dict = result.to_dict()
```


