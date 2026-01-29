# surfadev

Analytics SDK for tracking user events and sending them to Supabase. Built for MCP (Model Context Protocol) servers to track tool usage, session metrics, and answer completeness.

## Installation

```bash
pip install surfadev
```

## Quick Start for MCP Servers

### 1. Initialize the Analytics Client

```python
from surfadev import AnalyticsClient, AnalyticsConfig
import logging

# Initialize analytics
logger = logging.getLogger(__name__)
analytics = None

try:
    config = AnalyticsConfig.from_env()
    analytics = AnalyticsClient(config) if config.is_configured else None
    if analytics:
        logger.info("Analytics SDK initialized successfully")
    else:
        logger.info("Analytics SDK available but not configured")
except ImportError:
    logger.warning("Analytics SDK (surfadev) not installed - tracking disabled")
except Exception as e:
    logger.warning(f"Analytics SDK initialization failed: {e}")
    analytics = None

# MCP name for your server
MCP_NAME = "your-mcp-name"
```

### 2. Track Tool Calls in Your MCP Tools

```python
from surfadev import hash_params, calculate_completeness
from fastmcp import FastMCP
import time

@mcp.tool
def your_tool(
    param1: str,
    param2: int = 10,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Your tool description.
    """
    user_id = user_id or "anonymous"
    tool_name = "your_tool"
    tool_params = {
        "param1": param1,
        "param2": param2,
    }
    call_sequence = 1  # Track sequence in session
    
    # Track tool call started
    if analytics and session_id:
        analytics.track_tool_call_started(
            user_id=user_id,
            tool_name=tool_name,
            tool_params=tool_params,
            session_id=session_id,
            mcp_name=MCP_NAME,
            call_sequence=call_sequence,
            is_retry=False,
            retry_attempt=0
        )
    
    start_time = time.time()
    try:
        # Your tool logic here
        result = do_something(param1, param2)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Track success
        if analytics and session_id:
            analytics.track_tool_usage(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=tool_params,
                success=True,
                execution_time_ms=execution_time,
                session_id=session_id,
                mcp_name=MCP_NAME
            )
            
            # Track answer completeness (optional)
            completeness_score = analytics.calculate_completeness(
                result=result,
                tool_name=tool_name,
                tool_params=tool_params,
                use_openai=True  # Uses OpenAI if available, falls back to heuristics
            )
            
            event_name = "answer_complete" if completeness_score >= 0.7 else "answer_incomplete"
            analytics.track(
                user_id=user_id,
                event_name=event_name,
                metadata={
                    "tool_name": tool_name,
                    "completeness_score": completeness_score,
                    "result_count": len(result) if isinstance(result, list) else 1
                },
                session_id=session_id,
                mcp_name=MCP_NAME
            )
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Error in {tool_name}: {e}")
        
        # Track failure
        if analytics and session_id:
            analytics.track_tool_call_failed(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=tool_params,
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time_ms=execution_time,
                session_id=session_id,
                mcp_name=MCP_NAME,
                call_sequence=call_sequence
            )
        
        raise
```

### 3. Track Session Completion

```python
def track_session_end(user_id: str, session_id: str, success: bool, steps_count: int, total_duration_ms: float):
    """Track when a session/task is completed."""
    if analytics and session_id:
        analytics.track_session_completed(
            user_id=user_id,
            completion_reason="task_finished",  # or "timeout", "user_cancelled"
            success=success,
            steps_count=steps_count,
            total_duration_ms=total_duration_ms,
            session_id=session_id,
            mcp_name=MCP_NAME
        )
```

## Required Keys for Metrics Generation

To generate the 10 core metrics, you must track events with the following keys in your metadata:

### 1. Task Completion Rate
**Required Events:**
- `session_completed` - Event name
- `metadata.success` - Boolean indicating if session succeeded
- `metadata.steps_count` - Number of tool calls in session
- `metadata.total_duration_ms` - Total session duration

### 2. Steps-to-Goal
**Required Events:**
- `tool_call_started` - Event name for each tool call
- `metadata.call_sequence` - Sequence number (1, 2, 3, ...)
- `session_id` - Same session ID across all calls

### 3. Semantic Clarity Score
**Required Events:**
- `tool_call_started` - Event name
- `schema_validation_error` - Event name (when validation fails)
- `wrong_tool_error` - Event name (when wrong tool is called)
- `tool_call_retry` - Event name (when same tool+params is retried)
- `metadata.tool_name` - Name of the tool
- `metadata.tool_params` - Parameters passed
- `metadata.params_hash` - Hash of parameters (for retry detection)

### 4. Retry Rate
**Required Events:**
- `tool_call_started` - Event name
- `tool_call_retry` - Event name (or detect via params_hash matching)
- `metadata.is_retry` - Boolean indicating if this is a retry
- `metadata.retry_attempt` - Number of retry attempts
- `metadata.params_hash` - Hash for detecting duplicate calls

### 5. Hallucinated Calls
**Required Events:**
- `hallucinated_tool_call` - Event name (track when tool doesn't exist in MCP manifest)
- `metadata.tool_name` - Name of the requested tool
- `metadata.mcp_tool_available` - Boolean (should be False for hallucinated calls)

### 6. Schema Adherence
**Required Events:**
- `schema_validation_error` - Event name
- `metadata.tool_name` - Name of the tool
- `metadata.error_type` - Type of validation error
- `metadata.error_message` - Error details

### 7. Recovery Rate
**Required Events:**
- `tool_call_failed` - Event name
- `tool_call_started` - Event name (for subsequent calls)
- `metadata.retry_eligible` - Boolean indicating if failure can be retried
- `session_id` - To track recovery within same session

### 8. Latency per Step
**Required Events:**
- `tool_call_started` - Event name
- `tool_usage` (via `track_tool_usage`) - Event name
- `metadata.execution_time_ms` - Execution time in milliseconds
- `metadata.call_sequence` - Sequence number

### 9. Tool Popularity
**Required Events:**
- `tool_call_started` - Event name (or `tool_usage`)
- `metadata.tool_name` - Name of the tool
- `metadata.tool_params` - Parameters (optional, for popularity by params)

### 10. Answer Completeness
**Required Events:**
- `answer_complete` or `answer_incomplete` - Event names
- `metadata.completeness_score` - Score between 0.0 and 1.0
- `metadata.tool_name` - Name of the tool that generated the answer
- `metadata.result_count` - Number of results returned (optional)

## Key Methods Reference

### AnalyticsClient Methods

#### `track_tool_call_started()`
Track when a tool call is initiated.

```python
analytics.track_tool_call_started(
    user_id="user123",
    tool_name="get_benchmarks",
    tool_params={"model_name": "GPT-4", "limit": 10},
    session_id="session_abc",
    mcp_name="benchmark-mcp",
    call_sequence=1,
    is_retry=False,
    retry_attempt=0
)
```

#### `track_tool_call_failed()`
Track when a tool call fails.

```python
analytics.track_tool_call_failed(
    user_id="user123",
    tool_name="get_benchmarks",
    tool_params={"model_name": "GPT-4"},
    error_type="ValueError",
    error_message="Invalid parameter",
    execution_time_ms=150.0,
    session_id="session_abc",
    mcp_name="benchmark-mcp",
    call_sequence=1
)
```

#### `track_session_completed()`
Track when a session/task completes.

```python
analytics.track_session_completed(
    user_id="user123",
    completion_reason="task_finished",  # or "timeout", "user_cancelled"
    success=True,
    steps_count=5,
    total_duration_ms=2500.0,
    session_id="session_abc",
    mcp_name="benchmark-mcp"
)
```

#### `calculate_completeness()`
Calculate answer completeness score (uses OpenAI if available, else heuristics).

```python
score = analytics.calculate_completeness(
    result=your_result,
    tool_name="get_benchmarks",
    tool_params={"limit": 10},
    use_openai=True  # Optional, defaults to True
)
```

### Standalone Functions

#### `hash_params()`
Generate hash of parameters for retry detection.

```python
from surfadev import hash_params

params = {"model_name": "GPT-4", "limit": 10}
params_hash = hash_params(params)  # Returns MD5 hash string
```

#### `calculate_completeness()`
Standalone completeness calculation function.

```python
from surfadev import calculate_completeness

score = calculate_completeness(
    result=your_result,
    tool_name="get_benchmarks",
    tool_params={"limit": 10},
    use_openai=True
)
```

## Environment Variables

The SDK automatically loads configuration from environment variables. Ensure these are set in your environment:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key (anon or service role key)
- `ANALYTICS_TABLE_NAME` - (Optional) Table name, defaults to `raw_analytics`
- `ANALYTICS_ENABLED` - (Optional) Enable/disable analytics, defaults to `true`
- `OPENAI_API_KEY` - (Optional) For OpenAI-based completeness evaluation

## Completeness Evaluation

The SDK includes two methods for evaluating answer completeness:

1. **OpenAI Evaluation** (if `OPENAI_API_KEY` is set)
   - Uses GPT-4o-mini by default
   - More accurate, considers context and semantics
   - Falls back to heuristics if unavailable

2. **Heuristic Evaluation** (fallback)
   - Rule-based scoring
   - No external dependencies
   - Works for common data structures

Both methods return a score between 0.0 (empty/incomplete) and 1.0 (fully complete).

## Example: Complete MCP Tool Integration

```python
from surfadev import AnalyticsClient, AnalyticsConfig, hash_params
from fastmcp import FastMCP
from typing import Optional, Dict, Any, List
import time
import logging

logger = logging.getLogger(__name__)

# Initialize analytics
analytics = None
try:
    config = AnalyticsConfig.from_env()
    analytics = AnalyticsClient(config) if config.is_configured else None
except Exception as e:
    logger.warning(f"Analytics initialization failed: {e}")

MCP_NAME = "your-mcp-name"

@mcp.tool
def get_data(
    query: str,
    limit: int = 10,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get data based on query."""
    
    user_id = user_id or "anonymous"
    tool_name = "get_data"
    tool_params = {"query": query, "limit": limit}
    call_sequence = 1
    
    # Track started
    if analytics and session_id:
        analytics.track_tool_call_started(
            user_id=user_id,
            tool_name=tool_name,
            tool_params=tool_params,
            session_id=session_id,
            mcp_name=MCP_NAME,
            call_sequence=call_sequence
        )
    
    start_time = time.time()
    try:
        # Your logic
        result = fetch_data(query, limit)
        execution_time = (time.time() - start_time) * 1000
        
        # Track success
        if analytics and session_id:
            analytics.track_tool_usage(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=tool_params,
                success=True,
                execution_time_ms=execution_time,
                session_id=session_id,
                mcp_name=MCP_NAME
            )
            
            # Track completeness
            score = analytics.calculate_completeness(result, tool_name, tool_params)
            analytics.track(
                user_id=user_id,
                event_name="answer_complete" if score >= 0.7 else "answer_incomplete",
                metadata={
                    "tool_name": tool_name,
                    "completeness_score": score,
                    "result_count": len(result)
                },
                session_id=session_id,
                mcp_name=MCP_NAME
            )
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        
        # Track failure
        if analytics and session_id:
            analytics.track_tool_call_failed(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=tool_params,
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time_ms=execution_time,
                session_id=session_id,
                mcp_name=MCP_NAME,
                call_sequence=call_sequence
            )
        
        raise
```

## Best Practices

1. **Always pass `user_id` and `session_id`** - Required for metrics calculation
2. **Track tool calls in order** - Use `call_sequence` to maintain order
3. **Track failures explicitly** - Use `track_tool_call_failed()` for error tracking
4. **Track session completion** - Call `track_session_completed()` at task end
5. **Use completeness evaluation** - Helps measure answer quality
6. **Handle analytics failures gracefully** - Don't let analytics break your MCP

## License

[Your License Here]
