"""
admesh-weave-python - Backend SDK for Python

Enables AI platforms to consume recommendations from admesh-protocol
and weave them into LLM responses.

Example:
    ```python
    from admesh_weave import AdMeshClient

    client = AdMeshClient(api_key='your-api-key')

    # In your LLM handler
    result = await client.get_recommendations_for_weave(
        session_id='sess_123',
        message_id='msg_1',
        query=user_query
    )

    if result['found']:
        # Pass recommendations to LLM
        recommendations = result['recommendations']
    ```
"""

from .client import AdMeshClient
from .types import (
    AdMeshClientConfig,
    AdMeshIntegrationResult,
    AdMeshPromptContext,
    AdMeshPublishedRecommendations,
    AdMeshRecommendation,
    AdMeshSubscriptionOptions,
    AdMeshWaitOptions,
    AdMeshWaitResult,
    ProductLogo,
)

__version__ = "0.3.0"

__all__ = [
    # Client
    "AdMeshClient",
    # Types
    "AdMeshRecommendation",
    "AdMeshPublishedRecommendations",
    "AdMeshWaitResult",
    "AdMeshClientConfig",
    "AdMeshSubscriptionOptions",
    "AdMeshWaitOptions",
    "AdMeshIntegrationResult",
    "AdMeshPromptContext",
    "ProductLogo",
    # Version
    "__version__",
]

