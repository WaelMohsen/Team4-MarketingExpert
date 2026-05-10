import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load env vars before importing Langfuse
load_dotenv()

from langfuse import Langfuse, get_client, observe, propagate_attributes

logger = logging.getLogger(__name__)

# Initialize client
langfuse = get_client()

def get_langfuse_client() -> Langfuse:
    """Returns the initialized Langfuse client."""
    return langfuse

def set_trace_metadata(user_id: Optional[str] = None, session_id: Optional[str] = None, metadata: Optional[Dict[str, str]] = None, tags: Optional[list] = None):
    """
    Sets metadata for the current trace/observation context.
    In v4, use propagate_attributes for context-wide attributes.
    For dynamic updates to the current observation, use update_current_observation logic.
    """
    # Note: propagate_attributes is a context manager. 
    # For one-off updates to the current span:
    if user_id or session_id or metadata or tags:
        try:
            langfuse.update_current_span(
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
                tags=tags
            )
        except Exception as e:
            logger.warning(f"Failed to update current span metadata: {e}")

def log_evaluation_score(name: str, value: float, comment: Optional[str] = None):
    """Logs an evaluation score to the current Langfuse trace."""
    try:
        langfuse.score_current_trace(
            name=name,
            value=float(value),
            comment=comment
        )
    except Exception as e:
        logger.error(f"Failed to log evaluation score: {e}")

def flush_langfuse():
    """Ensure all traces are sent before exit."""
    try:
        langfuse.flush()
    except Exception as e:
        logger.error(f"Failed to flush Langfuse: {e}")

def update_current_observation(metadata: Optional[Dict[str, str]] = None, **kwargs):
    """
    Updates the current observation (span/generation) metadata and attributes.
    In v4, this calls update_current_span or update_current_generation under the hood.
    """
    try:
        # Langfuse v4 uses update_current_span for general observations
        langfuse.update_current_span(metadata=metadata, **kwargs)
    except Exception as e:
        # Fallback to update_current_generation if it's a generation
        try:
            langfuse.update_current_generation(metadata=metadata, **kwargs)
        except:
            logger.warning(f"Failed to update current observation: {e}")

def track_event(name: str, metadata: Optional[Dict[str, Any]] = None):
    """Logs a custom event within a span or trace."""
    update_current_observation(metadata={**(metadata or {}), "event_name": str(name)})
