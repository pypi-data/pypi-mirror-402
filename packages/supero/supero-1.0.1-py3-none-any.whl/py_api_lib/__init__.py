"""
py_api_lib - Build-aware API library for Supero Platform

Build mode is determined at build time and embedded in _build_config.py
"""
import warnings

__version__ = "1.0.0"

# Default build configuration (fallback)
_BUILD_MODE = 'platform'
_PRIMARY_SCHEMA_NAMESPACE = 'pymodel_system'
_SCHEMA_NAMESPACES = ['pymodel_system']
_TENANT_NAMESPACE = None

def _default_get_build_info():
    """Default build info function"""
    return {
        'mode': _BUILD_MODE,
        'primary_namespace': _PRIMARY_SCHEMA_NAMESPACE,
        'available_namespaces': _SCHEMA_NAMESPACES,
        'tenant': 'system',
        'timestamp': 'unknown',
        'version': __version__,
    }

# Try to load actual build config
try:
    from ._build_config import (
        BUILD_MODE as _BUILD_MODE,
        PRIMARY_SCHEMA_NAMESPACE as _PRIMARY_SCHEMA_NAMESPACE,
        SCHEMA_NAMESPACES as _SCHEMA_NAMESPACES,
        TENANT_NAMESPACE as _TENANT_NAMESPACE,  # ← Add this
        get_build_info as _get_build_info_func
    )
    get_build_info = _get_build_info_func
except ImportError:
    # Use fallback
    get_build_info = _default_get_build_info
    _TENANT_NAMESPACE = None  # ← Add this
    warnings.warn(
        "Build configuration not found. Using default (platform mode). "
        "Run build.sh to generate proper configuration.",
        RuntimeWarning
    )

# Export as module-level variables (so they can be imported)
BUILD_MODE = _BUILD_MODE
PRIMARY_SCHEMA_NAMESPACE = _PRIMARY_SCHEMA_NAMESPACE
SCHEMA_NAMESPACES = _SCHEMA_NAMESPACES
TENANT_NAMESPACE = _TENANT_NAMESPACE

# Core exports
__all__ = [
    'TENANT_NAMESPACE',
    'ApiClient',
    'ApiLib',
    'ApiException',
    'AuthenticationError',
    'ValidationError',
    'NotFoundError',
    'ConflictError',
    'ServerError',
    'BUILD_MODE',
    'PRIMARY_SCHEMA_NAMESPACE',
    'SCHEMA_NAMESPACES',
    'get_build_info',
    'get_version',
    'get_info',
]

# Import exceptions (no schema dependency)
from .exceptions import (
    ApiException,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    ServerError,
)

# Import ApiClient (no schema dependency at import time)
ApiClient = None
try:
    from .api_client import ApiClient
except ImportError as e:
    warnings.warn(f"ApiClient import issue: {e}")
except Exception as e:
    warnings.warn(f"ApiClient unexpected error: {e}")

# Import ApiLib (has runtime schema discovery)
ApiLib = None
try:
    from .api_lib import ApiLib
except ImportError as e:
    warnings.warn(f"ApiLib import issue: {e}")
except Exception as e:
    warnings.warn(f"ApiLib unexpected error: {e}")


def check_schema_availability():
    """
    Check which schema packages are available.
    Respects build configuration priorities.

    Returns:
        dict: Schema availability status
    """
    import importlib

    schemas = {}

    # Check dynamically using importlib (works with any namespace)
    for namespace in SCHEMA_NAMESPACES:
        try:
            importlib.import_module(f"{namespace}.objects")
            schemas[namespace] = True
        except ImportError:
            schemas[namespace] = False

    return schemas

def get_version():
    """Get library version"""
    return __version__


def get_info():
    """
    Get comprehensive library information.
    
    Returns:
        dict: Library information including build config
    """
    schemas = check_schema_availability()
    build_info = get_build_info()
    
    return {
        'version': __version__,
        'build_mode': BUILD_MODE,
        'primary_namespace': PRIMARY_SCHEMA_NAMESPACE,
        'expected_namespaces': SCHEMA_NAMESPACES,
        'schemas_available': schemas,
        'schemas_missing': [ns for ns in SCHEMA_NAMESPACES if not schemas.get(ns, False)],
        'api_client_available': ApiClient is not None,
        'api_lib_available': ApiLib is not None,
        'build_info': build_info,
    }
