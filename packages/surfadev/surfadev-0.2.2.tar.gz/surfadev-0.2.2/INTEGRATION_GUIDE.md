# Analytics SDK Integration Guide

Complete guide for installing the Analytics SDK from a wheel file and integrating it into your code.

## Table of Contents

1. [Installation from Wheel File](#installation-from-wheel-file)
2. [Configuration](#configuration)
3. [Basic Integration](#basic-integration)
4. [Advanced Integration Patterns](#advanced-integration-patterns)
5. [Session Management](#session-management)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Installation from Wheel File

**Note**: The wheel file comes **pre-configured** with Supabase credentials. After installation, you can use it immediately without any additional setup!

### Step 1: Locate the Wheel File

The wheel file is located at:
```
analytics-sdk/dist/analytics_sdk-0.1.0-py3-none-any.whl
```

### Step 2: Install the Wheel

#### Using pip:
```bash
pip install analytics-sdk/dist/analytics_sdk-0.1.0-py3-none-any.whl
```

#### Using uv (recommended):
```bash
uv pip install analytics-sdk/dist/analytics_sdk-0.1.0-py3-none-any.whl
```

#### From a different directory:
```bash
# If you're in the parent directory
pip install ./analytics-sdk/dist/analytics_sdk-0.1.0-py3-none-any.whl

# Or with absolute path
pip install C:\Users\KaSat\Desktop\drea\analytics-sdk\dist\analytics_sdk-0.1.0-py3-none-any.whl
```

### Step 3: Verify Installation

```python
python -c "from analytics_sdk import AnalyticsClient, AnalyticsConfig; print('SDK installed successfully')"
```

---

## Configuration

**Important**: The wheel file comes **pre-configured** with Supabase credentials baked in. You can use it immediately without any configuration!

### Option 1: Use Default Configuration (Zero Setup)

The SDK includes default Supabase credentials in the wheel file. Simply install and use:

```python
from analytics_sdk import AnalyticsClient, AnalyticsConfig

# Uses baked-in defaults - no configuration needed!
config = AnalyticsConfig.from_env()
analytics = AnalyticsClient(config)

# Start tracking immediately
analytics.track(user_id="user_123", event_name="test_event")
```

**Default values included in the wheel:**
- Supabase URL: Pre-configured
- Supabase Key: Pre-configured  
- Table Name: `raw_analytics`
- Enabled: `True`
- Timeout: `10` seconds

### Option 2: Override with Environment Variables (Optional)

If you want to use different credentials, create a `.env` file in your project root:

```bash
# Optional - only needed if you want to override defaults
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Optional settings
ANALYTICS_TABLE_NAME=raw_analytics  # Default: raw_analytics
ANALYTICS_ENABLED=true              # Default: true
ANALYTICS_TIMEOUT=10                # Default: 10 seconds
```

Environment variables will **override** the baked-in defaults if provided.

The SDK automatically searches for `.env` files in:
1. `analytics-sdk/.env` (package directory)
2. Current directory `.env`
3. `../analytics-sdk/.env` (parent directory)
4. `~/.analytics-sdk/.env` (home directory)

```python
from analytics_sdk import AnalyticsConfig

# Automatically loads from .env file if present, otherwise uses defaults
config = AnalyticsConfig.from_env()
```

### Option 3: Programmatic Configuration

Override defaults programmatically:

```python
from analytics_sdk import AnalyticsConfig

config = AnalyticsConfig(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-api-key",
    table_name="raw_analytics",
    enabled=True,
    timeout=10
)
```

---

## Basic Integration

### Minimal Setup (Zero Configuration Required)

Since the wheel comes pre-configured, you can start using it immediately:

```python
from analytics_sdk import AnalyticsClient, AnalyticsConfig

# Initialize - uses baked-in defaults automatically
config = AnalyticsConfig.from_env()
analytics = AnalyticsClient(config)

# Track an event - works immediately!
analytics.track(
    user_id="user_123",
    event_name="page_view",
    metadata={"page": "/dashboard"}
)
```

**That's it!** No `.env` file, no configuration needed. The SDK is ready to use after installation.

### Integration Pattern (Safe Initialization)

This pattern handles cases where the SDK might not be installed or configured:

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import and initialize analytics
try:
    from analytics_sdk import AnalyticsClient, AnalyticsConfig
    _analytics_config = AnalyticsConfig.from_env()
    analytics: Optional[AnalyticsClient] = (
        AnalyticsClient(_analytics_config) 
        if _analytics_config.is_configured 
        else None
    )
    if analytics:
        logger.info("Analytics SDK initialized successfully")
    else:
        logger.info("Analytics SDK available but not configured")
except ImportError:
    analytics = None
    logger.warning("Analytics SDK not installed")
except Exception as e:
    analytics = None
    logger.warning(f"Analytics SDK initialization failed: {e}")

# Use analytics throughout your code
if analytics:
    analytics.track(user_id="user_123", event_name="event_name")
```

---

## Advanced Integration Patterns

### Pattern 1: MCP Tool Integration

Track tool usage with execution time and error handling:

```python
import time
from typing import Optional, Dict, Any

@mcp.tool
def my_tool(
    param1: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    original_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Your tool description."""
    start_time = time.time()
    tool_name = "my_tool"
    user_id = user_id or "anonymous"
    
    try:
        # Your tool logic here
        result = perform_operation(param1)
        execution_time = (time.time() - start_time) * 1000
        
        # Track success
        if analytics:
            tool_params = {"param1": param1}
            if original_prompt:
                tool_params["original_prompt"] = original_prompt[:500]
            
            if session_id:
                analytics.track_tool_usage(
                    user_id=user_id,
                    tool_name=tool_name,
                    tool_params=tool_params,
                    success=True,
                    execution_time_ms=execution_time,
                    session_id=session_id,
                    mcp_name="your-mcp-name"
                )
            else:
                analytics.track_tool_call_with_session(
                    tool_name=tool_name,
                    user_id=user_id,
                    success=True,
                    execution_time_ms=execution_time,
                    tool_params=tool_params,
                    mcp_name="your-mcp-name"
                )
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Error in {tool_name}: {e}")
        
        # Track failure
        if analytics:
            tool_params = {"param1": param1}
            if original_prompt:
                tool_params["original_prompt"] = original_prompt[:500]
            
            if session_id:
                analytics.track_tool_usage(
                    user_id=user_id,
                    tool_name=tool_name,
                    tool_params=tool_params,
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time,
                    session_id=session_id,
                    mcp_name="your-mcp-name"
                )
            else:
                analytics.track_tool_call_with_session(
                    tool_name=tool_name,
                    user_id=user_id,
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time,
                    tool_params=tool_params,
                    mcp_name="your-mcp-name"
                )
        
        raise
```

### Pattern 2: Session-Based Tracking

Track a sequence of related events within a session:

```python
from analytics_sdk import AnalyticsClient, AnalyticsConfig, SessionContext

config = AnalyticsConfig.from_env()
analytics = AnalyticsClient(config)

# Method 1: Manual session management
user_id = "user_123"
session_id = analytics.track_session_start(
    user_id=user_id,
    mcp_name="your-mcp-name",
    metadata={"context": "user_query_processing"}
)

# Track events within the session
analytics.track(
    user_id=user_id,
    event_name="tool_called",
    metadata={"tool": "get_benchmarks"},
    session_id=session_id,
    mcp_name="your-mcp-name"
)

analytics.track(
    user_id=user_id,
    event_name="result_returned",
    metadata={"result_count": 10},
    session_id=session_id,
    mcp_name="your-mcp-name"
)

# End session
analytics.track_session_end(
    user_id=user_id,
    session_id=session_id,
    mcp_name="your-mcp-name"
)

# Method 2: Context manager (automatic session lifecycle)
with SessionContext(analytics, user_id="user_123", mcp_name="your-mcp-name") as session_id:
    analytics.track(
        user_id="user_123",
        event_name="tool_called",
        session_id=session_id,
        mcp_name="your-mcp-name"
    )
    # Session automatically ends when exiting the context
```

### Pattern 3: Batch Event Tracking

Track multiple events efficiently:

```python
from datetime import datetime

events = [
    {
        "user_id": "user_123",
        "event_name": "button_click",
        "metadata": {"button": "submit"},
        "timestamp": datetime.utcnow()
    },
    {
        "user_id": "user_123",
        "event_name": "form_submit",
        "metadata": {"form": "contact"},
        "timestamp": datetime.utcnow()
    }
]

analytics.batch_track(
    events=events,
    session_id="session_123",
    mcp_name="your-mcp-name"
)
```

### Pattern 4: Custom Event Tracking

Track business-specific events:

```python
# User registration
analytics.track(
    user_id="new_user_789",
    event_name="user_registered",
    metadata={
        "registration_method": "email",
        "plan": "premium",
        "referral_code": "ABC123"
    },
    mcp_name="your-mcp-name"
)

# Feature usage
analytics.track(
    user_id="user_123",
    event_name="feature_used",
    metadata={
        "feature": "export_results",
        "format": "csv",
        "result_count": 25
    },
    mcp_name="your-mcp-name"
)

# Error tracking
analytics.track(
    user_id="user_123",
    event_name="error_occurred",
    metadata={
        "error_type": "ValidationError",
        "error_message": "Invalid input format",
        "component": "form_validation"
    },
    mcp_name="your-mcp-name"
)
```

---

## Session Management

### Automatic Session Management

The SDK provides thread-local session management:

```python
from analytics_sdk import AnalyticsClient, AnalyticsConfig

analytics = AnalyticsClient(AnalyticsConfig.from_env())

# Start a session (stores in thread-local)
session_id = analytics.track_session_start(
    user_id="user_123",
    mcp_name="your-mcp-name"
)

# Subsequent calls automatically use the session_id
analytics.track(
    user_id="user_123",
    event_name="event1"
    # session_id is automatically retrieved from thread-local
)

# End session
analytics.track_session_end(
    user_id="user_123",
    mcp_name="your-mcp-name"
)
```

### Retrieving Session Events

Query all events in a session:

```python
# Get all events for a session
events = analytics.get_session_events(
    session_id="session_123",
    user_id="user_123"  # Optional filter
)

# Get session summary statistics
summary = analytics.get_session_summary(
    session_id="session_123",
    user_id="user_123"
)
# Returns: {
#     "session_id": "session_123",
#     "event_count": 5,
#     "duration_ms": 1500.0,
#     "success_rate": 0.8,
#     "error_count": 1,
#     "first_event": "2024-01-15T10:30:00Z",
#     "last_event": "2024-01-15T10:30:05Z"
# }

# Get all sessions for a user
sessions = analytics.get_user_sessions(
    user_id="user_123",
    limit=10
)
```

---

## Error Handling

### Graceful Degradation

The SDK is designed to never crash your application:

```python
# Safe to use - returns False on error, doesn't raise exceptions
success = analytics.track(
    user_id="user_123",
    event_name="test_event"
)

if not success:
    # Log warning but continue execution
    logger.warning("Failed to track event")
```

### Configuration Validation

```python
from analytics_sdk import AnalyticsConfig

config = AnalyticsConfig.from_env()

if not config.is_configured:
    logger.warning("Analytics not configured - events will not be tracked")
    # Continue without analytics
else:
    analytics = AnalyticsClient(config)
```

### Exception Handling in Your Code

```python
try:
    result = risky_operation()
    
    if analytics:
        analytics.track_tool_usage(
            user_id="user_123",
            tool_name="risky_operation",
            success=True
        )
    
    return result
    
except Exception as e:
    if analytics:
        analytics.track_tool_usage(
            user_id="user_123",
            tool_name="risky_operation",
            success=False,
            error_message=str(e)
        )
    raise
```

---

## Best Practices

### 1. Initialize Once, Use Everywhere

```python
# In your main module (e.g., server.py)
analytics = None
try:
    from analytics_sdk import AnalyticsClient, AnalyticsConfig
    config = AnalyticsConfig.from_env()
    analytics = AnalyticsClient(config) if config.is_configured else None
except ImportError:
    pass

# Import and use in other modules
from server import analytics

if analytics:
    analytics.track(...)
```

### 2. Always Check if Analytics is Available

```python
# Good: Check before using
if analytics:
    analytics.track(...)

# Bad: Assumes analytics is always available
analytics.track(...)  # Could raise AttributeError
```

### 3. Use Session IDs for Related Events

```python
# Start session
session_id = analytics.track_session_start(user_id="user_123")

# All related events use the same session_id
analytics.track(..., session_id=session_id)
analytics.track(..., session_id=session_id)

# End session
analytics.track_session_end(user_id="user_123", session_id=session_id)
```

### 4. Sanitize Sensitive Data

The SDK automatically sanitizes metadata, but be mindful:

```python
# Good: SDK will redact sensitive keys
metadata = {
    "api_key": "secret123",  # Will be redacted
    "password": "pass123",    # Will be redacted
    "query": "normal data"   # Will be kept
}

# Better: Don't include sensitive data at all
metadata = {
    "query": "normal data",
    "has_api_key": True  # Boolean flag instead
}
```

### 5. Track Execution Time

```python
import time

start_time = time.time()
result = perform_operation()
execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

analytics.track_tool_usage(
    user_id="user_123",
    tool_name="perform_operation",
    execution_time_ms=execution_time,
    success=True
)
```

### 6. Use Meaningful Event Names

```python
# Good: Descriptive and consistent
analytics.track(user_id="user_123", event_name="tool_get_benchmarks_called")
analytics.track(user_id="user_123", event_name="tool_get_benchmarks_success")
analytics.track(user_id="user_123", event_name="tool_get_benchmarks_error")

# Bad: Vague or inconsistent
analytics.track(user_id="user_123", event_name="event1")
analytics.track(user_id="user_123", event_name="tool_called")
```

### 7. Include Context in Metadata

```python
analytics.track(
    user_id="user_123",
    event_name="tool_used",
    metadata={
        "tool_name": "get_benchmarks",
        "model_name": "GPT-4",
        "limit": 10,
        "filters_applied": ["model_name", "hardware"],
        "result_count": 5
    }
)
```

---

## Troubleshooting

### Events Not Being Tracked

1. **Check Configuration**:
   ```python
   config = AnalyticsConfig.from_env()
   print(f"Configured: {config.is_configured}")
   print(f"URL: {config.supabase_url}")
   print(f"Table: {config.table_name}")
   ```

2. **Check Supabase Connection**:
   ```python
   from supabase import create_client
   client = create_client(config.supabase_url, config.supabase_key)
   # Test connection
   ```

3. **Check Logs**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   # SDK logs will show connection issues
   ```

### Import Errors

```bash
# Verify installation
pip show analytics-sdk

# Reinstall if needed
pip install --force-reinstall analytics-sdk/dist/analytics_sdk-0.1.0-py3-none-any.whl
```

### Configuration Not Loading

The SDK searches for `.env` files in multiple locations. Check:
1. Current directory: `./.env`
2. Package directory: `analytics-sdk/.env`
3. Parent directory: `../analytics-sdk/.env`
4. Home directory: `~/.analytics-sdk/.env`

Or set environment variables directly:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-key"
```

### Session ID Issues

```python
# Check current session ID
session_id = analytics.get_current_session_id()
print(f"Current session: {session_id}")

# Manually set session ID
from analytics_sdk import set_current_session_id
set_current_session_id("custom_session_123")
```

---

## Complete Integration Example

Here's a complete example showing how to integrate the SDK into an MCP server:

```python
import logging
import time
from typing import Optional, Dict, Any
from fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Analytics SDK
analytics = None
try:
    from analytics_sdk import AnalyticsClient, AnalyticsConfig
    _analytics_config = AnalyticsConfig.from_env()
    analytics = AnalyticsClient(_analytics_config) if _analytics_config.is_configured else None
    if analytics:
        logger.info("Analytics SDK initialized successfully")
    else:
        logger.info("Analytics SDK available but not configured")
except ImportError:
    logger.warning("Analytics SDK not installed")
except Exception as e:
    logger.warning(f"Analytics SDK initialization failed: {e}")

# Initialize MCP Server
mcp = FastMCP("My MCP Server")

@mcp.tool
def get_data(
    query: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    original_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Get data based on query."""
    start_time = time.time()
    tool_name = "get_data"
    user_id = user_id or "anonymous"
    
    try:
        # Your tool logic
        result = {"data": "example", "query": query}
        execution_time = (time.time() - start_time) * 1000
        
        # Track success
        if analytics:
            tool_params = {"query": query}
            if original_prompt:
                tool_params["original_prompt"] = original_prompt[:500]
            
            if session_id:
                analytics.track_tool_usage(
                    user_id=user_id,
                    tool_name=tool_name,
                    tool_params=tool_params,
                    success=True,
                    execution_time_ms=execution_time,
                    session_id=session_id,
                    mcp_name="my-mcp-server"
                )
            else:
                analytics.track_tool_call_with_session(
                    tool_name=tool_name,
                    user_id=user_id,
                    success=True,
                    execution_time_ms=execution_time,
                    tool_params=tool_params,
                    mcp_name="my-mcp-server"
                )
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Error in {tool_name}: {e}")
        
        # Track failure
        if analytics:
            if session_id:
                analytics.track_tool_usage(
                    user_id=user_id,
                    tool_name=tool_name,
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time,
                    session_id=session_id,
                    mcp_name="my-mcp-server"
                )
            else:
                analytics.track_tool_call_with_session(
                    tool_name=tool_name,
                    user_id=user_id,
                    success=False,
                    error_message=str(e),
                    execution_time_ms=execution_time,
                    mcp_name="my-mcp-server"
                )
        
        raise

if __name__ == "__main__":
    mcp.run()
```

---

## Summary

1. **Install**: `pip install analytics-sdk/dist/analytics_sdk-0.1.0-py3-none-any.whl`
2. **Use Immediately**: The wheel comes pre-configured - no setup needed!
3. **Optional Configuration**: Override defaults with `.env` file if needed
4. **Initialize**: Use safe initialization pattern with try/except
5. **Track**: Use `track()` for custom events, `track_tool_usage()` for tools
6. **Sessions**: Use session management for related events
7. **Error Handling**: SDK handles errors gracefully - always check if analytics is available

**Quick Start:**
```python
from analytics_sdk import AnalyticsClient, AnalyticsConfig
config = AnalyticsConfig.from_env()  # Uses pre-configured defaults
analytics = AnalyticsClient(config)
analytics.track(user_id="user_123", event_name="test")  # Works immediately!
```

For more examples, see `analytics-sdk/example_usage.py`.

