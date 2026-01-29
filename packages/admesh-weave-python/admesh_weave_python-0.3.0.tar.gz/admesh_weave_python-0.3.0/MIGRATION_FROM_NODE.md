# Migration Guide: Node.js to Python

This guide helps developers familiar with `@admesh/weave-node` (Node.js) migrate to `admesh-weave-python`.

## Package Names

| Node.js | Python |
|---------|--------|
| `@admesh/weave-node` | `admesh-weave-python` |

## Installation

**Node.js:**
```bash
npm install @admesh/weave-node
```

**Python:**
```bash
pip install admesh-weave-python
```

## Import Statements

**Node.js:**
```typescript
import { AdMeshClient } from '@admesh/weave-node';
```

**Python:**
```python
from admesh_weave import AdMeshClient
```

## Client Initialization

**Node.js:**
```typescript
const client = new AdMeshClient({
  apiKey: process.env.ADMESH_API_KEY
});
```

**Python:**
```python
import os

client = AdMeshClient(
    api_key=os.environ["ADMESH_API_KEY"]
)
```

## Method Names

Python uses `snake_case` instead of `camelCase`:

| Node.js | Python |
|---------|--------|
| `getRecommendationsForWeave()` | `get_recommendations_for_weave()` |
| N/A | `get_recommendations_for_weave_sync()` |

## Fetching Recommendations

### Node.js (Async)

```typescript
const result = await client.getRecommendationsForWeave({
  sessionId: 'sess_123',
  messageId: 'msg_1',
  query: 'best laptops',
  timeoutMs: 30000
});

if (result.found) {
  console.log(result.recommendations);
}
```

### Python (Async)

```python
result = await client.get_recommendations_for_weave(
    session_id='sess_123',
    message_id='msg_1',
    query='best laptops',
    timeout_ms=30000
)

if result["found"]:
    print(result["recommendations"])
```

### Python (Sync)

Python also provides a synchronous version:

```python
result = client.get_recommendations_for_weave_sync(
    session_id='sess_123',
    message_id='msg_1',
    query='best laptops'
)
```

## Parameter Names

All parameters use `snake_case` in Python:

| Node.js | Python |
|---------|--------|
| `sessionId` | `session_id` |
| `messageId` | `message_id` |
| `timeoutMs` | `timeout_ms` |
| `apiKey` | `api_key` |
| `apiBaseUrl` | `api_base_url` |

## Response Structure

The response structure is similar, but Python uses dictionaries instead of objects:

**Node.js:**
```typescript
interface AdMeshWaitResult {
  found: boolean;
  recommendations?: AdMeshRecommendation[];
  query?: string;
  requestId?: string;
  error?: string;
}
```

**Python:**
```python
# TypedDict
class AdMeshWaitResult(TypedDict, total=False):
    found: bool
    recommendations: Optional[List[AdMeshRecommendation]]
    query: Optional[str]
    request_id: Optional[str]
    error: Optional[str]
```

**Accessing fields:**

Node.js:
```typescript
result.found
result.recommendations
result.requestId
```

Python:
```python
result["found"]
result["recommendations"]
result["request_id"]
```

## Recommendation Object

Field names use `snake_case` in Python:

| Node.js | Python |
|---------|--------|
| `adId` | `ad_id` |
| `productId` | `product_id` |
| `recommendationId` | `recommendation_id` |
| `productTitle` | `product_title` |
| `citationSummary` | `tail_summary` |
| `weaveSummary` | `weave_summary` |
| `exposureUrl` | `exposure_url` |
| `clickUrl` | `click_url` |
| `productLogo` | `product_logo` |
| `contextualRelevanceScore` | `contextual_relevance_score` |
| `trustScore` | `trust_score` |
| `modelUsed` | `model_used` |

## Error Handling

**Node.js:**
```typescript
try {
  const result = await client.getRecommendationsForWeave({
    sessionId: 'sess_123',
    messageId: 'msg_1'
  });
  
  if (!result.found) {
    console.error('No recommendations:', result.error);
  }
} catch (error) {
  console.error('Error:', error.message);
}
```

**Python:**
```python
try:
    result = await client.get_recommendations_for_weave(
        session_id='sess_123',
        message_id='msg_1'
    )
    
    if not result["found"]:
        print(f"No recommendations: {result.get('error')}")
except Exception as error:
    print(f"Error: {str(error)}")
```

## Type Definitions

**Node.js (TypeScript):**
```typescript
import type {
  AdMeshRecommendation,
  AdMeshWaitResult,
  AdMeshClientConfig
} from '@admesh/weave-node';
```

**Python:**
```python
from admesh_weave import (
    AdMeshRecommendation,
    AdMeshWaitResult,
    AdMeshClientConfig
)
```

Note: Python SDK does not include backward compatibility aliases like `WeaveClient` or `WeaveRecommendation`. Use the `AdMesh*` naming convention directly.

## Environment Variables

Both versions support the same environment variables:

```bash
ADMESH_API_KEY=your_api_key_here
ADMESH_API_BASE_URL=https://api.useadmesh.com  # Optional
```

## Dependencies

**Node.js:**
- uuid: ^9.0.0

**Python:**
- httpx >= 0.23.0, < 1
- typing-extensions >= 4.5.0, < 5

## Complete Example Comparison

### Node.js

```typescript
import { AdMeshClient } from '@admesh/weave-node';

const client = new AdMeshClient({
  apiKey: process.env.ADMESH_API_KEY
});

async function main() {
  const result = await client.getRecommendationsForWeave({
    sessionId: 'sess_123',
    messageId: 'msg_1',
    query: 'best laptops',
    timeoutMs: 30000
  });

  if (result.found) {
    result.recommendations.forEach(rec => {
      console.log(`${rec.productTitle}: ${rec.clickUrl}`);
    });
  }
}

main();
```

### Python

```python
import asyncio
import os
from admesh_weave import AdMeshClient

client = AdMeshClient(api_key=os.environ["ADMESH_API_KEY"])

async def main():
    result = await client.get_recommendations_for_weave(
        session_id='sess_123',
        message_id='msg_1',
        query='best laptops',
        timeout_ms=30000
    )

    if result["found"]:
        for rec in result["recommendations"]:
            print(f"{rec['product_title']}: {rec['click_url']}")

asyncio.run(main())
```

## Key Differences Summary

1. **Naming Convention**: `camelCase` (Node.js) → `snake_case` (Python)
2. **Object Access**: `result.field` (Node.js) → `result["field"]` (Python)
3. **Async/Sync**: Node.js is async-only, Python provides both async and sync methods
4. **Type System**: TypeScript interfaces → Python TypedDict
5. **HTTP Client**: fetch API (Node.js) → httpx (Python)
6. **Package Manager**: npm (Node.js) → pip (Python)

## Architecture

Both versions share the same architecture:
- Direct HTTP POST to `/agent/recommend` endpoint
- Database-backed caching with 60-second TTL
- No Pub/Sub, no SSE
- Simple request/response pattern
- Graceful fallback if recommendations unavailable

## Performance

Both versions have similar performance characteristics:
- Cache hit: < 100ms
- Cache miss: 1-3 seconds
- Default timeout: 12 seconds (Node.js) / 12 seconds (Python)

