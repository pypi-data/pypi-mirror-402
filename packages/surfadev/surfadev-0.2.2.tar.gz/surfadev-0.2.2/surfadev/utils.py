"""
Utility functions for analytics SDK.
"""

import hashlib
import json
from typing import Dict, Any


def hash_params(params: Dict[str, Any]) -> str:
    """
    Generate hash of parameters for retry detection.
    
    Args:
        params: Dictionary of parameters to hash
    
    Returns:
        MD5 hash of the sorted JSON representation of params
    """
    params_json = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(params_json.encode()).hexdigest()
