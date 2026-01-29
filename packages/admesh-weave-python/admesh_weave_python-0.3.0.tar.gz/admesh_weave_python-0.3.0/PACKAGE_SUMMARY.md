# Package Summary: admesh-weave-python

## Overview

`admesh-weave-python` is a lightweight Python SDK for fetching recommendations from the AdMesh Protocol service. It mirrors the functionality of `@admesh/weave-node` (v0.2.9) while following Python best practices and conventions.

## Key Features

✅ **Database-backed caching** - Fast retrieval with < 100ms cache hits  
✅ **Async & Sync support** - Both async and synchronous methods available  
✅ **Type-safe** - Full type hints with TypedDict  
✅ **Minimal dependencies** - Only httpx and typing-extensions  
✅ **Python 3.8+** - Supports Python 3.8 through 3.12  
✅ **Production-ready** - Error handling, validation, and testing  
✅ **Well-documented** - Comprehensive docs and examples  

## Installation

```bash
pip install admesh-weave-python
```

## Quick Start

```python
from admesh_weave import AdMeshClient

# Initialize
client = AdMeshClient(api_key="your-api-key")

# Async usage
result = await client.get_recommendations_for_weave(
    session_id="sess_123",
    message_id="msg_1",
    query="best laptops for programming"
)

# Sync usage
result = client.get_recommendations_for_weave_sync(
    session_id="sess_123",
    message_id="msg_1",
    query="best laptops for programming"
)

if result["found"]:
    for rec in result["recommendations"]:
        print(f"{rec['product_title']}: {rec['click_url']}")
```

## Package Structure

```
admesh-weave-python/
├── src/admesh_weave/
│   ├── __init__.py          # Package exports
│   ├── client.py            # AdMeshClient class
│   ├── types.py             # Type definitions
│   └── py.typed             # Type marker
├── examples/
│   └── basic_usage.py       # Usage examples
├── tests/
│   └── test_client.py       # Unit tests
└── Documentation (8 files)
```

## Core API

### AdMeshClient

```python
client = AdMeshClient(
    api_key: str,              # Required
    api_base_url: str = None   # Optional
)
```

### Methods

**Async:**
```python
result = await client.get_recommendations_for_weave(
    session_id: str,
    message_id: str,
    query: str = None,
    timeout_ms: int = None
) -> AdMeshWaitResult
```

**Sync:**
```python
result = client.get_recommendations_for_weave_sync(
    session_id: str,
    message_id: str,
    query: str = None,
    timeout_ms: int = None
) -> AdMeshWaitResult
```

## Type Definitions

- `AdMeshRecommendation` - Individual recommendation (13 fields)
- `AdMeshWaitResult` - Method return type
- `AdMeshClientConfig` - Client configuration
- `AdMeshSubscriptionOptions` - Subscription options
- `ProductLogo` - Product logo structure

## Dependencies

**Runtime:**
- httpx >= 0.23.0, < 1
- typing-extensions >= 4.5.0, < 5

**Development:**
- pytest >= 7.0.0
- pytest-asyncio >= 0.21.0
- ruff >= 0.1.0
- mypy >= 1.0.0
- black >= 23.0.0

## Documentation

1. **README.md** - Full documentation with API reference
2. **QUICK_START.md** - 5-minute quick start guide
3. **MIGRATION_FROM_NODE.md** - Node.js to Python migration
4. **IMPLEMENTATION_SUMMARY.md** - Technical details
5. **SDK_COMPARISON.md** - Node.js vs Python comparison
6. **CHANGELOG.md** - Version history
7. **CONTRIBUTING.md** - Contribution guidelines
8. **LICENSE** - MIT License

## Architecture

```
Python Application
    ↓
admesh-weave-python SDK
    ↓ (HTTP POST)
admesh-protocol /agent/recommend
    ↓
Database Cache (session_id + message_id)
    ↓
Cache Hit? → Return (< 100ms)
    ↓
Generate → Save → Return (1-3s)
```

## Performance

- **Cache Hit**: < 100ms
- **Cache Miss**: 1-3 seconds
- **Default Timeout**: 12 seconds
- **TTL**: 60 seconds

## Python Conventions

- **Naming**: `snake_case` for functions/variables
- **Classes**: `PascalCase`
- **Type Hints**: Full coverage with TypedDict
- **Package Layout**: src layout (PEP 420)
- **Configuration**: pyproject.toml (PEP 518)

## Differences from Node.js SDK

1. **Naming**: `snake_case` vs `camelCase`
2. **Object Access**: `result["field"]` vs `result.field`
3. **Async/Sync**: Both available vs async-only
4. **Type System**: TypedDict vs TypeScript interfaces
5. **HTTP Client**: httpx vs fetch
6. **No Backward Compatibility**: No `WeaveClient` aliases

## Version

Current version: **0.1.0**

## License

MIT License

## Repository

- GitHub: https://github.com/GouniManikumar12/admesh-weave-python
- Issues: https://github.com/GouniManikumar12/admesh-weave-python/issues

## Support

- Email: mani@useadmesh.com
- Documentation: See README.md
- Examples: See examples/basic_usage.py

## Next Steps

1. Install the package: `pip install admesh-weave-python`
2. Read the [Quick Start Guide](QUICK_START.md)
3. Check out [examples](examples/basic_usage.py)
4. Review the [API Reference](README.md#api-reference)
5. See [Migration Guide](MIGRATION_FROM_NODE.md) if coming from Node.js

---

**Status**: ✅ Production Ready  
**Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12  
**Maintained by**: AdMesh Team

