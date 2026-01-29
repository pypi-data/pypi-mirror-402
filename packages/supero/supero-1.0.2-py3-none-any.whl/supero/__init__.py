"""
Supero - High-level API for multi-tenant object management.

Enhanced with Platform UI integration for tenant management, schema uploads, and SDK generation.
"""

def init(app_name: str = "supero", log_level: str = "INFO"):
    """Initialize Supero environment (loggers, etc.) without connecting to API."""
    try:
        from py_api_lib import api_logger
        api_logger.initialize_logger(app_name, log_level=log_level)
    except Exception:
        pass


# Import main classes
from .core import Supero, SchemaRegistry, SchemaProxy
from .reference import Reference
from .platform_client import (
    PlatformClient,
    AuthenticationError,
    AuthorizationError,
    RateLimitError
)

# Import platform operations
from .platform_operations import (
    register_domain,
    register_user,
    login
)

# Add to imports:
from .ai_manager import (
    ChatResponse,
    Session,
    Tool,
    ToolResult,
    VectorSearchResult,
)
from .crud_manager import CrudManager, CrudQueryBuilder

# Convenience functions for quickstart and connect
def quickstart(name: str, package_namespace: str = None, **kwargs):
    """Convenience function for Supero.quickstart()"""
    return Supero.quickstart(name, package_namespace=package_namespace, **kwargs)


def connect(domain_name: str, api_key: str = None, package_namespace: str = None, **kwargs):
    """Convenience function for Supero.connect()"""
    return Supero.connect(domain_name, api_key=api_key, 
                           package_namespace=package_namespace, **kwargs)


# Public API exports
__all__ = [
    'init',               # Environment initialization
    'register_domain',    # Platform operation
    'register_user',      # Platform operation
    'login',              # Platform operation
    'signup',
    'quickstart',         # Convenience function
    'connect',            # Convenience function
    'Supero',           # Main class
    'Reference',          # For link data
    'SchemaRegistry',     # Explicit registry access
    'SchemaProxy',        # Schema operations proxy
    'CrudManager',        # CRUD operations without SDK
    'CrudQueryBuilder',   # Query builder for CRUD
    'PlatformClient',     # Platform HTTP client
    'AuthenticationError',  # Exception
    'AuthorizationError',   # Exception
    'RateLimitError',       # Exception
    # AI data classes (for type hints)
    'ChatResponse',
    'Session',
    'Tool',
    'ToolResult',
    'VectorSearchResult',
]

__version__ = '1.0.0'
