# LLM Filter Configuration API

The configuration module provides comprehensive configuration management for the LLM Filter system, including validation, environment variable handling, and configuration file support.

## Core Classes

### `LLMConfig` Dataclass

Configuration for LLM-related settings.

```python
@dataclass
class LLMConfig:
    api_key: str
    model: str = "qwen-plus"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    cache_dir: str = "./cache"
```

**Attributes:**
- `api_key` (str): API key for the LLM service
- `model` (str): Model name to use
- `temperature` (float): Sampling temperature (0.0-2.0)
- `max_tokens` (int): Maximum tokens to generate
- `max_concurrent_requests` (int): Maximum concurrent API requests
- `request_timeout` (int): Request timeout in seconds
- `enable_cache` (bool): Whether to enable response caching
- `cache_ttl_hours` (int): Cache time-to-live in hours
- `cache_dir` (str): Directory for cache files

### `ProcessingConfig` Dataclass

Configuration for document processing settings.

```python
@dataclass
class ProcessingConfig:
    input_dir: str = "./input"
    output_dir: str = "./output"
    file_pattern: str = "*.md"
    recursive: bool = True
    output_format: str = "markdown"
    overwrite: bool = False
    backup: bool = True
    max_file_size_mb: int = 10
    supported_formats: List[str] = field(default_factory=lambda: ["pdf", "md", "txt"])
```

**Attributes:**
- `input_dir` (str): Input directory path
- `output_dir` (str): Output directory path
- `file_pattern` (str): File pattern to match
- `recursive` (bool): Whether to process subdirectories
- `output_format` (str): Output format (markdown, json, etc.)
- `overwrite` (bool): Whether to overwrite existing files
- `backup` (bool): Whether to create backup files
- `max_file_size_mb` (int): Maximum file size in MB
- `supported_formats` (List[str]): List of supported file formats

### `AppConfig` Dataclass

Main application configuration combining all settings.

```python
@dataclass
class AppConfig:
    llm: LLMConfig
    processing: ProcessingConfig
    log_level: str = "INFO"
    debug: bool = False
    
    def __post_init__(self):
        if isinstance(self.llm, dict):
            self.llm = LLMConfig(**self.llm)
        if isinstance(self.processing, dict):
            self.processing = ProcessingConfig(**self.processing)
```

## Configuration Manager

### `ConfigManager` Class

Manages configuration loading, validation, and saving.

```python
class ConfigManager:
    def __init__(self, config_file: Optional[str] = None) -> None
    def load_config(self, config_file: Optional[str] = None) -> AppConfig
    def save_config(self, config: AppConfig, config_file: Optional[str] = None) -> None
    def validate_config(self, config: Optional[AppConfig] = None) -> Tuple[bool, List[str]]
    def get_config(self) -> AppConfig
    def update_config(self, **kwargs) -> None
```

#### Methods

##### `load_config(config_file: Optional[str] = None) -> AppConfig`

Load configuration from file or environment variables.

**Parameters:**
- `config_file` (Optional[str]): Path to configuration file

**Returns:**
- `AppConfig`: Loaded configuration object

**Example:**
```python
from information_composer.llm_filter.config.settings import ConfigManager

# Load from default location
config_manager = ConfigManager()
config = config_manager.load_config()

# Load from specific file
config = config_manager.load_config("custom_config.json")
```

##### `save_config(config: AppConfig, config_file: Optional[str] = None) -> None`

Save configuration to file.

**Parameters:**
- `config` (AppConfig): Configuration to save
- `config_file` (Optional[str]): Path to save configuration

**Example:**
```python
# Save current configuration
config_manager.save_config(config)

# Save to specific file
config_manager.save_config(config, "backup_config.json")
```

##### `validate_config(config: Optional[AppConfig] = None) -> Tuple[bool, List[str]]`

Validate configuration for required fields and values.

**Parameters:**
- `config` (Optional[AppConfig]): Configuration to validate

**Returns:**
- `Tuple[bool, List[str]]`: (is_valid, error_messages)

**Example:**
```python
is_valid, errors = config_manager.validate_config()
if not is_valid:
    for error in errors:
        print(f"Configuration error: {error}")
```

## Environment Variable Support

The configuration system supports loading from environment variables:

### LLM Configuration

```bash
export DASHSCOPE_API_KEY="your-api-key"
export DASHSCOPE_MODEL="qwen-plus"
export DASHSCOPE_TEMPERATURE="0.7"
export DASHSCOPE_MAX_TOKENS="4096"
export MAX_CONCURRENT_REQUESTS="5"
export REQUEST_TIMEOUT="30"
export ENABLE_CACHE="true"
export CACHE_TTL_HOURS="24"
export CACHE_DIR="./cache"
```

### Processing Configuration

```bash
export INPUT_DIR="./input"
export OUTPUT_DIR="./output"
export FILE_PATTERN="*.md"
export RECURSIVE="true"
export OUTPUT_FORMAT="markdown"
export OVERWRITE="false"
export BACKUP="true"
export MAX_FILE_SIZE_MB="10"
```

### Application Configuration

```bash
export LOG_LEVEL="INFO"
export DEBUG="false"
```

## Configuration File Formats

### JSON Configuration

```json
{
  "llm": {
    "api_key": "your-api-key",
    "model": "qwen-plus",
    "temperature": 0.7,
    "max_tokens": 4096,
    "max_concurrent_requests": 5,
    "request_timeout": 30,
    "enable_cache": true,
    "cache_ttl_hours": 24,
    "cache_dir": "./cache"
  },
  "processing": {
    "input_dir": "./input",
    "output_dir": "./output",
    "file_pattern": "*.md",
    "recursive": true,
    "output_format": "markdown",
    "overwrite": false,
    "backup": true,
    "max_file_size_mb": 10,
    "supported_formats": ["pdf", "md", "txt"]
  },
  "log_level": "INFO",
  "debug": false
}
```

### YAML Configuration

```yaml
llm:
  api_key: "your-api-key"
  model: "qwen-plus"
  temperature: 0.7
  max_tokens: 4096
  max_concurrent_requests: 5
  request_timeout: 30
  enable_cache: true
  cache_ttl_hours: 24
  cache_dir: "./cache"

processing:
  input_dir: "./input"
  output_dir: "./output"
  file_pattern: "*.md"
  recursive: true
  output_format: "markdown"
  overwrite: false
  backup: true
  max_file_size_mb: 10
  supported_formats:
    - "pdf"
    - "md"
    - "txt"

log_level: "INFO"
debug: false
```

## Usage Examples

### Basic Configuration

```python
from information_composer.llm_filter.config.settings import AppConfig, LLMConfig, ProcessingConfig

# Create configuration manually
llm_config = LLMConfig(
    api_key="your-api-key",
    model="qwen-plus",
    temperature=0.7
)

processing_config = ProcessingConfig(
    input_dir="./input",
    output_dir="./output",
    file_pattern="*.md"
)

config = AppConfig(
    llm=llm_config,
    processing=processing_config
)
```

### Using Configuration Manager

```python
from information_composer.llm_filter.config.settings import ConfigManager

# Initialize manager
config_manager = ConfigManager()

# Load configuration
config = config_manager.load_config("config.json")

# Validate configuration
is_valid, errors = config_manager.validate_config(config)
if not is_valid:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")

# Update configuration
config_manager.update_config(
    llm={"temperature": 0.5},
    processing={"recursive": False}
)

# Save updated configuration
config_manager.save_config(config, "updated_config.json")
```

### Environment Variable Configuration

```python
import os
from information_composer.llm_filter.config.settings import ConfigManager

# Set environment variables
os.environ["DASHSCOPE_API_KEY"] = "your-api-key"
os.environ["DASHSCOPE_MODEL"] = "qwen-plus"
os.environ["INPUT_DIR"] = "./input"
os.environ["OUTPUT_DIR"] = "./output"

# Load from environment
config_manager = ConfigManager()
config = config_manager.load_config()
```

## Validation Rules

### Required Fields

- `llm.api_key`: Must be non-empty string
- `llm.model`: Must be non-empty string
- `processing.input_dir`: Must be valid directory path
- `processing.output_dir`: Must be valid directory path

### Value Ranges

- `llm.temperature`: 0.0 <= value <= 2.0
- `llm.max_tokens`: value > 0
- `llm.max_concurrent_requests`: 1 <= value <= 100
- `llm.request_timeout`: 1 <= value <= 300
- `processing.max_file_size_mb`: 1 <= value <= 1000

### File System Validation

- Input and output directories must be valid paths
- Cache directory must be writable
- File patterns must be valid glob patterns

## Error Handling

### Configuration Errors

```python
try:
    config = config_manager.load_config("invalid_config.json")
except FileNotFoundError:
    print("Configuration file not found")
except ValueError as e:
    print(f"Invalid configuration: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Validation Errors

```python
is_valid, errors = config_manager.validate_config()
if not is_valid:
    for error in errors:
        if "api_key" in error:
            print("Please set DASHSCOPE_API_KEY environment variable")
        elif "input_dir" in error:
            print("Please check input directory path")
```

## Best Practices

1. **Use Environment Variables**: For sensitive data like API keys
2. **Validate Configuration**: Always validate before use
3. **Provide Defaults**: Use sensible default values
4. **Document Settings**: Document all configuration options
5. **Handle Errors**: Implement proper error handling
6. **Test Configuration**: Test with different configuration scenarios

## Migration and Compatibility

### Version Compatibility

The configuration system maintains backward compatibility:
- Old configuration files are automatically migrated
- Deprecated options are handled gracefully
- New options have sensible defaults

### Migration Example

```python
# Old configuration format
old_config = {
    "api_key": "key",
    "model": "qwen-plus"
}

# Automatically converted to new format
config_manager = ConfigManager()
config = config_manager.load_config_from_dict(old_config)
# config.llm.api_key and config.llm.model are set
```
