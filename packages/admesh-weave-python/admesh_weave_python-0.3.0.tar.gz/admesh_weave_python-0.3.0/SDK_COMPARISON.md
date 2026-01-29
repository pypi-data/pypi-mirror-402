# SDK Comparison: Node.js vs Python

Quick reference comparing `@admesh/weave-node` and `admesh-weave-python`.

## Installation

| Feature | Node.js | Python |
|---------|---------|--------|
| Package Manager | npm | pip |
| Install Command | `npm install @admesh/weave-node` | `pip install admesh-weave-python` |
| Package Name | `@admesh/weave-node` | `admesh-weave-python` |
| Version | 0.2.9 | 0.1.0 |

## Import

| Feature | Node.js | Python |
|---------|---------|--------|
| Import Statement | `import { AdMeshClient } from '@admesh/weave-node'` | `from admesh_weave import AdMeshClient` |
| Module Name | `@admesh/weave-node` | `admesh_weave` |

## Client Initialization

| Feature | Node.js | Python |
|---------|---------|--------|
| Constructor | `new AdMeshClient({ apiKey })` | `AdMeshClient(api_key=...)` |
| API Key Parameter | `apiKey` | `api_key` |
| Base URL Parameter | `apiBaseUrl` | `api_base_url` |

## Methods

| Feature | Node.js | Python Async | Python Sync |
|---------|---------|--------------|-------------|
| Method Name | `getRecommendationsForWeave()` | `get_recommendations_for_weave()` | `get_recommendations_for_weave_sync()` |
| Async/Await | Yes | Yes | No |
| Return Type | `Promise<AdMeshWaitResult>` | `AdMeshWaitResult` | `AdMeshWaitResult` |

## Parameters

| Parameter | Node.js | Python |
|-----------|---------|--------|
| Session ID | `sessionId` | `session_id` |
| Message ID | `messageId` | `message_id` |
| Query | `query` | `query` |
| Timeout | `timeoutMs` | `timeout_ms` |

## Response Access

| Feature | Node.js | Python |
|---------|---------|--------|
| Check if found | `result.found` | `result["found"]` |
| Get recommendations | `result.recommendations` | `result["recommendations"]` |
| Get query | `result.query` | `result["query"]` |
| Get request ID | `result.requestId` | `result["request_id"]` |
| Get error | `result.error` | `result.get("error")` |

## Recommendation Fields

| Field | Node.js | Python |
|-------|---------|--------|
| Ad ID | `rec.adId` | `rec["ad_id"]` |
| Product ID | `rec.productId` | `rec["product_id"]` |
| Recommendation ID | `rec.recommendationId` | `rec["recommendation_id"]` |
| Product Title | `rec.productTitle` | `rec["product_title"]` |
| Tail Summary | `rec.citationSummary` | `rec["tail_summary"]` |
| Weave Summary | `rec.weaveSummary` | `rec["weave_summary"]` |
| Exposure URL | `rec.exposureUrl` | `rec["exposure_url"]` |
| Click URL | `rec.clickUrl` | `rec["click_url"]` |
| Product Logo | `rec.productLogo.url` | `rec["product_logo"]["url"]` |
| Categories | `rec.categories` | `rec["categories"]` |
| Relevance Score | `rec.contextualRelevanceScore` | `rec["contextual_relevance_score"]` |
| Trust Score | `rec.trustScore` | `rec["trust_score"]` |
| Model Used | `rec.modelUsed` | `rec["model_used"]` |

## Type System

| Feature | Node.js | Python |
|---------|---------|--------|
| Type System | TypeScript | TypedDict |
| Type Definitions | Interfaces | TypedDict classes |
| Type Checking | tsc | mypy |
| Runtime Types | No | Yes (TypedDict) |

## Dependencies

| Feature | Node.js | Python |
|---------|---------|--------|
| HTTP Client | fetch (built-in) | httpx |
| UUID | uuid package | N/A |
| Type Extensions | N/A | typing-extensions |
| Total Dependencies | 1 | 2 |

## Code Examples

### Async Usage

**Node.js:**
```typescript
const result = await client.getRecommendationsForWeave({
  sessionId: 'sess_123',
  messageId: 'msg_1',
  query: 'best laptops'
});

if (result.found) {
  result.recommendations.forEach(rec => {
    console.log(rec.productTitle);
  });
}
```

**Python:**
```python
result = await client.get_recommendations_for_weave(
    session_id='sess_123',
    message_id='msg_1',
    query='best laptops'
)

if result["found"]:
    for rec in result["recommendations"]:
        print(rec["product_title"])
```

### Sync Usage

**Node.js:**
```typescript
// Not available - async only
```

**Python:**
```python
result = client.get_recommendations_for_weave_sync(
    session_id='sess_123',
    message_id='msg_1',
    query='best laptops'
)
```

## Architecture

| Feature | Node.js | Python |
|---------|---------|--------|
| HTTP Method | POST | POST |
| Endpoint | `/agent/recommend` | `/agent/recommend` |
| Caching | Database-backed | Database-backed |
| Pub/Sub | No | No |
| SSE | No | No |
| Source Identifier | `admesh_weave_node` | `admesh_weave_python` |

## Performance

| Metric | Node.js | Python |
|--------|---------|--------|
| Cache Hit | < 100ms | < 100ms |
| Cache Miss | 1-3s | 1-3s |
| Default Timeout | 12s | 12s |
| TTL | 60s | 60s |

## Development

| Feature | Node.js | Python |
|---------|---------|--------|
| Build Tool | tsc | hatchling |
| Linter | eslint | ruff |
| Formatter | prettier | ruff/black |
| Type Checker | tsc | mypy |
| Test Framework | vitest | pytest |
| Package Config | package.json | pyproject.toml |

## File Structure

| Component | Node.js | Python |
|-----------|---------|--------|
| Source Directory | `src/` | `src/admesh_weave/` |
| Main Client | `src/AdMeshClient.ts` | `src/admesh_weave/client.py` |
| Types | `src/types.ts` | `src/admesh_weave/types.py` |
| Entry Point | `src/index.ts` | `src/admesh_weave/__init__.py` |
| Tests | `tests/` | `tests/` |
| Examples | N/A | `examples/` |
| Build Output | `dist/` | `dist/` |

## Documentation

| Document | Node.js | Python |
|----------|---------|--------|
| README | ✓ | ✓ |
| CHANGELOG | ✓ | ✓ |
| LICENSE | ✓ | ✓ |
| Quick Start | ✗ | ✓ |
| Migration Guide | ✗ | ✓ (from Node.js) |
| Contributing | ✗ | ✓ |
| Implementation Summary | ✗ | ✓ |

## Key Differences

1. **Naming Convention**: camelCase (Node.js) vs snake_case (Python)
2. **Object Access**: Dot notation (Node.js) vs bracket notation (Python)
3. **Sync Support**: Async only (Node.js) vs both async and sync (Python)
4. **Type System**: TypeScript interfaces vs Python TypedDict
5. **HTTP Client**: fetch vs httpx
6. **Package Structure**: Flat (Node.js) vs src layout (Python)

## Similarities

1. **Architecture**: Same database-backed caching
2. **API Endpoint**: Both use `/agent/recommend`
3. **Response Format**: Same recommendation schema
4. **Performance**: Similar latency characteristics
5. **Configuration**: Same environment variables
6. **Error Handling**: Similar patterns

## Recommendation

- **Use Node.js SDK** if you're building a Node.js/TypeScript application
- **Use Python SDK** if you're building a Python application
- Both SDKs provide the same functionality and performance
- Choose based on your application's primary language

