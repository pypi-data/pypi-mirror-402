# PDF Validator Guide

The PDF Validator is a comprehensive tool for validating PDF file formats and integrity. This guide covers installation, basic usage, advanced features, and best practices.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-username/information-composer.git
cd information-composer

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install pypdfium2
```

### Verify Installation

```bash
# Test the CLI
python -m information_composer.pdf.cli.main --help

# Test the Python API
python -c "from information_composer.pdf.validator import PDFValidator; print('Installation successful')"
```

## Quick Start

### Command Line Usage

```bash
# Validate a single PDF file
python -m information_composer.pdf.cli.main document.pdf

# Validate all PDFs in a directory
python -m information_composer.pdf.cli.main -d /path/to/pdfs

# Get detailed output
python -m information_composer.pdf.cli.main -v document.pdf
```

### Python API Usage

```python
from information_composer.pdf.validator import PDFValidator

# Create validator
validator = PDFValidator(verbose=True)

# Validate a single file
result = validator.validate_single_pdf("document.pdf")
if result.is_valid:
    print(f"✓ Valid PDF: {result.page_count} pages")
else:
    print(f"✗ Invalid PDF: {result.error_message}")
```

## Basic Usage

### Single File Validation

#### Command Line

```bash
# Basic validation
python -m information_composer.pdf.cli.main document.pdf

# With verbose output
python -m information_composer.pdf.cli.main -v document.pdf

# JSON output for scripting
python -m information_composer.pdf.cli.main --json document.pdf
```

#### Python API

```python
from information_composer.pdf.validator import PDFValidator

validator = PDFValidator()

# Validate single file
result = validator.validate_single_pdf("document.pdf")

# Check result
if result.is_valid:
    print(f"Valid PDF with {result.page_count} pages")
    print(f"File size: {result.file_size} bytes")
else:
    print(f"Invalid PDF: {result.error_message}")
```

### Multiple File Validation

#### Command Line

```bash
# Validate multiple files
python -m information_composer.pdf.cli.main file1.pdf file2.pdf file3.pdf

# With statistics only
python -m information_composer.pdf.cli.main --stats-only file1.pdf file2.pdf
```

#### Python API

```python
# Validate multiple files
files = ["file1.pdf", "file2.pdf", "file3.pdf"]
validator.validate_files(files)

# Get statistics
stats = validator.get_validation_stats()
print(f"Processed {stats.total_files} files")
print(f"Success rate: {stats.success_rate:.1f}%")
```

### Directory Validation

#### Command Line

```bash
# Validate all PDFs in directory
python -m information_composer.pdf.cli.main -d /path/to/pdfs

# Recursively validate all PDFs
python -m information_composer.pdf.cli.main -d /path/to/pdfs -r

# With verbose output
python -m information_composer.pdf.cli.main -d /path/to/pdfs -v
```

#### Python API

```python
# Validate directory
validator.validate_directory("/path/to/pdfs")

# Recursively validate
validator.validate_directory("/path/to/pdfs", recursive=True)

# Print summary
validator.print_summary()
```

## Advanced Features

### Batch Processing

#### Process Large Directories

```python
from pathlib import Path
from information_composer.pdf.validator import PDFValidator

def process_large_directory(directory_path, batch_size=100):
    """Process large directories in batches."""
    directory = Path(directory_path)
    pdf_files = list(directory.rglob("*.pdf"))
    
    validator = PDFValidator(verbose=False)
    
    # Process in batches
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} files)")
        
        validator.validate_files([str(f) for f in batch])
        
        # Print intermediate results
        stats = validator.get_validation_stats()
        print(f"  Processed: {stats.total_files}, Valid: {stats.valid_files}, Invalid: {stats.invalid_files}")
    
    return validator.get_validation_stats()

# Usage
stats = process_large_directory("/path/to/large/pdf/collection")
print(f"Final results: {stats.success_rate:.1f}% success rate")
```

#### Parallel Processing

```python
import concurrent.futures
from information_composer.pdf.validator import PDFValidator

def validate_file_parallel(file_path):
    """Validate a single file in parallel."""
    validator = PDFValidator(verbose=False)
    return validator.validate_single_pdf(file_path)

def parallel_validation(file_paths, max_workers=4):
    """Validate files in parallel."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(validate_file_parallel, file_paths))
    
    # Count results
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count
    
    return {
        "total_files": len(results),
        "valid_files": valid_count,
        "invalid_files": invalid_count,
        "success_rate": (valid_count / len(results)) * 100 if results else 0
    }

# Usage
files = ["file1.pdf", "file2.pdf", "file3.pdf"]
results = parallel_validation(files)
print(f"Parallel validation: {results['success_rate']:.1f}% success rate")
```

### Custom Error Handling

```python
from information_composer.pdf.validator import PDFValidator, ValidationResult

class CustomPDFValidator(PDFValidator):
    """Custom validator with enhanced error handling."""
    
    def validate_single_pdf(self, pdf_path):
        """Override with custom error handling."""
        result = super().validate_single_pdf(pdf_path)
        
        if not result.is_valid:
            # Log detailed error information
            self.log_error(pdf_path, result.error_message)
            
            # Categorize errors
            if "File not found" in result.error_message:
                self.handle_file_not_found(pdf_path)
            elif "File is empty" in result.error_message:
                self.handle_empty_file(pdf_path)
            elif "PDF format error" in result.error_message:
                self.handle_format_error(pdf_path, result.error_message)
        
        return result
    
    def log_error(self, file_path, error_message):
        """Log error details."""
        print(f"ERROR: {file_path} - {error_message}")
    
    def handle_file_not_found(self, file_path):
        """Handle file not found errors."""
        print(f"WARNING: File not found: {file_path}")
    
    def handle_empty_file(self, file_path):
        """Handle empty file errors."""
        print(f"WARNING: Empty file: {file_path}")
    
    def handle_format_error(self, file_path, error_message):
        """Handle PDF format errors."""
        print(f"ERROR: Corrupted PDF: {file_path} - {error_message}")

# Usage
validator = CustomPDFValidator(verbose=True)
validator.validate_files(["file1.pdf", "file2.pdf", "file3.pdf"])
```

### Integration with Other Tools

#### File System Monitoring

```python
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from information_composer.pdf.validator import PDFValidator

class PDFValidationHandler(FileSystemEventHandler):
    """Monitor directory for new PDF files and validate them."""
    
    def __init__(self):
        self.validator = PDFValidator(verbose=True)
    
    def on_created(self, event):
        if event.is_file and event.src_path.endswith('.pdf'):
            print(f"New PDF detected: {event.src_path}")
            result = self.validator.validate_single_pdf(event.src_path)
            
            if result.is_valid:
                print(f"✓ Valid PDF: {result.page_count} pages")
            else:
                print(f"✗ Invalid PDF: {result.error_message}")

# Usage
event_handler = PDFValidationHandler()
observer = Observer()
observer.schedule(event_handler, "/path/to/watch", recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

#### Database Integration

```python
import sqlite3
from information_composer.pdf.validator import PDFValidator

class DatabasePDFValidator:
    """PDF validator with database integration."""
    
    def __init__(self, db_path):
        self.validator = PDFValidator()
        self.conn = sqlite3.connect(db_path)
        self.create_table()
    
    def create_table(self):
        """Create validation results table."""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS pdf_validation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                is_valid BOOLEAN,
                page_count INTEGER,
                file_size INTEGER,
                error_message TEXT,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def validate_and_store(self, file_path):
        """Validate PDF and store results in database."""
        result = self.validator.validate_single_pdf(file_path)
        
        self.conn.execute('''
            INSERT OR REPLACE INTO pdf_validation 
            (file_path, is_valid, page_count, file_size, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            file_path,
            result.is_valid,
            result.page_count,
            result.file_size,
            result.error_message
        ))
        self.conn.commit()
        
        return result
    
    def get_validation_stats(self):
        """Get validation statistics from database."""
        cursor = self.conn.execute('''
            SELECT 
                COUNT(*) as total_files,
                SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as valid_files,
                SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) as invalid_files
            FROM pdf_validation
        ''')
        
        row = cursor.fetchone()
        total = row[0]
        valid = row[1]
        invalid = row[2]
        success_rate = (valid / total * 100) if total > 0 else 0
        
        return {
            "total_files": total,
            "valid_files": valid,
            "invalid_files": invalid,
            "success_rate": success_rate
        }

# Usage
db_validator = DatabasePDFValidator("pdf_validation.db")
result = db_validator.validate_and_store("document.pdf")
stats = db_validator.get_validation_stats()
print(f"Database stats: {stats['success_rate']:.1f}% success rate")
```

## Best Practices

### Performance Optimization

1. **Use non-verbose mode for batch operations**:
   ```python
   validator = PDFValidator(verbose=False)  # Better performance
   ```

2. **Process files in batches**:
   ```python
   # Instead of processing all files at once
   validator.validate_files(all_files)  # May cause memory issues
   
   # Process in smaller batches
   for i in range(0, len(all_files), 100):
       batch = all_files[i:i+100]
       validator.validate_files(batch)
   ```

3. **Use appropriate file paths**:
   ```python
   # Use Path objects for better path handling
   from pathlib import Path
   validator.validate_single_pdf(Path("document.pdf"))
   ```

### Error Handling

1. **Always check validation results**:
   ```python
   result = validator.validate_single_pdf("file.pdf")
   if not result.is_valid:
       # Handle error appropriately
       logger.error(f"Validation failed: {result.error_message}")
   ```

2. **Use try-catch for file operations**:
   ```python
   try:
       result = validator.validate_single_pdf("file.pdf")
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
   ```

3. **Implement retry logic for transient errors**:
   ```python
   import time
   
   def validate_with_retry(file_path, max_retries=3):
       for attempt in range(max_retries):
           try:
               result = validator.validate_single_pdf(file_path)
               return result
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               time.sleep(1)  # Wait before retry
   ```

### Memory Management

1. **Reset statistics between batches**:
   ```python
   for batch in batches:
       validator.validate_files(batch)
       # Process results
       validator.reset_stats()  # Clear memory
   ```

2. **Use generators for large file lists**:
   ```python
   def pdf_file_generator(directory):
       for file_path in Path(directory).rglob("*.pdf"):
           yield file_path
   
   # Process files one at a time
   for pdf_file in pdf_file_generator("/path/to/pdfs"):
       result = validator.validate_single_pdf(pdf_file)
   ```

## Troubleshooting

### Common Issues

#### 1. "File not found" errors

**Problem**: PDF files cannot be found
**Solutions**:
- Check file paths are correct
- Ensure files exist before validation
- Use absolute paths when possible

```python
# Check if file exists first
from pathlib import Path
file_path = Path("document.pdf")
if file_path.exists():
    result = validator.validate_single_pdf(file_path)
else:
    print("File does not exist")
```

#### 2. "PDF format error" for valid PDFs

**Problem**: Valid PDFs are reported as invalid
**Solutions**:
- Check if PDF is password protected
- Verify PDF is not corrupted
- Try opening in a PDF viewer first

```python
# Check file size first
file_size = Path("document.pdf").stat().st_size
if file_size == 0:
    print("File is empty")
elif file_size < 1000:  # Very small PDF
    print("File may be corrupted")
```

#### 3. Memory issues with large files

**Problem**: Out of memory when processing large PDFs
**Solutions**:
- Process files individually
- Use smaller batch sizes
- Monitor memory usage

```python
import psutil
import gc

def validate_with_memory_monitoring(file_path):
    # Check available memory
    memory = psutil.virtual_memory()
    if memory.available < 100 * 1024 * 1024:  # Less than 100MB
        gc.collect()  # Force garbage collection
    
    result = validator.validate_single_pdf(file_path)
    return result
```

#### 4. Permission errors

**Problem**: Cannot access files due to permissions
**Solutions**:
- Check file permissions
- Run with appropriate user privileges
- Use try-catch for permission errors

```python
try:
    result = validator.validate_single_pdf("protected_file.pdf")
except PermissionError:
    print("Permission denied: Cannot access file")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Debug Mode

Enable debug mode for detailed error information:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebugPDFValidator(PDFValidator):
    def validate_single_pdf(self, pdf_path):
        logger.debug(f"Validating: {pdf_path}")
        result = super().validate_single_pdf(pdf_path)
        logger.debug(f"Result: {result}")
        return result
```

## Examples

### Complete Validation Script

```python
#!/usr/bin/env python3
"""
Complete PDF validation script with error handling and reporting.
"""

import argparse
import json
import sys
from pathlib import Path
from information_composer.pdf.validator import PDFValidator

def main():
    parser = argparse.ArgumentParser(description="PDF Validation Tool")
    parser.add_argument("path", help="File or directory to validate")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursive directory search")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-o", "--output", help="Output file for results")
    parser.add_argument("--json", action="store_true", help="JSON output format")
    
    args = parser.parse_args()
    
    validator = PDFValidator(verbose=args.verbose)
    path = Path(args.path)
    
    try:
        if path.is_file():
            # Validate single file
            result = validator.validate_single_pdf(path)
            if result.is_valid:
                print(f"✓ {path}: Valid PDF ({result.page_count} pages)")
            else:
                print(f"✗ {path}: {result.error_message}")
        elif path.is_dir():
            # Validate directory
            validator.validate_directory(path, recursive=args.recursive)
        else:
            print(f"Error: {path} is not a valid file or directory")
            return 1
        
        # Get results
        stats = validator.get_validation_stats()
        
        if args.json:
            # JSON output
            output = {
                "path": str(path),
                "recursive": args.recursive,
                "results": {
                    "total_files": stats.total_files,
                    "valid_files": stats.valid_files,
                    "invalid_files": stats.invalid_files,
                    "success_rate": stats.success_rate,
                    "error_details": stats.error_details
                }
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(output, f, indent=2)
            else:
                print(json.dumps(output, indent=2))
        else:
            # Standard output
            if not args.verbose:
                validator.print_summary()
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(f"PDF Validation Report\n")
                    f.write(f"Path: {path}\n")
                    f.write(f"Recursive: {args.recursive}\n")
                    f.write(f"Total files: {stats.total_files}\n")
                    f.write(f"Valid files: {stats.valid_files}\n")
                    f.write(f"Invalid files: {stats.invalid_files}\n")
                    f.write(f"Success rate: {stats.success_rate:.1f}%\n")
        
        return 0 if stats.invalid_files == 0 else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Batch Processing with Progress

```python
#!/usr/bin/env python3
"""
Batch PDF validation with progress tracking.
"""

import time
from pathlib import Path
from information_composer.pdf.validator import PDFValidator

def validate_with_progress(directory, recursive=True):
    """Validate PDFs with progress tracking."""
    directory = Path(directory)
    
    # Find all PDF files
    if recursive:
        pdf_files = list(directory.rglob("*.pdf"))
    else:
        pdf_files = list(directory.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    validator = PDFValidator(verbose=False)
    start_time = time.time()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        # Show progress
        progress = (i / len(pdf_files)) * 100
        print(f"\rProgress: {progress:.1f}% ({i}/{len(pdf_files)})", end="", flush=True)
        
        # Validate file
        result = validator.validate_single_pdf(pdf_file)
        
        # Show result for invalid files
        if not result.is_valid:
            print(f"\n✗ {pdf_file}: {result.error_message}")
    
    # Show final results
    elapsed_time = time.time() - start_time
    stats = validator.get_validation_stats()
    
    print(f"\n\nValidation completed in {elapsed_time:.1f} seconds")
    print(f"Total files: {stats.total_files}")
    print(f"Valid files: {stats.valid_files}")
    print(f"Invalid files: {stats.invalid_files}")
    print(f"Success rate: {stats.success_rate:.1f}%")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python validate_batch.py <directory>")
        sys.exit(1)
    
    validate_with_progress(sys.argv[1])
```

This comprehensive guide covers all aspects of using the PDF Validator, from basic usage to advanced integration patterns. The examples demonstrate real-world usage scenarios and best practices for efficient PDF validation.
