# Event Tracking Design for Analytics Metrics

This document outlines the event types and metadata structures needed to generate the specified analytics metrics.

## Event Type Taxonomy

### Core Event Types

1. **Session Lifecycle Events**
   - `session_start` - Already exists
   - `session_end` - Already exists
   - `session_completed` - **NEW**: Explicit task completion
   - `session_failed` - **NEW**: Explicit task failure
   - `session_abandoned` - **NEW**: Session ended without completion

2. **Tool Call Events**
   - `tool_call_started` - **NEW**: When agent initiates a tool call
   - `tool_call_completed` - Currently tracked as `event_name=tool_name`
   - `tool_call_failed` - **NEW**: Tool execution failed
   - `tool_call_retry` - **NEW**: Retry of same tool with same params
   - `hallucinated_tool_call` - **NEW**: Tool name not in MCP manifest

3. **Validation Events**
   - `schema_validation_error` - **NEW**: JSON schema validation failed
   - `wrong_tool_error` - **NEW**: Agent called wrong tool (detected via retry pattern)

4. **Task/Answer Events**
   - `task_completed` - **NEW**: Explicit task completion signal
   - `answer_complete` - **NEW**: Answer completeness heuristic passed
   - `answer_incomplete` - **NEW**: Answer completeness heuristic failed

---

## Event Metadata Structures

### 1. Session Completion Event

```python
analytics.track(
    user_id="user_123",
    event_name="session_completed",
    metadata={
        "completion_reason": "task_finished",  # or "timeout", "user_cancelled", etc.
        "success": True,
        "steps_count": 5,  # Number of tool calls in session
        "total_duration_ms": 2500.0,
        "final_result_type": "agent_summary"  # or "tool_result", "error"
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 2. Tool Call Started Event

```python
analytics.track(
    user_id="user_123",
    event_name="tool_call_started",
    metadata={
        "tool_name": "get_benchmark_results_by_filters",
        "tool_params": {...},  # Parameters being used
        "call_sequence": 1,  # Order in session (1, 2, 3...)
        "is_retry": False,  # Whether this is a retry
        "previous_tool_name": None,  # Previous tool in session
        "params_hash": "abc123",  # Hash of params for retry detection
        "mcp_tool_available": True  # Whether tool exists in manifest
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 3. Tool Call Failed Event

```python
analytics.track(
    user_id="user_123",
    event_name="tool_call_failed",
    metadata={
        "tool_name": "get_benchmark_results_by_filters",
        "tool_params": {...},
        "error_type": "execution_error",  # or "validation_error", "timeout"
        "error_message": "Database connection failed",
        "execution_time_ms": 150.0,
        "call_sequence": 2,
        "retry_eligible": True  # Whether this can be retried
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 4. Schema Validation Error Event

```python
analytics.track(
    user_id="user_123",
    event_name="schema_validation_error",
    metadata={
        "tool_name": "get_benchmark_results_by_filters",
        "tool_params": {...},  # Invalid params
        "validation_errors": [
            {
                "field": "model_name",
                "error": "required field missing",
                "schema_path": "properties.model_name"
            }
        ],
        "call_sequence": 3,
        "schema_version": "1.0.0"
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 5. Hallucinated Tool Call Event

```python
analytics.track(
    user_id="user_123",
    event_name="hallucinated_tool_call",
    metadata={
        "requested_tool_name": "get_benchmark_results_advanced",  # Not in manifest
        "tool_params": {...},
        "available_tools": ["get_benchmark_results_by_filters", ...],  # Actual tools
        "call_sequence": 4,
        "similar_tool_suggested": "get_benchmark_results_by_filters"  # If fuzzy match exists
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 6. Tool Call Retry Event

```python
analytics.track(
    user_id="user_123",
    event_name="tool_call_retry",
    metadata={
        "tool_name": "get_benchmark_results_by_filters",
        "tool_params": {...},
        "params_hash": "abc123",  # Same as original call
        "original_call_sequence": 2,  # First attempt sequence number
        "retry_attempt": 1,  # 1st retry, 2nd retry, etc.
        "retry_reason": "execution_failed",  # Why retrying
        "call_sequence": 5
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 7. Wrong Tool Error Event

```python
analytics.track(
    user_id="user_123",
    event_name="wrong_tool_error",
    metadata={
        "first_tool_name": "get_benchmark_results",
        "second_tool_name": "get_benchmark_results_by_filters",
        "first_tool_params": {...},
        "second_tool_params": {...},
        "detection_pattern": "retry_with_different_tool",  # or "immediate_switch"
        "call_sequence": [2, 3]  # Sequence numbers of both calls
    },
    session_id=session_id,
    mcp_name="drea"
)
```

### 8. Answer Completeness Event

```python
analytics.track(
    user_id="user_123",
    event_name="answer_complete",  # or "answer_incomplete"
    metadata={
        "completeness_score": 0.85,  # 0.0 to 1.0
        "detection_method": "heuristic_validation",  # or "user_feedback", "explicit_signal"
        "checks_passed": [
            "has_result_data",
            "has_multiple_results",
            "includes_metrics"
        ],
        "checks_failed": [
            "missing_cost_analysis"
        ],
        "tool_name": "get_benchmark_results_by_filters",
        "result_count": 5
    },
    session_id=session_id,
    mcp_name="drea"
)
```

---

## Enhanced Tool Usage Tracking

### Current vs Enhanced

**Current approach:**
```python
analytics.track_tool_usage(
    user_id="user_123",
    tool_name="get_benchmark_results_by_filters",
    tool_params={...},
    success=True,
    execution_time_ms=111.46
)
```

**Enhanced approach (supports all metrics):**
```python
# Track tool call START
analytics.track_tool_call_started(
    user_id="user_123",
    tool_name="get_benchmark_results_by_filters",
    tool_params={...},
    session_id=session_id,
    mcp_name="drea",
    mcp_tools_manifest=["get_benchmark_results_by_filters", ...]  # For hallucination detection
)

# ... tool executes ...

# Track tool call COMPLETION or FAILURE
if success:
    analytics.track_tool_usage(  # Existing method, now tracks "completed"
        user_id="user_123",
        tool_name="get_benchmark_results_by_filters",
        tool_params={...},
        success=True,
        execution_time_ms=111.46,
        session_id=session_id,
        mcp_name="drea"
    )
else:
    analytics.track_tool_call_failed(
        user_id="user_123",
        tool_name="get_benchmark_results_by_filters",
        tool_params={...},
        error_type="execution_error",
        error_message=str(e),
        execution_time_ms=111.46,
        session_id=session_id,
        mcp_name="drea"
    )
```

---

## Integration Patterns

### Pattern 1: MCP Server Middleware

Wrap tool calls in middleware that tracks all events:

```python
def track_tool_call(analytics_client, tool_func):
    """Middleware to track tool calls with full event lifecycle"""
    @wraps(tool_func)
    def wrapper(*args, **kwargs):
        # Extract user_id, session_id from kwargs or context
        user_id = kwargs.get("user_id", "anonymous")
        session_id = kwargs.get("session_id") or analytics_client.get_current_session_id()
        tool_name = tool_func.__name__
        
        # Get tool params (sanitized)
        tool_params = {k: v for k, v in kwargs.items() 
                      if k not in ["user_id", "session_id", "original_prompt"]}
        
        # Generate params hash for retry detection
        params_hash = hash_json(tool_params)
        
        # Check if this is a retry (same tool + params in same session)
        is_retry, retry_attempt = check_retry(analytics_client, session_id, tool_name, params_hash)
        
        # Check if tool exists in MCP manifest (hallucination detection)
        mcp_tools = get_mcp_tools_manifest()  # Get from MCP server
        is_hallucinated = tool_name not in mcp_tools
        
        if is_hallucinated:
            analytics_client.track(
                user_id=user_id,
                event_name="hallucinated_tool_call",
                metadata={
                    "requested_tool_name": tool_name,
                    "available_tools": mcp_tools,
                    ...
                },
                session_id=session_id,
                mcp_name="drea"
            )
            return {"error": "Tool not found in manifest"}
        
        # Track tool call STARTED
        call_sequence = analytics_client.get_session_tool_call_count(session_id) + 1
        analytics_client.track(
            user_id=user_id,
            event_name="tool_call_started",
            metadata={
                "tool_name": tool_name,
                "tool_params": tool_params,
                "call_sequence": call_sequence,
                "is_retry": is_retry,
                "retry_attempt": retry_attempt,
                "params_hash": params_hash,
                "mcp_tool_available": True
            },
            session_id=session_id,
            mcp_name="drea"
        )
        
        # Validate schema BEFORE execution
        validation_errors = validate_tool_params(tool_name, tool_params)
        if validation_errors:
            analytics_client.track(
                user_id=user_id,
                event_name="schema_validation_error",
                metadata={
                    "tool_name": tool_name,
                    "tool_params": tool_params,
                    "validation_errors": validation_errors,
                    "call_sequence": call_sequence
                },
                session_id=session_id,
                mcp_name="drea"
            )
            return {"error": "Schema validation failed", "validation_errors": validation_errors}
        
        # Execute tool
        start_time = time.time()
        try:
            result = tool_func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Track SUCCESS
            analytics_client.track_tool_usage(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=tool_params,
                success=True,
                execution_time_ms=execution_time,
                session_id=session_id,
                mcp_name="drea"
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Track FAILURE
            analytics_client.track(
                user_id=user_id,
                event_name="tool_call_failed",
                metadata={
                    "tool_name": tool_name,
                    "tool_params": tool_params,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "execution_time_ms": execution_time,
                    "call_sequence": call_sequence,
                    "retry_eligible": True
                },
                session_id=session_id,
                mcp_name="drea"
            )
            raise
    
    return wrapper
```

### Pattern 2: Session Completion Detection

```python
# At end of user interaction/query
def mark_session_completed(analytics_client, user_id, session_id, completion_reason="task_finished"):
    """Mark session as completed and calculate session stats"""
    
    # Get session events
    session_events = analytics_client.get_session_events(session_id, user_id)
    
    # Calculate stats
    tool_calls = [e for e in session_events if e["event_name"].startswith("tool_")]
    tool_call_count = len([e for e in tool_calls if e["event_name"] == "tool_call_started"])
    
    failed_calls = [e for e in session_events if e["event_name"] == "tool_call_failed"]
    retries = [e for e in session_events if e["event_name"] == "tool_call_retry"]
    schema_errors = [e for e in session_events if e["event_name"] == "schema_validation_error"]
    
    # Calculate duration
    if session_events:
        start_time = datetime.fromisoformat(session_events[0]["created_at"])
        end_time = datetime.fromisoformat(session_events[-1]["created_at"])
        duration_ms = (end_time - start_time).total_seconds() * 1000
    else:
        duration_ms = 0
    
    # Track completion event
    analytics_client.track(
        user_id=user_id,
        event_name="session_completed",
        metadata={
            "completion_reason": completion_reason,
            "success": len(failed_calls) == 0,  # Simplified
            "steps_count": tool_call_count,
            "total_duration_ms": duration_ms,
            "failed_calls_count": len(failed_calls),
            "retry_count": len(retries),
            "schema_errors_count": len(schema_errors),
            "final_result_type": determine_result_type(session_events)
        },
        session_id=session_id,
        mcp_name="drea"
    )
```

### Pattern 3: Retry Detection

```python
def check_retry(analytics_client, session_id, tool_name, params_hash):
    """Check if this tool call is a retry of a previous call"""
    session_events = analytics_client.get_session_events(session_id)
    
    # Find previous calls with same tool_name and params_hash
    previous_calls = [
        e for e in session_events 
        if e.get("event_name") == "tool_call_started"
        and e.get("metadata", {}).get("tool_name") == tool_name
        and e.get("metadata", {}).get("params_hash") == params_hash
    ]
    
    if previous_calls:
        retry_attempt = len(previous_calls)  # 1st retry, 2nd retry, etc.
        return True, retry_attempt
    
    return False, 0

def detect_wrong_tool_error(analytics_client, session_id):
    """Detect pattern: tool called, failed, then different tool called"""
    session_events = analytics_client.get_session_events(session_id)
    
    for i, event in enumerate(session_events):
        if event.get("event_name") == "tool_call_failed":
            # Check if next tool call is different tool
            next_events = session_events[i+1:i+3]
            next_tool_calls = [
                e for e in next_events 
                if e.get("event_name") == "tool_call_started"
            ]
            
            if next_tool_calls:
                failed_tool = event.get("metadata", {}).get("tool_name")
                next_tool = next_tool_calls[0].get("metadata", {}).get("tool_name")
                
                if failed_tool != next_tool:
                    # Track wrong tool error
                    analytics_client.track(
                        user_id=event.get("user_id"),
                        event_name="wrong_tool_error",
                        metadata={
                            "first_tool_name": failed_tool,
                            "second_tool_name": next_tool,
                            "detection_pattern": "retry_with_different_tool"
                        },
                        session_id=session_id,
                        mcp_name=event.get("mcp_name")
                    )
```

---

## Helper Methods Needed in SDK

```python
# In AnalyticsClient class:

def track_tool_call_started(
    self,
    user_id: str,
    tool_name: str,
    tool_params: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    mcp_name: Optional[str] = None,
    mcp_tools_manifest: Optional[List[str]] = None
) -> bool:
    """Track when a tool call is initiated"""
    # Check for hallucination
    if mcp_tools_manifest and tool_name not in mcp_tools_manifest:
        self.track(
            user_id=user_id,
            event_name="hallucinated_tool_call",
            metadata={
                "requested_tool_name": tool_name,
                "available_tools": mcp_tools_manifest
            },
            session_id=session_id,
            mcp_name=mcp_name
        )
        return False
    
    # Generate params hash for retry detection
    params_hash = self._hash_params(tool_params)
    
    # Check for retry
    is_retry, retry_attempt = self._check_retry(session_id, tool_name, params_hash)
    
    # Get call sequence
    call_sequence = self.get_session_tool_call_count(session_id) + 1
    
    return self.track(
        user_id=user_id,
        event_name="tool_call_started",
        metadata={
            "tool_name": tool_name,
            "tool_params": tool_params,
            "call_sequence": call_sequence,
            "is_retry": is_retry,
            "retry_attempt": retry_attempt,
            "params_hash": params_hash,
            "mcp_tool_available": True
        },
        session_id=session_id,
        mcp_name=mcp_name
    )

def track_tool_call_failed(
    self,
    user_id: str,
    tool_name: str,
    tool_params: Optional[Dict[str, Any]] = None,
    error_type: str = "execution_error",
    error_message: Optional[str] = None,
    execution_time_ms: Optional[float] = None,
    session_id: Optional[str] = None,
    mcp_name: Optional[str] = None
) -> bool:
    """Track failed tool call"""
    call_sequence = self.get_session_tool_call_count(session_id)
    
    return self.track(
        user_id=user_id,
        event_name="tool_call_failed",
        metadata={
            "tool_name": tool_name,
            "tool_params": tool_params,
            "error_type": error_type,
            "error_message": error_message,
            "execution_time_ms": execution_time_ms,
            "call_sequence": call_sequence,
            "retry_eligible": True
        },
        session_id=session_id,
        mcp_name=mcp_name
    )

def track_schema_validation_error(
    self,
    user_id: str,
    tool_name: str,
    tool_params: Optional[Dict[str, Any]] = None,
    validation_errors: Optional[List[Dict[str, Any]]] = None,
    session_id: Optional[str] = None,
    mcp_name: Optional[str] = None
) -> bool:
    """Track schema validation error"""
    call_sequence = self.get_session_tool_call_count(session_id)
    
    return self.track(
        user_id=user_id,
        event_name="schema_validation_error",
        metadata={
            "tool_name": tool_name,
            "tool_params": tool_params,
            "validation_errors": validation_errors,
            "call_sequence": call_sequence
        },
        session_id=session_id,
        mcp_name=mcp_name
    )

def track_session_completed(
    self,
    user_id: str,
    session_id: Optional[str] = None,
    completion_reason: str = "task_finished",
    mcp_name: Optional[str] = None
) -> bool:
    """Track session completion with calculated stats"""
    if session_id is None:
        session_id = self.get_current_session_id()
    
    session_events = self.get_session_events(session_id, user_id)
    
    # Calculate stats
    stats = self._calculate_session_stats(session_events)
    
    return self.track(
        user_id=user_id,
        event_name="session_completed",
        metadata={
            "completion_reason": completion_reason,
            **stats
        },
        session_id=session_id,
        mcp_name=mcp_name
    )

def get_session_tool_call_count(self, session_id: str) -> int:
    """Get count of tool calls in session"""
    events = self.get_session_events(session_id)
    return len([e for e in events if e.get("event_name") == "tool_call_started"])

def _hash_params(self, params: Dict[str, Any]) -> str:
    """Generate hash of params for retry detection"""
    import hashlib
    import json
    params_json = json.dumps(params, sort_keys=True)
    return hashlib.md5(params_json.encode()).hexdigest()

def _check_retry(self, session_id: str, tool_name: str, params_hash: str) -> tuple[bool, int]:
    """Check if this is a retry"""
    events = self.get_session_events(session_id)
    previous_calls = [
        e for e in events 
        if e.get("event_name") == "tool_call_started"
        and e.get("metadata", {}).get("tool_name") == tool_name
        and e.get("metadata", {}).get("params_hash") == params_hash
    ]
    if previous_calls:
        return True, len(previous_calls)
    return False, 0

def _calculate_session_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate session statistics"""
    tool_calls = [e for e in events if "tool" in e.get("event_name", "").lower()]
    failed_calls = [e for e in events if e.get("event_name") == "tool_call_failed"]
    retries = [e for e in events if e.get("event_name") == "tool_call_retry"]
    schema_errors = [e for e in events if e.get("event_name") == "schema_validation_error"]
    
    if events:
        start_time = datetime.fromisoformat(events[0]["created_at"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(events[-1]["created_at"].replace("Z", "+00:00"))
        duration_ms = (end_time - start_time).total_seconds() * 1000
    else:
        duration_ms = 0
    
    return {
        "steps_count": len([e for e in events if e.get("event_name") == "tool_call_started"]),
        "total_duration_ms": duration_ms,
        "failed_calls_count": len(failed_calls),
        "retry_count": len(retries),
        "schema_errors_count": len(schema_errors),
        "success": len(failed_calls) == 0
    }
```

---

## SQL Queries for Metrics

### 1. Task Completion Rate

```sql
SELECT 
    user_id,
    COUNT(DISTINCT CASE WHEN event_name = 'session_completed' THEN session_id END) as completed_sessions,
    COUNT(DISTINCT CASE WHEN event_name = 'session_start' THEN session_id END) as total_sessions,
    COUNT(DISTINCT CASE WHEN event_name = 'session_completed' THEN session_id END)::float / 
    NULLIF(COUNT(DISTINCT CASE WHEN event_name = 'session_start' THEN session_id END), 0) as completion_rate
FROM raw_analytics
WHERE user_id = 'user_123'
GROUP BY user_id;
```

### 2. Steps-to-Goal

```sql
SELECT 
    session_id,
    COUNT(*) as tool_calls
FROM raw_analytics
WHERE event_name = 'tool_call_started'
    AND session_id IN (
        SELECT DISTINCT session_id 
        FROM raw_analytics 
        WHERE event_name = 'session_completed' 
            AND metadata->>'success' = 'true'
    )
GROUP BY session_id;
```

### 3. Semantic Clarity Score

```sql
SELECT 
    session_id,
    COUNT(CASE WHEN event_name = 'tool_call_started' THEN 1 END) as total_tool_calls,
    COUNT(CASE WHEN event_name = 'tool_call_failed' THEN 1 END) as failed_calls,
    COUNT(CASE WHEN event_name = 'schema_validation_error' THEN 1 END) as schema_errors,
    COUNT(CASE WHEN event_name = 'wrong_tool_error' THEN 1 END) as wrong_tool_errors,
    1.0 - (
        (COUNT(CASE WHEN event_name = 'schema_validation_error' THEN 1 END) +
         COUNT(CASE WHEN event_name = 'wrong_tool_error' THEN 1 END) +
         COUNT(CASE WHEN event_name = 'tool_call_retry' THEN 1 END))::float /
        NULLIF(COUNT(CASE WHEN event_name = 'tool_call_started' THEN 1 END), 0)
    ) as clarity_score
FROM raw_analytics
WHERE session_id = 'session_123'
GROUP BY session_id;
```

### 4. Retry Rate

```sql
SELECT 
    session_id,
    COUNT(CASE WHEN event_name = 'tool_call_retry' THEN 1 END)::float /
    NULLIF(COUNT(CASE WHEN event_name = 'tool_call_started' THEN 1 END), 0) as retry_rate
FROM raw_analytics
WHERE session_id = 'session_123'
GROUP BY session_id;
```

### 5. Hallucinated Calls

```sql
SELECT 
    user_id,
    COUNT(CASE WHEN event_name = 'hallucinated_tool_call' THEN 1 END)::float /
    NULLIF(COUNT(DISTINCT session_id), 0) as hallucination_rate
FROM raw_analytics
WHERE user_id = 'user_123'
GROUP BY user_id;
```

### 6. Schema Adherence

```sql
SELECT 
    session_id,
    COUNT(CASE WHEN event_name = 'schema_validation_error' THEN 1 END)::float /
    NULLIF(COUNT(CASE WHEN event_name = 'tool_call_started' THEN 1 END), 0) as violation_rate
FROM raw_analytics
WHERE session_id = 'session_123'
GROUP BY session_id;
```

### 7. Recovery Rate

```sql
WITH sessions_with_errors AS (
    SELECT DISTINCT session_id
    FROM raw_analytics
    WHERE event_name IN ('tool_call_failed', 'schema_validation_error')
),
recovered_sessions AS (
    SELECT DISTINCT session_id
    FROM raw_analytics
    WHERE event_name = 'session_completed'
        AND metadata->>'success' = 'true'
        AND session_id IN (SELECT session_id FROM sessions_with_errors)
)
SELECT 
    COUNT(DISTINCT r.session_id)::float /
    NULLIF(COUNT(DISTINCT e.session_id), 0) as recovery_rate
FROM sessions_with_errors e
LEFT JOIN recovered_sessions r ON e.session_id = r.session_id;
```

### 8. Latency per Step

```sql
WITH tool_calls AS (
    SELECT 
        session_id,
        metadata->>'tool_name' as tool_name,
        created_at,
        event_name,
        LAG(created_at) OVER (PARTITION BY session_id ORDER BY created_at) as prev_time
    FROM raw_analytics
    WHERE event_name IN ('tool_call_started', 'tool_call_completed')
        AND session_id = 'session_123'
)
SELECT 
    tool_name,
    EXTRACT(EPOCH FROM (created_at - prev_time)) * 1000 as latency_ms
FROM tool_calls
WHERE event_name = 'tool_call_completed'
ORDER BY created_at;
```

### 9. Tool Popularity

```sql
SELECT 
    metadata->>'tool_name' as tool_name,
    COUNT(*) as call_count
FROM raw_analytics
WHERE event_name = 'tool_call_started'
    AND user_id = 'user_123'
GROUP BY metadata->>'tool_name'
ORDER BY call_count DESC;
```

### 10. Answer Completeness

```sql
SELECT 
    session_id,
    COUNT(CASE WHEN event_name = 'answer_complete' THEN 1 END)::float /
    NULLIF(COUNT(CASE WHEN event_name IN ('answer_complete', 'answer_incomplete') THEN 1 END), 0) as completeness_rate
FROM raw_analytics
WHERE session_id = 'session_123'
GROUP BY session_id;
```

---

## Summary

To support all 10 metrics, you need to track:

1. **Event Types**: 15+ event types (session lifecycle, tool calls, validation, completion)
2. **Metadata Fields**: Structured metadata for each event type
3. **Helper Methods**: SDK methods to simplify tracking
4. **Middleware Integration**: Wrap tool calls to automatically track events
5. **Completion Detection**: Explicit or heuristic-based session completion tracking

The key insight is that most metrics are **computed from event patterns**, not stored directly. The SDK just needs to emit the right events with the right metadata, and the analytics layer queries and aggregates them.
