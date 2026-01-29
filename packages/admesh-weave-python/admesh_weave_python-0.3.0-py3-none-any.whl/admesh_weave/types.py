"""
AdMesh Weave Python SDK Types

Type definitions for the AdMesh Weave Python SDK.
"""

from typing import Any, Dict, List, Optional, TypedDict, Literal


class ProductLogo(TypedDict):
    """Product logo information."""

    url: str


class CreativeInput(TypedDict, total=False):
    """Creative input structure for all ad formats."""
    
    brand_name: str
    product_name: str
    product_id: Optional[str]
    short_description: str
    long_description: str
    context_snippet: Optional[str]
    value_props: List[str]
    cta_label: Optional[str]
    cta_url: str
    assets: Dict[str, Any]  # { logo_url, image_urls, primary_image_url }
    keywords: Optional[List[str]]
    categories: Optional[List[str]]
    allowed_formats: Optional[List[str]]
    preferred_format: Optional[str]
    fallback_formats: Optional[List[str]]
    offer_summary: Optional[str]  # Factual offer summary displayed below short_description


class AdMeshRecommendation(TypedDict, total=False):
    """
    Individual recommendation object returned by /aip/context endpoint.
    """

    recommendation_id: str
    session_id: str
    agent_id: str
    ad_id: str
    product_id: str
    brand_id: str
    realtime_offer_id: Optional[str]
    title: str
    url: str
    admesh_link: str
    exposure_url: str
    click_url: str
    contextual_relevance_score: float
    engagement_status: str
    payout_model: str  # "CPA" | "CPC" | "CPX"
    payout_amount_usd: float
    cpx_value: int
    cpc_value: int
    cpa_value: int
    creative_input: CreativeInput
    timestamps: Dict[str, Optional[str]]
    created_at: str
    
    # Legacy compatibility fields
    product_title: Optional[str]
    tail_summary: Optional[str]
    weave_summary: Optional[str]
    product_logo: Optional[ProductLogo]
    categories: Optional[List[str]]


class AdMeshPublishedRecommendations(TypedDict):
    """Published recommendations with metadata."""

    request_id: str
    session_id: str
    message_id: str
    query: str
    recommendations: List[AdMeshRecommendation]
    published_at: str
    ttl_ms: int


class AdMeshWaitOptions(TypedDict, total=False):
    """Options for waiting for recommendations."""

    timeout_ms: Optional[int]
    poll_interval_ms: Optional[int]


class AdMeshWaitResult(TypedDict, total=False):
    """Result from get_recommendations_for_weave method."""

    found: bool
    recommendations: Optional[List[AdMeshRecommendation]]
    query: Optional[str]
    request_id: Optional[str]
    error: Optional[str]


class AdMeshClientConfig(TypedDict, total=False):
    """Configuration for initializing the AdMeshClient."""

    api_key: str
    api_base_url: Optional[str]


class AdMeshSubscriptionOptions(TypedDict, total=False):
    """Options for getting recommendations."""

    session_id: str  # Required: Must be provided by frontend
    message_id: str  # Required: Unique identifier for this message (must be provided by frontend)
    query: str  # Required: User query for contextual recommendations
    platform_id: Optional[str]
    platform_surface: Optional[str]
    model: Optional[str]
    messages: Optional[List[Dict[str, str]]]  # Messages can have optional 'id' field
    locale: Optional[str]
    geo: Optional[str]
    user_id: Optional[str]
    latency_budget_ms: Optional[int]


class AdMeshIntegrationResult(TypedDict, total=False):
    """Result from integrate_recommendations method."""

    success: bool
    recommendations: List[AdMeshRecommendation]
    query: str
    weave_text: str
    error: Optional[str]


class AdMeshPromptContext(TypedDict, total=False):
    """Context for formatting recommendations in prompts."""

    query: str
    recommendations: List[AdMeshRecommendation]
    format: Optional[Literal["markdown", "json", "text"]]

