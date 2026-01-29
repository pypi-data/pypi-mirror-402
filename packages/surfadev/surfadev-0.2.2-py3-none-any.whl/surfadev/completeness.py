"""
Completeness evaluation functions for analytics SDK.
"""

import json
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def evaluate_completeness_with_openai(
    tool_name: str,
    tool_params: Dict[str, Any],
    result: Any,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> Optional[float]:
    """
    Use OpenAI API to evaluate answer completeness.
    
    Args:
        tool_name: Name of the tool that was called
        tool_params: Parameters passed to the tool
        result: Result returned by the tool
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: OpenAI model to use (default: gpt-4o-mini)
    
    Returns:
        Completeness score between 0.0 and 1.0, or None if evaluation fails
    """
    try:
        from openai import OpenAI
    except ImportError:
        logger.debug("OpenAI package not installed, skipping LLM-based completeness evaluation")
        return None
    
    # Get API key
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.debug("OpenAI API key not found, skipping LLM-based completeness evaluation")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Prepare result summary (truncate if too long)
        result_str = json.dumps(result, indent=2, default=str)
        if len(result_str) > 3000:  # Limit context
            result_str = result_str[:3000] + "... (truncated)"
        
        # Prepare params summary
        params_str = json.dumps(tool_params, indent=2, default=str)
        if len(params_str) > 1000:
            params_str = params_str[:1000] + "... (truncated)"
        
        # Create evaluation prompt
        prompt = f"""Evaluate the completeness of this tool result. Consider:
1. Does the result address the request comprehensively?
2. Are all relevant fields/data present?
3. Is the result meaningful and useful?
4. Does it match what would be expected for this query?

Tool Name: {tool_name}
Tool Parameters:
{params_str}

Result:
{result_str}

Rate completeness from 0.0 to 1.0 where:
- 0.0 = Completely empty or irrelevant
- 0.3 = Partially addresses the request but missing critical information
- 0.5 = Addresses the request but incomplete
- 0.7 = Mostly complete, minor gaps
- 1.0 = Fully complete and comprehensive

Respond ONLY with a JSON object: {{"score": <number>, "reasoning": "<brief explanation>"}}
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at evaluating the completeness and quality of tool responses. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent scoring
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        response_text = response.choices[0].message.content
        evaluation = json.loads(response_text)
        score = float(evaluation.get("score", 0.0))
        
        # Clamp score to [0.0, 1.0]
        score = max(0.0, min(1.0, score))
        
        logger.debug(f"OpenAI completeness evaluation for {tool_name}: {score:.2f} - {evaluation.get('reasoning', '')}")
        return score
        
    except Exception as e:
        logger.warning(f"OpenAI completeness evaluation failed: {e}")
        return None


def _calculate_completeness_heuristic(result: Any) -> float:
    """
    Heuristic to calculate answer completeness score (fallback method).
    
    Args:
        result: Result from tool call (list, dict, or other)
    
    Returns:
        Completeness score between 0.0 and 1.0
    """
    score = 0.0
    
    # Handle different result types
    if isinstance(result, list):
        if len(result) == 0:
            return 0.0
        
        # Has results
        score += 0.3
        
        # Has multiple results
        if len(result) > 1:
            score += 0.2
        
        # Results have required fields (if dicts)
        if result and isinstance(result[0], dict):
            required_fields = ["pod_id", "model_name", "inference_engine"]
            complete_results = sum(
                1 for r in result
                if all(field in r and r[field] for field in required_fields)
            )
            if complete_results > 0:
                score += 0.3 * (complete_results / len(result))
            
            # Results have optional fields (likes, icon_url)
            rich_results = sum(
                1 for r in result
                if "likes" in r or "icon_url" in r
            )
            if rich_results > 0:
                score += 0.2 * (rich_results / len(result))
    
    elif isinstance(result, dict):
        # Has result dict
        if result:
            score += 0.5
        
        # Has results key with items
        if "results" in result and isinstance(result["results"], list):
            if len(result["results"]) > 0:
                score += 0.3
            if len(result["results"]) > 1:
                score += 0.2
        
        # Has error key (negative)
        if "error" in result:
            score -= 0.3
    
    elif result is not None:
        # Non-empty result
        score += 0.5
    
    return min(max(score, 0.0), 1.0)


def calculate_completeness(
    result: Any,
    tool_name: Optional[str] = None,
    tool_params: Optional[Dict[str, Any]] = None,
    use_openai: bool = True
) -> float:
    """
    Calculate answer completeness score using OpenAI API (if available) or heuristics.
    
    Args:
        result: Result from tool call (list, dict, or other)
        tool_name: Name of the tool (for OpenAI evaluation)
        tool_params: Parameters passed to the tool (for OpenAI evaluation)
        use_openai: Whether to try OpenAI evaluation first (default: True)
    
    Returns:
        Completeness score between 0.0 and 1.0
    """
    # Try OpenAI evaluation first if enabled and we have the necessary info
    if use_openai and tool_name and tool_params is not None:
        openai_score = evaluate_completeness_with_openai(
            tool_name=tool_name,
            tool_params=tool_params,
            result=result
        )
        if openai_score is not None:
            return openai_score
    
    # Fallback to heuristic evaluation
    return _calculate_completeness_heuristic(result)
