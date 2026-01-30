# LLM Filter Utilities API

The utilities module provides helper functions and classes for text processing, markdown manipulation, and other common operations used throughout the LLM Filter system.

## Text Processing Utilities

### `extract_keywords(content: str, top_k: int = 10) -> List[str]`

Extract keywords from text content using various algorithms.

**Parameters:**
- `content` (str): Input text content
- `top_k` (int): Number of top keywords to return

**Returns:**
- `List[str]`: List of extracted keywords

**Example:**
```python
from information_composer.llm_filter.utils.text_processing import extract_keywords

content = "Machine learning is a subset of artificial intelligence..."
keywords = extract_keywords(content, top_k=5)
print(keywords)  # ['machine learning', 'artificial intelligence', ...]
```

### `calculate_readability_score(content: str) -> float`

Calculate the readability score of text content using various metrics.

**Parameters:**
- `content` (str): Input text content

**Returns:**
- `float`: Readability score (0.0-100.0, higher is more readable)

**Example:**
```python
from information_composer.llm_filter.utils.text_processing import calculate_readability_score

content = "This is a simple sentence with basic words."
score = calculate_readability_score(content)
print(f"Readability score: {score}")
```

### `summarize_text(content: str, max_length: int = 200) -> str`

Generate a summary of text content.

**Parameters:**
- `content` (str): Input text content
- `max_length` (int): Maximum length of summary

**Returns:**
- `str`: Generated summary

**Example:**
```python
from information_composer.llm_filter.utils.text_processing import summarize_text

content = "Long article content here..."
summary = summarize_text(content, max_length=150)
print(summary)
```

### `clean_text(content: str) -> str`

Clean and normalize text content.

**Parameters:**
- `content` (str): Input text content

**Returns:**
- `str`: Cleaned text content

**Example:**
```python
from information_composer.llm_filter.utils.text_processing import clean_text

content = "  This   has   extra   spaces  \n\n"
cleaned = clean_text(content)
print(cleaned)  # "This has extra spaces"
```

## Markdown Processing Utilities

### `extract_headings(content: str) -> List[Dict[str, Any]]`

Extract all headings from markdown content.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `List[Dict[str, Any]]`: List of heading information

**Example:**
```python
from information_composer.llm_filter.utils.markdown_utils import extract_headings

content = """
# Main Title
## Section 1
### Subsection 1.1
## Section 2
"""

headings = extract_headings(content)
for heading in headings:
    print(f"Level {heading['level']}: {heading['text']}")
```

**Return Format:**
```python
[
    {"level": 1, "text": "Main Title", "line": 1},
    {"level": 2, "text": "Section 1", "line": 2},
    {"level": 3, "text": "Subsection 1.1", "line": 3},
    {"level": 2, "text": "Section 2", "line": 4}
]
```

### `extract_links(content: str) -> List[Dict[str, str]]`

Extract all links from markdown content.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `List[Dict[str, str]]`: List of link information

**Example:**
```python
from information_composer.llm_filter.utils.markdown_utils import extract_links

content = """
[Google](https://google.com)
[GitHub](https://github.com "GitHub Homepage")
"""

links = extract_links(content)
for link in links:
    print(f"Text: {link['text']}, URL: {link['url']}")
```

**Return Format:**
```python
[
    {"text": "Google", "url": "https://google.com", "title": ""},
    {"text": "GitHub", "url": "https://github.com", "title": "GitHub Homepage"}
]
```

### `extract_tables(content: str) -> List[Dict[str, Any]]`

Extract all tables from markdown content.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `List[Dict[str, Any]]`: List of table information

**Example:**
```python
from information_composer.llm_filter.utils.markdown_utils import extract_tables

content = """
| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |
"""

tables = extract_tables(content)
for table in tables:
    print(f"Headers: {table['headers']}")
    print(f"Rows: {table['rows']}")
```

**Return Format:**
```python
[
    {
        "headers": ["Name", "Age", "City"],
        "rows": [["John", "25", "NYC"], ["Jane", "30", "LA"]],
        "line": 1
    }
]
```

### `clean_markdown(content: str) -> str`

Clean and normalize markdown content.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `str`: Cleaned markdown content

**Example:**
```python
from information_composer.llm_filter.utils.markdown_utils import clean_markdown

content = """
#   Title with extra spaces   

Some content here...

##   Another heading   
"""

cleaned = clean_markdown(content)
print(cleaned)
```

## File Processing Utilities

### `FileProcessor` Class

Utility class for file operations.

```python
class FileProcessor:
    def __init__(self, config: ProcessingConfig) -> None
    def find_files(self, directory: str, pattern: str = "*.md", recursive: bool = True) -> List[Path]
    def read_file(self, file_path: Union[str, Path]) -> str
    def write_file(self, file_path: Union[str, Path], content: str) -> bool
    def backup_file(self, file_path: Union[str, Path]) -> Optional[Path]
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]
```

#### Methods

##### `find_files(directory: str, pattern: str = "*.md", recursive: bool = True) -> List[Path]`

Find files matching a pattern in a directory.

**Parameters:**
- `directory` (str): Directory to search
- `pattern` (str): File pattern to match
- `recursive` (bool): Whether to search subdirectories

**Returns:**
- `List[Path]`: List of matching file paths

**Example:**
```python
from information_composer.llm_filter.utils.file_utils import FileProcessor

processor = FileProcessor(config)
files = processor.find_files("./documents", "*.md", recursive=True)
print(f"Found {len(files)} markdown files")
```

##### `read_file(file_path: Union[str, Path]) -> str`

Read content from a file.

**Parameters:**
- `file_path` (Union[str, Path]): Path to the file

**Returns:**
- `str`: File content

**Example:**
```python
content = processor.read_file("document.md")
print(f"File size: {len(content)} characters")
```

##### `write_file(file_path: Union[str, Path], content: str) -> bool`

Write content to a file.

**Parameters:**
- `file_path` (Union[str, Path]): Path to write to
- `content` (str): Content to write

**Returns:**
- `bool`: Whether the write was successful

**Example:**
```python
success = processor.write_file("output.md", filtered_content)
if success:
    print("File written successfully")
```

## Validation Utilities

### `ContentValidator` Class

Validate content and files.

```python
class ContentValidator:
    def __init__(self, config: ProcessingConfig) -> None
    def validate_file_size(self, file_path: Union[str, Path]) -> bool
    def validate_file_format(self, file_path: Union[str, Path]) -> bool
    def validate_content(self, content: str) -> Tuple[bool, List[str]]
    def validate_markdown(self, content: str) -> Tuple[bool, List[str]]
```

#### Methods

##### `validate_file_size(file_path: Union[str, Path]) -> bool`

Validate if file size is within limits.

**Parameters:**
- `file_path` (Union[str, Path]): Path to the file

**Returns:**
- `bool`: Whether file size is valid

**Example:**
```python
from information_composer.llm_filter.utils.validation import ContentValidator

validator = ContentValidator(config)
is_valid = validator.validate_file_size("large_file.md")
if not is_valid:
    print("File too large")
```

##### `validate_content(content: str) -> Tuple[bool, List[str]]`

Validate content for basic requirements.

**Parameters:**
- `content` (str): Content to validate

**Returns:**
- `Tuple[bool, List[str]]`: (is_valid, error_messages)

**Example:**
```python
is_valid, errors = validator.validate_content(content)
if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")
```

## Statistics Utilities

### `StatisticsCalculator` Class

Calculate various statistics about content.

```python
class StatisticsCalculator:
    def __init__(self) -> None
    def calculate_text_stats(self, content: str) -> Dict[str, Any]
    def calculate_markdown_stats(self, content: str) -> Dict[str, Any]
    def compare_content(self, original: str, filtered: str) -> Dict[str, Any]
```

#### Methods

##### `calculate_text_stats(content: str) -> Dict[str, Any]`

Calculate text statistics.

**Parameters:**
- `content` (str): Text content

**Returns:**
- `Dict[str, Any]`: Text statistics

**Example:**
```python
from information_composer.llm_filter.utils.statistics import StatisticsCalculator

calculator = StatisticsCalculator()
stats = calculator.calculate_text_stats(content)
print(f"Word count: {stats['word_count']}")
print(f"Character count: {stats['char_count']}")
print(f"Line count: {stats['line_count']}")
```

**Return Format:**
```python
{
    "word_count": 150,
    "char_count": 800,
    "line_count": 20,
    "sentence_count": 10,
    "paragraph_count": 5,
    "avg_words_per_sentence": 15.0,
    "avg_chars_per_word": 5.3
}
```

##### `compare_content(original: str, filtered: str) -> Dict[str, Any]`

Compare original and filtered content.

**Parameters:**
- `original` (str): Original content
- `filtered` (str): Filtered content

**Returns:**
- `Dict[str, Any]`: Comparison statistics

**Example:**
```python
comparison = calculator.compare_content(original_content, filtered_content)
print(f"Compression ratio: {comparison['compression_ratio']:.2f}")
print(f"Words removed: {comparison['words_removed']}")
```

## Error Handling Utilities

### `ErrorHandler` Class

Handle and format errors consistently.

```python
class ErrorHandler:
    def __init__(self, log_level: str = "INFO") -> None
    def handle_file_error(self, file_path: str, error: Exception) -> str
    def handle_processing_error(self, operation: str, error: Exception) -> str
    def format_error_message(self, error: Exception) -> str
    def log_error(self, message: str, error: Exception) -> None
```

#### Methods

##### `handle_file_error(file_path: str, error: Exception) -> str`

Handle file-related errors.

**Parameters:**
- `file_path` (str): Path to the file
- `error` (Exception): Error that occurred

**Returns:**
- `str`: Formatted error message

**Example:**
```python
from information_composer.llm_filter.utils.error_handling import ErrorHandler

error_handler = ErrorHandler()
try:
    content = processor.read_file("nonexistent.md")
except FileNotFoundError as e:
    message = error_handler.handle_file_error("nonexistent.md", e)
    print(message)  # "File not found: nonexistent.md"
```

## Usage Examples

### Complete Text Processing Pipeline

```python
from information_composer.llm_filter.utils.text_processing import (
    extract_keywords, calculate_readability_score, summarize_text
)
from information_composer.llm_filter.utils.markdown_utils import (
    extract_headings, extract_links, clean_markdown
)

def process_document(content: str) -> Dict[str, Any]:
    """Process a document and extract various information."""
    
    # Clean content
    cleaned = clean_markdown(content)
    
    # Extract information
    keywords = extract_keywords(cleaned, top_k=10)
    headings = extract_headings(cleaned)
    links = extract_links(cleaned)
    readability = calculate_readability_score(cleaned)
    summary = summarize_text(cleaned, max_length=200)
    
    return {
        "keywords": keywords,
        "headings": headings,
        "links": links,
        "readability_score": readability,
        "summary": summary,
        "original_length": len(content),
        "cleaned_length": len(cleaned)
    }

# Usage
content = """
# Research Paper

This is a research paper about machine learning...

## Introduction

Machine learning is a subset of artificial intelligence...
"""

result = process_document(content)
print(f"Keywords: {result['keywords']}")
print(f"Readability: {result['readability_score']}")
```

### File Processing with Validation

```python
from information_composer.llm_filter.utils.file_utils import FileProcessor
from information_composer.llm_filter.utils.validation import ContentValidator

def process_files_safely(input_dir: str, output_dir: str):
    """Process files with validation and error handling."""
    
    processor = FileProcessor(config)
    validator = ContentValidator(config)
    
    # Find files
    files = processor.find_files(input_dir, "*.md")
    
    for file_path in files:
        try:
            # Validate file
            if not validator.validate_file_size(file_path):
                print(f"Skipping {file_path}: File too large")
                continue
            
            # Read and validate content
            content = processor.read_file(file_path)
            is_valid, errors = validator.validate_content(content)
            
            if not is_valid:
                print(f"Skipping {file_path}: {errors}")
                continue
            
            # Process content (your filtering logic here)
            processed_content = process_content(content)
            
            # Write output
            output_path = Path(output_dir) / file_path.name
            processor.write_file(output_path, processed_content)
            
            print(f"Processed: {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
```

## Best Practices

1. **Use Appropriate Utilities**: Choose the right utility for your task
2. **Handle Errors**: Always handle potential errors from utility functions
3. **Validate Input**: Validate input before processing
4. **Monitor Performance**: Track performance of utility operations
5. **Cache Results**: Cache expensive operations when possible
6. **Document Usage**: Document how utilities are used in your code
