"""
Basic usage example for admesh-weave-python SDK.

This example demonstrates how to use the AdMeshClient to fetch recommendations
for Weave format integration.
"""

import asyncio
import os

from admesh_weave import AdMeshClient


async def async_example():
    """Example using async/await (recommended)."""
    # Initialize the client with your API key
    api_key = os.environ.get("ADMESH_API_KEY", "your-api-key-here")
    client = AdMeshClient(api_key=api_key)

    # Example session and message IDs
    session_id = "sess_example_123"
    message_id = "msg_example_1"
    user_query = "best laptops for programming"

    print("=" * 60)
    print("Async Example: Fetching recommendations for Weave")
    print("=" * 60)

    try:
        # Get recommendations for Weave
        result = await client.get_recommendations_for_weave(
            session_id=session_id,
            message_id=message_id,
            query=user_query,
            timeout_ms=30000,  # 30 second timeout
        )

        if result["found"]:
            print(f"\n✓ Found {len(result['recommendations'])} recommendations")
            print(f"Query: {result['query']}")
            print(f"Request ID: {result.get('request_id')}")

            # Display each recommendation
            for i, rec in enumerate(result["recommendations"], 1):
                print(f"\n--- Recommendation {i} ---")
                print(f"Product: {rec['product_title']}")
                print(f"Summary: {rec['weave_summary']}")
                print(f"Categories: {', '.join(rec['categories'])}")
                print(f"Trust Score: {rec['trust_score']}")
                print(f"Relevance Score: {rec['contextual_relevance_score']}")
                print(f"Click URL: {rec['click_url']}")
                print(f"Exposure URL: {rec['exposure_url']}")
        else:
            print(f"\n✗ No recommendations found")
            print(f"Error: {result.get('error')}")

    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")


def sync_example():
    """Example using synchronous API."""
    # Initialize the client
    api_key = os.environ.get("ADMESH_API_KEY", "your-api-key-here")
    client = AdMeshClient(api_key=api_key)

    # Example session and message IDs
    session_id = "sess_example_456"
    message_id = "msg_example_2"
    user_query = "best project management tools"

    print("\n" + "=" * 60)
    print("Sync Example: Fetching recommendations for Weave")
    print("=" * 60)

    try:
        # Get recommendations using synchronous method
        result = client.get_recommendations_for_weave_sync(
            session_id=session_id,
            message_id=message_id,
            query=user_query,
            timeout_ms=30000,
        )

        if result["found"]:
            print(f"\n✓ Found {len(result['recommendations'])} recommendations")
            print(f"Query: {result['query']}")

            # Display summary
            for i, rec in enumerate(result["recommendations"], 1):
                print(f"\n{i}. {rec['product_title']}")
                print(f"   {rec['weave_summary'][:100]}...")
        else:
            print(f"\n✗ No recommendations found")
            print(f"Error: {result.get('error')}")

    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")


async def cache_example():
    """Example demonstrating database caching behavior."""
    api_key = os.environ.get("ADMESH_API_KEY", "your-api-key-here")
    client = AdMeshClient(api_key=api_key)

    session_id = "sess_cache_test"
    message_id = "msg_cache_test"
    user_query = "best CRM software"

    print("\n" + "=" * 60)
    print("Cache Example: Demonstrating cache behavior")
    print("=" * 60)

    try:
        # First call - may take 1-3 seconds (cache miss)
        print("\nFirst call (cache miss - generating recommendations)...")
        import time

        start = time.time()
        result1 = await client.get_recommendations_for_weave(
            session_id=session_id,
            message_id=message_id,
            query=user_query,
            timeout_ms=30000,
        )
        elapsed1 = time.time() - start

        if result1["found"]:
            print(f"✓ Found {len(result1['recommendations'])} recommendations")
            print(f"⏱  Time taken: {elapsed1:.2f} seconds")

        # Second call - should be fast (< 100ms, cache hit)
        print("\nSecond call (cache hit - retrieving from database)...")
        start = time.time()
        result2 = await client.get_recommendations_for_weave(
            session_id=session_id,
            message_id=message_id,
            query=user_query,
            timeout_ms=5000,  # Shorter timeout for cached results
        )
        elapsed2 = time.time() - start

        if result2["found"]:
            print(f"✓ Found {len(result2['recommendations'])} recommendations")
            print(f"⏱  Time taken: {elapsed2:.2f} seconds")
            print(f"\n📊 Speedup: {elapsed1/elapsed2:.1f}x faster!")

    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")


async def main():
    """Run all examples."""
    # Run async example
    await async_example()

    # Run sync example
    sync_example()

    # Run cache example
    await cache_example()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())

