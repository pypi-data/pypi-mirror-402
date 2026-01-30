# Configuration Guide

This guide provides comprehensive information about configuring Information Composer for different use cases and environments.

## 📋 Configuration Overview

Information Composer supports multiple configuration methods:

- **Environment Variables** - For sensitive data and deployment
- **Configuration Files** - For complex setups and team sharing
- **Command Line Arguments** - For temporary overrides
- **Code Configuration** - For programmatic setup

## 🔧 Environment Variables

### Required Configuration

#### DASHSCOPE_API_KEY
API key for DashScope LLM services.

```bash
export DASHSCOPE_API_KEY="sk-your-api-key-here"
```

**How to get:**
1. Visit [DashScope Console](https://dashscope.aliyun.com/)
2. Register and login
3. Create an API key in the console

### Optional Configuration

#### LLM Settings
```bash
# Model selection
export DASHSCOPE_MODEL="qwen-plus"  # qwen-plus, qwen-max, qwen-turbo

# Performance settings
export MAX_CONCURRENT_REQUESTS=5
export REQUEST_TIMEOUT=30

# Caching
export ENABLE_CACHE=true
export CACHE_TTL_HOURS=24
export CACHE_DIR="./cache"
```

#### Processing Settings
```bash
# File processing
export MAX_FILE_SIZE_MB=10
export SUPPORTED_FORMATS="pdf,md,txt"
export INPUT_DIR="./input"
export OUTPUT_DIR="./output"

# Application settings
export LOG_LEVEL="INFO"
export DEBUG=false
```

## 📄 Configuration Files

### YAML Configuration

Create `config.yaml`:

```yaml
# LLM Configuration
llm:
  api_key: "sk-your-api-key-here"
  model: "qwen-plus"
  temperature: 0.7
  max_tokens: 4096
  max_concurrent_requests: 5
  request_timeout: 30
  enable_cache: true
  cache_ttl_hours: 24
  cache_dir: "./cache"

# Processing Configuration
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

# Application Configuration
app:
  log_level: "INFO"
  debug: false

# PDF Validation Settings
pdf:
  strict_mode: true
  check_encryption: true
  max_pages: 1000

# Markdown Processing Settings
markdown:
  preserve_formatting: true
  extract_metadata: true
  clean_html: true

# PubMed Settings
pubmed:
  email: "your-email@example.com"
  batch_size: 100
  delay_between_requests: 1.0
```

### JSON Configuration

Create `config.json`:

```json
{
  "llm": {
    "api_key": "sk-your-api-key-here",
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
  "app": {
    "log_level": "INFO",
    "debug": false
  }
}
```

## 🐍 Programmatic Configuration

### Using Configuration Manager

```python
from information_composer.llm_filter.config.settings import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()

# Load from file
config = config_manager.load_config("config.yaml")

# Validate configuration
is_valid, errors = config_manager.validate_config()
if not is_valid:
    for error in errors:
        print(f"Configuration error: {error}")

# Update configuration
config_manager.update_config(
    llm={"temperature": 0.5},
    processing={"recursive": False}
)

# Save configuration
config_manager.save_config(config, "updated_config.json")
```

### Direct Configuration

```python
from information_composer.llm_filter.config.settings import (
    AppConfig, LLMConfig, ProcessingConfig
)

# Create configuration objects
llm_config = LLMConfig(
    api_key="sk-your-api-key-here",
    model="qwen-plus",
    temperature=0.7,
    max_tokens=4096
)

processing_config = ProcessingConfig(
    input_dir="./input",
    output_dir="./output",
    file_pattern="*.md",
    recursive=True
)

app_config = AppConfig(
    llm=llm_config,
    processing=processing_config,
    log_level="INFO",
    debug=False
)
```

## 🎯 Module-Specific Configuration

### PDF Validator Configuration

```python
from information_composer.pdf.validator import PDFValidator

# Create validator with custom settings
validator = PDFValidator(
    verbose=True,           # Detailed output
    strict_mode=True,       # Strict validation
    check_encryption=True,  # Check for encrypted PDFs
    max_pages=1000         # Maximum pages to process
)
```

### Markdown Processor Configuration

```python
from information_composer.markdown import jsonify, markdownify

# Processing options
options = {
    "preserve_formatting": True,
    "extract_metadata": True,
    "clean_html": True,
    "remove_links": False
}

# Use with options
json_data = jsonify(content, **options)
markdown_content = markdownify(json_data, **options)
```

### PubMed Query Configuration

```python
from information_composer.pubmed.pubmed import query_pmid_by_date

# Query with custom settings
pmids = query_pmid_by_date(
    query="machine learning",
    email="your-email@example.com",
    start_date="2023/01/01",
    end_date="2023/12/31",
    batch_months=6,  # Process in 6-month batches
    delay=1.0        # 1 second delay between requests
)
```

## 🔄 Configuration Priority

Configuration is loaded in the following priority order (highest to lowest):

1. **Command Line Arguments** - Highest priority
2. **Environment Variables** - Second priority
3. **Configuration Files** - Third priority
4. **Default Values** - Lowest priority

## 📝 Configuration Examples

### Development Environment

```bash
# .env.development
DASHSCOPE_API_KEY=sk-dev-key
DEBUG=true
LOG_LEVEL=DEBUG
MAX_CONCURRENT_REQUESTS=2
ENABLE_CACHE=false
INPUT_DIR=./test_documents
OUTPUT_DIR=./test_output
```

### Production Environment

```bash
# .env.production
DASHSCOPE_API_KEY=sk-prod-key
DEBUG=false
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
ENABLE_CACHE=true
CACHE_TTL_HOURS=24
INPUT_DIR=/data/input
OUTPUT_DIR=/data/output
```

### Testing Environment

```bash
# .env.testing
DASHSCOPE_API_KEY=sk-test-key
DEBUG=true
LOG_LEVEL=DEBUG
MAX_CONCURRENT_REQUESTS=1
ENABLE_CACHE=false
INPUT_DIR=./tests/data
OUTPUT_DIR=./tests/output
```

## 🔍 Configuration Validation

### Validation Rules

#### Required Fields
- `llm.api_key`: Must be non-empty string
- `llm.model`: Must be non-empty string
- `processing.input_dir`: Must be valid directory path
- `processing.output_dir`: Must be valid directory path

#### Value Ranges
- `llm.temperature`: 0.0 <= value <= 2.0
- `llm.max_tokens`: value > 0
- `llm.max_concurrent_requests`: 1 <= value <= 100
- `llm.request_timeout`: 1 <= value <= 300
- `processing.max_file_size_mb`: 1 <= value <= 1000

#### File System Validation
- Input and output directories must be valid paths
- Cache directory must be writable
- File patterns must be valid glob patterns

### Validation Example

```python
from information_composer.llm_filter.config.settings import ConfigManager

config_manager = ConfigManager()
config = config_manager.load_config()

# Validate configuration
is_valid, errors = config_manager.validate_config()
if not is_valid:
    print("Configuration validation failed:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

## 🚨 Troubleshooting

### Common Issues

#### 1. API Key Not Set
```
Error: DashScope API key not configured
```

**Solution:**
```bash
export DASHSCOPE_API_KEY="your-api-key"
# or add to .env file
echo "DASHSCOPE_API_KEY=your-api-key" >> .env
```

#### 2. Invalid Configuration File
```
Error: Invalid YAML format
```

**Solution:**
- Check YAML syntax
- Use online YAML validator
- Compare with provided examples

#### 3. Permission Errors
```
Error: Permission denied
```

**Solution:**
- Check file permissions
- Ensure directories exist
- Run with appropriate user privileges

#### 4. Module Import Errors
```
Error: No module named 'information_composer'
```

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or install from PyPI
pip install information-composer
```

## 📚 Best Practices

### 1. Security
- Use environment variables for sensitive data
- Never commit API keys to version control
- Use different keys for different environments

### 2. Performance
- Adjust `MAX_CONCURRENT_REQUESTS` based on your system
- Enable caching for repeated operations
- Use appropriate file size limits

### 3. Maintenance
- Document your configuration choices
- Use version control for configuration files
- Regular validation of configuration

### 4. Development
- Use separate configurations for different environments
- Test configuration changes thoroughly
- Keep configuration files simple and readable

## 🔗 Related Documentation

- [Installation Guide](../installation.md) - Setup instructions
- [Quick Start](../quickstart.md) - Get started quickly
- [API Reference](../api/) - Detailed API documentation
- [Development Guide](../development/) - Development setup

---

**Configuration Complete!** You now have a comprehensive understanding of how to configure Information Composer for your specific needs.
