"""
Analytics SDK for tracking user events and sending them to Supabase.

This SDK tracks user_id, event_name, and metadata (JSON) and sends them
to a Supabase table.
"""

from .client import AnalyticsClient
from .config import AnalyticsConfig
from .session import SessionContext, generate_session_id
from .utils import hash_params
from .completeness import calculate_completeness

__all__ = [
    "AnalyticsClient",
    "AnalyticsConfig",
    "SessionContext",
    "generate_session_id",
    "hash_params",
    "calculate_completeness",
]
__version__ = "0.2.2"

