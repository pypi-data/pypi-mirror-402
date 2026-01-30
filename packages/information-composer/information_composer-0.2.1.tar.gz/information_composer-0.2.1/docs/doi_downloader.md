# DOI Downloader

The DOI Downloader module provides functionality to download academic papers using their Digital Object Identifiers (DOIs).

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Detailed Usage](#detailed-usage)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Error Handling](#error-handling)
8. [Output Format](#output-format)
9. [Best Practices](#best-practices)

## Features

- Download PDFs using DOI
- Batch download multiple DOIs
- Configurable delay between requests
- Email registration for better Crossref API service
- Detailed download status reporting
- CSV export of download results
- Progress tracking for batch downloads
- Robust error handling

## Installation

```bash
pip install information-composer
```

Required dependencies:
```bash
pip install requests habanero
```

## Quick Start

```python
from information_composer.core.doi_downloader import DOIDownloader

# Initialize downloader
downloader = DOIDownloader(email="your_email@example.com")

# Download a single paper
result = downloader.download_single(
    doi="10.1038/s41477-024-01771-3",
    output_dir="downloads"
)
```

## Detailed Usage

### Single DOI Download

```python
# Initialize downloader with email
downloader = DOIDownloader(email="your_email@example.com")

# Download single paper
result = downloader.download_single(
    doi="10.1038/s41477-024-01771-3",
    output_dir="downloads/single"
)

# Check result
if result['downloaded']:
    print(f"Successfully downloaded to: {result['file_name']}")
    print(f"File size: {os.path.getsize(result['file_name']) / 1024:.2f} KB")
else:
    print(f"Failed to download DOI: {result['DOI']}")
```

### Batch Download

```python
# List of DOIs to download
dois = [
    "10.1038/s41477-024-01771-3",
    "10.1038/s41592-024-02305-7",
    "10.1038/s41592-024-02201-0"
]

# Download multiple papers
results = downloader.download_batch(
    dois=dois,
    output_dir="downloads/batch",
    delay=2  # 2 seconds delay between downloads
)
```

### Saving Results to CSV

```python
def save_results_to_csv(results, output_file):
    fieldnames = ['DOI', 'file_name', 'downloaded']
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
```

## API Reference

### DOIDownloader Class

```python
class DOIDownloader:
    def __init__(self, email: str = None):
        """Initialize with optional email for Crossref API"""
        
    def get_pdf_url(self, doi: str) -> Optional[str]:
        """Get PDF URL from DOI"""
        
    def download_pdf(self, url: str, output_path: str) -> bool:
        """Download PDF from URL"""
        
    def download_single(self, doi: str, output_dir: str) -> Dict:
        """Download single paper with detailed output"""
        
    def download_batch(self, dois: List[str], output_dir: str, delay: int = 2) -> List[Dict]:
        """Download multiple papers with delay"""
```

## Examples

### Complete Example Script

```python
from information_composer.core.doi_downloader import DOIDownloader
import os

def main():
    # Configuration
    base_dir = os.path.join(os.getcwd(), "downloads")
    email = "your_email@example.com"
    
    # Initialize downloader
    downloader = DOIDownloader(email=email)
    
    # Single download
    single_result = downloader.download_single(
        doi="10.1038/s41477-024-01771-3",
        output_dir=os.path.join(base_dir, "single")
    )
    
    # Batch download
    dois = [
        "10.1038/s41477-024-01771-3",
        "10.1038/s41592-024-02305-7",
        "10.1038/s41592-024-02201-0"
    ]
    batch_results = downloader.download_batch(
        dois=dois,
        output_dir=os.path.join(base_dir, "batch"),
        delay=2
    )
```

## Error Handling

The module handles various error scenarios:

- Access denied (401/403): Subscription required
- Not found (404): Invalid DOI or URL
- SSL errors: Security connection issues
- Connection errors: Network problems
- Content type mismatches: Non-PDF responses

Example error messages:
```
Access denied: This paper requires subscription or payment
PDF not found: The URL is no longer valid
SSL Error: Could not establish secure connection
Connection Error: Could not connect to the server
```

## Output Format

### Download Results Dictionary
```python
{
    'DOI': 'paper_doi',
    'file_name': 'path/to/downloaded.pdf',
    'downloaded': True/False
}
```

### CSV Output Format
```csv
DOI,file_name,downloaded
10.1038/s41477-024-01771-3,downloads/10.1038_s41477-024-01771-3.pdf,True
```

### Directory Structure
```
downloads/
├── single/
│   └── 10.1038_s41477-024-01771-3.pdf
├── batch/
│   ├── 10.1038_s41477-024-01771-3.pdf
│   ├── 10.1038_s41592-024-02305-7.pdf
│   └── 10.1038_s41592-024-02201-0.pdf
├── single_download_results.csv
└── batch_download_results.csv
```

## Best Practices

1. **Rate Limiting**
   - Use appropriate delays between requests
   - Default delay is 2 seconds
   ```python
   downloader.download_batch(dois=dois, delay=2)
   ```

2. **Email Registration**
   - Provide email for better Crossref API service
   ```python
   downloader = DOIDownloader(email="your_email@example.com")
   ```

3. **Error Handling**
   - Always check download results
   ```python
   if result['downloaded']:
       print(f"Success: {result['file_name']}")
   else:
       print(f"Failed: {result['DOI']}")
   ```

4. **File Organization**
   - Use structured output directories
   - Keep single and batch downloads separate
   ```python
   single_dir = os.path.join(base_dir, "single")
   batch_dir = os.path.join(base_dir, "batch")
   ```

5. **Results Tracking**
   - Save results to CSV for record keeping
   - Monitor download statistics
   ```python
   save_results_to_csv(results, "download_results.csv")
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.