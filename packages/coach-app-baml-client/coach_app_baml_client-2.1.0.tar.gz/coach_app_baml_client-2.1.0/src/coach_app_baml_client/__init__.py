"""
Coach App BAML Client - Generated Types and Client

This package provides BAML-generated Pydantic models and client code
for coach-app boundary contracts. Types are generated from BAML source
files and should not be manually edited.

Usage:
    from coach_app_baml_client.types import (
        ChatRequest,
        ChatResponse,
        EventEnvelope,
        EventType,
        MessageRole,
    )

The baml_client subpackage contains the generated BAML client code.
"""

__version__ = "2.1.0"

# Re-export types from generated baml_client when available
# This file serves as the entry point; actual types are in baml_client/
try:
    from .baml_client.types import *  # noqa: F401, F403
except ImportError:
    # baml_client not yet generated - this is expected during initial setup
    pass
