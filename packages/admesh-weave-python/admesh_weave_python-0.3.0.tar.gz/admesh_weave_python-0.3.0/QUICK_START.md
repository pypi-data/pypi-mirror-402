# Quick Start Guide

Get started with admesh-weave-python in 5 minutes.

## Installation

```bash
pip install admesh-weave-python
```

## Basic Usage

### 1. Initialize the Client

```python
from admesh_weave import AdMeshClient

client = AdMeshClient(api_key="your-api-key")
```

### 2. Fetch Recommendations (Async)

```python
import asyncio

async def get_recommendations():
    result = await client.get_recommendations_for_weave(
        session_id="sess_123",
        message_id="msg_1",
        query="best laptops for programming"
    )
    
    if result["found"]:
        for rec in result["recommendations"]:
            print(f"- {rec['product_title']}: {rec['click_url']}")
    else:
        print("No recommendations found")

# Run the async function
asyncio.run(get_recommendations())
```

### 3. Fetch Recommendations (Sync)

```python
result = client.get_recommendations_for_weave_sync(
    session_id="sess_123",
    message_id="msg_1",
    query="best laptops for programming"
)

if result["found"]:
    for rec in result["recommendations"]:
        print(f"- {rec['product_title']}: {rec['click_url']}")
```

## Environment Variables

Create a `.env` file:

```bash
ADMESH_API_KEY=your_api_key_here
```

Load it in your code:

```python
import os
from dotenv import load_dotenv
from admesh_weave import AdMeshClient

load_dotenv()

client = AdMeshClient(api_key=os.environ["ADMESH_API_KEY"])
```

## Complete Example

```python
import asyncio
import os
from admesh_weave import AdMeshClient

async def main():
    # Initialize client
    client = AdMeshClient(api_key=os.environ["ADMESH_API_KEY"])
    
    # Get recommendations
    result = await client.get_recommendations_for_weave(
        session_id="sess_example",
        message_id="msg_1",
        query="best project management tools",
        timeout_ms=30000
    )
    
    # Process results
    if result["found"]:
        print(f"Found {len(result['recommendations'])} recommendations:")
        
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"\n{i}. {rec['product_title']}")
            print(f"   Summary: {rec['weave_summary']}")
            print(f"   Trust Score: {rec['trust_score']}")
            print(f"   Click URL: {rec['click_url']}")
    else:
        print(f"No recommendations: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [examples](examples/)
- Learn about [type definitions](src/admesh_weave/types.py)
- See [API reference](README.md#api-reference)

## Common Issues

### Import Error

If you get an import error, make sure the package is installed:

```bash
pip install admesh-weave-python
```

### Timeout Error

If requests timeout, increase the timeout:

```python
result = await client.get_recommendations_for_weave(
    session_id="sess_123",
    message_id="msg_1",
    query="your query",
    timeout_ms=45000  # 45 seconds
)
```

### No Recommendations Found

This is normal if:
- The query doesn't match any products
- It's the first request (cache miss)
- The admesh-protocol service is not running

## Support

- GitHub Issues: https://github.com/GouniManikumar12/admesh-weave-python/issues
- Email: mani@useadmesh.com

