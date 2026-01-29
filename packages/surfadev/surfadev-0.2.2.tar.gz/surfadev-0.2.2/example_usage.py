"""
Example usage of the Analytics SDK.
"""

from analytics_sdk import AnalyticsClient, AnalyticsConfig
from datetime import datetime

# Example 1: Load configuration from environment
def example_from_env():
    """Load configuration from environment variables."""
    config = AnalyticsConfig.from_env()
    client = AnalyticsClient(config)
    
    # Track a simple event
    client.track(
        user_id="user_12345",
        event_name="page_view",
        metadata={"page": "/dashboard"}
    )


# Example 2: Programmatic configuration
def example_programmatic():
    """Configure programmatically."""
    config = AnalyticsConfig(
        supabase_url="https://your-project.supabase.co",
        supabase_key="your-key",
        table_name="analytics_events"
    )
    client = AnalyticsClient(config)
    
    # Track tool usage
    client.track_tool_usage(
        user_id="user_12345",
        tool_name="get_benchmark_results",
        tool_params={"model_name": "GPT-4", "limit": 10},
        success=True,
        execution_time_ms=150.0
    )


# Example 3: Track custom events
def example_custom_events():
    """Track custom business events."""
    config = AnalyticsConfig.from_env()
    client = AnalyticsClient(config)
    
    # Track user registration
    client.track(
        user_id="new_user_789",
        event_name="user_registered",
        metadata={
            "registration_method": "email",
            "plan": "premium"
        }
    )
    
    # Track feature usage
    client.track(
        user_id="user_12345",
        event_name="feature_used",
        metadata={
            "feature": "export_results",
            "format": "csv",
            "result_count": 25
        }
    )


# Example 4: Batch tracking
def example_batch_tracking():
    """Track multiple events in a batch."""
    config = AnalyticsConfig.from_env()
    client = AnalyticsClient(config)
    
    events = [
        {
            "user_id": "user_12345",
            "event_name": "button_click",
            "metadata": {"button": "submit"},
            "timestamp": datetime.utcnow()
        },
        {
            "user_id": "user_12345",
            "event_name": "form_submit",
            "metadata": {"form": "contact"},
            "timestamp": datetime.utcnow()
        }
    ]
    
    client.batch_track(events)


# Example 5: Error tracking
def example_error_tracking():
    """Track errors and failures."""
    config = AnalyticsConfig.from_env()
    client = AnalyticsClient(config)
    
    try:
        # Some operation that might fail
        result = risky_operation()
        client.track_tool_usage(
            user_id="user_12345",
            tool_name="risky_operation",
            success=True
        )
    except Exception as e:
        client.track_tool_usage(
            user_id="user_12345",
            tool_name="risky_operation",
            success=False,
            error_message=str(e)
        )


if __name__ == "__main__":
    print("Analytics SDK Examples")
    print("=" * 50)
    print("\nMake sure to set SUPABASE_URL and SUPABASE_KEY in .env file")
    print("\nRun individual examples:")
    print("  - example_from_env()")
    print("  - example_programmatic()")
    print("  - example_custom_events()")
    print("  - example_batch_tracking()")
    print("  - example_error_tracking()")

