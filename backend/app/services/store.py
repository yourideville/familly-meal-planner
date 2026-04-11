"""Factory module for the meal planner store.

This module creates the appropriate store implementation based on the
BACKEND_PERSISTENCE_MODE environment variable. It maintains backward
compatibility by delegating module-level function calls to the store instance.

Usage:
    from app.services import store
    
    # Both work the same:
    dishes = store.list_dishes()
    store.add_vote(payload)
    
    # Or use the factory directly:
    from app.services.store import get_store
    store = get_store()
    dishes = store.list_dishes()
"""

import os
import sys
from typing import Any

from app.services.store_interface import StoreInterface

_store: StoreInterface | None = None


def get_store() -> StoreInterface:
    """Get the store singleton based on BACKEND_PERSISTENCE_MODE.
    
    Environment Variables:
        BACKEND_PERSISTENCE_MODE: Either 'inmemory' (default) or 'dynamodb'
        TABLE_NAME: Required when using 'dynamodb' mode
    
    Local Development:
        No environment variables needed - defaults to in-memory mode.
    
    AWS Deployment:
        Set BACKEND_PERSISTENCE_MODE=dynamodb and TABLE_NAME=<your-table>
    """
    global _store
    if _store is None:
        mode = os.getenv("BACKEND_PERSISTENCE_MODE", "inmemory").lower()
        
        if mode == "dynamodb":
            # Validate required environment variables for DynamoDB
            table_name = os.getenv("TABLE_NAME")
            if not table_name:
                raise RuntimeError(
                    "TABLE_NAME environment variable is required when using dynamodb persistence mode. "
                    "Set it to your DynamoDB table name (e.g., 'MealPlanner-production')."
                )
            
            from app.services.store_dynamodb import DynamoDBStore
            _store = DynamoDBStore()
        else:
            # Default to in-memory mode for local development
            from app.services.store_inmemory import InMemoryStore
            _store = InMemoryStore()
    
    return _store


def reset_store() -> None:
    """Reset the store singleton (useful for testing)."""
    global _store
    _store = None


# ---------------------------------------------------------------------------
# Backward compatibility: delegate module-level calls to store instance
# ---------------------------------------------------------------------------

def __getattr__(name: str) -> Any:
    """Delegate module-level attribute access to store instance.
    
    This allows existing code to continue using:
        from app.services import store
        store.list_dishes()
    
    Without any changes, while the factory pattern creates the correct
    implementation based on environment variables.
    """
    store = get_store()
    if hasattr(store, name):
        return getattr(store, name)
    raise AttributeError(f"'{name}' not found in store")
