# Markdown Processing Guide

This guide explains how to use the `information_composer.markdown` module for converting between markdown text and structured data formats.

## Overview

The markdown module provides a comprehensive set of tools for:
- Converting markdown text to structured dictionaries
- Converting structured data back to markdown
- Processing CommonMark AST (Abstract Syntax Tree) structures
- Rendering markdown elements to various formats

## Quick Start

### Basic Conversion

```python
from information_composer.markdown import dictify, jsonify, markdownify

# Your markdown content
markdown_text = """# Project Title
This is a sample project with multiple sections.

## Features
- Feature 1
- Feature 2
- Feature 3

## Code Example
```python
def hello_world():
    print("Hello, World!")
```
"""

# Convert to dictionary
data = dictify(markdown_text)
print("Dictionary representation:")
print(data)

# Convert to JSON
json_str = jsonify(markdown_text)
print("\nJSON representation:")
print(json_str)

# Convert back to markdown
converted = markdownify(data)
print("\nConverted back to markdown:")
print(converted)
```

## Core Functions

### 1. Converting Markdown to Dictionary

The `dictify()` function converts markdown text into a nested dictionary structure:

```python
from information_composer.markdown import dictify

markdown_text = """# Main Title
This is the main content.

## Subtitle
Some subtitle content.

### Sub-subtitle
More detailed content.
"""

result = dictify(markdown_text)
# Result will be a nested OrderedDict structure
```

**Key Features:**
- Preserves the hierarchical structure of headers
- Maintains order of elements
- Handles various markdown elements (headers, lists, code blocks, etc.)

### 2. Converting to JSON

The `jsonify()` function provides a JSON representation:

```python
from information_composer.markdown import jsonify

markdown_text = "# Title\nSome content"
json_str = jsonify(markdown_text)
# Returns: '{"Title": "Some content"}'
```

### 3. Converting Back to Markdown

The `markdownify()` function converts structured data back to markdown:

```python
from information_composer.markdown import markdownify

# From dictionary
data = {
    "root": {
        "title": "Main Title",
        "content": "Main content",
        "sections": {
            "intro": "Introduction text",
            "body": "Body text"
        }
    }
}
markdown_text = markdownify(data)

# From JSON string
json_str = '{"Title": "Some content"}'
markdown_text = markdownify(json_str)
```

## Advanced Usage

### Working with AST Structures

For more control over the parsing process, you can work directly with the CommonMark AST:

```python
from information_composer.markdown import CMarkASTNester, Renderer
from information_composer.markdown.vendor import CommonMark

# Parse markdown to AST
parser = CommonMark.DocParser()
ast = parser.parse(markdown_text)

# Process AST
nester = CMarkASTNester()
structured_data = nester.nest(ast)

# Render to different formats
renderer = Renderer()
string_dict = renderer.stringify_dict(structured_data)
```

### Custom Block Processing

You can process specific types of blocks using the `dictify_list_by()` function:

```python
from information_composer.markdown import dictify_list_by

# Example: Group content by headers
def is_header(block):
    return hasattr(block, 't') and block.t == "ATXHeader"

blocks = [block1, block2, block3]  # Your blocks
grouped = dictify_list_by(blocks, is_header)
```

## Error Handling

The module provides comprehensive error handling:

```python
from information_composer.markdown import ContentError

try:
    result = dictify(markdown_text)
except ContentError as e:
    print(f"Markdown processing error: {e}")
    if e.details:
        print(f"Additional details: {e.details}")
```

## Supported Markdown Elements

The module supports most CommonMark elements:

### Headers
```markdown
# H1 Header
## H2 Header
### H3 Header
```

### Lists
```markdown
- Unordered list item 1
- Unordered list item 2

1. Ordered list item 1
2. Ordered list item 2
```

### Code Blocks
```markdown
```python
def example():
    return "Hello, World!"
```
```

### Emphasis
```markdown
**Bold text**
*Italic text*
```

### Links and Images
```markdown
[Link text](https://example.com)
![Alt text](image.png)
```

## Best Practices

### 1. Input Validation

Always validate your input before processing:

```python
def safe_dictify(markdown_text: str) -> dict:
    if not isinstance(markdown_text, str):
        raise ValueError("Input must be a string")
    
    if not markdown_text.strip():
        return {"root": ""}
    
    return dictify(markdown_text)
```

### 2. Error Handling

Implement proper error handling for production use:

```python
def process_markdown_safely(markdown_text: str) -> dict:
    try:
        return dictify(markdown_text)
    except ContentError as e:
        logger.error(f"Markdown processing failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": "Processing failed"}
```

### 3. Performance Considerations

For large documents, consider processing in chunks:

```python
def process_large_markdown(markdown_text: str, chunk_size: int = 1000) -> list:
    lines = markdown_text.split('\n')
    chunks = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
    
    results = []
    for chunk in chunks:
        chunk_text = '\n'.join(chunk)
        result = dictify(chunk_text)
        results.append(result)
    
    return results
```

## Integration Examples

### With Web Frameworks

```python
from flask import Flask, request, jsonify
from information_composer.markdown import dictify, markdownify

app = Flask(__name__)

@app.route('/api/markdown/parse', methods=['POST'])
def parse_markdown():
    data = request.get_json()
    markdown_text = data.get('markdown', '')
    
    try:
        result = dictify(markdown_text)
        return jsonify({"success": True, "data": result})
    except ContentError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/markdown/render', methods=['POST'])
def render_markdown():
    data = request.get_json()
    structured_data = data.get('data', {})
    
    try:
        markdown_text = markdownify(structured_data)
        return jsonify({"success": True, "markdown": markdown_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
```

### With Data Processing Pipelines

```python
import pandas as pd
from information_composer.markdown import dictify

def process_documentation_files(file_paths: list) -> pd.DataFrame:
    results = []
    
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        try:
            structured_data = dictify(markdown_text)
            results.append({
                'file_path': file_path,
                'title': structured_data.get('root', {}).get('title', ''),
                'sections': list(structured_data.get('root', {}).keys()),
                'success': True
            })
        except Exception as e:
            results.append({
                'file_path': file_path,
                'title': '',
                'sections': [],
                'success': False,
                'error': str(e)
            })
    
    return pd.DataFrame(results)
```

## Troubleshooting

### Common Issues

1. **Empty or Invalid Markdown**
   ```python
   # Check for empty input
   if not markdown_text.strip():
       return {"root": ""}
   ```

2. **Encoding Issues**
   ```python
   # Ensure proper encoding
   with open(file_path, 'r', encoding='utf-8') as f:
       markdown_text = f.read()
   ```

3. **Large File Processing**
   ```python
   # Process in chunks for large files
   chunk_size = 1000
   for i in range(0, len(lines), chunk_size):
       chunk = lines[i:i+chunk_size]
       process_chunk(chunk)
   ```

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('information_composer.markdown')

# Your markdown processing code
```

## API Reference

For detailed API documentation, see [Markdown Module API](../api/markdown/markdown.md).

## Examples

Check the `examples/` directory for complete working examples:

- `markdown_converter.py` - Basic conversion examples
- `markdown_filter_ref.py` - Advanced filtering and processing
- `llm_filter_example.py` - Integration with LLM filtering

## Contributing

When contributing to the markdown module:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for any API changes
4. Ensure all tests pass before submitting
5. Consider performance implications for large documents
