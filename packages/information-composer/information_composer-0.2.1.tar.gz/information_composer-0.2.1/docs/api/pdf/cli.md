# PDF Validator CLI

The PDF Validator CLI provides a command-line interface for validating PDF files using the PDFValidator class. It supports various output formats and validation modes.

## Command Line Interface

### Basic Usage

```bash
python -m information_composer.pdf.cli.main [files...] [options]
```

### Arguments

**Positional Arguments:**
- `files` (optional): PDF file paths to validate

**Options:**
- `-d DIRECTORY, --directory DIRECTORY`: Directory path to validate
- `-r, --recursive`: Recursively search subdirectories for PDF files
- `-v, --verbose`: Show detailed output information
- `--json`: Output results in JSON format
- `--stats-only`: Show only statistics, not detailed errors
- `-h, --help`: Show help message and exit

### Usage Examples

#### Validate Specific Files

```bash
# Validate single file
python -m information_composer.pdf.cli.main document.pdf

# Validate multiple files
python -m information_composer.pdf.cli.main file1.pdf file2.pdf file3.pdf
```

#### Validate Directory

```bash
# Validate all PDFs in directory
python -m information_composer.pdf.cli.main -d /path/to/pdfs

# Recursively validate all PDFs in directory and subdirectories
python -m information_composer.pdf.cli.main -d /path/to/pdfs -r
```

#### Verbose Output

```bash
# Show detailed validation messages
python -m information_composer.pdf.cli.main -v document.pdf
```

#### JSON Output

```bash
# Output results in JSON format
python -m information_composer.pdf.cli.main --json document.pdf
```

#### Statistics Only

```bash
# Show only summary statistics
python -m information_composer.pdf.cli.main --stats-only document.pdf
```

## Output Formats

### Standard Output

Default output shows validation progress and a summary:

```
Starting validation of 1 PDF files...
------------------------------------------------------------
✓ document.pdf: Valid PDF file with 5 pages

============================================================
Validation Results Summary
============================================================
Total files: 1
Valid PDFs: 1
Invalid PDFs: 0
Success rate: 100.0%
```

### Verbose Output

With `-v` flag, shows detailed information for each file:

```
Starting validation of 2 PDF files...
------------------------------------------------------------
✓ valid.pdf: Valid PDF file with 3 pages
✗ invalid.pdf: PDF format error: Failed to load document

============================================================
Validation Results Summary
============================================================
Total files: 2
Valid PDFs: 1
Invalid PDFs: 1
Success rate: 50.0%

Invalid files details:
----------------------------------------
File: invalid.pdf
Error: PDF format error: Failed to load document
```

### JSON Output

With `--json` flag, outputs structured JSON data:

```json
{
  "total_files": 2,
  "valid_files": 1,
  "invalid_files": 1,
  "success_rate": 50.0,
  "error_details": [
    ["invalid.pdf", "PDF format error: Failed to load document"]
  ]
}
```

### Statistics Only

With `--stats-only` flag, shows only summary statistics:

```
Total files: 2
Valid PDFs: 1
Invalid PDFs: 1
Success rate: 50.0%
```

## Exit Codes

The CLI returns the following exit codes:

- `0`: Success (validation completed)
- `1`: Error (argument error, validation failed, or exception occurred)

## Error Handling

### Argument Errors

```bash
# No files or directory specified
python -m information_composer.pdf.cli.main
# Output: Argument error: No files or directory specified
# Exit code: 1
```

### File Not Found

```bash
# File doesn't exist
python -m information_composer.pdf.cli.main nonexistent.pdf
# Output: Validation completed with errors
# Exit code: 0 (validation completed, but file was invalid)
```

### Directory Errors

```bash
# Directory doesn't exist
python -m information_composer.pdf.cli.main -d /nonexistent/directory
# Output: Error: Directory does not exist - /nonexistent/directory
# Exit code: 0
```

### Keyboard Interrupt

```bash
# User interrupts validation (Ctrl+C)
python -m information_composer.pdf.cli.main large_directory/
# Output: Validation interrupted by user
# Exit code: 1
```

## Integration Examples

### Shell Scripts

```bash
#!/bin/bash
# Validate all PDFs in a directory and check results

python -m information_composer.pdf.cli.main -d /path/to/pdfs --json > results.json

# Check if validation was successful
if [ $? -eq 0 ]; then
    echo "Validation completed successfully"
    
    # Extract success rate using jq
    success_rate=$(jq '.success_rate' results.json)
    echo "Success rate: ${success_rate}%"
    
    # Check if there are any invalid files
    invalid_count=$(jq '.invalid_files' results.json)
    if [ "$invalid_count" -gt 0 ]; then
        echo "Warning: $invalid_count invalid files found"
        jq -r '.error_details[] | "\(.[0]): \(.[1])"' results.json
    fi
else
    echo "Validation failed"
    exit 1
fi
```

### Python Integration

```python
import subprocess
import json

def validate_pdfs_cli(files):
    """Validate PDFs using CLI and return results."""
    cmd = [
        "python", "-m", "information_composer.pdf.cli.main",
        "--json"
    ] + files
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"CLI error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None

# Usage
files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = validate_pdfs_cli(files)

if results:
    print(f"Processed {results['total_files']} files")
    print(f"Success rate: {results['success_rate']:.1f}%")
```

### Batch Processing

```bash
#!/bin/bash
# Process multiple directories and generate reports

directories=("/path/to/pdfs1" "/path/to/pdfs2" "/path/to/pdfs3")
report_file="validation_report.txt"

echo "PDF Validation Report - $(date)" > "$report_file"
echo "=================================" >> "$report_file"

for dir in "${directories[@]}"; do
    echo "" >> "$report_file"
    echo "Directory: $dir" >> "$report_file"
    echo "----------------------------------------" >> "$report_file"
    
    python -m information_composer.pdf.cli.main -d "$dir" --stats-only >> "$report_file"
done

echo "Report saved to: $report_file"
```

## Performance Tips

1. **Use non-verbose mode for batch operations**: Remove `-v` flag for better performance
2. **Use `--stats-only` for automated scripts**: Reduces output overhead
3. **Use JSON output for programmatic processing**: Easier to parse and process
4. **Consider file size**: Large PDF files take longer to validate
5. **Use recursive search carefully**: Can process many files quickly

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure you have read access to the files/directories
2. **File locked**: Close any applications that might have the PDF files open
3. **Memory issues**: For very large PDF files, consider processing in smaller batches
4. **Unicode errors**: Ensure file paths don't contain invalid characters

### Debug Mode

For debugging, you can modify the CLI to add more verbose output or use Python's logging module to capture detailed information about the validation process.

## API Reference

The CLI is built on top of the PDFValidator class. For detailed API documentation, see the [PDF Validator API](validator.md) documentation.
