# LLM Filtering Guide

This guide explains how to use the LLM Filter module for intelligent content filtering and processing using Large Language Models.

## Overview

The LLM Filter module provides comprehensive functionality for:
- Intelligent content filtering using LLMs
- Markdown document processing and analysis
- Text extraction and structured data processing
- Batch processing capabilities
- Multiple LLM provider support (DashScope, etc.)
- Configuration management and validation

## Installation

The LLM Filter module is part of the Information Composer package. Install it with:

```bash
pip install information-composer
```

### Optional Dependencies

For full functionality, install optional dependencies:

```bash
# For DashScope integration
pip install llama-index-llms-dashscope

# For additional text processing
pip install nltk spacy
```

## Basic Usage

### Simple Content Filtering

```python
from information_composer.llm_filter.core.filter import MarkdownFilter
from information_composer.llm_filter.config.settings import AppConfig

# Create configuration
config = AppConfig()
config.dashscope.api_key = "your-dashscope-api-key"

# Initialize filter
filter_processor = MarkdownFilter(config)

# Filter content
input_text = """
# Research Paper

This is a research paper about machine learning.
It contains important findings and methodology.

## Introduction

Machine learning is a subset of artificial intelligence...
"""

filtered_content = filter_processor.filter_content(input_text)
print(filtered_content)
```

### Batch File Processing

```python
from pathlib import Path

# Process multiple files
input_dir = Path("input_documents")
output_dir = Path("filtered_documents")

# Filter all markdown files
output_files = filter_processor.filter_files(
    input_dir=str(input_dir),
    output_dir=str(output_dir),
    file_pattern="*.md"
)

print(f"Processed {len(output_files)} files")
```

## Configuration

### Basic Configuration

```python
from information_composer.llm_filter.config.settings import AppConfig

# Create configuration
config = AppConfig()

# Set DashScope API key
config.dashscope.api_key = "your-api-key"
config.dashscope.model = "qwen-plus"
config.dashscope.temperature = 0.1
config.dashscope.max_tokens = 4096

# Set processing options
config.processing.input_dir = "/path/to/input"
config.processing.output_dir = "/path/to/output"
config.processing.file_pattern = "*.md"
config.processing.recursive = True
config.processing.output_format = "markdown"
config.processing.overwrite = False
config.processing.backup = True

# Set logging
config.log_level = "INFO"
config.debug = False
```

### Environment Variables

You can also configure using environment variables:

```bash
export DASHSCOPE_API_KEY="your-api-key"
export DASHSCOPE_MODEL="qwen-plus"
export LOG_LEVEL="DEBUG"
export INPUT_DIR="/path/to/input"
export OUTPUT_DIR="/path/to/output"
```

### Configuration from File

```python
from information_composer.llm_filter.config.settings import ConfigManager

# Load configuration from file
config_manager = ConfigManager()
config_manager.load_config("config.json")
config = config_manager.get_config()
```

## Advanced Usage

### Custom Filtering Rules

```python
from information_composer.llm_filter.core.filter import MarkdownFilter

# Create custom filter with specific rules
filter_processor = MarkdownFilter(config)

# Set custom filtering prompt
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

# Apply custom filtering
filtered_content = filter_processor.filter_content(
    input_text,
    custom_prompt=custom_prompt
)
```

### Structured Data Extraction

```python
from information_composer.llm_filter.core.extractor import ContentExtractor

# Initialize extractor
extractor = ContentExtractor(config)

# Extract specific sections
abstract = extractor.extract_section(input_text, "abstract")
methodology = extractor.extract_section(input_text, "methodology")
results = extractor.extract_section(input_text, "results")

# Extract structured data
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

structured_data = extractor.extract_structured_data(input_text, schema)
```

### Text Analysis and Processing

```python
from information_composer.llm_filter.utils.text_processing import (
    extract_keywords,
    calculate_readability_score,
    summarize_text
)

# Extract keywords
keywords = extract_keywords(input_text, top_k=10)
print(f"Keywords: {keywords}")

# Calculate readability
readability = calculate_readability_score(input_text)
print(f"Readability score: {readability}")

# Summarize text
summary = summarize_text(input_text, max_length=200)
print(f"Summary: {summary}")
```

### Markdown Processing

```python
from information_composer.llm_filter.utils.markdown_utils import (
    extract_headings,
    extract_links,
    extract_tables,
    clean_markdown
)

# Extract document structure
headings = extract_headings(input_text)
links = extract_links(input_text)
tables = extract_tables(input_text)

print(f"Found {len(headings)} headings")
print(f"Found {len(links)} links")
print(f"Found {len(tables)} tables")

# Clean markdown
cleaned_text = clean_markdown(input_text)
```

## CLI Usage

### Basic Command

```bash
# Filter a single file
md-llm-filter input.md -o output.md

# Filter multiple files
md-llm-filter input_dir/ -o output_dir/

# Use specific model
md-llm-filter input.md -o output.md --model qwen-plus

# Set custom temperature
md-llm-filter input.md -o output.md --temperature 0.1
```

### Advanced Options

```bash
# Recursive processing
md-llm-filter input_dir/ -o output_dir/ --recursive

# Specific file pattern
md-llm-filter input_dir/ -o output_dir/ --pattern "*.txt"

# Overwrite existing files
md-llm-filter input_dir/ -o output_dir/ --overwrite

# Enable backup
md-llm-filter input_dir/ -o output_dir/ --backup

# Debug mode
md-llm-filter input_dir/ -o output_dir/ --debug

# Verbose output
md-llm-filter input_dir/ -o output_dir/ --verbose
```

### Configuration File

```bash
# Use configuration file
md-llm-filter input_dir/ -o output_dir/ --config config.json

# Save current configuration
md-llm-filter --save-config config.json
```

## Error Handling

### Common Issues and Solutions

1. **API Key Not Set**
   ```python
   # Check configuration
   if not config.dashscope.api_key:
       raise ValueError("DashScope API key not configured")
   ```

2. **Rate Limiting**
   ```python
   # Add retry logic
   import time
   
   try:
       result = filter_processor.filter_content(text)
   except Exception as e:
       if "rate limit" in str(e).lower():
           time.sleep(5)  # Wait before retry
           result = filter_processor.filter_content(text)
   ```

3. **Invalid Input**
   ```python
   # Validate input
   if not input_text or len(input_text.strip()) == 0:
       raise ValueError("Input text cannot be empty")
   ```

### Debugging

Enable debug mode for detailed logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or use configuration
config.debug = True
config.log_level = "DEBUG"
```

## Performance Optimization

### Batch Processing

```python
# Process files in batches
batch_size = 10
files = list(input_dir.glob("*.md"))

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
config.cache_enabled = True
config.cache_dir = "./cache"
config.cache_ttl_hours = 24
```

### Memory Management

```python
# Process large files in chunks
def process_large_file(file_path, chunk_size=1000):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    
    results = []
    for chunk in chunks:
        result = filter_processor.filter_content(chunk)
        results.append(result)
    
    return '\n'.join(results)
```

## Best Practices

### 1. Configuration Management

```python
# Use environment variables for sensitive data
import os

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("DASHSCOPE_API_KEY environment variable not set")

config.dashscope.api_key = api_key
```

### 2. Error Handling

```python
def safe_filter_content(text, max_retries=3):
    for attempt in range(max_retries):
        try:
            return filter_processor.filter_content(text)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Resource Management

```python
# Use context managers when available
with filter_processor as fp:
    result = fp.filter_content(text)
```

### 4. Monitoring and Logging

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log processing progress
logger.info(f"Processing file: {file_path}")
result = filter_processor.filter_content(text)
logger.info(f"Completed processing: {file_path}")
```

## Example Scripts

### Complete Processing Pipeline

```python
#!/usr/bin/env python3
"""
Complete LLM Filtering Pipeline
"""

import os
import logging
from pathlib import Path
from information_composer.llm_filter.core.filter import MarkdownFilter
from information_composer.llm_filter.config.settings import AppConfig

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Configuration
    config = AppConfig()
    config.dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    config.processing.input_dir = "input_documents"
    config.processing.output_dir = "filtered_documents"
    config.processing.recursive = True
    config.processing.backup = True
    
    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration")
        return
    
    # Initialize filter
    filter_processor = MarkdownFilter(config)
    
    try:
        # Process files
        logger.info("Starting file processing...")
        output_files = filter_processor.filter_files(
            input_dir=config.processing.input_dir,
            output_dir=config.processing.output_dir,
            file_pattern="*.md"
        )
        
        logger.info(f"Successfully processed {len(output_files)} files")
        
        # Print statistics
        stats = filter_processor.get_filter_statistics(
            "original content", "filtered content"
        )
        logger.info(f"Filter statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

### Custom Filtering Application

```python
#!/usr/bin/env python3
"""
Custom Academic Paper Filter
"""

from information_composer.llm_filter.core.filter import MarkdownFilter
from information_composer.llm_filter.config.settings import AppConfig

def filter_academic_paper(text):
    """Filter academic paper to keep only essential content."""
    
    # Custom filtering prompt
    prompt = """
    Please filter this academic paper to extract only the core content:
    
    Keep:
    - Title and abstract
    - Introduction and background
    - Methodology and approach
    - Key findings and results
    - Main conclusions
    
    Remove:
    - References and citations
    - Acknowledgments
    - Appendices
    - Detailed data tables
    - Author affiliations
    - Funding information
    """
    
    config = AppConfig()
    config.dashscope.api_key = "your-api-key"
    config.dashscope.temperature = 0.1  # Low temperature for consistency
    
    filter_processor = MarkdownFilter(config)
    
    return filter_processor.filter_content(text, custom_prompt=prompt)

# Usage
if __name__ == "__main__":
    with open("paper.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    filtered = filter_academic_paper(content)
    
    with open("filtered_paper.md", "w", encoding="utf-8") as f:
        f.write(filtered)
    
    print("Paper filtered successfully!")
```

This guide provides comprehensive information for using the LLM Filter module effectively. The module is designed to be flexible and powerful while remaining easy to use for common filtering tasks.
