# DOI Download Guide

This guide explains how to use the `information_composer.core` module to download academic papers using their Digital Object Identifier (DOI).

## Overview

The DOI download functionality allows you to:
- Download academic papers using their DOI
- Handle batch downloads with progress tracking
- Get detailed status information for each download
- Customize download behavior and error handling

## Quick Start

### Basic Single Download

```python
from information_composer.core.doi_downloader import DOIDownloader

# Initialize the downloader
downloader = DOIDownloader(email="your-email@example.com")

# Download a single paper
result = downloader.download_single("10.1000/182", "downloads")
if result.downloaded:
    print(f"Successfully downloaded: {result.file_name}")
    print(f"File size: {result.file_size} bytes")
else:
    print(f"Download failed: {result.error_message}")
```

### Batch Download

```python
# Download multiple papers
dois = [
    "10.1000/182",
    "10.1000/183",
    "10.1000/184"
]

results = downloader.download_batch(dois, "papers", delay=2)

# Check results
successful = [r for r in results if r.downloaded]
print(f"Downloaded {len(successful)} out of {len(dois)} papers")
```

## Configuration

### Email Configuration

Providing an email address improves service quality and helps with rate limiting:

```python
# With email (recommended)
downloader = DOIDownloader(email="your-email@example.com")

# Without email (uses anonymous@example.com)
downloader = DOIDownloader()
```

### Custom Filenames

You can specify custom filenames for downloaded papers:

```python
# Custom filename with extension
result = downloader.download_single(
    "10.1000/182", 
    "papers", 
    file_name="my_paper.pdf"
)

# Custom filename without extension (automatically adds .pdf)
result = downloader.download_single(
    "10.1000/182", 
    "papers", 
    file_name="my_paper"
)
```

### Output Directory

The downloader automatically creates output directories if they don't exist:

```python
# Using string path
result = downloader.download_single("10.1000/182", "papers")

# Using Path object
from pathlib import Path
result = downloader.download_single("10.1000/182", Path("papers"))
```

## Error Handling

### Understanding Download Results

The `DownloadResult` object provides detailed information about each download:

```python
result = downloader.download_single("10.1000/182", "downloads")

print(f"DOI: {result.doi}")
print(f"Downloaded: {result.downloaded}")
print(f"File name: {result.file_name}")
print(f"File size: {result.file_size}")
print(f"Error message: {result.error_message}")
```

### Common Error Types

1. **Access Denied**: Paper requires subscription or payment
2. **DOI Not Found**: Invalid or non-existent DOI
3. **Access Restricted**: Redirected to login or payment page
4. **Network Errors**: SSL, connection, or timeout issues

### Error Handling Example

```python
def download_with_error_handling(doi: str, output_dir: str):
    """Download a paper with comprehensive error handling."""
    result = downloader.download_single(doi, output_dir)
    
    if result.downloaded:
        print(f"✓ Successfully downloaded: {result.file_name}")
        return True
    else:
        error_msg = result.error_message or "Unknown error"
        if "subscription" in error_msg.lower():
            print(f"✗ {doi}: Requires subscription")
        elif "not found" in error_msg.lower():
            print(f"✗ {doi}: DOI not found")
        elif "access" in error_msg.lower():
            print(f"✗ {doi}: Access restricted")
        else:
            print(f"✗ {doi}: {error_msg}")
        return False

# Usage
success = download_with_error_handling("10.1000/182", "downloads")
```

## Batch Processing

### Basic Batch Download

```python
# List of DOIs to download
dois = [
    "10.1000/182",
    "10.1000/183",
    "10.1000/184",
    "10.1000/185"
]

# Download with 2-second delay between requests
results = downloader.download_batch(dois, "papers", delay=2)

# Process results
successful = []
failed = []

for result in results:
    if result.downloaded:
        successful.append(result)
    else:
        failed.append(result)

print(f"Successfully downloaded: {len(successful)}")
print(f"Failed: {len(failed)}")
```

### Advanced Batch Processing

```python
def process_batch_results(results):
    """Process batch download results with detailed statistics."""
    stats = {
        "total": len(results),
        "successful": 0,
        "subscription_required": 0,
        "not_found": 0,
        "access_restricted": 0,
        "other_errors": 0
    }
    
    for result in results:
        if result.downloaded:
            stats["successful"] += 1
        else:
            error_msg = result.error_message or ""
            if "subscription" in error_msg.lower():
                stats["subscription_required"] += 1
            elif "not found" in error_msg.lower():
                stats["not_found"] += 1
            elif "access" in error_msg.lower():
                stats["access_restricted"] += 1
            else:
                stats["other_errors"] += 1
    
    return stats

# Usage
results = downloader.download_batch(dois, "papers")
stats = process_batch_results(results)

print("Download Statistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")
```

## Rate Limiting and Best Practices

### Rate Limiting

The Crossref API has rate limits. The downloader includes built-in delays:

```python
# Conservative delay (recommended for large batches)
results = downloader.download_batch(dois, "papers", delay=3)

# Faster delay (use with caution)
results = downloader.download_batch(dois, "papers", delay=1)
```

### Best Practices

1. **Use Email**: Always provide an email address for better service
2. **Respect Rate Limits**: Use appropriate delays between requests
3. **Handle Errors**: Always check download results and handle errors gracefully
4. **Monitor Progress**: Use the progress bar in batch downloads
5. **Validate DOIs**: Ensure DOIs are properly formatted before downloading

### Example: Robust Batch Download

```python
def robust_batch_download(dois: list, output_dir: str, delay: int = 2):
    """Robust batch download with error handling and progress tracking."""
    print(f"Starting batch download of {len(dois)} papers...")
    print(f"Output directory: {output_dir}")
    print(f"Delay between requests: {delay} seconds")
    
    # Validate DOIs
    valid_dois = []
    for doi in dois:
        if doi and doi.strip():
            valid_dois.append(doi.strip())
        else:
            print(f"Warning: Skipping invalid DOI: '{doi}'")
    
    if not valid_dois:
        print("No valid DOIs provided")
        return []
    
    print(f"Processing {len(valid_dois)} valid DOIs...")
    
    # Download with progress tracking
    results = downloader.download_batch(valid_dois, output_dir, delay)
    
    # Summary
    successful = [r for r in results if r.downloaded]
    print(f"\nBatch download completed:")
    print(f"  Total: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(results) - len(successful)}")
    
    return results

# Usage
dois = ["10.1000/182", "10.1000/183", "10.1000/184"]
results = robust_batch_download(dois, "papers", delay=2)
```

## Integration Examples

### With File Management

```python
import os
from pathlib import Path

def download_and_organize(dois: list, base_dir: str):
    """Download papers and organize by year."""
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    for doi in dois:
        # Create year-based subdirectory
        year_dir = base_path / "2024"  # You might extract year from DOI
        year_dir.mkdir(exist_ok=True)
        
        result = downloader.download_single(doi, year_dir)
        if result.downloaded:
            print(f"Downloaded to: {result.file_name}")
        else:
            print(f"Failed to download {doi}: {result.error_message}")

# Usage
dois = ["10.1000/182", "10.1000/183"]
download_and_organize(dois, "research_papers")
```

### With Data Analysis

```python
import pandas as pd

def download_and_analyze(dois: list, output_dir: str):
    """Download papers and create analysis report."""
    results = downloader.download_batch(dois, output_dir)
    
    # Convert to DataFrame for analysis
    data = []
    for result in results:
        data.append({
            "doi": result.doi,
            "downloaded": result.downloaded,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "error_message": result.error_message
        })
    
    df = pd.DataFrame(data)
    
    # Analysis
    print("Download Analysis:")
    print(f"Success rate: {df['downloaded'].mean():.2%}")
    print(f"Average file size: {df[df['downloaded']]['file_size'].mean():.0f} bytes")
    
    # Save report
    df.to_csv(f"{output_dir}/download_report.csv", index=False)
    
    return df

# Usage
dois = ["10.1000/182", "10.1000/183", "10.1000/184"]
df = download_and_analyze(dois, "papers")
```

## Troubleshooting

### Common Issues

1. **SSL Errors**: Check your internet connection and SSL certificates
2. **Connection Errors**: Verify network connectivity and try again
3. **Timeout Errors**: Increase timeout or check server status
4. **Access Denied**: Some papers require institutional access
5. **DOI Not Found**: Verify DOI format and existence

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('information_composer.core.doi_downloader')

# Your download code here
result = downloader.download_single("10.1000/182", "downloads")
```

### Testing Connectivity

```python
def test_connectivity():
    """Test basic connectivity to Crossref API."""
    try:
        # Try to get a simple DOI
        pdf_url = downloader.get_pdf_url("10.1000/182")
        if pdf_url:
            print("✓ Crossref API is accessible")
            return True
        else:
            print("✗ Crossref API returned no results")
            return False
    except Exception as e:
        print(f"✗ Error connecting to Crossref API: {e}")
        return False

# Test before batch download
if test_connectivity():
    results = downloader.download_batch(dois, "papers")
else:
    print("Cannot proceed with downloads due to connectivity issues")
```

## API Reference

For detailed API documentation, see:
- [BaseDownloader API](../api/core/downloader.md)
- [DOIDownloader API](../api/core/doi_downloader.md)

## Examples

Check the `examples/` directory for complete working examples:
- `doi_download_example.py` - Basic DOI download examples
- `doi_download_by_using_pubmed_batch_example.py` - Integration with PubMed
- `doi_download_single.py` - Single download examples
