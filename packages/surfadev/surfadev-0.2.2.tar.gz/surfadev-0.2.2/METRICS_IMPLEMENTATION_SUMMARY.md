# Metrics Implementation Summary

## Quick Reference: What Needs to Be Tracked

### Required Event Types

| Event Name | Purpose | Required For Metrics |
|------------|---------|---------------------|
| `session_start` | ✅ Already exists | - |
| `session_end` | ✅ Already exists | - |
| `session_completed` | Explicit task completion | 1, 7 |
| `tool_call_started` | Tool call initiation | 2, 4, 8, 9 |
| `tool_call_completed` | ✅ Already exists (via `track_tool_usage`) | 8 |
| `tool_call_failed` | Tool execution failure | 3, 7 |
| `tool_call_retry` | Retry of same tool+params | 3, 4 |
| `schema_validation_error` | JSON schema validation failed | 3, 6 |
| `wrong_tool_error` | Wrong tool selected (detected pattern) | 3 |
| `hallucinated_tool_call` | Tool name not in MCP manifest | 5 |
| `answer_complete` / `answer_incomplete` | Answer completeness detection | 10 |

### Required Metadata Fields

#### For `tool_call_started`:
```python
{
    "tool_name": str,
    "tool_params": dict,
    "call_sequence": int,  # Order in session (1, 2, 3...)
    "is_retry": bool,
    "retry_attempt": int,  # 1st retry, 2nd retry, etc.
    "params_hash": str,  # Hash for retry detection
    "mcp_tool_available": bool
}
```

#### For `tool_call_failed`:
```python
{
    "tool_name": str,
    "tool_params": dict,
    "error_type": str,  # "execution_error", "validation_error", "timeout"
    "error_message": str,
    "execution_time_ms": float,
    "call_sequence": int,
    "retry_eligible": bool
}
```

#### For `session_completed`:
```python
{
    "completion_reason": str,  # "task_finished", "timeout", "user_cancelled"
    "success": bool,
    "steps_count": int,
    "total_duration_ms": float,
    "final_result_type": str  # "agent_summary", "tool_result", "error"
}
```

---

## Implementation Checklist

### Phase 1: Core Events (Required for Most Metrics)

- [ ] Add `track_tool_call_started()` method
- [ ] Add `track_tool_call_failed()` method
- [ ] Add `track_session_completed()` method
- [ ] Add `get_session_tool_call_count()` helper
- [ ] Add params hashing for retry detection

### Phase 2: Validation Events (Required for Schema/Clarity Metrics)

- [ ] Add `track_schema_validation_error()` method
- [ ] Add validation middleware wrapper

### Phase 3: Advanced Detection (Required for Retry/Wrong Tool/Hallucination)

- [ ] Add `track_tool_call_retry()` method
- [ ] Add `track_wrong_tool_error()` method
- [ ] Add `track_hallucinated_tool_call()` method
- [ ] Add retry detection logic
- [ ] Add wrong tool detection logic
- [ ] Add MCP manifest checking

### Phase 4: Completion Detection (Required for Completeness Metric)

- [ ] Add `track_answer_complete()` / `track_answer_incomplete()` methods
- [ ] Add completeness heuristics

---

## Integration Patterns

### Minimal Integration (Just Track Tool Calls)

```python
# Before tool call
analytics.track_tool_call_started(
    user_id=user_id,
    tool_name=tool_name,
    tool_params=tool_params,
    session_id=session_id,
    mcp_name="drea",
    mcp_tools_manifest=available_tools  # For hallucination detection
)

# After tool call
if success:
    analytics.track_tool_usage(...)  # Existing method
else:
    analytics.track_tool_call_failed(
        user_id=user_id,
        tool_name=tool_name,
        tool_params=tool_params,
        error_type="execution_error",
        error_message=str(e),
        session_id=session_id,
        mcp_name="drea"
    )

# At end of session
analytics.track_session_completed(
    user_id=user_id,
    session_id=session_id,
    completion_reason="task_finished",
    mcp_name="drea"
)
```

### Full Integration (All Metrics)

Use middleware wrapper that automatically tracks:
- Tool call lifecycle (started → completed/failed)
- Schema validation
- Retry detection
- Wrong tool detection
- Hallucination detection

See `EVENT_TRACKING_DESIGN.md` for complete middleware example.

---

## Key Design Decisions

### 1. Retry Detection
- **Method**: Hash tool_name + tool_params (JSON sorted)
- **Storage**: Store `params_hash` in `tool_call_started` metadata
- **Detection**: Query session events, find matches with same hash

### 2. Wrong Tool Detection
- **Pattern**: Tool failed → Different tool called immediately after
- **Storage**: Track `wrong_tool_error` event with both tool names
- **Detection**: Post-processing query or real-time detection in middleware

### 3. Hallucination Detection
- **Method**: Compare requested tool name to MCP manifest
- **Storage**: Track `hallucinated_tool_call` event
- **Timing**: Check BEFORE execution (in middleware)

### 4. Session Completion
- **Methods**:
  1. **Explicit**: Call `track_session_completed()` at end of task
  2. **Heuristic**: Detect terminal events (agent summary, final tool result)
  3. **Timeout**: Session ends after X seconds of inactivity
- **Recommendation**: Use explicit tracking for accuracy

### 5. Answer Completeness
- **Method**: Heuristic checks (has data, has multiple results, includes metrics, etc.)
- **Storage**: Track `answer_complete` or `answer_incomplete` event
- **Timing**: After final tool call or agent summary

---

## Metrics Formula Reference

### 1. Task Completion Rate
```sql
COUNT(DISTINCT session_id WHERE event_name='session_completed') /
COUNT(DISTINCT session_id WHERE event_name='session_start')
```

### 2. Steps-to-Goal
```sql
COUNT(*) WHERE event_name='tool_call_started' AND session_id IN (completed_sessions)
```

### 3. Semantic Clarity Score
```sql
1 - (
  (schema_errors + wrong_tool_errors + retries) / total_tool_calls
)
```

### 4. Retry Rate
```sql
COUNT(*) WHERE event_name='tool_call_retry' /
COUNT(*) WHERE event_name='tool_call_started'
```

### 5. Hallucinated Calls
```sql
COUNT(*) WHERE event_name='hallucinated_tool_call' /
COUNT(DISTINCT session_id)
```

### 6. Schema Adherence
```sql
COUNT(*) WHERE event_name='schema_validation_error' /
COUNT(*) WHERE event_name='tool_call_started'
```

### 7. Recovery Rate
```sql
COUNT(DISTINCT session_id WHERE has_errors AND completed) /
COUNT(DISTINCT session_id WHERE has_errors)
```

### 8. Latency per Step
```sql
tool_call_completed.created_at - tool_call_started.created_at
```

### 9. Tool Popularity
```sql
COUNT(*) GROUP BY tool_name WHERE event_name='tool_call_started'
```

### 10. Answer Completeness
```sql
COUNT(*) WHERE event_name='answer_complete' /
COUNT(*) WHERE event_name IN ('answer_complete', 'answer_incomplete')
```

---

## Next Steps

1. **Review** the design document (`EVENT_TRACKING_DESIGN.md`)
2. **Prioritize** which metrics are most important
3. **Implement** Phase 1 events (core tracking)
4. **Add** middleware for automatic tracking
5. **Build** SQL queries for metric calculation
6. **Test** with sample data
7. **Iterate** based on real usage patterns
