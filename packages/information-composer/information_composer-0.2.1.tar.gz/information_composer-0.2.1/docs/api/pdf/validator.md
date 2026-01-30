# PDF Validator API

The PDF Validator module provides comprehensive PDF file validation functionality using the pypdfium2 library. This module includes data classes for validation results and a main validator class with extensive type annotations and error handling.

## Data Classes

### ValidationResult

Represents the validation result for a single PDF file.

```python
@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    file_size: Optional[int] = None
```

**Attributes:**
- `is_valid` (bool): Whether the PDF file is valid
- `error_message` (Optional[str]): Error message if validation failed
- `page_count` (Optional[int]): Number of pages in the PDF (if valid)
- `file_size` (Optional[int]): File size in bytes (if valid)

### ValidationStats

Aggregated statistics from PDF validation operations.

```python
@dataclass
class ValidationStats:
    total_files: int
    valid_files: int
    invalid_files: int
    success_rate: float
    error_details: List[Tuple[str, str]]
```

**Attributes:**
- `total_files` (int): Total number of files processed
- `valid_files` (int): Number of valid PDF files
- `invalid_files` (int): Number of invalid PDF files
- `success_rate` (float): Success rate as a percentage (0.0-100.0)
- `error_details` (List[Tuple[str, str]]): List of (file_path, error_message) tuples for invalid files

## Main Class

### PDFValidator

A comprehensive tool for validating PDF file formats using pypdfium2.

```python
class PDFValidator:
    def __init__(self, verbose: bool = False) -> None
```

**Parameters:**
- `verbose` (bool): If True, prints detailed validation messages for each file

#### Methods

##### validate_single_pdf

Validates a single PDF file.

```python
def validate_single_pdf(self, pdf_path: Union[str, Path]) -> ValidationResult
```

**Parameters:**
- `pdf_path` (Union[str, Path]): The path to the PDF file

**Returns:**
- `ValidationResult`: Object containing validation status, error message, page count, and file size

**Raises:**
- No exceptions are raised; errors are captured in the returned ValidationResult

**Example:**
```python
from information_composer.pdf.validator import PDFValidator

validator = PDFValidator(verbose=True)
result = validator.validate_single_pdf("document.pdf")

if result.is_valid:
    print(f"Valid PDF with {result.page_count} pages")
else:
    print(f"Invalid PDF: {result.error_message}")
```

##### validate_directory

Validates all PDF files within a specified directory.

```python
def validate_directory(
    self, 
    directory_path: Union[str, Path], 
    recursive: bool = False
) -> None
```

**Parameters:**
- `directory_path` (Union[str, Path]): The path to the directory
- `recursive` (bool): If True, recursively searches subdirectories

**Example:**
```python
# Validate all PDFs in a directory
validator.validate_directory("/path/to/pdfs")

# Recursively validate all PDFs in directory and subdirectories
validator.validate_directory("/path/to/pdfs", recursive=True)
```

##### validate_files

Validates a list of specified PDF files.

```python
def validate_files(self, file_paths: List[Union[str, Path]]) -> None
```

**Parameters:**
- `file_paths` (List[Union[str, Path]]): List of PDF file paths to validate

**Example:**
```python
files = ["file1.pdf", "file2.pdf", "file3.pdf"]
validator.validate_files(files)
```

##### get_validation_stats

Get validation statistics.

```python
def get_validation_stats(self) -> ValidationStats
```

**Returns:**
- `ValidationStats`: Object containing comprehensive validation statistics

**Example:**
```python
stats = validator.get_validation_stats()
print(f"Processed {stats.total_files} files")
print(f"Success rate: {stats.success_rate:.1f}%")
```

##### print_summary

Prints a summary of the validation results.

```python
def print_summary(self) -> None
```

**Example:**
```python
validator.print_summary()
# Output:
# ============================================================
# Validation Results Summary
# ============================================================
# Total files: 10
# Valid PDFs: 8
# Invalid PDFs: 2
# Success rate: 80.0%
```

##### reset_stats

Resets all validation statistics.

```python
def reset_stats(self) -> None
```

**Example:**
```python
validator.reset_stats()  # Reset counters and error details
```

## Usage Examples

### Basic Validation

```python
from information_composer.pdf.validator import PDFValidator

# Create validator
validator = PDFValidator(verbose=True)

# Validate a single file
result = validator.validate_single_pdf("document.pdf")
if result.is_valid:
    print(f"✓ Valid PDF: {result.page_count} pages, {result.file_size} bytes")
else:
    print(f"✗ Invalid PDF: {result.error_message}")
```

### Batch Validation

```python
# Validate multiple files
files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
validator.validate_files(files)

# Get statistics
stats = validator.get_validation_stats()
print(f"Processed {stats.total_files} files")
print(f"Success rate: {stats.success_rate:.1f}%")

# Print detailed summary
validator.print_summary()
```

### Directory Validation

```python
# Validate all PDFs in a directory
validator.validate_directory("/path/to/pdfs")

# Recursively validate all PDFs
validator.validate_directory("/path/to/pdfs", recursive=True)

# Check results
stats = validator.get_validation_stats()
if stats.invalid_files > 0:
    print("Invalid files found:")
    for file_path, error in stats.error_details:
        print(f"  {file_path}: {error}")
```

### Error Handling

```python
validator = PDFValidator()

# Validate a file that doesn't exist
result = validator.validate_single_pdf("nonexistent.pdf")
# result.is_valid will be False
# result.error_message will contain "File not found: nonexistent.pdf"

# Validate an empty file
result = validator.validate_single_pdf("empty.pdf")
# result.is_valid will be False
# result.error_message will contain "File is empty"

# Validate a corrupted PDF
result = validator.validate_single_pdf("corrupted.pdf")
# result.is_valid will be False
# result.error_message will contain "PDF format error: ..."
```

## Error Types

The validator handles several types of errors:

1. **File not found**: When the specified file doesn't exist
2. **Empty file**: When the file exists but has zero bytes
3. **PDF format error**: When the file exists but is not a valid PDF (PdfiumError)
4. **Unknown error**: Any other unexpected error during validation

All errors are captured in the ValidationResult object and don't raise exceptions, making the validator safe to use in batch operations.

## Performance Considerations

- The validator uses pypdfium2 for PDF processing, which is efficient for most PDF files
- Large PDF files may take longer to validate
- The verbose mode adds overhead due to print statements
- For batch operations, consider using the non-verbose mode for better performance

## Thread Safety

The PDFValidator class is not thread-safe. If you need to validate files concurrently, create separate validator instances for each thread.
