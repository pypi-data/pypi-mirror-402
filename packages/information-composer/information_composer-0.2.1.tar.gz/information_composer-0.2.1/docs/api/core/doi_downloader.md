# DOIDownloader API

The `DOIDownloader` class provides functionality to download academic papers using their Digital Object Identifier (DOI) through the Crossref API.

## Class Definition

```python
class DOIDownloader:
    def __init__(self, email: Optional[str] = None) -> None
    def get_pdf_url(self, doi: str) -> Optional[str]
    def download_pdf(self, url: str, output_path: Union[str, Path]) -> bool
    def download_by_doi(self, doi: str, output_dir: Union[str, Path] = "downloads") -> Optional[str]
    def download_single(self, doi: str, output_dir: Union[str, Path], file_name: Optional[str] = None) -> DownloadResult
    def download_batch(self, dois: List[str], output_dir: Union[str, Path], delay: int = 2) -> List[DownloadResult]
```

## Data Classes

### `DownloadResult`

Result of a single download operation.

```python
@dataclass
class DownloadResult:
    doi: str
    file_name: str
    downloaded: bool
    file_size: Optional[int] = None
    error_message: Optional[str] = None
```

**Fields:**
- `doi` (str): The DOI that was processed
- `file_name` (str): Path to the downloaded file (empty if download failed)
- `downloaded` (bool): Whether the download was successful
- `file_size` (Optional[int]): Size of the downloaded file in bytes
- `error_message` (Optional[str]): Error message if download failed

### `BatchDownloadStats`

Statistics for batch download operations.

```python
@dataclass
class BatchDownloadStats:
    total_papers: int
    successfully_downloaded: int
    subscription_required: int
    doi_not_found: int
    access_restricted: int
    other_errors: int
```

## Constructor

### `__init__(email: Optional[str] = None) -> None`

Initialize DOIDownloader.

**Parameters:**
- `email` (Optional[str]): Email for Crossref API. Providing an email improves service and helps with rate limiting. If None, uses anonymous@example.com.

**Attributes:**
- `cr` (Crossref): Crossref API client
- `headers` (Dict[str, str]): HTTP headers for requests

## Methods

### `get_pdf_url(doi: str) -> Optional[str]`

Get PDF URL from DOI using Crossref.

**Parameters:**
- `doi` (str): The DOI of the paper

**Returns:**
- `Optional[str]`: The URL of the PDF if found, None otherwise

**Example:**
```python
downloader = DOIDownloader()
pdf_url = downloader.get_pdf_url("10.1000/182")
if pdf_url:
    print(f"Found PDF at: {pdf_url}")
```

### `download_pdf(url: str, output_path: Union[str, Path]) -> bool`

Download PDF from URL.

**Parameters:**
- `url` (str): The URL of the PDF
- `output_path` (Union[str, Path]): Path where the PDF should be saved

**Returns:**
- `bool`: True if download was successful, False otherwise

**Error Handling:**
- Returns False for access denied (401/403)
- Returns False for not found (404)
- Returns False for wrong content type
- Returns False for SSL/connection errors

**Example:**
```python
success = downloader.download_pdf("https://example.com/paper.pdf", "paper.pdf")
if success:
    print("Download successful")
```

### `download_by_doi(doi: str, output_dir: Union[str, Path] = "downloads") -> Optional[str]`

Download PDF by DOI.

**Parameters:**
- `doi` (str): The DOI of the paper
- `output_dir` (Union[str, Path]): Directory where PDFs should be saved. Defaults to "downloads"

**Returns:**
- `Optional[str]`: Path to the downloaded PDF if successful, None otherwise

**Example:**
```python
result = downloader.download_by_doi("10.1000/182", "papers")
if result:
    print(f"Downloaded to: {result}")
```

### `download_single(doi: str, output_dir: Union[str, Path], file_name: Optional[str] = None) -> DownloadResult`

Download a single paper by DOI with detailed output.

**Parameters:**
- `doi` (str): The DOI of the paper to download
- `output_dir` (Union[str, Path]): Directory to save the downloaded paper
- `file_name` (Optional[str]): Custom filename for the PDF. If None, uses DOI as filename

**Returns:**
- `DownloadResult`: Download result containing DOI, file_name, and download status

**Example:**
```python
result = downloader.download_single("10.1000/182", "papers", "my_paper.pdf")
print(f"DOI: {result.doi}")
print(f"Downloaded: {result.downloaded}")
print(f"File: {result.file_name}")
if result.file_size:
    print(f"Size: {result.file_size} bytes")
```

### `download_batch(dois: List[str], output_dir: Union[str, Path], delay: int = 2) -> List[DownloadResult]`

Download multiple papers by their DOIs with detailed output.

**Parameters:**
- `dois` (List[str]): List of DOIs to download
- `output_dir` (Union[str, Path]): Directory to save the downloaded papers
- `delay` (int): Delay between downloads in seconds. Defaults to 2

**Returns:**
- `List[DownloadResult]`: List of download results

**Example:**
```python
dois = ["10.1000/182", "10.1000/183", "10.1000/184"]
results = downloader.download_batch(dois, "papers", delay=1)

successful = [r for r in results if r.downloaded]
print(f"Downloaded {len(successful)} out of {len(dois)} papers")
```

## Usage Examples

### Basic Usage

```python
from information_composer.core.doi_downloader import DOIDownloader

# Initialize with email for better service
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

# Process results
for result in results:
    if result.downloaded:
        print(f"✓ {result.doi}: {result.file_name}")
    else:
        print(f"✗ {result.doi}: {result.error_message}")
```

### Error Handling

```python
# Check for specific error types
result = downloader.download_single("10.1000/invalid", "downloads")
if not result.downloaded:
    if "subscription" in result.error_message.lower():
        print("This paper requires a subscription")
    elif "not found" in result.error_message.lower():
        print("DOI not found")
    else:
        print(f"Other error: {result.error_message}")
```

## Error Types

The downloader handles various error conditions:

1. **Access Denied (401/403)**: Paper requires subscription or payment
2. **Not Found (404)**: DOI or PDF URL is invalid
3. **Access Restricted**: Redirected to login or payment page
4. **SSL Error**: Could not establish secure connection
5. **Connection Error**: Could not connect to the server
6. **Timeout Error**: Request timed out
7. **Wrong Content Type**: URL does not point to a PDF

## Rate Limiting

The Crossref API has rate limits. The downloader includes:
- Configurable delay between requests in batch downloads
- Proper User-Agent headers
- Email identification for better service

## Dependencies

- `requests`: For HTTP requests
- `habanero`: For Crossref API access
- `tqdm`: For progress bars in batch downloads
- `pathlib`: For path handling
