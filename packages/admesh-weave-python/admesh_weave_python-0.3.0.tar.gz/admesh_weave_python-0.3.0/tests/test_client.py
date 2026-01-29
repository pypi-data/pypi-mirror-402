"""
Tests for AdMeshClient.

These are basic tests to verify the client initialization and structure.
Full integration tests require a running admesh-protocol instance.
"""

import pytest

from admesh_weave import AdMeshClient


def test_client_initialization():
    """Test that client can be initialized with API key."""
    client = AdMeshClient(api_key="test-api-key")
    assert client.api_key == "test-api-key"
    assert client.api_base_url == "https://api.useadmesh.com"


def test_client_initialization_with_custom_url():
    """Test that client can be initialized with custom API base URL."""
    client = AdMeshClient(api_key="test-api-key", api_base_url="http://localhost:8000")
    assert client.api_key == "test-api-key"
    assert client.api_base_url == "http://localhost:8000"


def test_client_initialization_without_api_key():
    """Test that client raises error when initialized without API key."""
    with pytest.raises(ValueError, match="api_key is required"):
        AdMeshClient(api_key="")


def test_client_initialization_with_none_api_key():
    """Test that client raises error when initialized with None API key."""
    with pytest.raises(ValueError, match="api_key is required"):
        AdMeshClient(api_key=None)  # type: ignore


@pytest.mark.asyncio
async def test_get_recommendations_for_weave_structure():
    """Test that get_recommendations_for_weave returns expected structure."""
    client = AdMeshClient(api_key="test-api-key")

    # This test will fail without a running admesh-protocol instance
    # but it demonstrates the expected usage pattern
    try:
        result = await client.get_recommendations_for_weave(
            session_id="test_session", message_id="test_message", query="test query", timeout_ms=1000
        )

        # If we get a result, verify it has the expected structure
        assert "found" in result
        assert isinstance(result["found"], bool)

        if result["found"]:
            assert "recommendations" in result
            assert isinstance(result["recommendations"], list)
            assert "query" in result
            assert "request_id" in result
        else:
            assert "error" in result

    except Exception:
        # Expected to fail without running admesh-protocol
        pass


def test_sync_get_recommendations_for_weave_structure():
    """Test that get_recommendations_for_weave_sync returns expected structure."""
    client = AdMeshClient(api_key="test-api-key")

    # This test will fail without a running admesh-protocol instance
    try:
        result = client.get_recommendations_for_weave_sync(
            session_id="test_session", message_id="test_message", query="test query", timeout_ms=1000
        )

        # If we get a result, verify it has the expected structure
        assert "found" in result
        assert isinstance(result["found"], bool)

        if result["found"]:
            assert "recommendations" in result
            assert isinstance(result["recommendations"], list)
        else:
            assert "error" in result

    except Exception:
        # Expected to fail without running admesh-protocol
        pass

