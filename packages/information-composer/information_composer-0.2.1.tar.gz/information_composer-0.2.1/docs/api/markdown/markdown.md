# Markdown Module API

The `information_composer.markdown` module provides utilities for converting between markdown text and structured data formats, enabling programmatic manipulation of markdown content.

## Functions

### `dictify(markdown_str: str) -> OrderedDict[str, Any]`

Convert a markdown string into a nested Python dictionary.

**Parameters:**
- `markdown_str` (str): The markdown text to convert

**Returns:**
- `OrderedDict[str, Any]`: A nested dictionary representation of the markdown content

**Example:**
```python
from information_composer.markdown import dictify

markdown_text = """# Main Title
This is a paragraph.

## Subtitle
- List item 1
- List item 2
"""

result = dictify(markdown_text)
# Returns: OrderedDict with structured representation
```

### `jsonify(markdown_str: str) -> str`

Convert a markdown string into a JSON string representation.

**Parameters:**
- `markdown_str` (str): The markdown text to convert

**Returns:**
- `str`: JSON string representation of the markdown content

**Example:**
```python
from information_composer.markdown import jsonify

markdown_text = "# Title\nSome content"
json_str = jsonify(markdown_text)
# Returns: '{"Title": "Some content"}'
```

### `markdownify(data: Union[Dict[str, Any], str]) -> str`

Convert a dictionary or JSON string back into markdown format.

**Parameters:**
- `data` (Union[Dict[str, Any], str]): Dictionary or JSON string to convert

**Returns:**
- `str`: Markdown formatted string

**Example:**
```python
from information_composer.markdown import markdownify

data = {"Title": "Some content"}
markdown_text = markdownify(data)
# Returns: "# Title\n\nSome content"
```

### `dictify_list_by(list_of_blocks: List[Any], filter_function: Callable[[Any], bool]) -> Dict[Any, List[Any]]`

Turn list of tokens into dictionary of lists of tokens based on a filter function.

**Parameters:**
- `list_of_blocks` (List[Any]): List of blocks to process
- `filter_function` (Callable[[Any], bool]): Function to determine grouping criteria

**Returns:**
- `Dict[Any, List[Any]]`: Dictionary mapping filtered items to their associated content

**Raises:**
- `ValueError`: If filter_function is None

**Example:**
```python
from information_composer.markdown import dictify_list_by

blocks = [block1, block2, block3]
result = dictify_list_by(blocks, lambda x: x.type == "header")
# Groups blocks by header type
```

## Classes

### `CMarkASTNester`

Processes CommonMark AST (Abstract Syntax Tree) into nested dictionary structures.

#### Methods

##### `nest(ast: Any) -> Any`

Nest an AST into a structured format.

**Parameters:**
- `ast` (Any): The AST to process

**Returns:**
- `Any`: Nested structure representation

##### `_dictify_blocks(blocks: List[Any], heading_level: int) -> Any`

Convert blocks into dictionary format based on heading level.

**Parameters:**
- `blocks` (List[Any]): List of blocks to process
- `heading_level` (int): Current heading level

**Returns:**
- `Any`: Dictionary representation of blocks

##### `_ensure_list_singleton(blocks: List[Any]) -> None`

Ensure list blocks are properly formatted as singletons.

**Parameters:**
- `blocks` (List[Any]): List of blocks to process

### `Renderer`

Processes DOM (Document Object Model) into string representations.

#### Methods

##### `stringify_dict(dictionary: Any) -> OrderedDict[str, Any]`

Create dictionary of keys and values as strings.

**Parameters:**
- `dictionary` (Any): Dictionary or list to convert to string representation

**Returns:**
- `OrderedDict[str, Any]`: OrderedDict with string keys and processed values

##### `_valuify(cm_vals: Any) -> Any`

Render values of dictionary as scalars or lists.

**Parameters:**
- `cm_vals` (Any): Values to render

**Returns:**
- `Any`: Rendered values as strings or lists

##### `_render_block(block: Any) -> Any`

Render any block based on its type.

**Parameters:**
- `block` (Any): The block to render

**Returns:**
- `Any`: String or list representation of the block

##### `_render_generic_block(block: Any) -> Any`

Render any block using generic logic.

**Parameters:**
- `block` (Any): The block to render

**Returns:**
- `Any`: Generic string representation

##### `_render_List(block: Any) -> Any`

Render list blocks.

**Parameters:**
- `block` (Any): The list block to render

**Returns:**
- `Any`: List of rendered list items

##### `_render_FencedCode(block: Any) -> str`

Render fenced code blocks.

**Parameters:**
- `block` (Any): The fenced code block to render

**Returns:**
- `str`: String representation of the code block with markdown formatting

### `ContentError`

Exception raised for content-related errors in markdown processing.

**Inherits from:** `ValueError`

#### Constructor

##### `__init__(message: str, details: Optional[Dict[str, Any]] = None) -> None`

Initialize ContentError with message and optional details.

**Parameters:**
- `message` (str): Error message
- `details` (Optional[Dict[str, Any]]): Optional additional details about the error

## Usage Examples

### Basic Markdown Processing

```python
from information_composer.markdown import dictify, jsonify, markdownify

# Convert markdown to dictionary
markdown_text = """# Main Title
This is a paragraph with **bold** text.

## Subtitle
- List item 1
- List item 2
"""

# Convert to structured data
data = dictify(markdown_text)
print(data)

# Convert to JSON
json_str = jsonify(markdown_text)
print(json_str)

# Convert back to markdown
converted = markdownify(data)
print(converted)
```

### Advanced Block Processing

```python
from information_composer.markdown import CMarkASTNester, Renderer

# Process AST
nester = CMarkASTNester()
ast = parse_markdown(markdown_text)
result = nester.nest(ast)

# Render to string
renderer = Renderer()
output = renderer.stringify_dict(result)
```

### Error Handling

```python
from information_composer.markdown import ContentError

try:
    result = dictify(invalid_markdown)
except ContentError as e:
    print(f"Error: {e}")
    if e.details:
        print(f"Details: {e.details}")
```

## Notes

- The module uses CommonMark for markdown parsing
- All functions are designed to be stateless and thread-safe
- The `OrderedDict` is used to maintain the order of elements as they appear in the markdown
- Vendor code (CommonMark) is excluded from type checking and quality checks
