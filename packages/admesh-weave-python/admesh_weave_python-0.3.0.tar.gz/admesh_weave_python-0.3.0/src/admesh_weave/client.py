"""
AdMesh Client - Backend SDK for Python

Uses the /aip/context endpoint for auction-based recommendations.
"""

import os
import time
import random
import string
from typing import Any, Dict, List, Optional

import httpx

from .types import AdMeshRecommendation, AdMeshWaitResult


class AdMeshClient:
    """
    AdMesh Client for consuming recommendations from the AdMesh Protocol service.

    This client provides a simple interface to fetch recommendations by calling
    the /aip/context endpoint which runs a full auction pipeline.

    Example:
        ```python
        from admesh_weave import AdMeshClient

        client = AdMeshClient(api_key="your-api-key")

        # In your LLM handler
        result = await client.get_recommendations_for_weave(
            session_id="sess_123",
            query=user_query
        )

        if result["found"]:
            # Pass recommendation to LLM
            recommendation = result["recommendations"][0]
        ```
    """

    def __init__(self, api_key: str, api_base_url: Optional[str] = None) -> None:
        """
        Initialize the AdMesh Client.

        Args:
            api_key: Your AdMesh API key (required)
            api_base_url: Optional API base URL. Defaults to environment variable
                         ADMESH_API_BASE_URL or 'https://api.useadmesh.com'

        Raises:
            ValueError: If api_key is not provided
        """
        if not api_key:
            raise ValueError("AdMeshClient: api_key is required")

        self.api_key = api_key

        # Set API base URL with priority: config > environment variable > production default
        self.api_base_url = (
            api_base_url or os.environ.get("ADMESH_API_BASE_URL") or "https://api.useadmesh.com"
        )

    async def get_recommendations_for_weave(
        self,
        session_id: str,
        message_id: str,
        query: str,
        platform_id: Optional[str] = None,
        platform_surface: Optional[str] = None,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        locale: Optional[str] = None,
        geo: Optional[str] = None,
        user_id: Optional[str] = None,
        latency_budget_ms: Optional[int] = None,
        timeout_ms: Optional[int] = None,
    ) -> AdMeshWaitResult:
        """
        Get recommendation by calling /aip/context endpoint.

        The backend runs a full auction pipeline and returns a single recommendation.

        Args:
            session_id: Session ID (required, must be provided by frontend)
            message_id: Message ID (required, must be provided by frontend)
            query: User query (required for contextual recommendations)
            platform_id: Platform identifier (default: 'admesh_weave_python')
            platform_surface: Platform surface (default: 'web')
            model: Model name
            messages: Conversation messages
            locale: Locale (default: 'en-US')
            geo: Geographic location
            user_id: User ID
            latency_budget_ms: Latency budget in milliseconds (used to calculate HTTP timeout)
            timeout_ms: Max wait time in milliseconds (default: calculated from latency_budget_ms or 30000ms)

        Returns:
            AdMeshWaitResult dictionary with:
                - found: Whether recommendation was found
                - recommendations: List with single recommendation (if found)
                - query: Original query
                - request_id: Recommendation ID
                - error: Error message (if not found)

        Example:
            ```python
            result = await client.get_recommendations_for_weave(
                session_id="sess_123",
                message_id="msg_123",
                query="best laptops for programming",
                latency_budget_ms=10000
            )

            if result["found"]:
                print("Recommendation:", result["recommendations"][0])
            else:
                print("No recommendation found:", result.get("error"))
            ```
        """
        # Validate required parameters
        if not query or not query.strip():
            raise ValueError("AdMeshClient.get_recommendations_for_weave: 'query' parameter is required and cannot be empty")
        
        if not session_id:
            raise ValueError("AdMeshClient.get_recommendations_for_weave: 'session_id' parameter is required and must be provided by frontend")
        
        if not message_id:
            raise ValueError("AdMeshClient.get_recommendations_for_weave: 'message_id' parameter is required and must be provided by frontend")

        # Calculate HTTP timeout from latency_budget_ms (use 3x latency budget or default 30s)
        # This ensures the HTTP request doesn't timeout before the auction completes
        if latency_budget_ms:
            http_timeout_ms = max(latency_budget_ms * 3, 30000)  # At least 30s, or 3x latency budget
        else:
            http_timeout_ms = timeout_ms or 30000  # Default 30s if no latency budget specified
        timeout_seconds = http_timeout_ms / 1000.0

        # Use messageId directly from parameter (must be provided by frontend)
        message_id_val = message_id

        # Generate context_id for UCP structure
        context_id = f"ctx_{int(time.time() * 1000)}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=9))}"

        # Build PlatformRequest payload with UCP structure
        # Note: producer.agent_id will be extracted from API key by the backend
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
        platform_id_val = platform_id or "admesh_weave_python"
        locale_val = locale or "en-US"
        geo_val = geo or "US"
        platform_surface_val = platform_surface or "web"
        
        # Calculate turn_index from messages length
        turn_index = len(messages or [])
        
        payload: Dict[str, Any] = {
            "spec_version": "1.0.0",
            "message_id": message_id_val,
            "timestamp": timestamp,
            "producer": {
                "agent_id": platform_id_val,  # Will be overridden by backend from API key
                "agent_role": "publisher",
                "software": "admesh_weave_python",
                "software_version": model or "1.0.0"
            },
            "context": {
                "context_id": context_id,
                "language": locale_val,
                "publisher": platform_id_val,  # Will be overridden by backend from API key
                "placement": {
                    "ad_unit": platform_surface_val
                },
                "device": {
                    "platform": "web",  # Default for Python backend
                    "form_factor": "desktop"  # Default for Python backend
                },
                "geography": {
                    "country": geo_val
                }
            },
            "identity": {
                "namespace": "platform_user",
                "value_hash": user_id or "",
                "confidence": 1.0
            },
            "extensions": {
                "aip": {
                    "session_id": session_id,
                    "conversation_id": session_id,  # Use session_id as conversation_id if not provided separately
                    "turn_index": turn_index,
                    "query_text": query,
                    "messages": messages or [],
                    "latency_budget_ms": latency_budget_ms,
                    "cpx_floor": 0.0
                }
            }
        }

        url = f"{self.api_base_url.rstrip('/')}/aip/context"

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )

                if not response.is_success:
                    error_text = ""
                    try:
                        error_text = response.text
                    except Exception:
                        pass

                    raise Exception(
                        f"HTTP {response.status_code}: {response.reason_phrase}"
                        + (f" - {error_text}" if error_text else "")
                    )

                data = response.json()

                # /aip/context returns a single recommendation object
                # Convert to array format for compatibility and ensure offer_summary is included
                if data and data.get("recommendation_id"):
                    # Filter by format: only return recommendations with "weave" format
                    # Check resolved_format first (what was actually used), then fallback to preferred_format
                    resolved_format = data.get("format_resolution", {}).get("resolved_format")
                    preferred_format = data.get("creative_input", {}).get("preferred_format")
                    format_val = resolved_format or preferred_format
                    
                    # If format is not "weave", return empty result so other formats can be picked up by other clients
                    if format_val != "weave":
                        return AdMeshWaitResult(
                            found=False,
                            error="Preferred format is not weave"
                        )
                    
                    # Ensure creative_input exists and includes offer_summary
                    if "creative_input" not in data:
                        data["creative_input"] = {}
                    
                    # Extract offer_summary from creative_input if it exists
                    # The operator sends offer_summary in creative_input, so ensure it's preserved
                    normalized_recommendation = {
                        **data,
                        "creative_input": {
                            **data.get("creative_input", {}),
                            # Preserve offer_summary if it exists in creative_input
                            "offer_summary": data.get("creative_input", {}).get("offer_summary"),
                        },
                        # Preserve realtime_offer_id at top level
                        "realtime_offer_id": data.get("realtime_offer_id"),
                    }
                    
                    return AdMeshWaitResult(
                        found=True,
                        recommendations=[normalized_recommendation],
                        query=query,
                        request_id=data.get("recommendation_id"),
                    )

                return AdMeshWaitResult(found=False, error="No recommendation found")

        except Exception as err:
            raise err

    def get_recommendations_for_weave_sync(
        self,
        session_id: str,
        message_id: str,
        query: str,
        platform_id: Optional[str] = None,
        platform_surface: Optional[str] = None,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        locale: Optional[str] = None,
        geo: Optional[str] = None,
        user_id: Optional[str] = None,
        latency_budget_ms: Optional[int] = None,
        timeout_ms: Optional[int] = None,
    ) -> AdMeshWaitResult:
        """
        Synchronous version of get_recommendations_for_weave.

        Get recommendation by calling /aip/context endpoint.

        Args:
            session_id: Session ID (required, must be provided by frontend)
            message_id: Message ID (required, must be provided by frontend)
            query: User query (required for contextual recommendations)
            platform_id: Platform identifier (default: 'admesh_weave_python')
            platform_surface: Platform surface (default: 'web')
            model: Model name
            messages: Conversation messages
            locale: Locale (default: 'en-US')
            geo: Geographic location
            user_id: User ID
            latency_budget_ms: Latency budget in milliseconds (used to calculate HTTP timeout)
            timeout_ms: Max wait time in milliseconds (default: calculated from latency_budget_ms or 30000ms)

        Returns:
            AdMeshWaitResult dictionary with recommendation or error

        Example:
            ```python
            result = client.get_recommendations_for_weave_sync(
                session_id="sess_123",
                message_id="msg_123",
                query="best laptops for programming",
                latency_budget_ms=10000
            )
            ```
        """
        # Validate required parameters
        if not query or not query.strip():
            raise ValueError("AdMeshClient.get_recommendations_for_weave_sync: 'query' parameter is required and cannot be empty")
        
        if not session_id:
            raise ValueError("AdMeshClient.get_recommendations_for_weave_sync: 'session_id' parameter is required and must be provided by frontend")
        
        if not message_id:
            raise ValueError("AdMeshClient.get_recommendations_for_weave_sync: 'message_id' parameter is required and must be provided by frontend")

        # Calculate HTTP timeout from latency_budget_ms (use 3x latency budget or default 30s)
        # This ensures the HTTP request doesn't timeout before the auction completes
        if latency_budget_ms:
            http_timeout_ms = max(latency_budget_ms * 3, 30000)  # At least 30s, or 3x latency budget
        else:
            http_timeout_ms = timeout_ms or 30000  # Default 30s if no latency budget specified
        timeout_seconds = http_timeout_ms / 1000.0

        # Use messageId directly from parameter (must be provided by frontend)
        message_id_val = message_id

        # Generate context_id for UCP structure
        context_id = f"ctx_{int(time.time() * 1000)}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=9))}"

        # Build PlatformRequest payload with UCP structure
        # Note: producer.agent_id will be extracted from API key by the backend
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
        platform_id_val = platform_id or "admesh_weave_python"
        locale_val = locale or "en-US"
        geo_val = geo or "US"
        platform_surface_val = platform_surface or "web"
        
        # Calculate turn_index from messages length
        turn_index = len(messages or [])
        
        payload: Dict[str, Any] = {
            "spec_version": "1.0.0",
            "message_id": message_id_val,
            "timestamp": timestamp,
            "producer": {
                "agent_id": platform_id_val,  # Will be overridden by backend from API key
                "agent_role": "publisher",
                "software": "admesh_weave_python",
                "software_version": model or "1.0.0"
            },
            "context": {
                "context_id": context_id,
                "language": locale_val,
                "publisher": platform_id_val,  # Will be overridden by backend from API key
                "placement": {
                    "ad_unit": platform_surface_val
                },
                "device": {
                    "platform": "web",  # Default for Python backend
                    "form_factor": "desktop"  # Default for Python backend
                },
                "geography": {
                    "country": geo_val
                }
            },
            "identity": {
                "namespace": "platform_user",
                "value_hash": user_id or "",
                "confidence": 1.0
            },
            "extensions": {
                "aip": {
                    "session_id": session_id,
                    "conversation_id": session_id,  # Use session_id as conversation_id if not provided separately
                    "turn_index": turn_index,
                    "query_text": query,
                    "messages": messages or [],
                    "latency_budget_ms": latency_budget_ms,
                    "cpx_floor": 0.0
                }
            }
        }

        url = f"{self.api_base_url.rstrip('/')}/aip/context"

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )

                if not response.is_success:
                    error_text = ""
                    try:
                        error_text = response.text
                    except Exception:
                        pass

                    raise Exception(
                        f"HTTP {response.status_code}: {response.reason_phrase}"
                        + (f" - {error_text}" if error_text else "")
                    )

                data = response.json()

                # /aip/context returns a single recommendation object
                # Convert to array format for compatibility and ensure offer_summary is included
                if data and data.get("recommendation_id"):
                    # Filter by format: only return recommendations with "weave" format
                    # Check resolved_format first (what was actually used), then fallback to preferred_format
                    resolved_format = data.get("format_resolution", {}).get("resolved_format")
                    preferred_format = data.get("creative_input", {}).get("preferred_format")
                    format_val = resolved_format or preferred_format
                    
                    # If format is not "weave", return empty result so other formats can be picked up by other clients
                    if format_val != "weave":
                        return AdMeshWaitResult(
                            found=False,
                            error="Preferred format is not weave"
                        )
                    
                    # Ensure creative_input exists and includes offer_summary
                    if "creative_input" not in data:
                        data["creative_input"] = {}
                    
                    # Extract offer_summary from creative_input if it exists
                    # The operator sends offer_summary in creative_input, so ensure it's preserved
                    normalized_recommendation = {
                        **data,
                        "creative_input": {
                            **data.get("creative_input", {}),
                            # Preserve offer_summary if it exists in creative_input
                            "offer_summary": data.get("creative_input", {}).get("offer_summary"),
                        },
                        # Preserve realtime_offer_id at top level
                        "realtime_offer_id": data.get("realtime_offer_id"),
                    }
                    
                    return AdMeshWaitResult(
                        found=True,
                        recommendations=[normalized_recommendation],
                        query=query,
                        request_id=data.get("recommendation_id"),
                    )

                return AdMeshWaitResult(found=False, error="No recommendation found")

        except Exception as err:
            raise err

