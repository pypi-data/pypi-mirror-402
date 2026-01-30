# Markdown Converter

A Python module for converting between Markdown, Python dictionaries, and JSON formats using the CommonMark specification.

## Overview

The Markdown Converter is built on top of CommonMark-py (version 0.5.4) and provides a simple interface for:

- Converting Markdown to nested Python dictionaries
- Converting Markdown to JSON
- Converting JSON back to Markdown

## Installation

The module is part of the information-composer package.

## Usage

### Converting Markdown to Dictionary

Use the `dictify()` function to convert a Markdown string into a nested Python dictionary:

  ```python
  from information_composer.markdown import dictify
  
  markdown_str = """
  # Title
  Some content
  ## Section
  More content
  """
  
  dict_output = dictify(markdown_str)
  ```

### Converting Markdown to JSON

Use the `jsonify()` function to convert a Markdown string directly to JSON:

  ```python
  from information_composer.markdown import jsonify
  
  json_output = jsonify(markdown_str)
  ```

### Converting JSON back to Markdown

Use the `markdownfy()` function to convert JSON back to Markdown format:

  ```python
  from information_composer.markdown import markdownfy
  
  markdown_output = markdownfy(json_output)
  ```

## Structure

The converter maintains the hierarchical structure of the Markdown document based on heading levels. The resulting dictionary/JSON will nest content under its respective headers.

## Error Handling

- Empty JSON strings return empty strings
- Invalid JSON strings raise ValueError
- Content mixing errors raise ContentError

## Limitations

- Currently supports CommonMark specification features
- Headers are used as dictionary keys
- Nested content follows header hierarchy
