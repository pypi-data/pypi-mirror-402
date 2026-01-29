"""
Schema Management - Handle schema upload, validation, and organization.

Manages schemas in the standard directory structure:
    schemas/
    ├── objects/        → DB Object schemas (CRUD enabled)
    ├── types/          → Composite types (no CRUD)
    ├── enums/          → Enumeration types (no CRUD)
    └── operational/    → Operational workflow objects (no CRUD)

SCHEMA TYPES (singular form - used in schema content):
- 'object': First-class entities with CRUD APIs
- 'type': User-defined embedded types (no CRUD)
- 'enum': Fixed set of allowed values (no CRUD)
- 'operational': Operational workflow objects (no CRUD)

STORAGE DIRECTORIES (plural form - used for paths):
- /objects/: Object schema files
- /types/: Type schema files
- /enums/: Enum schema files
- /operational/: Operational schema files

REFACTORED v4.0 (Context-Aware Architecture):
- ✅ Context-aware: Gets domain/project from PlatformClient
- ✅ Single source of truth: No redundant domain parameters
- ✅ Cleaner API: Fewer parameters needed
- ✅ Project-level filtering in list/search operations
- ✅ RBAC support: api_key parameter in all methods
- ✅ Schema type normalization (singular/plural handling)
- ✅ Storage directory mapping utilities
- ✅ Operational type handling (no CRUD operations)
- ✅ Enhanced logging with domain/project context
- ✅ Backward compatible
"""

import os
import json
import glob
from typing import Dict, List, Any, Optional
import logging

from .schema_validator import SchemaValidator, SchemaValidationError


# =============================================================================
# SCHEMA TYPE UTILITIES
# =============================================================================

# Valid schema_type values (singular form - stored in schema content)
VALID_SCHEMA_TYPES = {'object', 'type', 'enum', 'operational'}

# Schema types that support CRUD operations
CRUD_ENABLED_TYPES = {'object'}

# Mapping from schema_type (singular) to storage directory (plural)
SCHEMA_TYPE_TO_DIRECTORY = {
    'object': 'objects',
    'type': 'types',
    'enum': 'enums',
    'operational': 'operational',  # Same for both (no plural form)
    # Legacy support: also accept plural forms and map to correct directory
    'objects': 'objects',
    'types': 'types',
    'enums': 'enums',
}

# Mapping from storage directory (plural) to schema_type (singular)
DIRECTORY_TO_SCHEMA_TYPE = {
    'objects': 'object',
    'types': 'type',
    'enums': 'enum',
    'operational': 'operational',
}

# All valid storage directories (plural)
STORAGE_DIRECTORIES = ['objects', 'types', 'enums', 'operational']


def get_storage_directory(schema_type: str) -> str:
    """
    Convert schema_type to storage directory name.
    
    Schema types are stored as singular ('object', 'type', 'enum', 'operational')
    but storage directories use plural ('objects', 'types', 'enums', 'operational').
    
    Args:
        schema_type: Schema type (singular or plural for backward compatibility)
        
    Returns:
        Storage directory name (plural form, except 'operational')
        
    Examples:
        >>> get_storage_directory('object')
        'objects'
        >>> get_storage_directory('enum')
        'enums'
        >>> get_storage_directory('operational')
        'operational'
        >>> get_storage_directory('objects')  # Legacy support
        'objects'
    """
    if not schema_type:
        return 'objects'  # Default
    
    directory = SCHEMA_TYPE_TO_DIRECTORY.get(schema_type.lower())
    if not directory:
        # Default to objects if unknown
        return 'objects'
    return directory


def normalize_schema_type(schema_type: str) -> str:
    """
    Normalize schema_type to singular form.
    
    Args:
        schema_type: Schema type (singular or plural)
        
    Returns:
        Normalized schema type (always singular: 'object', 'type', 'enum', 'operational')
        
    Examples:
        >>> normalize_schema_type('objects')
        'object'
        >>> normalize_schema_type('object')
        'object'
        >>> normalize_schema_type('enums')
        'enum'
        >>> normalize_schema_type('operational')
        'operational'
    """
    if not schema_type:
        return 'object'  # Default
    
    schema_type_lower = schema_type.lower()
    
    # If already singular, return as-is
    if schema_type_lower in VALID_SCHEMA_TYPES:
        return schema_type_lower
    
    # Convert plural to singular
    singular = DIRECTORY_TO_SCHEMA_TYPE.get(schema_type_lower)
    if singular:
        return singular
    
    return 'object'  # Default


def is_crud_enabled(schema_type: str) -> bool:
    """
    Check if a schema type supports CRUD operations.
    
    Only 'object' schemas have CRUD operations (create, read, update, delete).
    Types, enums, and operational schemas are embedded/referenced only.
    
    Args:
        schema_type: Schema type (singular or plural)
        
    Returns:
        True if CRUD operations are supported
        
    Examples:
        >>> is_crud_enabled('object')
        True
        >>> is_crud_enabled('objects')
        True
        >>> is_crud_enabled('type')
        False
        >>> is_crud_enabled('operational')
        False
    """
    normalized = normalize_schema_type(schema_type)
    return normalized in CRUD_ENABLED_TYPES


def get_schema_type_description(schema_type: str) -> str:
    """
    Get a human-readable description of a schema type.
    
    Args:
        schema_type: Schema type (singular or plural)
        
    Returns:
        Description string
    """
    normalized = normalize_schema_type(schema_type)
    descriptions = {
        'object': 'DB Object schema (CRUD enabled)',
        'type': 'Composite type (embedded, no CRUD)',
        'enum': 'Enumeration type (no CRUD)',
        'operational': 'Operational workflow object (no CRUD)',
    }
    return descriptions.get(normalized, 'Unknown schema type')


class SchemaManager:
    """
    Manages schema operations for a domain with multi-project support.
    
    Handles:
    - Schema upload (single and batch)
    - Schema validation
    - Schema listing and retrieval (with project filtering)
    - Schema export
    - Type auto-detection from directory structure
    
    Schema Type Handling:
    - 'object': First-class entities with CRUD APIs
    - 'type': User-defined embedded types (no CRUD)
    - 'enum': Fixed set of allowed values (no CRUD)
    - 'operational': Operational workflow objects (no CRUD)
    
    NEW in v3.0:
    - Multi-project support: schemas can be scoped to projects
    - RBAC support: api_key parameter for per-call authorization
    - Project-level filtering for schema operations
    - Schema type normalization (singular/plural)
    - Storage directory mapping
    - Enhanced logging with domain/project context
    
    Data Model:
    - Schemas: domain level (with optional project scope)
    - NOT at tenant level (schemas are shared across tenants)
    """
    
    def __init__(
        self,
        platform_client,
        logger: logging.Logger = None,
        project_uuid: str = None
    ):
        """
        Initialize SchemaManager with context-aware client.
        
        Args:
            platform_client: PlatformClient instance (contains domain/project context)
            logger: Logger instance (creates new if None)
            project_uuid: Project UUID override (uses client.project_uuid if None)
        
        Example:
            >>> # Simple - context from client (recommended)
            >>> schema_mgr = SchemaManager(platform_client=client, logger=logger)
            >>> print(schema_mgr.domain_name)  # From client.domain_name
            >>> 
            >>> # Override project if needed
            >>> schema_mgr = SchemaManager(
            ...     platform_client=client,
            ...     project_uuid='other-project'  # Override
            ... )
            >>> 
            >>> # Operations use context automatically
            >>> result = schema_mgr.upload_schema(
            ...     schema_file='schemas/objects/Customer.json'
            ...     # domain/project automatically included!
            ... )
        """
        self.client = platform_client
        self.logger = logger or logging.getLogger(__name__)
        
        # ✅ REFACTORED: Extract from client, allow override
        self.domain_name = platform_client.domain_name
        self.domain_uuid = platform_client.domain_uuid
        self.project_uuid = project_uuid or platform_client.project_uuid
        
        # Log context
        if project_uuid:
            self.logger.debug(
                f"SchemaManager initialized: domain={self.domain_name}, "
                f"project={self.project_uuid[:8]}..."
            )
        else:
            self.logger.debug(f"SchemaManager initialized: domain={self.domain_name}")
    
    # ============================================
    # SCHEMA TYPE UTILITIES (Instance Methods)
    # ============================================
    
    def get_storage_directory(self, schema_type: str) -> str:
        """
        Convert schema_type to storage directory name.
        
        Args:
            schema_type: Schema type (singular or plural)
            
        Returns:
            Storage directory name
        """
        return get_storage_directory(schema_type)
    
    def normalize_schema_type(self, schema_type: str) -> str:
        """
        Normalize schema_type to singular form.
        
        Args:
            schema_type: Schema type (singular or plural)
            
        Returns:
            Normalized schema type (singular)
        """
        return normalize_schema_type(schema_type)
    
    def is_crud_enabled(self, schema_type: str) -> bool:
        """
        Check if a schema type supports CRUD operations.
        
        Args:
            schema_type: Schema type (singular or plural)
            
        Returns:
            True if CRUD operations are supported
        """
        return is_crud_enabled(schema_type)
    
    # ============================================
    # SCHEMA UPLOAD
    # ============================================
    
    def upload_schema(
        self,
        schema_file: str,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        schema_type: str = None,
        description: str = None,
        validate: bool = True,
        version: str = '1.0.0',
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Upload schema definition (JSON format) to domain/project.
        
        Args:
            schema_file: Path to schema JSON file
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            schema_type: Schema type ('object', 'type', 'enum', 'operational')
                        Also accepts plural forms for backward compatibility
            description: Schema description
            validate: Validate schema before upload (default: True)
            version: Schema version (default: '1.0.0')
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            Schema upload result with schema info
        
        Note:
            - 'object' schemas will have CRUD operations generated
            - 'type', 'enum', 'operational' schemas are embedded/referenced only
            - Schemas are stored at domain level, optionally scoped to project
        
        Example:
            >>> # Domain-level schema
            >>> result = schema_mgr.upload_schema(
            ...     schema_file='schemas/objects/project.json',
            ...     schema_type='object'
            ... )
            >>> 
            >>> # Project-scoped schema with RBAC
            >>> result = schema_mgr.upload_schema(
            ...     schema_file='schemas/objects/customer.json',
            ...     project_uuid='project-456',
            ...     api_key=admin_api_key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        if not schema_file.endswith('.json'):
            raise ValueError(
                f"Only JSON format is supported. Got: {schema_file}\n"
                "Please use .json extension for schema files."
            )
        
        # Read schema file
        try:
            with open(schema_file, 'r') as f:
                schema_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
        
        # Auto-detect schema type from directory structure
        if schema_type is None:
            schema_type = self._detect_schema_type(schema_file)
        
        # ✅ Normalize schema_type to singular form
        normalized_type = normalize_schema_type(schema_type)
        storage_dir = get_storage_directory(schema_type)
        
        # Validate schema type
        if normalized_type not in VALID_SCHEMA_TYPES:
            raise ValueError(
                f"Invalid schema_type: {schema_type}. "
                f"Must be one of: {', '.join(VALID_SCHEMA_TYPES)} "
                f"(or plural forms: {', '.join(STORAGE_DIRECTORIES)})"
            )
        
        # ✅ Log CRUD status for transparency
        if is_crud_enabled(normalized_type):
            self.logger.debug(
                f"Schema type '{normalized_type}' supports CRUD operations"
            )
        else:
            self.logger.debug(
                f"Schema type '{normalized_type}' does NOT support CRUD operations "
                "(embedded/referenced only)"
            )
        
        # Validate if requested (basic client-side validation)
        if validate:
            validation = self._validate_schema_basic(schema_data, normalized_type)
            if not validation['valid']:
                errors = '\n  - '.join(validation['errors'])
                raise ValueError(f"Schema validation failed:\n  - {errors}")
        
        # Build payload matching actual API format
        payload = {
            'domain_uuid': domain_uuid,
            'domain_name': self.domain_name,
            'schemas': [
                {
                    'name': schema_data.get('name'),
                    'schema_type': normalized_type,
                    'schema_category': 'tenant',
                    'schema_content': schema_data,
                    'version': version,
                    'description': description
                }
            ],
            'skip_existing': True,
            'check_compatibility': True
        }
        
        # ✅ Add project_uuid if provided
        if project_uuid:
            payload['project_uuid'] = project_uuid
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key
        
        # Send as JSON request
        result = self.client.post('/schemas/upload', **kwargs)
        
        # Parse response - API returns array
        if result.get('schemas'):
            schema_info = result['schemas'][0]
            schema_name = schema_info.get('name', 'unknown')
            
            # ✅ Enhanced logging with project context
            crud_status = "CRUD enabled" if is_crud_enabled(normalized_type) else "no CRUD"
            project_str = f", project={project_uuid[:8]}..." if project_uuid else ""
            self.logger.info(
                f"✓ Uploaded {normalized_type} schema '{schema_name}' to domain "
                f"'{self.domain_name}'{project_str} ({crud_status})"
            )
            return {'schema': schema_info, 'full_response': result}
        
        # Handle errors
        if result.get('failed'):
            failed_info = result['failed'][0]
            raise ValueError(f"Schema upload failed: {failed_info.get('error')}")
        
        return result
    
    def upload_schemas(
        self,
        directory: str,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        recursive: bool = True,
        api_key: str = None,  # ✅ NEW (RBAC)
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Upload multiple schemas from directory structure.
        
        Supports the standard directory structure:
            schemas/
            ├── objects/        → DB Object schemas (CRUD enabled)
            ├── types/          → Composite types (no CRUD)
            ├── enums/          → Enumeration types (no CRUD)
            └── operational/    → Operational workflow objects (no CRUD)
        
        Args:
            directory: Base directory containing schema files
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            recursive: Recursively scan subdirectories (default: True)
            api_key: API key for RBAC (optional, overrides instance default)
            **kwargs: Additional args for upload_schema (e.g., validate=False)
        
        Returns:
            {
                'objects': [result1, result2, ...],    # CRUD enabled
                'types': [result1, ...],              # No CRUD
                'enums': [result1, ...],              # No CRUD
                'operational': [result1, ...],        # No CRUD
                'errors': [{'file': 'path', 'error': 'msg'}, ...]
            }
        
        Example:
            >>> # Upload to domain
            >>> results = schema_mgr.upload_schemas(directory='schemas/')
            >>> 
            >>> # Upload to specific project with RBAC
            >>> results = schema_mgr.upload_schemas(
            ...     directory='schemas/',
            ...     project_uuid='project-456',
            ...     api_key=admin_api_key
            ... )
        """
        validator = SchemaValidator()
        
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find all JSON files
        if recursive:
            pattern = os.path.join(directory, '**', '*.json')
            schema_files = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(directory, '*.json')
            schema_files = glob.glob(pattern)
        
        if not schema_files:
            context_str = f"domain '{self.domain_name}'"
            if project_uuid:
                context_str += f", project {project_uuid[:8]}..."
            self.logger.warning(
                f"No JSON schema files found in: {directory} for {context_str}"
            )
            return {
                'objects': [],
                'types': [],
                'enums': [],
                'operational': [],
                'errors': []
            }
        
        # ✅ Categorize results by storage directory (plural)
        results = {
            'objects': [],
            'types': [],
            'enums': [],
            'operational': [],
            'errors': []
        }
        
        context_str = f"domain '{self.domain_name}'"
        if project_uuid:
            context_str += f", project {project_uuid[:8]}..."
        self.logger.info(
            f"Found {len(schema_files)} schema files in {directory} for {context_str}"
        )
        
        # Upload each schema
        for schema_file in sorted(schema_files):
            try:
                detected_type = self._detect_schema_type(schema_file)
                normalized_type = normalize_schema_type(detected_type)
                storage_dir = get_storage_directory(detected_type)
                
                # Validate schema
                with open(schema_file, 'r') as f:
                    schema = json.load(f)

                if not schema:
                    raise ValueError(f"Empty schema file: {schema_file}")

                # Validate schema structure
                validation_errors = validator.validate_schema(
                     schema,
                     schema.get('name'),
                     schema_file
                )

                if validation_errors:
                    # User-friendly console output
                    print(f"\n{'='*80}")
                    print(f"❌ Schema Validation Failed: {os.path.basename(schema_file)}")
                    print(f"{'='*80}\n")
                    
                    for error in validation_errors:
                        print(error)
                        print()
                    
                    self.logger.error(
                        f"Schema validation failed: {os.path.basename(schema_file)} "
                        f"({len(validation_errors)} error(s))"
                    )
                    
                    results['errors'].append({
                        'file': os.path.basename(schema_file),
                        'error': 'Validation failed',
                        'count': len(validation_errors)
                    })
                    continue

                result = self.upload_schema(
                    domain_uuid=domain_uuid,
                    project_uuid=project_uuid,  # ✅ Pass project context
                    schema_file=schema_file,
                    schema_type=normalized_type,
                    api_key=api_key  # ✅ Pass RBAC
                )

                # ✅ Categorize by storage directory (plural)
                if storage_dir in results:
                    results[storage_dir].append(result)
                else:
                    results['objects'].append(result)  # Default

                # ✅ Include CRUD status in log
                crud_indicator = "✓" if is_crud_enabled(normalized_type) else "○"
                self.logger.info(f"  {crud_indicator} {os.path.basename(schema_file)} ({normalized_type})")

            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {os.path.basename(schema_file)}: {e}")
                results['errors'].append({
                    'file': os.path.basename(schema_file),
                    'error': f'Invalid JSON: {str(e)}'
                })
            except Exception as e:
                error_entry = {
                    'file': schema_file,
                    'filename': os.path.basename(schema_file),
                    'error': str(e)
                }
                results['errors'].append(error_entry)
                self.logger.error(f"  ✗ {os.path.basename(schema_file)}: {e}")
        
        # ✅ Enhanced summary with CRUD status and project context
        total_crud = len(results['objects'])
        total_no_crud = len(results['types']) + len(results['enums']) + len(results['operational'])
        total_success = total_crud + total_no_crud
        total_errors = len(results['errors'])
        
        project_str = f", project {project_uuid[:8]}..." if project_uuid else ""
        self.logger.info(
            f"\nUpload Summary for domain '{self.domain_name}'{project_str}:\n"
            f"  Objects (CRUD enabled): {len(results['objects'])}\n"
            f"  Types (no CRUD): {len(results['types'])}\n"
            f"  Enums (no CRUD): {len(results['enums'])}\n"
            f"  Operational (no CRUD): {len(results['operational'])}\n"
            f"  Errors: {total_errors}\n"
            f"  ─────────────────────────\n"
            f"  Total with CRUD: {total_crud}\n"
            f"  Total without CRUD: {total_no_crud}\n"
            f"  Total Success: {total_success}/{total_success + total_errors}"
        )
        
        return results
    
    # ============================================
    # SCHEMA RETRIEVAL
    # ============================================
    
    def list_schemas(
        self,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        schema_type: str = None,
        status: str = 'active',
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> List[Dict[str, Any]]:
        """
        List schemas in domain/project from Platform Core.
        
        Args:
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            schema_type: Filter by type ('object', 'type', 'enum', 'operational')
                        Also accepts plural forms for backward compatibility
            status: Filter by status (default: 'active')
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            List of schema info dicts
        
        Example:
            >>> # List all schemas in domain
            >>> schemas = schema_mgr.list_schemas()
            >>> 
            >>> # List schemas in specific project
            >>> schemas = schema_mgr.list_schemas(project_uuid='project-456')
            >>> 
            >>> # List object schemas with RBAC
            >>> schemas = schema_mgr.list_schemas(
            ...     schema_type='object',
            ...     api_key=user_api_key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        
        params = {}
        
        # ✅ Add project filter
        if project_uuid:
            params['project_uuid'] = project_uuid
        
        if schema_type:
            # ✅ Normalize schema_type for API call
            params['schema_type'] = normalize_schema_type(schema_type)
        if status:
            params['status'] = status
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        result = self.client.get(f'/domains/{self.domain_name}/schemas', **kwargs)
        
        schemas = result.get('schemas', []) if isinstance(result, dict) else result
        
        context_str = f"domain '{self.domain_name}'"
        if project_uuid:
            context_str += f", project {project_uuid[:8]}..."
        self.logger.debug(f"Listed {len(schemas)} schemas in {context_str}")
        
        if isinstance(result, dict):
            return result.get('schemas', [])
        return result
    
    def list_crud_schemas(
        self,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> List[Dict[str, Any]]:
        """
        List only schemas that have CRUD operations enabled.
        
        This is a convenience method that filters to only 'object' type schemas.
        
        Args:
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            List of object schema info dicts
        
        Example:
            >>> crud_schemas = schema_mgr.list_crud_schemas()
            >>> print(f"Found {len(crud_schemas)} schemas with CRUD operations")
        """
        return self.list_schemas(
            domain_uuid=domain_uuid,
            project_uuid=project_uuid,
            schema_type='object',
            api_key=api_key
        )
    
    def list_non_crud_schemas(
        self,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> List[Dict[str, Any]]:
        """
        List schemas that do NOT have CRUD operations.
        
        Returns types, enums, and operational schemas.
        
        Args:
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            List of non-CRUD schema info dicts
        
        Example:
            >>> non_crud = schema_mgr.list_non_crud_schemas()
            >>> print(f"Found {len(non_crud)} schemas without CRUD operations")
        """
        all_schemas = self.list_schemas(
            domain_uuid=domain_uuid,
            project_uuid=project_uuid,
            api_key=api_key
        )
        return [s for s in all_schemas if not is_crud_enabled(s.get('schema_type', 'object'))]
    
    def get_schema(
        self,
        schema_uuid: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Get schema definition and metadata from Platform Core.
        
        Args:
            schema_uuid: Schema UUID (not filename)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            Schema info dict with full definition
        
        Example:
            >>> schema = schema_mgr.get_schema('schema-uuid-123')
            >>> print(f"Name: {schema['name']}")
            >>> print(f"Type: {schema['schema_type']}")
            >>> print(f"CRUD enabled: {is_crud_enabled(schema['schema_type'])}")
            >>> 
            >>> # With RBAC override
            >>> schema = schema_mgr.get_schema('schema-uuid-123', api_key=admin_key)
        """
        self.logger.debug(
            f"Fetching schema {schema_uuid[:8]}... from domain '{self.domain_name}'"
        )
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get(f'/schemas/{schema_uuid}', **kwargs)
    
    def get_hierarchy(
        self,
        domain_uuid: str = None,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Get complete schema hierarchy for domain.
        
        WARNING: This endpoint is not documented in official API.
        May not be implemented in all Platform Core versions.
        
        Args:
            domain_uuid: Domain UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'config-root': {'children': ['domain', ...]},
                'domain': {'parent': 'config-root', 'children': [...]},
                'project': {'parent': 'domain', 'children': [...]},
                ...
            }
        
        Example:
            >>> hierarchy = schema_mgr.get_hierarchy()
            >>> domain_children = hierarchy['domain']['children']
            >>> 
            >>> # With RBAC override
            >>> hierarchy = schema_mgr.get_hierarchy(api_key=admin_key)
        """
        domain_uuid = domain_uuid or self.domain_uuid
        
        params = {'domain_uuid': domain_uuid}
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        self.logger.debug(
            f"Fetching schema hierarchy for domain '{self.domain_name}'"
        )
        
        return self.client.get('/schemas/hierarchy', **kwargs)
    
    # ============================================
    # SCHEMA VALIDATION
    # ============================================
    
    def validate_schema(
        self,
        schema_data: Dict[str, Any],
        domain_uuid: str = None,
        schema_type: str = 'object',
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Validate schema definition against schema rules.
        
        WARNING: This endpoint is not documented in official API.
        May not be implemented in all Platform Core versions.
        
        For basic validation, use _validate_schema_basic() instead.
        
        Args:
            schema_data: Schema dictionary (JSON content)
            domain_uuid: Domain UUID (optional if set at initialization)
            schema_type: Schema type ('object', 'type', 'enum', 'operational')
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'valid': True/False,
                'errors': [...],
                'warnings': [...]
            }
        
        Example:
            >>> with open('schemas/objects/project.json') as f:
            ...     schema_data = json.load(f)
            >>> validation = schema_mgr.validate_schema(
            ...     schema_data=schema_data,
            ...     schema_type='object'
            ... )
            >>> if not validation['valid']:
            ...     print(f"Errors: {validation['errors']}")
            >>> 
            >>> # With RBAC override
            >>> validation = schema_mgr.validate_schema(
            ...     schema_data=schema_data,
            ...     api_key=admin_key
            ... )
        """
        domain_uuid = domain_uuid or self.domain_uuid
        
        # ✅ Normalize schema_type
        normalized_type = normalize_schema_type(schema_type)
        
        payload = {
            'schema': schema_data,
            'schema_type': normalized_type,
            'domain_uuid': domain_uuid
        }
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key
        
        schema_name = schema_data.get('name', 'unknown')
        self.logger.debug(
            f"Validating schema '{schema_name}' ({normalized_type}) for domain '{self.domain_name}'"
        )
        
        return self.client.post('/schemas/validate', **kwargs)
    
    def _validate_schema_basic(
        self,
        schema_data: Dict[str, Any],
        schema_type: str = 'object'
    ) -> Dict[str, Any]:
        """
        Basic client-side schema validation.
        
        Args:
            schema_data: Schema dictionary
            schema_type: Schema type (singular or plural)
        
        Returns:
            {'valid': bool, 'errors': [...]}
        """
        errors = []
        
        # ✅ Normalize schema_type
        normalized_type = normalize_schema_type(schema_type)
        
        # Check required fields
        if not schema_data.get('name'):
            errors.append("Schema must have a 'name' field")
        
        if normalized_type == 'object':
            if not schema_data.get('parent_type'):
                errors.append("Object schema must have 'parent_type' field")
        
        if normalized_type in ['type', 'object']:
            if 'attributes' not in schema_data:
                errors.append(f"{normalized_type} schema must have 'attributes' field")
        
        if normalized_type == 'enum':
            if not schema_data.get('type'):
                errors.append("Enum schema must have 'type' field")
            if not schema_data.get('values'):
                errors.append("Enum schema must have 'values' field")
        
        if normalized_type == 'operational':
            # Operational schemas have more flexible validation
            pass
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    # ============================================
    # SCHEMA MODIFICATION
    # ============================================
    
    def delete_schema(
        self,
        schema_uuid: str,
        force_delete: bool = False,
        delete_objects: bool = False,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> bool:
        """
        Delete schema from domain.
        
        Args:
            schema_uuid: Schema UUID (not filename)
            force_delete: Force deletion even if dependencies exist
            delete_objects: Delete all objects created with this schema
                           (only applicable for 'object' type schemas)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            True if successful
        
        Warning:
            This will affect any generated SDKs. You may need to regenerate
            SDKs after deleting schemas.
        
        Note:
            delete_objects only applies to 'object' type schemas since
            types, enums, and operational schemas don't have CRUD objects.
        
        Example:
            >>> schema_mgr.delete_schema('schema-uuid-123')
            >>> 
            >>> # Force delete with RBAC
            >>> schema_mgr.delete_schema(
            ...     'schema-uuid-123',
            ...     force_delete=True,
            ...     api_key=admin_api_key
            ... )
        """
        params = {}
        if force_delete:
            params['force_delete'] = 'true'
        if delete_objects:
            params['delete_objects'] = 'true'
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        response = self.client.delete(f'/schemas/{schema_uuid}', **kwargs)
        
        if response.get('success', False):
            self.logger.info(
                f"✓ Deleted schema {schema_uuid[:8]}... from domain '{self.domain_name}'"
            )
        
        return response.get('success', False)
    
    # ============================================
    # SCHEMA EXPORT
    # ============================================
    
    def export_schemas(
        self,
        output_directory: str,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        schema_type: str = None,
        create_structure: bool = True,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Export schemas to local directory in standard structure.
        
        Args:
            output_directory: Base directory for exports
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            schema_type: Export specific type only (None = all)
                        Accepts singular or plural forms
            create_structure: Create standard directory structure
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'exported': [
                    {'name': 'Project', 'path': 'schemas/objects/Project.json', 'crud': True},
                    {'name': 'Status', 'path': 'schemas/enums/Status.json', 'crud': False},
                    ...
                ],
                'failed': [{'name': 'X', 'error': 'msg'}, ...],
                'directory': 'path'
            }
        
        Example:
            >>> # Export all schemas
            >>> result = schema_mgr.export_schemas(output_directory='my_schemas/')
            >>> 
            >>> # Export project-scoped schemas with RBAC
            >>> result = schema_mgr.export_schemas(
            ...     output_directory='my_schemas/',
            ...     project_uuid='project-456',
            ...     api_key=user_api_key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        
        # Create base directory
        os.makedirs(output_directory, exist_ok=True)
        
        # ✅ Create standard structure using STORAGE_DIRECTORIES
        if create_structure:
            for storage_dir in STORAGE_DIRECTORIES:
                os.makedirs(os.path.join(output_directory, storage_dir), exist_ok=True)
        
        # Get schemas from Platform Core
        schemas = self.list_schemas(
            domain_uuid=domain_uuid,
            project_uuid=project_uuid,
            schema_type=schema_type,
            api_key=api_key
        )
        
        exported = []
        failed = []
        
        for schema_info in schemas:
            try:
                schema_uuid = schema_info['uuid']
                schema_name = schema_info['name']
                schema_type_val = schema_info.get('schema_type', 'object')
                
                # ✅ Get storage directory from schema_type
                storage_dir = get_storage_directory(schema_type_val)
                has_crud = is_crud_enabled(schema_type_val)
                
                # Get full schema definition
                full_schema = self.get_schema(schema_uuid, api_key=api_key)
                
                # Create filename from schema name
                filename = f"{schema_name}.json"
                
                # Determine output path
                if create_structure:
                    output_path = os.path.join(output_directory, storage_dir, filename)
                else:
                    output_path = os.path.join(output_directory, filename)
                
                # Write schema file
                with open(output_path, 'w') as f:
                    # Write the schema_content if available, otherwise full_schema
                    schema_content = full_schema.get('schema_content', full_schema)
                    json.dump(schema_content, f, indent=2)
                
                exported.append({
                    'name': schema_name,
                    'filename': filename,
                    'path': output_path,
                    'schema_type': normalize_schema_type(schema_type_val),
                    'crud': has_crud
                })
                
                crud_indicator = "✓" if has_crud else "○"
                self.logger.info(f"  {crud_indicator} Exported: {filename} → {output_path}")
                
            except Exception as e:
                failed.append({
                    'name': schema_info.get('name', 'unknown'),
                    'error': str(e)
                })
                self.logger.error(f"  ✗ Failed: {schema_info.get('name')} - {e}")
        
        # ✅ Enhanced summary with CRUD breakdown and project context
        crud_count = sum(1 for e in exported if e.get('crud', False))
        no_crud_count = len(exported) - crud_count
        
        context_str = f"domain '{self.domain_name}'"
        if project_uuid:
            context_str += f", project {project_uuid[:8]}..."
        
        self.logger.info(
            f"\nExport Summary for {context_str}:\n"
            f"  Exported: {len(exported)} ({crud_count} CRUD, {no_crud_count} no CRUD)\n"
            f"  Failed: {len(failed)}\n"
            f"  Directory: {output_directory}"
        )
        
        return {
            'exported': exported,
            'failed': failed,
            'directory': output_directory
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _detect_schema_type(self, schema_file: str) -> str:
        """
        Auto-detect schema type from file path.
        
        Args:
            schema_file: Path to schema file
        
        Returns:
            Schema type (singular form: 'object', 'type', 'enum', 'operational')
        
        Detection Logic:
            schemas/objects/       → 'object'
            schemas/types/         → 'type'
            schemas/enums/         → 'enum'
            schemas/operational/   → 'operational'
            Otherwise              → 'object' (default)
        """
        # Normalize path separators
        normalized_path = schema_file.replace('\\', '/')
        
        # ✅ Check directory structure and return SINGULAR form
        if '/objects/' in normalized_path:
            return 'object'
        elif '/types/' in normalized_path:
            return 'type'
        elif '/enums/' in normalized_path:
            return 'enum'
        elif '/operational/' in normalized_path:
            return 'operational'
        else:
            # Default to object
            self.logger.debug(
                f"Could not detect schema type from path: {schema_file}. "
                "Defaulting to 'object'."
            )
            return 'object'
    
    def get_schema_type_info(self, schema_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a schema type.
        
        Args:
            schema_type: Schema type (singular or plural)
        
        Returns:
            {
                'type': 'object',           # Normalized singular form
                'storage_dir': 'objects',   # Storage directory (plural)
                'crud_enabled': True,       # Whether CRUD operations are supported
                'description': '...'        # Human-readable description
            }
        
        Example:
            >>> info = schema_mgr.get_schema_type_info('operational')
            >>> print(f"CRUD enabled: {info['crud_enabled']}")  # False
        """
        normalized = normalize_schema_type(schema_type)
        return {
            'type': normalized,
            'storage_dir': get_storage_directory(schema_type),
            'crud_enabled': is_crud_enabled(schema_type),
            'description': get_schema_type_description(schema_type)
        }
