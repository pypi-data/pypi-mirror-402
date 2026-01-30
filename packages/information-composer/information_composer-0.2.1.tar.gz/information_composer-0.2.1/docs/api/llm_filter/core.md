# LLM Filter Core API

The core module provides the main filtering and processing functionality for the LLM Filter system, including content filtering, batch processing, and result management.

## Core Classes

### `MarkdownFilter` Class

Main class for filtering markdown content using LLM.

```python
class MarkdownFilter:
    def __init__(self, config: AppConfig) -> None
    def filter_content(self, content: str, custom_prompt: Optional[str] = None) -> str
    def filter_file(self, file_path: Union[str, Path]) -> FilterResult
    def filter_files(self, input_dir: str, output_dir: str, file_pattern: str = "*.md") -> List[FilterResult]
    def get_filter_statistics(self, original_content: str, filtered_content: str) -> FilterStats
```

#### Constructor

##### `__init__(config: AppConfig) -> None`

Initialize the MarkdownFilter with configuration.

**Parameters:**
- `config` (AppConfig): Application configuration

**Example:**
```python
from information_composer.llm_filter.core.filter import MarkdownFilter
from information_composer.llm_filter.config.settings import AppConfig

config = AppConfig()
filter_processor = MarkdownFilter(config)
```

#### Methods

##### `filter_content(content: str, custom_prompt: Optional[str] = None) -> str`

Filter markdown content using LLM.

**Parameters:**
- `content` (str): Input markdown content
- `custom_prompt` (Optional[str]): Custom filtering prompt

**Returns:**
- `str`: Filtered content

**Example:**
```python
content = """
# Research Paper

This is a research paper about machine learning.
It contains important findings and methodology.

## Introduction

Machine learning is a subset of artificial intelligence...
"""

filtered = filter_processor.filter_content(content)
print(filtered)
```

##### `filter_file(file_path: Union[str, Path]) -> FilterResult`

Filter a single markdown file.

**Parameters:**
- `file_path` (Union[str, Path]): Path to the markdown file

**Returns:**
- `FilterResult`: Result of the filtering operation

**Example:**
```python
from pathlib import Path

result = filter_processor.filter_file("document.md")
if result.success:
    print(f"Filtered content: {result.filtered_content}")
else:
    print(f"Error: {result.error_message}")
```

##### `filter_files(input_dir: str, output_dir: str, file_pattern: str = "*.md") -> List[FilterResult]`

Filter multiple markdown files in a directory.

**Parameters:**
- `input_dir` (str): Input directory path
- `output_dir` (str): Output directory path
- `file_pattern` (str): File pattern to match

**Returns:**
- `List[FilterResult]`: List of filtering results

**Example:**
```python
results = filter_processor.filter_files(
    input_dir="./input",
    output_dir="./output",
    file_pattern="*.md"
)

successful = [r for r in results if r.success]
print(f"Successfully filtered {len(successful)} files")
```

### `ContentExtractor` Class

Extract structured data from content using LLM.

```python
class ContentExtractor:
    def __init__(self, config: AppConfig) -> None
    def extract_section(self, content: str, section_name: str) -> str
    def extract_structured_data(self, content: str, schema: Dict[str, Any]) -> Dict[str, Any]
    def extract_keywords(self, content: str, top_k: int = 10) -> List[str]
    def summarize_content(self, content: str, max_length: int = 200) -> str
```

#### Methods

##### `extract_section(content: str, section_name: str) -> str`

Extract a specific section from content.

**Parameters:**
- `content` (str): Input content
- `section_name` (str): Name of the section to extract

**Returns:**
- `str`: Extracted section content

**Example:**
```python
extractor = ContentExtractor(config)

# Extract abstract
abstract = extractor.extract_section(content, "abstract")

# Extract methodology
methodology = extractor.extract_section(content, "methodology")
```

##### `extract_structured_data(content: str, schema: Dict[str, Any]) -> Dict[str, Any]`

Extract structured data using a JSON schema.

**Parameters:**
- `content` (str): Input content
- `schema` (Dict[str, Any]): JSON schema for extraction

**Returns:**
- `Dict[str, Any]`: Extracted structured data

**Example:**
```python
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "abstract": {"type": "string"}
    }
}

data = extractor.extract_structured_data(content, schema)
print(f"Title: {data['title']}")
print(f"Authors: {data['authors']}")
```

## Data Classes

### `FilterResult` Dataclass

Result of a filtering operation.

```python
@dataclass
class FilterResult:
    file_path: str
    success: bool
    original_content: str
    filtered_content: str
    processing_time: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

**Attributes:**
- `file_path` (str): Path to the processed file
- `success` (bool): Whether the operation was successful
- `original_content` (str): Original content before filtering
- `filtered_content` (str): Content after filtering
- `processing_time` (float): Time taken to process in seconds
- `error_message` (Optional[str]): Error message if failed
- `metadata` (Optional[Dict[str, Any]]): Additional metadata

### `FilterStats` Dataclass

Statistics about filtering operations.

```python
@dataclass
class FilterStats:
    original_length: int
    filtered_length: int
    compression_ratio: float
    processing_time: float
    word_count_original: int
    word_count_filtered: int
    sections_removed: int
    sections_kept: int
```

**Attributes:**
- `original_length` (int): Length of original content
- `filtered_length` (int): Length of filtered content
- `compression_ratio` (float): Compression ratio (0.0-1.0)
- `processing_time` (float): Total processing time
- `word_count_original` (int): Word count in original content
- `word_count_filtered` (int): Word count in filtered content
- `sections_removed` (int): Number of sections removed
- `sections_kept` (int): Number of sections kept

## Utility Functions

### Text Processing

```python
def extract_keywords(content: str, top_k: int = 10) -> List[str]
def calculate_readability_score(content: str) -> float
def summarize_text(content: str, max_length: int = 200) -> str
def clean_markdown(content: str) -> str
```

#### `extract_keywords(content: str, top_k: int = 10) -> List[str]`

Extract keywords from content.

**Parameters:**
- `content` (str): Input content
- `top_k` (int): Number of top keywords to return

**Returns:**
- `List[str]`: List of keywords

**Example:**
```python
from information_composer.llm_filter.utils.text_processing import extract_keywords

keywords = extract_keywords(content, top_k=10)
print(f"Keywords: {keywords}")
```

#### `calculate_readability_score(content: str) -> float`

Calculate readability score of content.

**Parameters:**
- `content` (str): Input content

**Returns:**
- `float`: Readability score (0.0-100.0)

**Example:**
```python
from information_composer.llm_filter.utils.text_processing import calculate_readability_score

score = calculate_readability_score(content)
print(f"Readability score: {score}")
```

### Markdown Processing

```python
def extract_headings(content: str) -> List[Dict[str, Any]]
def extract_links(content: str) -> List[Dict[str, str]]
def extract_tables(content: str) -> List[Dict[str, Any]]
def clean_markdown(content: str) -> str
```

#### `extract_headings(content: str) -> List[Dict[str, Any]]`

Extract headings from markdown content.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `List[Dict[str, Any]]`: List of heading information

**Example:**
```python
from information_composer.llm_filter.utils.markdown_utils import extract_headings

headings = extract_headings(content)
for heading in headings:
    print(f"Level {heading['level']}: {heading['text']}")
```

## Usage Examples

### Basic Content Filtering

```python
from information_composer.llm_filter.core.filter import MarkdownFilter
from information_composer.llm_filter.config.settings import AppConfig

# Setup configuration
config = AppConfig()
config.llm.api_key = "your-api-key"

# Initialize filter
filter_processor = MarkdownFilter(config)

# Filter content
content = """
# Research Paper

This is a research paper about machine learning.
It contains important findings and methodology.

## Introduction

Machine learning is a subset of artificial intelligence...
"""

filtered_content = filter_processor.filter_content(content)
print(filtered_content)
```

### Batch File Processing

```python
from pathlib import Path

# Process multiple files
results = filter_processor.filter_files(
    input_dir="./input_documents",
    output_dir="./filtered_documents",
    file_pattern="*.md"
)

# Process results
for result in results:
    if result.success:
        print(f"✓ {result.file_path}: {result.processing_time:.2f}s")
    else:
        print(f"✗ {result.file_path}: {result.error_message}")
```

### Structured Data Extraction

```python
from information_composer.llm_filter.core.extractor import ContentExtractor

extractor = ContentExtractor(config)

# Define extraction schema
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "abstract": {"type": "string"},
        "publication_date": {"type": "string"}
    }
}

# Extract structured data
data = extractor.extract_structured_data(content, schema)
print(f"Title: {data['title']}")
print(f"Authors: {', '.join(data['authors'])}")
```

### Custom Filtering

```python
# Custom filtering prompt
custom_prompt = """
Please filter this academic paper to keep only:
1. Abstract and introduction
2. Methodology section
3. Key findings and results
4. Conclusion

Remove:
- References and citations
- Acknowledgments
- Appendices
- Non-essential details
"""

filtered_content = filter_processor.filter_content(
    content, 
    custom_prompt=custom_prompt
)
```

### Error Handling

```python
try:
    result = filter_processor.filter_file("document.md")
    if result.success:
        print("Filtering successful")
    else:
        print(f"Filtering failed: {result.error_message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Optimization

### Batch Processing

```python
# Process files in batches for better performance
batch_size = 10
files = list(Path("input").glob("*.md"))

for i in range(0, len(files), batch_size):
    batch = files[i:i + batch_size]
    
    for file_path in batch:
        try:
            result = filter_processor.filter_file(file_path)
            print(f"Processed: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Add delay between batches
    time.sleep(1)
```

### Caching

```python
# Enable caching for repeated operations
config.llm.enable_cache = True
config.llm.cache_dir = "./cache"
config.llm.cache_ttl_hours = 24

filter_processor = MarkdownFilter(config)
```

## Best Practices

1. **Use Appropriate Prompts**: Design clear, specific filtering prompts
2. **Handle Errors**: Implement proper error handling for all operations
3. **Monitor Performance**: Track processing times and resource usage
4. **Validate Results**: Check filtered content quality
5. **Use Caching**: Enable caching for repeated operations
6. **Batch Processing**: Process multiple files efficiently
7. **Resource Management**: Monitor memory and API usage
