# admesh-weave-python

[![PyPI version](https://badge.fury.io/py/admesh-weave-python.svg)](https://badge.fury.io/py/admesh-weave-python)
[![Python Versions](https://img.shields.io/pypi/pyversions/admesh-weave-python.svg)](https://pypi.org/project/admesh-weave-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python SDK for integrating AdMesh's **Weave Ad Format** into AI-powered applications. This lightweight backend client enables seamless integration of contextual product recommendations into LLM responses.

## Overview

The `admesh-weave-python` SDK provides a simple interface to:

- **Fetch contextual recommendations** based on user queries and conversation context
- **Integrate seamlessly** with your LLM application flow
- **Handle caching automatically** for optimal performance
- **Gracefully degrade** when recommendations aren't available

### How It Works

```
Your Application
    ↓
admesh-weave-python SDK
    ↓
AdMesh API
    ↓
Contextual Recommendations
    ↓
Integrate into LLM Response
```

### Key Features

- **Simple API**: Just two methods - async and sync versions
- **Fast Performance**: Intelligent caching for sub-100ms response times
- **Type-Safe**: Full type hints for excellent IDE support
- **Lightweight**: Minimal dependencies (httpx, typing-extensions)
- **Flexible**: Works with any Python async framework or synchronous code
- **Reliable**: Automatic retries and graceful error handling

## Installation

Install via pip:

```bash
pip install admesh-weave-python
```

Or with poetry:

```bash
poetry add admesh-weave-python
```

## Getting Started

### 1. Get Your API Key

Sign up at [useadmesh.com](https://useadmesh.com) to get your API key.

### 2. Install the SDK

```bash
pip install admesh-weave-python
```

### 3. Start Using

See the Quick Start section below for code examples.

## Quick Start

### Async Usage (Recommended)

```python
from admesh_weave import AdMeshClient

# Initialize the SDK with your API key
client = AdMeshClient(api_key="your-api-key")

# Get recommendations for Weave
result = await client.get_recommendations_for_weave(
    session_id="sess_123",
    message_id="msg_1",
    query="best laptops for programming",
    timeout_ms=30000
)

if result["found"]:
    print("Recommendations:", result["recommendations"])
    print("Query:", result["query"])
else:
    print("No recommendations found:", result.get("error"))
```

### Synchronous Usage

```python
from admesh_weave import AdMeshClient

client = AdMeshClient(api_key="your-api-key")

# Synchronous version
result = client.get_recommendations_for_weave_sync(
    session_id="sess_123",
    message_id="msg_1",
    query="best laptops for programming"
)

if result["found"]:
    print("Recommendations:", result["recommendations"])
```

## API Reference

### AdMeshClient

Main client for consuming recommendations from the AdMesh Protocol service.

#### Constructor

```python
client = AdMeshClient(
    api_key: str,              # Required: Your AdMesh API key
    api_base_url: str = None   # Optional: Custom API endpoint (defaults to production)
)
```

**Parameters:**
- `api_key` (required): Your AdMesh API key. Get one at [AdMesh Dashboard](https://useadmesh.com)
- `api_base_url` (optional): Override the default API endpoint. Useful for testing or enterprise deployments.

#### Methods

##### `get_recommendations_for_weave()`

Async method to fetch contextual product recommendations based on user query and conversation context.

```python
result = await client.get_recommendations_for_weave(
    session_id: str,        # Required: Session ID
    message_id: str,        # Required: Message ID for this conversation message
    query: str,             # Required: User query for contextual recommendations
    timeout_ms: int = None  # Optional: Max wait time (default: 12000ms)
)

# Returns:
{
    "found": bool,                           # Whether recommendations were found
    "recommendations": List[dict],           # Array of recommendations
    "query": str,                            # Original query
    "request_id": str,                       # Request ID
    "error": str                             # Error message if not found
}
```

**Example:**
```python
result = await client.get_recommendations_for_weave(
    session_id="sess_123",
    message_id="msg_1",
    query="best project management tools",
    timeout_ms=30000
)

if result["found"]:
    print("Recommendations found:", result["recommendations"])
    print("Original query:", result["query"])

    # Use recommendations in your application
    for rec in result["recommendations"]:
        print(f"- {rec['product_title']}")
        print(f"  {rec['weave_summary']}")
        print(f"  Click: {rec['click_url']}")
        print(f"  Exposure: {rec['exposure_url']}")
else:
    print("No recommendations available:", result.get("error"))
```

##### `get_recommendations_for_weave_sync()`

Synchronous version of `get_recommendations_for_weave()`. Same parameters and return type.

```python
result = client.get_recommendations_for_weave_sync(
    session_id="sess_123",
    message_id="msg_1",
    query="best laptops for programming"
)
```

## Configuration

### Environment Variables (Optional)

You can configure the SDK using environment variables:

```bash
# Required: Your AdMesh API key
ADMESH_API_KEY=your_api_key_here

# Optional: Custom API endpoint (for testing or enterprise deployments)
ADMESH_API_BASE_URL=https://your-custom-endpoint.com
```

Then initialize without passing parameters:

```python
import os
from admesh_weave import AdMeshClient

# API key from environment variable
client = AdMeshClient(api_key=os.getenv("ADMESH_API_KEY"))
```

### Direct Initialization

Or pass the API key directly:

```python
client = AdMeshClient(api_key="your-api-key")
```

### How It Works

- **API Endpoint:** Automatically configured to `https://api.useadmesh.com`
- **Timeouts & Retries:** Configured internally with sensible defaults

## Integration Guide

### Step 1: Initialize the SDK

```python
from admesh_weave import AdMeshClient

client = AdMeshClient(api_key="your-api-key")
```

### Step 2: Get Recommendations for Weave

```python
async def handle_user_query(session_id, message_id, user_query):
    # Fetch contextual recommendations based on user query
    result = await client.get_recommendations_for_weave(
        session_id=session_id,
        message_id=message_id,
        query=user_query,
        timeout_ms=30000  # 30 second timeout
    )

    if result["found"]:
        # Recommendations available (either from cache or freshly generated)
        print(f"Found {len(result['recommendations'])} recommendations")
        return result["recommendations"]

    # No recommendations available
    print("No recommendations:", result.get("error"))
    return None
```

### Step 3: Use Recommendations

```python
recommendations = await handle_user_query(session_id, message_id, query)

if recommendations:
    # Use recommendations in your application
    for rec in recommendations:
        print(f"Product: {rec['product_title']}")
        print(f"Summary: {rec['weave_summary']}")
        print(f"Click URL: {rec['click_url']}")
        print(f"Exposure URL: {rec['exposure_url']}")
        print(f"Trust Score: {rec['trust_score']}")
else:
    # Fallback behavior
    print("No recommendations available")
```

## Performance

- **Typical Response Time**: < 100ms for cached recommendations
- **Fresh Generation**: 1-3 seconds for new recommendations
- **Default Timeout**: 12 seconds (configurable per request)
- **Caching**: Intelligent caching for optimal performance
- **Fallback**: Graceful degradation if recommendations unavailable
- **Lightweight**: Minimal overhead with only essential dependencies

## Security Best Practices

### Protecting Your API Key

**Never commit API keys to version control:**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

**Use environment variables:**

```python
import os
from admesh_weave import AdMeshClient

# Load from environment
api_key = os.getenv("ADMESH_API_KEY")
if not api_key:
    raise ValueError("ADMESH_API_KEY environment variable not set")

client = AdMeshClient(api_key=api_key)
```

**Use a secrets manager in production:**

```python
# Example with AWS Secrets Manager
import boto3
from admesh_weave import AdMeshClient

def get_api_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='admesh-api-key')
    return response['SecretString']

client = AdMeshClient(api_key=get_api_key())
```

### API Key Rotation

- Rotate API keys periodically (every 90 days recommended)
- Use separate keys for development, staging, and production
- Revoke compromised keys immediately in your dashboard

## Error Handling

```python
result = await client.get_recommendations_for_weave(
    session_id=session_id,
    message_id=message_id,
    timeout_ms=10000
)

if not result["found"]:
    print("Failed to retrieve recommendations:", result.get("error"))

    # Fallback behavior
    return {
        "success": False,
        "recommendations": [],
        "error": result.get("error")
    }

# Use recommendations
return {
    "success": True,
    "recommendations": result["recommendations"],
    "query": result["query"]
}
```

## Troubleshooting

### No recommendations found

**Possible causes:**
1. API service is temporarily unavailable
2. Query doesn't match available products
3. Session ID or Message ID format issue
4. Timeout too short for recommendation generation
5. Invalid or expired API key

**Solution:**
```python
# Try with longer timeout
result = await client.get_recommendations_for_weave(
    session_id=session_id,
    message_id=message_id,
    query="specific product query",  # Provide a clear query
    timeout_ms=45000  # Increase timeout for generation
)

print("Found:", result["found"])
print("Error:", result.get("error"))
```

### Connection errors

**Possible causes:**
1. Network connectivity issues
2. Invalid API key
3. AdMesh API service is down

**Solution:**
```python
import os

# Check API key format
api_key = os.environ.get("ADMESH_API_KEY")
print(f"API key starts with: {api_key[:10] if api_key else 'None'}")

# Test the connection
try:
    result = await client.get_recommendations_for_weave(
        session_id="test",
        message_id="test",
        query="test query",
        timeout_ms=5000
    )
    print("Connection successful:", result["found"])
except Exception as error:
    print("Connection failed:", str(error))
```

### Slow response times

**Possible causes:**
1. First request for a query - recommendations are being generated
2. Complex query requiring more processing
3. Network latency

**Solution:**
```python
# First request may take 1-3 seconds - this is expected
result1 = await client.get_recommendations_for_weave(
    session_id=session_id,
    message_id=message_id,
    query=query,
    timeout_ms=30000
)
print("First call (generation):", result1["found"])

# Second call with same session_id + message_id should be fast (< 100ms)
result2 = await client.get_recommendations_for_weave(
    session_id=session_id,
    message_id=message_id,
    query=query,
    timeout_ms=5000  # Can use shorter timeout for cached results
)
print("Second call (cache hit):", result2["found"])
```

## Types

### AdMeshRecommendation

Individual recommendation object returned by the API.

```python
{
    "ad_id": str,                          # Unique ad identifier
    "product_id": str,                     # Product ID
    "recommendation_id": str,              # Recommendation identifier
    "product_title": str,                  # Product name
    "tail_summary": str,               # Tail text
    "weave_summary": str,                  # Weave format summary
    "exposure_url": str,                   # Exposure tracking URL
    "click_url": str,                      # Click tracking URL
    "product_logo": {"url": str},          # Product logo object
    "categories": List[str],               # Product categories
    "contextual_relevance_score": float,   # Contextual relevance score (0-100)
    "trust_score": float,                  # Trust score
    "model_used": str                      # Model used for generation
}
```

### AdMeshWaitResult

Result from `get_recommendations_for_weave()` method.

```python
{
    "found": bool,                         # Whether recommendations were found
    "recommendations": List[dict],         # Array of recommendations
    "query": str,                          # Original query
    "request_id": str,                     # Request ID
    "error": str                           # Error message if not found
}
```

### AdMeshClientConfig

Configuration for initializing the AdMeshClient.

```python
{
    "api_key": str,        # Required: Your AdMesh API key
    "api_base_url": str    # Optional: API base URL
}
```

## Architecture Details

### How It Works

1. **Your application** calls the SDK with user query and context
2. **SDK** sends request to AdMesh API
3. **AdMesh API** returns contextual recommendations
4. **SDK** formats recommendations for easy LLM integration
5. **Your application** integrates recommendations into LLM response

### Data Flow

```
Your Application
    ↓
admesh-weave-python SDK
    ↓
AdMesh API
    ↓
Contextual Recommendations
    ↓
Format for LLM Integration
    ↓
Return to Application
    ↓
Integrate into LLM Prompt
    ↓
LLM Response with Weave Ads
```

### Caching Strategy

The SDK benefits from intelligent server-side caching:

- **Fast Responses**: Cached recommendations return in < 100ms
- **Fresh Content**: New recommendations generated as needed (1-3s)
- **Automatic**: No cache management required on your end
- **Session-Aware**: Caching respects session and message context

### Design Principles

- **Lightweight**: Minimal dependencies, small footprint
- **Fast**: Optimized for low-latency responses
- **Simple**: Clean API with just two main methods
- **Reliable**: Robust error handling and automatic retries
- **Graceful Fallback**: Continues working even when recommendations unavailable
- **Configurable**: Flexible timeout and endpoint configuration
- **Type-Safe**: Full type hints for excellent IDE support and fewer bugs

## Requirements

- Python 3.8+
- httpx >= 0.23.0
- typing-extensions >= 4.5.0

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=admesh_weave
```

### Code Quality

```bash
# Format code
ruff format

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .

# Type check
mypy .
```

## Support

### Getting Help

- **Documentation**: Full documentation available in this README
- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/GouniManikumar12/admesh-weave-python/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/GouniManikumar12/admesh-weave-python/discussions)
- **API Key**: Get your API key at [AdMesh Dashboard](https://useadmesh.com)

### Common Questions

**Q: How do I get an API key?**
A: Sign up at [useadmesh.com](https://useadmesh.com) to get your API key.

**Q: What Python versions are supported?**
A: Python 3.8 and above.

**Q: Can I use this in production?**
A: Yes! The SDK is production-ready and actively maintained.

**Q: How are recommendations generated?**
A: AdMesh uses AI to match user queries with relevant products from our catalog.

**Q: Is there a rate limit?**
A: Rate limits depend on your plan. Check your dashboard for details.

## Contributing

We welcome contributions! Here's how you can help:

### Reporting Issues

Found a bug? Please open an issue with:
- Python version
- SDK version
- Minimal code to reproduce
- Expected vs actual behavior

### Suggesting Features

Have an idea? Open an issue with:
- Use case description
- Proposed API (if applicable)
- Why this would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run linting (`ruff check .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: https://pypi.org/project/admesh-weave-python/
- **GitHub**: https://github.com/GouniManikumar12/admesh-weave-python
- **AdMesh**: https://useadmesh.com
- **Documentation**: https://docs.useadmesh.com


