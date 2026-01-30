# BaseDownloader API

The `BaseDownloader` class provides a common interface for downloading content from various sources.

## Class Definition

```python
class BaseDownloader:
    def __init__(self, timeout: int = 30) -> None
    def download(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any
```

## Constructor

### `__init__(timeout: int = 30) -> None`

Initialize the base downloader.

**Parameters:**
- `timeout` (int): Request timeout in seconds. Defaults to 30.

**Attributes:**
- `timeout` (int): The configured timeout value
- `session` (requests.Session): HTTP session for making requests

## Methods

### `download(url: str, headers: Optional[Dict[str, str]] = None) -> Any`

Download content from specified URL.

This is an abstract method that should be implemented by subclasses to provide specific download functionality.

**Parameters:**
- `url` (str): The URL to download content from
- `headers` (Optional[Dict[str, str]]): Optional HTTP headers to include in the request

**Returns:**
- The downloaded content (type depends on implementation)

**Raises:**
- `NotImplementedError`: This method must be implemented by subclasses

## Usage Example

```python
from information_composer.core.downloader import BaseDownloader

class MyDownloader(BaseDownloader):
    def download(self, url: str, headers=None):
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        return response.content

# Usage
downloader = MyDownloader(timeout=60)
content = downloader.download("https://example.com", {"User-Agent": "MyApp"})
```

## Design Notes

The `BaseDownloader` class follows the Template Method pattern, providing a common structure for downloaders while allowing subclasses to implement specific download logic. The class manages HTTP sessions and timeouts, making it easy to create specialized downloaders for different content types or sources.
