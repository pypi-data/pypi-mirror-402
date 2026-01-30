# Sites Base Module API

The base site collector module provides the foundation for all site-specific information collectors in the Information Composer project.

## BaseSiteCollector Class

### `BaseSiteCollector(config: Optional[Dict[str, Any]] = None)`

Abstract base class for site-specific information collectors.

**Parameters:**
- `config` (Optional[Dict[str, Any]]): Optional configuration dictionary for the collector

**Attributes:**
- `name` (str): The name of the collector (derived from class name)
- `config` (Dict[str, Any]): Configuration dictionary for the collector

**Example:**
```python
from information_composer.sites.base import BaseSiteCollector

class MyCollector(BaseSiteCollector):
    def collect(self, **kwargs):
        # Implement collection logic
        return {"data": "collected"}
    
    def compose(self, data, **kwargs):
        # Implement composition logic
        return {"composed": data}

# Initialize with configuration
collector = MyCollector({"timeout": 30})
```

### Abstract Methods

#### `collect(**kwargs: Any) -> Any`

Implement the information collection logic.

**Parameters:**
- `**kwargs`: Additional keyword arguments specific to the collector

**Returns:**
- Collected data in a format specific to the implementation

**Raises:**
- `NotImplementedError`: If not implemented by subclass

#### `compose(data: Any, **kwargs: Any) -> Any`

Implement the information composition logic.

**Parameters:**
- `data`: The collected data to compose
- `**kwargs`: Additional keyword arguments for composition

**Returns:**
- Composed data in the desired output format

**Raises:**
- `NotImplementedError`: If not implemented by subclass

### Utility Methods

#### `validate_config(required_keys: List[str]) -> bool`

Validate that the configuration contains required keys.

**Parameters:**
- `required_keys` (List[str]): List of required configuration keys

**Returns:**
- `True` if all required keys are present, `False` otherwise

**Example:**
```python
collector = MyCollector({"api_key": "secret", "timeout": 30})
is_valid = collector.validate_config(["api_key", "timeout"])  # True
```

#### `get_config_value(key: str, default: Any = None) -> Any`

Get a configuration value with optional default.

**Parameters:**
- `key` (str): The configuration key to retrieve
- `default` (Any): Default value if key is not found

**Returns:**
- The configuration value or default

**Example:**
```python
collector = MyCollector({"timeout": 30})
timeout = collector.get_config_value("timeout", 60)  # 30
retries = collector.get_config_value("retries", 3)   # 3
```

#### `get_metadata() -> Dict[str, Any]`

Get metadata about the collector.

**Returns:**
- Dictionary containing collector metadata

**Example:**
```python
collector = MyCollector()
metadata = collector.get_metadata()
# Returns: {
#     "name": "MyCollector",
#     "class": "MyCollector", 
#     "module": "my_module"
# }
```

## Usage Examples

### Basic Implementation

```python
from information_composer.sites.base import BaseSiteCollector
from typing import Any, Dict, List

class WebScraper(BaseSiteCollector):
    """Example web scraper implementation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = self.get_config_value("base_url", "https://example.com")
        self.timeout = self.get_config_value("timeout", 30)
    
    def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data from web pages."""
        # Implementation here
        return [{"title": "Page 1", "content": "Content 1"}]
    
    def compose(self, data: List[Dict[str, Any]], **kwargs) -> str:
        """Compose collected data into final format."""
        # Implementation here
        return "\n".join([item["title"] for item in data])

# Usage
config = {
    "base_url": "https://my-site.com",
    "timeout": 60
}
scraper = WebScraper(config)
data = scraper.collect()
result = scraper.compose(data)
```

### Configuration Validation

```python
class APICollector(BaseSiteCollector):
    """Example API collector with configuration validation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Validate required configuration
        required_keys = ["api_key", "base_url"]
        if not self.validate_config(required_keys):
            raise ValueError(f"Missing required configuration keys: {required_keys}")
    
    def collect(self, **kwargs) -> Dict[str, Any]:
        """Collect data from API."""
        api_key = self.get_config_value("api_key")
        base_url = self.get_config_value("base_url")
        # Use api_key and base_url for API calls
        return {"status": "success", "data": []}
    
    def compose(self, data: Dict[str, Any], **kwargs) -> str:
        """Compose API data."""
        return f"API Status: {data['status']}"
```

## Best Practices

1. **Always call super().__init__()** in your subclass constructor
2. **Validate configuration** in your constructor if required
3. **Use get_config_value()** for accessing configuration with defaults
4. **Handle errors gracefully** in collect() and compose() methods
5. **Document your collector's specific parameters** in docstrings
6. **Use type hints** for better code clarity and IDE support

## Error Handling

The base class provides a foundation for error handling, but specific error handling should be implemented in subclasses:

```python
class RobustCollector(BaseSiteCollector):
    def collect(self, **kwargs) -> Any:
        try:
            # Collection logic
            return self._perform_collection()
        except Exception as e:
            # Log error and return appropriate fallback
            self.logger.error(f"Collection failed: {e}")
            return {"error": str(e), "data": []}
    
    def compose(self, data: Any, **kwargs) -> Any:
        try:
            # Composition logic
            return self._perform_composition(data)
        except Exception as e:
            # Log error and return appropriate fallback
            self.logger.error(f"Composition failed: {e}")
            return {"error": str(e), "result": ""}
```