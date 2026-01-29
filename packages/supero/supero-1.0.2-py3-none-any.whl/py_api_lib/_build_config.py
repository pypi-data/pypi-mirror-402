"""
Build configuration - auto-generated during build process.
DO NOT EDIT MANUALLY - this file is regenerated on each build.

Phase 1: Tenant builds use single merged namespace (system schemas included).
Phase 2: Isolated py_api_lib per tenant/platform.
"""
BUILD_MODE = 'platform'
PRIMARY_SCHEMA_NAMESPACE = 'pymodel_system'
SCHEMA_NAMESPACES = ['pymodel_system']
BUILD_TENANT = 'system'
BUILD_TIMESTAMP = '2026-01-20T16:48:24+00:00'
BUILD_VERSION = '1.0.0'
PY_API_LIB_PACKAGE = 'py_api_lib_system'

# Tenant-specific namespace for isolation (None for platform builds)
TENANT_NAMESPACE = None

def get_build_info():
    return {
        'mode': BUILD_MODE,
        'primary_namespace': PRIMARY_SCHEMA_NAMESPACE,
        'available_namespaces': SCHEMA_NAMESPACES,
        'tenant': BUILD_TENANT,
        'tenant_namespace': TENANT_NAMESPACE,
        'py_api_lib_package': PY_API_LIB_PACKAGE,
        'timestamp': BUILD_TIMESTAMP,
        'version': BUILD_VERSION,
    }
