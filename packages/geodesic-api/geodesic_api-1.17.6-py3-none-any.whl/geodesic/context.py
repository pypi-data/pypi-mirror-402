"""Context management for geodesic API.

This module provides a context manager that allows temporary switching of:
- Cluster (endpoint)
- API key (authentication)
- Project (active project)

This is useful for scenarios like:
1. Temporarily using admin credentials
2. MCP servers handling multiple user contexts
3. Switching between clusters/projects in notebooks

Example:
    >>> with use_context(cluster="prod", project="analysis"):
    ...     datasets = get_datasets()  # Uses prod cluster and analysis project

    >>> with use_context(api_key=admin_key):
    ...     create_project("new-project")  # Uses admin API key
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Optional, Dict, Any
from dataclasses import dataclass


# Context variables for thread/async-safe state management
_context_cluster = ContextVar("geodesic_context_cluster", default=None)
_context_api_key = ContextVar("geodesic_context_api_key", default=None)
_context_project = ContextVar("geodesic_context_project", default=None)

# Cache for context-specific objects (auth managers, configs, etc.)
_context_cache = ContextVar("geodesic_context_cache", default=None)


@dataclass
class _ContextState:
    """Internal state for a context."""

    cluster: Optional[str] = None
    api_key: Optional[str] = None
    project: Optional[str] = None

    def copy(self) -> "_ContextState":
        """Create a copy of this context state."""
        return _ContextState(cluster=self.cluster, api_key=self.api_key, project=self.project)


def _get_current_context() -> Optional[_ContextState]:
    """Get the current context state, or None if not in a context."""
    cluster = _context_cluster.get()
    api_key = _context_api_key.get()
    project = _context_project.get()

    # Only return a context if at least one value is set
    if cluster is None and api_key is None and project is None:
        return None

    return _ContextState(cluster=cluster, api_key=api_key, project=project)


def get_context_cluster() -> Optional[str]:
    """Get the cluster from the current context, or None if not set."""
    return _context_cluster.get()


def get_context_api_key() -> Optional[str]:
    """Get the API key from the current context, or None if not set."""
    return _context_api_key.get()


def get_context_project() -> Optional[str]:
    """Get the project from the current context, or None if not set."""
    return _context_project.get()


def get_context_cache() -> Dict[str, Any]:
    """Get the cache for the current context."""
    cache = _context_cache.get()
    if cache is None:
        cache = {}
        _context_cache.set(cache)
    return cache


def clear_context_cache():
    """Clear the cache for the current context."""
    _context_cache.set({})


@contextmanager
def use_context(
    cluster: Optional[str] = None,
    api_key: Optional[str] = None,
    project: Optional[str] = None,
):
    """Context manager for temporarily using a different context.

    This allows you to temporarily switch the cluster, API key, and/or project
    for API operations within the context block. Changes are scoped to the
    current thread/async task and do not affect other threads or persist after
    the context exits.

    Contexts can be nested, with inner contexts inheriting and optionally
    overriding values from outer contexts.

    Args:
        cluster: Name of the cluster to use (from config file)
        api_key: API key to use for authentication (overrides cluster's key)
        project: Project name/uid to use as active project

    Example:
        Basic usage:
        >>> with use_context(cluster="seerai", project="analysis"):
        ...     # All operations use seerai cluster and analysis project
        ...     datasets = get_datasets()

        Temporary admin access:
        >>> with use_context(api_key=admin_key):
        ...     create_project("new-project")  # Uses admin permissions

        Nested contexts (inherit and override):
        >>> with use_context(cluster="dev", project="test"):
        ...     with use_context(project="staging"):
        ...         # Uses cluster="dev" (inherited) and project="staging" (overridden)
        ...         get_datasets()

    Note:
        - Tokens obtained within a context are ephemeral (memory only)
        - Refresh tokens are NOT written to disk within a context
        - Context is thread/async-safe (each thread/task has its own context)
    """
    # Get current context to inherit from (for nesting)
    current = _get_current_context()

    # Determine the new context values (inherit and override)
    new_cluster = cluster if cluster is not None else (current.cluster if current else None)
    new_api_key = api_key if api_key is not None else (current.api_key if current else None)
    new_project = project if project is not None else (current.project if current else None)

    # Save the tokens for restoring
    prev_cluster_token = _context_cluster.set(new_cluster)
    prev_api_key_token = _context_api_key.set(new_api_key)
    prev_project_token = _context_project.set(new_project)
    prev_cache_token = _context_cache.set({})  # New cache for this context

    try:
        yield
    finally:
        # Restore previous context
        _context_cluster.reset(prev_cluster_token)
        _context_api_key.reset(prev_api_key_token)
        _context_project.reset(prev_project_token)
        _context_cache.reset(prev_cache_token)
