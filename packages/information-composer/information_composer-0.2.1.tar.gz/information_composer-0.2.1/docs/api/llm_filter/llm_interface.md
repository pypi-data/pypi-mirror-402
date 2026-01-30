# LLM Interface API

The LLM interface module provides a unified abstraction for different Large Language Model (LLM) providers, enabling easy switching between different models and services.

## Core Classes

### `MessageRole` Enum

Enumeration for message roles in chat conversations.

**Values:**
- `SYSTEM` - System messages that set context or instructions
- `USER` - User messages in the conversation
- `ASSISTANT` - Assistant/LLM response messages

**Example:**
```python
from information_composer.llm_filter.llm.llm_interface import MessageRole

role = MessageRole.USER
print(role.value)  # "user"
```

### `ChatMessage` Dataclass

Represents a single message in a chat conversation.

**Attributes:**
- `role` (MessageRole): The role of the message sender
- `content` (str): The text content of the message
- `metadata` (Optional[Dict[str, Any]]): Additional metadata for the message

**Example:**
```python
from information_composer.llm_filter.llm.llm_interface import ChatMessage, MessageRole

message = ChatMessage(
    role=MessageRole.USER,
    content="Hello, how are you?",
    metadata={"timestamp": "2023-01-01T00:00:00Z"}
)
```

### `LLMResponse` Dataclass

Represents the response from an LLM.

**Attributes:**
- `content` (str): The generated text content
- `metadata` (Optional[Dict[str, Any]]): Additional response metadata
- `usage` (Optional[Dict[str, Any]]): Token usage information
- `model` (Optional[str]): The model that generated the response

**Example:**
```python
from information_composer.llm_filter.llm.llm_interface import LLMResponse

response = LLMResponse(
    content="I'm doing well, thank you!",
    metadata={"model": "qwen-plus"},
    usage={"prompt_tokens": 10, "completion_tokens": 8},
    model="qwen-plus"
)
```

## Abstract Base Class

### `LLMInterface` Abstract Class

Base class for all LLM implementations.

**Constructor:**
```python
def __init__(self, model: str, **kwargs: Any) -> None
```

**Parameters:**
- `model` (str): The model name or identifier
- `**kwargs`: Additional configuration parameters

**Attributes:**
- `model` (str): The model name
- `config` (Dict[str, Any]): Configuration dictionary

### Abstract Methods

#### `chat(messages: List[ChatMessage], **kwargs: Any) -> LLMResponse`

Synchronous chat method for sending messages to the LLM.

**Parameters:**
- `messages` (List[ChatMessage]): List of messages in the conversation
- `**kwargs`: Additional parameters specific to the implementation

**Returns:**
- `LLMResponse`: The LLM's response

**Raises:**
- `NotImplementedError`: If not implemented by subclass

#### `achat(messages: List[ChatMessage], **kwargs: Any) -> LLMResponse`

Asynchronous chat method for sending messages to the LLM.

**Parameters:**
- `messages` (List[ChatMessage]): List of messages in the conversation
- `**kwargs`: Additional parameters specific to the implementation

**Returns:**
- `LLMResponse`: The LLM's response

**Raises:**
- `NotImplementedError`: If not implemented by subclass

#### `complete(prompt: str, **kwargs: Any) -> LLMResponse`

Complete a text prompt (for completion-based models).

**Parameters:**
- `prompt` (str): The text prompt to complete
- `**kwargs`: Additional parameters

**Returns:**
- `LLMResponse`: The completed text

**Raises:**
- `NotImplementedError`: If not implemented by subclass

#### `extract_structured(prompt: str, schema: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]`

Extract structured data from text using a schema.

**Parameters:**
- `prompt` (str): The text to extract from
- `schema` (Dict[str, Any]): The JSON schema for extraction
- `**kwargs`: Additional parameters

**Returns:**
- `Dict[str, Any]`: The extracted structured data

**Raises:**
- `NotImplementedError`: If not implemented by subclass

### Utility Methods

#### `get_model_info() -> Dict[str, Any]`

Get information about the current model and configuration.

**Returns:**
- Dictionary containing model information

**Example:**
```python
info = llm.get_model_info()
# Returns: {
#     "model": "qwen-plus",
#     "config": {"temperature": 0.7}
# }
```

#### `validate_config(required_keys: List[str]) -> bool`

Validate that the configuration contains required keys.

**Parameters:**
- `required_keys` (List[str]): List of required configuration keys

**Returns:**
- `True` if all required keys are present, `False` otherwise

#### `get_config_value(key: str, default: Any = None) -> Any`

Get a configuration value with optional default.

**Parameters:**
- `key` (str): The configuration key to retrieve
- `default` (Any): Default value if key is not found

**Returns:**
- The configuration value or default

## Factory Class

### `LLMFactory` Class

Factory class for creating LLM instances.

#### `create(provider: str, model: str, **kwargs: Any) -> LLMInterface`

Create an LLM instance for the specified provider.

**Parameters:**
- `provider` (str): The LLM provider name (e.g., "dashscope")
- `model` (str): The model name
- `**kwargs`: Additional configuration parameters

**Returns:**
- `LLMInterface`: An instance of the specified LLM provider

**Raises:**
- `ValueError`: If the provider is not supported

**Example:**
```python
from information_composer.llm_filter.llm.llm_interface import LLMFactory

# Create DashScope client
llm = LLMFactory.create(
    provider="dashscope",
    model="qwen-plus",
    api_key="your-api-key",
    temperature=0.7
)
```

#### `list_providers() -> List[str]`

List all available LLM providers.

**Returns:**
- List of provider names

**Example:**
```python
providers = LLMFactory.list_providers()
print(providers)  # ["dashscope"]
```

## Usage Examples

### Basic Chat Usage

```python
from information_composer.llm_filter.llm.llm_interface import (
    ChatMessage, LLMFactory, MessageRole
)

# Create LLM instance
llm = LLMFactory.create("dashscope", "qwen-plus", api_key="your-key")

# Prepare messages
messages = [
    ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    ChatMessage(role=MessageRole.USER, content="What is the capital of France?")
]

# Get response
response = llm.chat(messages)
print(response.content)  # "The capital of France is Paris."
```

### Async Usage

```python
import asyncio

async def async_chat():
    llm = LLMFactory.create("dashscope", "qwen-plus", api_key="your-key")
    
    messages = [
        ChatMessage(role=MessageRole.USER, content="Hello!")
    ]
    
    response = await llm.achat(messages)
    return response.content

# Run async function
result = asyncio.run(async_chat())
```

### Text Completion

```python
llm = LLMFactory.create("dashscope", "qwen-plus", api_key="your-key")

prompt = "The future of artificial intelligence is"
response = llm.complete(prompt)
print(response.content)
```

### Structured Data Extraction

```python
llm = LLMFactory.create("dashscope", "qwen-plus", api_key="your-key")

text = "John is 25 years old and works as a software engineer."
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "occupation": {"type": "string"}
    }
}

result = llm.extract_structured(text, schema)
print(result)  # {"name": "John", "age": 25, "occupation": "software engineer"}
```

### Configuration Management

```python
llm = LLMFactory.create(
    "dashscope",
    "qwen-plus",
    api_key="your-key",
    temperature=0.7,
    max_tokens=1000
)

# Get model information
info = llm.get_model_info()
print(f"Model: {info['model']}")
print(f"Config: {info['config']}")

# Validate configuration
is_valid = llm.validate_config(["api_key", "temperature"])
print(f"Config valid: {is_valid}")

# Get specific config value
temp = llm.get_config_value("temperature", 0.5)
print(f"Temperature: {temp}")
```

## Error Handling

### Common Exceptions

1. **NotImplementedError**: When calling abstract methods on base class
2. **ValueError**: When using unsupported providers
3. **ImportError**: When required dependencies are missing
4. **RuntimeError**: When API calls fail

### Error Handling Example

```python
try:
    llm = LLMFactory.create("dashscope", "qwen-plus", api_key="invalid-key")
    response = llm.chat(messages)
except ValueError as e:
    print(f"Configuration error: {e}")
except RuntimeError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use Factory Pattern**: Always use `LLMFactory.create()` to create instances
2. **Handle Errors**: Implement proper error handling for API calls
3. **Validate Configuration**: Check required configuration before use
4. **Use Async When Appropriate**: Use `achat()` for better performance in async contexts
5. **Manage Resources**: Properly close connections when done
6. **Monitor Usage**: Track token usage and costs

## Extending the Interface

To add a new LLM provider:

1. Create a new class inheriting from `LLMInterface`
2. Implement all abstract methods
3. Register the provider with `LLMFactory`

```python
class MyLLMProvider(LLMInterface):
    def chat(self, messages, **kwargs):
        # Implementation
        pass
    
    def achat(self, messages, **kwargs):
        # Implementation
        pass
    
    def complete(self, prompt, **kwargs):
        # Implementation
        pass
    
    def extract_structured(self, prompt, schema, **kwargs):
        # Implementation
        pass

# Register the provider
LLMFactory.register_provider("my_provider", MyLLMProvider)
```
