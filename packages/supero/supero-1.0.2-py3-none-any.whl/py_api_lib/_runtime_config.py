"""
Runtime configuration - centralizes build config and serialization imports.
Both api_lib.py and api_client.py import from here.
"""
import importlib

# ============================================================================
# BUILD CONFIGURATION (with safe fallbacks)
# ============================================================================
BUILD_MODE = 'platform'
PRIMARY_SCHEMA_NAMESPACE = 'pymodel_system'
SCHEMA_NAMESPACES = ['pymodel_system']
BUILD_TENANT = 'system'
TENANT_NAMESPACE = None
BUILD_TIMESTAMP = None
BUILD_VERSION = '1.0.0'

# Import module and explicitly assign to module-level variables
try:
    from . import _build_config

    # Explicitly assign each variable from _build_config to module scope
    BUILD_MODE = _build_config.BUILD_MODE
    PRIMARY_SCHEMA_NAMESPACE = _build_config.PRIMARY_SCHEMA_NAMESPACE
    SCHEMA_NAMESPACES = _build_config.SCHEMA_NAMESPACES
    BUILD_TENANT = _build_config.BUILD_TENANT
    TENANT_NAMESPACE = _build_config.TENANT_NAMESPACE
    BUILD_TIMESTAMP = _build_config.BUILD_TIMESTAMP
    BUILD_VERSION = _build_config.BUILD_VERSION
    get_build_info = _build_config.get_build_info

except ImportError as e:
    # Fallback function if _build_config doesn't exist
    def get_build_info():
        return {
            'mode': BUILD_MODE,
            'primary_namespace': PRIMARY_SCHEMA_NAMESPACE,
            'available_namespaces': SCHEMA_NAMESPACES,
            'tenant': BUILD_TENANT,
            'tenant_namespace': TENANT_NAMESPACE,
            'timestamp': BUILD_TIMESTAMP,
            'version': BUILD_VERSION,
        }

def is_platform():
    """Check if running in platform mode."""
    return BUILD_MODE == 'platform'


def is_tenant():
    """Check if running in tenant mode."""
    return BUILD_MODE == 'tenant'


# ============================================================================
# SERIALIZATION UTILITIES (dynamically imported)
# ============================================================================
def _import_serialization_utils():
    """Import serialization utilities from the primary namespace."""
    primary_ns = PRIMARY_SCHEMA_NAMESPACE
    
    # Try primary namespace first
    try:
        module = importlib.import_module(f"{primary_ns}.serialization_errors")
        return (
            getattr(module, 'SerializationError', None),
            getattr(module, 'ObjectSerializationError', None),
            getattr(module, 'ObjectDeserializationError', None),
            getattr(module, 'JSONSerializationError', None),
            getattr(module, 'JSONDeserializationError', None),
            getattr(module, 'safe_serialize_to_dict', None),
            getattr(module, 'safe_serialize_to_json', None),
            getattr(module, 'safe_deserialize_from_dict', None),
            getattr(module, 'safe_deserialize_from_json', None),
        )
    except ImportError:
        pass
    
    # Fallback to pymodel_system
    try:
        from pymodel_system.serialization_errors import (
            SerializationError,
            ObjectSerializationError,
            ObjectDeserializationError,
            JSONSerializationError,
            JSONDeserializationError,
            safe_serialize_to_dict,
            safe_serialize_to_json,
            safe_deserialize_from_dict,
            safe_deserialize_from_json
        )
        return (
            SerializationError,
            ObjectSerializationError,
            ObjectDeserializationError,
            JSONSerializationError,
            JSONDeserializationError,
            safe_serialize_to_dict,
            safe_serialize_to_json,
            safe_deserialize_from_dict,
            safe_deserialize_from_json,
        )
    except ImportError as e:
        raise ImportError(
            f"Could not import serialization utilities from '{primary_ns}' or 'pymodel_system'. "
            f"Ensure SDK is properly installed. Error: {e}"
        )


# Import once at module load
(
    SerializationError,
    ObjectSerializationError,
    ObjectDeserializationError,
    JSONSerializationError,
    JSONDeserializationError,
    safe_serialize_to_dict,
    safe_serialize_to_json,
    safe_deserialize_from_dict,
    safe_deserialize_from_json,
) = _import_serialization_utils()


# ============================================================================
# CONVENIENCE EXPORTS
# ============================================================================
__all__ = [
    # Build config
    'BUILD_MODE',
    'PRIMARY_SCHEMA_NAMESPACE', 
    'SCHEMA_NAMESPACES',
    'BUILD_TENANT',
    'TENANT_NAMESPACE',
    'BUILD_TIMESTAMP',
    'BUILD_VERSION',
    'get_build_info',
    'is_platform',
    'is_tenant',
    # Serialization errors
    'SerializationError',
    'ObjectSerializationError',
    'ObjectDeserializationError',
    'JSONSerializationError',
    'JSONDeserializationError',
    # Serialization functions
    'safe_serialize_to_dict',
    'safe_serialize_to_json',
    'safe_deserialize_from_dict',
    'safe_deserialize_from_json',
]
