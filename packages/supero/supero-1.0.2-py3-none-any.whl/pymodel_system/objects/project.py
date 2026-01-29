# File: pymodel_system/objects/project.py
"""
This file was generated from the project.json schema.
ENHANCED: Proper datetime handling with automatic string<->datetime conversion.
ENHANCED: Supero fluent API support with smart reference management.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import importlib
import uuid
import inflection
from pymodel_system.types.entity_relationship import EntityRelationship
from pymodel_system.types.status_workflow import StatusWorkflow
from datetime import datetime

if TYPE_CHECKING:
    from pymodel_system.objects.schema_registry import SchemaRegistry

from ..serialization_errors import ObjectDeserializationError, InvalidParentError
from datetime import datetime
import re

class Project:
    """
    Represents a Project instance.
    
    This class is auto-generated and includes:
    - Standard CRUD operations
    - Fluent API methods (when used with Supero)
    - Smart reference management with link data support
    - Parent-child hierarchy navigation
    """
    
    _OBJ_TYPE = "project"
    _PARENT_TYPE = "domain"

    # Type metadata for deserialization
    _type_metadata = {
    'name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'name',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'uuid': {
        'type': 'str',
        'is_list': False,
        'json_name': 'uuid',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'fq_name': {
        'type': 'str',
        'is_list': True,
        'json_name': 'fq_name',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'parent_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'parent_type',
        'original_type': 'string',
        'mandatory': True,
        'static': True,
    },
    'parent_uuid': {
        'type': 'str',
        'is_list': False,
        'json_name': 'parent_uuid',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'obj_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'obj_type',
        'original_type': 'string',
        'mandatory': True,
        'static': True,
    },
    'display_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'display_name',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'description': {
        'type': 'str',
        'is_list': False,
        'json_name': 'description',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'created_by': {
        'type': 'str',
        'is_list': False,
        'json_name': 'created_by',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'created_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'created_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'updated_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'updated_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'icon': {
        'type': 'str',
        'is_list': False,
        'json_name': 'icon',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'color': {
        'type': 'str',
        'is_list': False,
        'json_name': 'color',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'tagline': {
        'type': 'str',
        'is_list': False,
        'json_name': 'tagline',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'project_summary': {
        'type': 'str',
        'is_list': False,
        'json_name': 'project_summary',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'project_description': {
        'type': 'str',
        'is_list': False,
        'json_name': 'project_description',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'status': {
        'type': 'str',
        'is_list': False,
        'json_name': 'status',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'is_default': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'is_default',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'project_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'project_type',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'owner_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'owner_email',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'category': {
        'type': 'str',
        'is_list': False,
        'json_name': 'category',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'expected_scale': {
        'type': 'str',
        'is_list': False,
        'json_name': 'expected_scale',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'is_multi_tenant': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'is_multi_tenant',
        'original_type': 'bool',
        'mandatory': False,
        'static': False,
    },
    'primary_users': {
        'type': 'str',
        'is_list': True,
        'json_name': 'primary_users',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'entities': {
        'type': 'str',
        'is_list': True,
        'json_name': 'entities',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'central_entity': {
        'type': 'str',
        'is_list': False,
        'json_name': 'central_entity',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'relationships': {
        'type': 'entity_relationship',
        'is_list': True,
        'json_name': 'relationships',
        'original_type': 'entity_relationship',
        'mandatory': False,
        'static': False,
    },
    'status_workflows': {
        'type': 'status_workflow',
        'is_list': True,
        'json_name': 'status_workflows',
        'original_type': 'status_workflow',
        'mandatory': False,
        'static': False,
    },
    'embedded_data_notes': {
        'type': 'str',
        'is_list': False,
        'json_name': 'embedded_data_notes',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'database_preference': {
        'type': 'str',
        'is_list': False,
        'json_name': 'database_preference',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'include_streaming': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'include_streaming',
        'original_type': 'bool',
        'mandatory': False,
        'static': False,
    },
    'include_cache': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'include_cache',
        'original_type': 'bool',
        'mandatory': False,
        'static': False,
    },
    'include_vector_db': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'include_vector_db',
        'original_type': 'bool',
        'mandatory': False,
        'static': False,
    },
    'compliance_standards': {
        'type': 'str',
        'is_list': True,
        'json_name': 'compliance_standards',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'sensitive_data_types': {
        'type': 'str',
        'is_list': True,
        'json_name': 'sensitive_data_types',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'audit_requirements': {
        'type': 'str',
        'is_list': True,
        'json_name': 'audit_requirements',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'additional_requirements': {
        'type': 'str',
        'is_list': False,
        'json_name': 'additional_requirements',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'schema_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'schema_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'deployment_status': {
        'type': 'str',
        'is_list': False,
        'json_name': 'deployment_status',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'discovery_completed': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'discovery_completed',
        'original_type': 'bool',
        'mandatory': False,
        'static': False,
    },
    'discovery_completed_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'discovery_completed_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'archived_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'archived_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'archived_by': {
        'type': 'str',
        'is_list': False,
        'json_name': 'archived_by',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'tags': {
        'type': 'str',
        'is_list': True,
        'json_name': 'tags',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    }
}
    
    # Infrastructure end_points metadata
    _end_points = [
        {
            'type': 'database',
            'name': 'mongo',
            'cloud': ['private', 'platform'],
            'priority': 1,
            'config': {'indexes': ['idx_status', 'idx_category', 'idx_owner']},
            'operations': ['create', 'read', 'update', 'delete'],
        }
    ]
    
    # Index definitions
    _indexes = {}

    _CONSTRAINTS = {
        'tagline': {
            'max-length': 200,
            'type': 'string',
        },
        'project_summary': {
            'max-length': 500,
            'type': 'string',
        },
        'project_description': {
            'max-length': 5000,
            'type': 'string',
        },
        'embedded_data_notes': {
            'max-length': 2000,
            'type': 'string',
        },
        'additional_requirements': {
            'max-length': 5000,
            'type': 'string',
        }
    }

    # Supero context (set by Supero wrapper)
    _supero_context = None

    @staticmethod
    def _normalize_name(name: str) -> str:
        """ 
        Normalize object/domain name to lowercase with preserved special characters.
        
        SPECIAL CASES (preserved as-is, only lowercased):
        - Email addresses (valid format: user@domain)
        - Phone numbers (start with + or are digit-heavy)
        
        For regular names:
        - Converts to lowercase
        - Allows: alphanumeric, hyphen (-), dot (.), underscore (_)
        - Replaces spaces and other chars with hyphen
        - Collapses multiple separators
        
        Args:
            name: Raw name (e.g., "Acme Corporation", "user@example.com", "+1-555-1234")
        
        Returns:
            Normalized name or preserved special format
            
        Examples:
            >>> normalize_name("Acme Corporation")
            'acme-corporation'
            >>> normalize_name("My_Project.Name")
            'my-project.name'
            >>> normalize_name("user@example.com")
            'user@example.com'
            >>> normalize_name("+1-555-1234")
            '+1-555-1234'
            >>> normalize_name("platform-admin@system.com")
            'platform-admin@system.com'
            >>> normalize_name("@@@")
            ''
        """
        if not name or not isinstance(name, str):
            return name
        
        # Strip whitespace
        name = name.strip()
        
        # SPECIAL CASE 1: Email addresses (valid format)
        # Must have: one @, something before @, something after @
        if '@' in name:
            parts = name.split('@')
            # Valid email: exactly one @, non-empty local and domain parts
            if len(parts) == 2 and parts[0] and parts[1]:
                # Additional check: domain should have at least one char
                # (could be "localhost" or "example.com")
                return name.lower()
            # Invalid email format - fall through to normal normalization
        
        # SPECIAL CASE 2: Phone numbers (starts with + or is digit-heavy)
        # Preserve as-is (including formatting)
        if name.startswith('+'):
            return name
        
        # Check if digit-heavy (>50% digits) - likely a phone number
        if len(name) > 0:
            digit_ratio = sum(c.isdigit() for c in name) / len(name)
            if digit_ratio > 0.5:
                return name
        
        # REGULAR NAME: Apply normalization
        # Convert to lowercase
        name = name.lower()
        
        # Allow: alphanumeric, hyphen, dot, underscore
        # Replace spaces and other special chars with hyphen
        name = re.sub(r'[^a-z0-9.\-_]+', '-', name)
        
        # Collapse multiple consecutive separators to single hyphen
        name = re.sub(r'[-_.]{2,}', '-', name)
        
        # Strip leading/trailing separators
        name = name.strip('-._')
        
        return name

    def __init__(
        self,
        name: str,
        uuid: Optional[str] = None,
        fq_name: Optional[List[str]] = None,
        parent_uuid: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        tagline: Optional[str] = None,
        project_summary: Optional[str] = None,
        project_description: Optional[str] = None,
        status: Optional[str] = None,
        is_default: Optional[bool] = None,
        project_type: Optional[str] = None,
        owner_email: Optional[str] = None,
        category: Optional[str] = None,
        expected_scale: Optional[str] = None,
        is_multi_tenant: Optional[bool] = None,
        primary_users: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        central_entity: Optional[str] = None,
        relationships: Optional[List[EntityRelationship]] = None,
        status_workflows: Optional[List[StatusWorkflow]] = None,
        embedded_data_notes: Optional[str] = None,
        database_preference: Optional[str] = None,
        include_streaming: Optional[bool] = None,
        include_cache: Optional[bool] = None,
        include_vector_db: Optional[bool] = None,
        compliance_standards: Optional[List[str]] = None,
        sensitive_data_types: Optional[List[str]] = None,
        audit_requirements: Optional[List[str]] = None,
        additional_requirements: Optional[str] = None,
        schema_count: Optional[int] = None,
        deployment_status: Optional[str] = None,
        discovery_completed: Optional[bool] = None,
        discovery_completed_at: Optional[str] = None,
        archived_at: Optional[str] = None,
        archived_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        schema_registry_refs: List[Dict[str, Any]] = None
    ):
        # Set initialization flag to prevent tracking during __init__
        self._initializing = True
        
        self.obj_type = "project"
        self.parent_type = "domain"
        self._py_to_json_map = {
    'name': 'name',
    'uuid': 'uuid',
    'fq_name': 'fq_name',
    'parent_type': 'parent_type',
    'parent_uuid': 'parent_uuid',
    'obj_type': 'obj_type',
    'display_name': 'display_name',
    'description': 'description',
    'created_by': 'created_by',
    'created_at': 'created_at',
    'updated_at': 'updated_at',
    'icon': 'icon',
    'color': 'color',
    'tagline': 'tagline',
    'project_summary': 'project_summary',
    'project_description': 'project_description',
    'status': 'status',
    'is_default': 'is_default',
    'project_type': 'project_type',
    'owner_email': 'owner_email',
    'category': 'category',
    'expected_scale': 'expected_scale',
    'is_multi_tenant': 'is_multi_tenant',
    'primary_users': 'primary_users',
    'entities': 'entities',
    'central_entity': 'central_entity',
    'relationships': 'relationships',
    'status_workflows': 'status_workflows',
    'embedded_data_notes': 'embedded_data_notes',
    'database_preference': 'database_preference',
    'include_streaming': 'include_streaming',
    'include_cache': 'include_cache',
    'include_vector_db': 'include_vector_db',
    'compliance_standards': 'compliance_standards',
    'sensitive_data_types': 'sensitive_data_types',
    'audit_requirements': 'audit_requirements',
    'additional_requirements': 'additional_requirements',
    'schema_count': 'schema_count',
    'deployment_status': 'deployment_status',
    'discovery_completed': 'discovery_completed',
    'discovery_completed_at': 'discovery_completed_at',
    'archived_at': 'archived_at',
    'archived_by': 'archived_by',
    'tags': 'tags',
    'schema_registry_refs': 'schema_registry_refs'
}
        self._json_to_py_map = {
    'name': 'name',
    'uuid': 'uuid',
    'fq_name': 'fq_name',
    'parent_type': 'parent_type',
    'parent_uuid': 'parent_uuid',
    'obj_type': 'obj_type',
    'display_name': 'display_name',
    'description': 'description',
    'created_by': 'created_by',
    'created_at': 'created_at',
    'updated_at': 'updated_at',
    'icon': 'icon',
    'color': 'color',
    'tagline': 'tagline',
    'project_summary': 'project_summary',
    'project_description': 'project_description',
    'status': 'status',
    'is_default': 'is_default',
    'project_type': 'project_type',
    'owner_email': 'owner_email',
    'category': 'category',
    'expected_scale': 'expected_scale',
    'is_multi_tenant': 'is_multi_tenant',
    'primary_users': 'primary_users',
    'entities': 'entities',
    'central_entity': 'central_entity',
    'relationships': 'relationships',
    'status_workflows': 'status_workflows',
    'embedded_data_notes': 'embedded_data_notes',
    'database_preference': 'database_preference',
    'include_streaming': 'include_streaming',
    'include_cache': 'include_cache',
    'include_vector_db': 'include_vector_db',
    'compliance_standards': 'compliance_standards',
    'sensitive_data_types': 'sensitive_data_types',
    'audit_requirements': 'audit_requirements',
    'additional_requirements': 'additional_requirements',
    'schema_count': 'schema_count',
    'deployment_status': 'deployment_status',
    'discovery_completed': 'discovery_completed',
    'discovery_completed_at': 'discovery_completed_at',
    'archived_at': 'archived_at',
    'archived_by': 'archived_by',
    'tags': 'tags',
    'schema_registry_refs': 'schema_registry_refs'
}
        self._pending_field_updates = set()

        # ========================================================================
        # CRITICAL: Handle 'name' and 'display_name' BEFORE other attributes
        # This ensures we capture the original name before normalization
        # ========================================================================
        
        # Step 1: Store the original user-provided name (before normalization)
        _original_name = name
        
        # Step 2: Normalize the name for database consistency
        self.name = self._normalize_name(name) if name else name
        
        # Step 3: Set display_name
        if display_name is not None:
            self.display_name = display_name
        elif _original_name is not None:
            self.display_name = _original_name  # ✅ Preserve original formatting!
        else:
            self.display_name = None
        
        # Step 4: Set all other attributes (excluding name and display_name)
        
        self.uuid = uuid
        self.fq_name = fq_name if fq_name is not None else []
        self.parent_uuid = parent_uuid
        self.description = description
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
        self.icon = icon
        self.color = color
        self.tagline = tagline
        self.project_summary = project_summary
        self.project_description = project_description
        self.status = status
        self.is_default = is_default
        self.project_type = project_type
        self.owner_email = owner_email
        self.category = category
        self.expected_scale = expected_scale
        self.is_multi_tenant = is_multi_tenant
        self.primary_users = primary_users if primary_users is not None else []
        self.entities = entities if entities is not None else []
        self.central_entity = central_entity
        self.relationships = relationships if relationships is not None else []
        self.status_workflows = status_workflows if status_workflows is not None else []
        self.embedded_data_notes = embedded_data_notes
        self.database_preference = database_preference
        self.include_streaming = include_streaming
        self.include_cache = include_cache
        self.include_vector_db = include_vector_db
        self.compliance_standards = compliance_standards if compliance_standards is not None else []
        self.sensitive_data_types = sensitive_data_types if sensitive_data_types is not None else []
        self.audit_requirements = audit_requirements if audit_requirements is not None else []
        self.additional_requirements = additional_requirements
        self.schema_count = schema_count
        self.deployment_status = deployment_status
        self.discovery_completed = discovery_completed
        self.discovery_completed_at = discovery_completed_at
        self.archived_at = archived_at
        self.archived_by = archived_by
        self.tags = tags if tags is not None else []


        self.schema_registry_refs = schema_registry_refs if schema_registry_refs is not None else []
        self._pending_field_updates.add('name')
        if uuid is not None:
            self._pending_field_updates.add('uuid')
        self._pending_field_updates.add('fq_name')
        self._pending_field_updates.add('parent_uuid')
        if display_name is not None:
            self._pending_field_updates.add('display_name')
        if description is not None:
            self._pending_field_updates.add('description')
        if created_by is not None:
            self._pending_field_updates.add('created_by')
        if created_at is not None:
            self._pending_field_updates.add('created_at')
        if updated_at is not None:
            self._pending_field_updates.add('updated_at')
        if icon != '📁':
            self._pending_field_updates.add('icon')
        if color is not None:
            self._pending_field_updates.add('color')
        if tagline is not None:
            self._pending_field_updates.add('tagline')
        if project_summary is not None:
            self._pending_field_updates.add('project_summary')
        if project_description is not None:
            self._pending_field_updates.add('project_description')
        self._pending_field_updates.add('status')
        self._pending_field_updates.add('is_default')
        if project_type != 'default':
            self._pending_field_updates.add('project_type')
        if owner_email is not None:
            self._pending_field_updates.add('owner_email')
        if category != 'general':
            self._pending_field_updates.add('category')
        if expected_scale != 'small':
            self._pending_field_updates.add('expected_scale')
        if is_multi_tenant != False:
            self._pending_field_updates.add('is_multi_tenant')
        if primary_users is not None:
            self._pending_field_updates.add('primary_users')
        if entities is not None:
            self._pending_field_updates.add('entities')
        if central_entity is not None:
            self._pending_field_updates.add('central_entity')
        if relationships is not None:
            self._pending_field_updates.add('relationships')
        if status_workflows is not None:
            self._pending_field_updates.add('status_workflows')
        if embedded_data_notes is not None:
            self._pending_field_updates.add('embedded_data_notes')
        if database_preference != 'auto':
            self._pending_field_updates.add('database_preference')
        if include_streaming != False:
            self._pending_field_updates.add('include_streaming')
        if include_cache != False:
            self._pending_field_updates.add('include_cache')
        if include_vector_db != False:
            self._pending_field_updates.add('include_vector_db')
        if compliance_standards is not None:
            self._pending_field_updates.add('compliance_standards')
        if sensitive_data_types is not None:
            self._pending_field_updates.add('sensitive_data_types')
        if audit_requirements is not None:
            self._pending_field_updates.add('audit_requirements')
        if additional_requirements is not None:
            self._pending_field_updates.add('additional_requirements')
        if schema_count != 0:
            self._pending_field_updates.add('schema_count')
        if deployment_status != 'not_deployed':
            self._pending_field_updates.add('deployment_status')
        if discovery_completed != False:
            self._pending_field_updates.add('discovery_completed')
        if discovery_completed_at is not None:
            self._pending_field_updates.add('discovery_completed_at')
        if archived_at is not None:
            self._pending_field_updates.add('archived_at')
        if archived_by is not None:
            self._pending_field_updates.add('archived_by')
        if tags is not None:
            self._pending_field_updates.add('tags')
        if schema_registry_refs is not None:
            self._pending_field_updates.add('schema_registry_refs')
        
        # Initialize reference link data storage
        self._ref_link_data = {}
        
        # Mark initialization as complete
        self._initializing = False
        self.set_default_parent()

    def set_parent(self, parent):
        """
        Set the parent of this object and automatically construct fq_name and parent_uuid.
        Args:
            parent: Parent object instance
        Raises:
            AttributeError: If obj_type is missing
            InvalidParentError: If parent type doesn't match expected parent_type
        Example:
            domain = Domain.create(name="engineering")
            project = Project.create(name="backend")
            project.set_parent(domain)
        """
        # Validate parent matches expected type
        if parent.obj_type != self.parent_type:
            raise InvalidParentError(
                f"Invalid parent object. Expected parent_type '{self.parent_type}', "
                f"but got '{parent.obj_type}'"
            )
        
        # Set parent relationships
        self.parent_fq_name = parent.fq_name
        if self.name:
            # Ensure fq_name contains normalized name
            normalized_name = self._normalize_name(self.name)
            self.fq_name = self.parent_fq_name + [normalized_name]

        if hasattr(parent, 'uuid') and parent.uuid:
            self.parent_uuid = parent.uuid

    def set_default_parent(self):
        """Set default parent for root-level objects if not already set."""
        if not hasattr(self, 'obj_type'):
            return
    
        # Only set defaults if parent info wasn't explicitly provided
        if self.parent_type == "config_root":
            # Only set parent_fq_name if it's not already set
            if getattr(self, 'parent_fq_name', None) is None:
                self.parent_fq_name = ["config_root"]
        
            # Only construct fq_name if it's not already set and we have a name
            if not getattr(self, 'fq_name', None) and self.name:
                normalized_name = self._normalize_name(self.name)
                self.fq_name = self.parent_fq_name + [normalized_name]

    def __setattr__(self, name: str, value):
        """
        Override setattr to:
        1. Preserve original name as display_name if not explicitly set
        2. Automatically normalize 'name' attribute
        3. Track pending field updates
        """
        # ========================================================================
        # CRITICAL: When setting 'name', preserve original as display_name first
        # ========================================================================
        
        # ========================================================================
        # CRITICAL: When setting 'name', preserve original as display_name first
        # ========================================================================
        if name == 'name' and value is not None and isinstance(value, str):
            if (not getattr(self, '_initializing', True) and 
                hasattr(self, 'display_name') and 
                (self.display_name is None or self.display_name == '')):
                
                super().__setattr__('display_name', value)
                
                if (hasattr(self, '_pending_field_updates') and 
                    isinstance(self._pending_field_updates, set)):
                    self._pending_field_updates.add('display_name')
            
            value = self._normalize_name(value)
        
        
        # Always set the attribute (with normalized value if it was 'name')
        super().__setattr__(name, value)
        
        # Track pending field updates for partial updates
        try:
            # Only track if all conditions are met:
            if (hasattr(self, '_pending_field_updates') and 
                hasattr(self, '_py_to_json_map') and 
                name in self._py_to_json_map and
                name not in ['obj_type', 'parent_type', '_pending_field_updates', 
                           '_py_to_json_map', '_json_to_py_map', '_initializing', 
                           '_tracking_disabled', '_ref_link_data', '_supero_context'] and
                not getattr(self, '_initializing', False) and
                not getattr(self, '_tracking_disabled', False)):
                
                # Extra safety check - make sure _pending_field_updates is actually a set
                if isinstance(self._pending_field_updates, set):
                    self._pending_field_updates.add(name)
        except Exception:
            # If anything goes wrong with tracking, don't fail the attribute assignment
            # Just skip the tracking - the attribute was already set above
            pass

    # ========================================================================
    # SUPERO FLUENT API METHODS
    # ========================================================================

    @classmethod
    def create(cls, name: str, parent=None, **kwargs):
        """
        Fluent API: Create and optionally save object in one call.
        
        Args:
            name: Object name (required)
            parent: Optional parent object
            **kwargs: Additional attributes to set
            
        Returns:
            Created object instance (saved if Supero context is set)
            
        Example:
            # With Supero context:
            org = Supero.quickstart("acme")
            Project = org.get_schema("Project")
            project = Project.create(name="Alpha", status="active")
            
            # Or via parent:
            project = org.domain.create_project("Alpha", status="active")
        """
        obj = cls(name=name, **kwargs)
        if parent:
            obj.set_parent(parent)
        
        # Auto-save if _supero_context is set
        if hasattr(cls, '_supero_context') and cls._supero_context:
            saved_obj = cls._supero_context.save(obj)
            # Note: save() now handles method injection
            return saved_obj
        
        return obj

    @classmethod
    def find(cls, **filters):
        """
        Fluent API: Query objects with filters.
        
        Args:
            **filters: Filter conditions (supports Django-style lookups)
            
        Returns:
            QueryBuilder instance for chaining, or list if simple query
            
        Example:
            # Simple query:
            projects = Project.find(status="active")
            
            # Advanced query:
            projects = Project.find(status="active").limit(10).all()
            
            # Django-style lookups:
            projects = Project.find(priority__gte=5)
            projects = Project.find(name__contains="Alpha")
        """
        if not hasattr(cls, '_supero_context') or not cls._supero_context:
            raise RuntimeError(
                f"No Supero context set for {cls.__name__}. "
                f"Use: org = Supero.quickstart('name') then Project = org.get_schema('Project')"
            )
        
        if not filters:
            return cls.query()
        return cls.query().filter(**filters).all()

    @classmethod
    def find_one(cls, **filters):
        """
        Fluent API: Find single object matching filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            First matching object or None
            
        Example:
            project = Project.find_one(name="Alpha")
            lead = User.find_one(role="lead")
        """
        if not hasattr(cls, '_supero_context') or not cls._supero_context:
            raise RuntimeError(f"No Supero context set for {cls.__name__}")
        
        return cls.query().filter(**filters).first()

    @classmethod
    def query(cls):
        """
        Start a query builder for advanced queries.
        
        Returns:
            QueryBuilder instance
            
        Example:
            projects = (Project.query()
                .filter(status="active")
                .filter(priority__gte=5)
                .order_by("-created_at")
                .limit(10)
                .all())
        """
        if not hasattr(cls, '_supero_context') or not cls._supero_context:
            raise RuntimeError(f"No Supero context set for {cls.__name__}")
        
        from supero.query import QueryBuilder
        return QueryBuilder(cls, cls._supero_context)

    @classmethod
    def bulk_load(cls, uuids):
        """
        Load multiple objects by UUID in single request.
        
        Args:
            uuids: List of UUIDs to load
            
        Returns:
            List of objects
            
        Example:
            projects = Project.bulk_load(["uuid1", "uuid2", "uuid3"])
        """
        if not hasattr(cls, '_supero_context') or not cls._supero_context:
            raise RuntimeError(f"No Supero context set for {cls.__name__}")
        
        import inflection
        obj_type = inflection.underscore(cls.__name__).replace('_', '-')
        return cls._supero_context.api_lib.list_bulk(
            obj_type,
            uuids=uuids,
            detail=True
        )

    @classmethod
    def bulk_create(cls, objects_data):
        """
        Create multiple objects in batch.
        
        Args:
            objects_data: List of dicts with object attributes
            
        Returns:
            List of created objects
            
        Example:
            projects = Project.bulk_create([
                {"name": "A", "status": "active"},
                {"name": "B", "status": "pending"}
            ])
        """
        if not hasattr(cls, '_supero_context') or not cls._supero_context:
            raise RuntimeError(f"No Supero context set for {cls.__name__}")
        
        created = []
        for data in objects_data:
            obj = cls.create(**data)
            created.append(obj)
        
        return created

    @classmethod
    def bulk_update(cls, objects, updates):
        """
        Update multiple objects with same changes.
        
        Args:
            objects: List of objects to update
            updates: Dict of attributes to update
            
        Example:
            projects = Project.find(status="pending")
            Project.bulk_update(projects, {"status": "active"})
        """
        for obj in objects:
            for key, value in updates.items():
                setattr(obj, key, value)
            obj.save()
        
        return objects

    @classmethod
    def bulk_save(cls, objects):
        """
        Save multiple objects.
        
        Args:
            objects: List of objects to save
            
        Example:
            for project in projects:
                project.status = "completed"
            Project.bulk_save(projects)
        """
        for obj in objects:
            obj.save()
        
        return objects

    @classmethod
    def bulk_delete(cls, objects=None, uuids=None):
        """
        Delete multiple objects.
        
        Args:
            objects: List of objects to delete
            uuids: List of UUIDs to delete
            
        Example:
            Project.bulk_delete(old_projects)
            Project.bulk_delete(uuids=["uuid1", "uuid2"])
        """
        if objects:
            for obj in objects:
                obj.delete()
        elif uuids:
            import inflection
            obj_type = inflection.underscore(cls.__name__).replace('_', '-')
            for uuid in uuids:
                cls._supero_context.api_lib._object_delete(obj_type, id=uuid)

    def save(self):
        """
        Fluent API: Save this object (create or update).
        
        Returns:
            Saved object with updated fields
            
        Example:
            project.status = "completed"
            project.save()
        """
        if not hasattr(self.__class__, '_supero_context') or not self.__class__._supero_context:
            raise RuntimeError(f"No Supero context set for {self.__class__.__name__}")
        
        return self.__class__._supero_context.save(self)

    def delete(self):
        """
        Fluent API: Delete this object.
        
        Returns:
            True if successful
            
        Example:
            old_project.delete()
        """
        if not hasattr(self.__class__, '_supero_context') or not self.__class__._supero_context:
            raise RuntimeError(f"No Supero context set for {self.__class__.__name__}")
        
        return self.__class__._supero_context.delete(self)

    def refresh(self):
        """
        Fluent API: Reload this object from server.
        
        Returns:
            Refreshed object
            
        Example:
            project.refresh()
        """
        if not hasattr(self.__class__, '_supero_context') or not self.__class__._supero_context:
            raise RuntimeError(f"No Supero context set for {self.__class__.__name__}")
        
        return self.__class__._supero_context.refresh(self)

    def update(self):
        """
        Context manager for batch updates.
        
        Returns:
            Self for use as context manager
            
        Example:
            with project.update() as p:
                p.status = "active"
                p.priority = 1
                # Auto-saves on exit
        """
        return self

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and auto-save."""
        if exc_type is None:
            self.save()

    def _validate_field_constraint(self, field_name: str, value: Any):
        """Validate a field value against its constraints."""
        if field_name not in self._CONSTRAINTS:
            return

        constraints = self._CONSTRAINTS[field_name]
        field_type = constraints.get('type')

        # String constraints
        if field_type == 'string' and isinstance(value, str):
            min_len = constraints.get('min-length')
            max_len = constraints.get('max-length')
            pattern = constraints.get('pattern')

            if min_len and len(value) < min_len:
                raise ValueError(
                    f"Field '{field_name}': value too short (min {min_len} chars, got {len(value)})"
                )

            if max_len and len(value) > max_len:
                raise ValueError(
                    f"Field '{field_name}': value too long (max {max_len} chars, got {len(value)})"
                )

            if pattern:
                import re
                if not re.match(pattern, value):
                    raise ValueError(
                        f"Field '{field_name}': value doesn't match pattern {pattern}"
                    )

        # Numeric constraints
        elif field_type in ['int', 'float'] and isinstance(value, (int, float)):
            min_val = constraints.get('min-value')
            max_val = constraints.get('max-value')
            range_val = constraints.get('range')

            if min_val is not None and value < min_val:
                raise ValueError(f"Field '{field_name}': value {value} below minimum {min_val}")

            if max_val is not None and value > max_val:
                raise ValueError(f"Field '{field_name}': value {value} above maximum {max_val}")

            if range_val:
                # Parse range like "[1-5]"
                import re
                match = re.match(r'^\[(\d+)-(\d+)\]$', range_val)
                if match:
                    range_min, range_max = int(match.group(1)), int(match.group(2))
                    if not (range_min <= value <= range_max):
                        raise ValueError(
                            f"Field '{field_name}': value {value} outside range {range_val}"
                        )


    def get_name(self) -> str:
        """Get the value of name."""
        return self.name

    def set_name(self, value: str):
        """Set the value of name. AUTOMATICALLY NORMALIZES THE NAME."""
        if not self.display_name:
            self.display_name = value
        self.name = self._normalize_name(value) if value else value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('name')

    def is_set_name(self) -> bool:
        """Check if name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'name' in self._pending_field_updates)

    def get_uuid(self) -> str:
        """Get the value of uuid."""
        return self.uuid

    def set_uuid(self, value: str):
        """Set the value of uuid."""
        self.uuid = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('uuid')

    def is_set_uuid(self) -> bool:
        """Check if uuid was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'uuid' in self._pending_field_updates)

    def get_fq_name(self) -> List[str]:
        """Get the value of fq_name."""
        return self.fq_name

    def set_fq_name(self, value: List[str]):
        """Set the value of fq_name."""
        self.fq_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('fq_name')

    def add_fq_name(self, item: str):
        """Add an item to fq_name."""
        if self.fq_name is None:
            self.fq_name = []
        self.fq_name.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('fq_name')

    def del_fq_name(self, item: str):
        """Remove an item from fq_name."""
        if self.fq_name and item in self.fq_name:
            self.fq_name.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('fq_name')

    def del_fq_name_by_index(self, index: int):
        """Remove an item from fq_name by index."""
        if self.fq_name and 0 <= index < len(self.fq_name):
            del self.fq_name[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('fq_name')

    def is_set_fq_name(self) -> bool:
        """Check if fq_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'fq_name' in self._pending_field_updates)

    def get_parent_type(self) -> str:
        """Get the value of parent_type."""
        return self.parent_type

    def set_parent_type(self, value: str):
        """Set the value of parent_type."""
        self.parent_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('parent_type')

    def is_set_parent_type(self) -> bool:
        """Check if parent_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'parent_type' in self._pending_field_updates)

    def get_parent_uuid(self) -> str:
        """Get the value of parent_uuid."""
        return self.parent_uuid

    def set_parent_uuid(self, value: str):
        """Set the value of parent_uuid."""
        self.parent_uuid = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('parent_uuid')

    def is_set_parent_uuid(self) -> bool:
        """Check if parent_uuid was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'parent_uuid' in self._pending_field_updates)

    def get_obj_type(self) -> str:
        """Get the value of obj_type."""
        return self.obj_type

    def set_obj_type(self, value: str):
        """Set the value of obj_type."""
        self.obj_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('obj_type')

    def is_set_obj_type(self) -> bool:
        """Check if obj_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'obj_type' in self._pending_field_updates)

    def get_display_name(self) -> str:
        """Get the value of display_name."""
        return self.display_name

    def set_display_name(self, value: str):
        """Set the value of display_name."""
        self.display_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('display_name')

    def is_set_display_name(self) -> bool:
        """Check if display_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'display_name' in self._pending_field_updates)

    def get_description(self) -> str:
        """Get the value of description."""
        return self.description

    def set_description(self, value: str):
        """Set the value of description."""
        self.description = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('description')

    def is_set_description(self) -> bool:
        """Check if description was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'description' in self._pending_field_updates)

    def get_created_by(self) -> str:
        """Get the value of created_by."""
        return self.created_by

    def set_created_by(self, value: str):
        """Set the value of created_by."""
        self.created_by = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('created_by')

    def is_set_created_by(self) -> bool:
        """Check if created_by was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'created_by' in self._pending_field_updates)

    def get_created_at(self) -> str:
        """Get the value of created_at."""
        return self.created_at

    def set_created_at(self, value: str):
        """Set the value of created_at."""
        self.created_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('created_at')

    def is_set_created_at(self) -> bool:
        """Check if created_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'created_at' in self._pending_field_updates)

    def get_updated_at(self) -> str:
        """Get the value of updated_at."""
        return self.updated_at

    def set_updated_at(self, value: str):
        """Set the value of updated_at."""
        self.updated_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('updated_at')

    def is_set_updated_at(self) -> bool:
        """Check if updated_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'updated_at' in self._pending_field_updates)

    def get_icon(self) -> str:
        """Get the value of icon."""
        return self.icon

    def set_icon(self, value: str):
        """Set the value of icon."""
        self.icon = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('icon')

    def is_set_icon(self) -> bool:
        """Check if icon was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'icon' in self._pending_field_updates)

    def get_color(self) -> str:
        """Get the value of color."""
        return self.color

    def set_color(self, value: str):
        """Set the value of color."""
        self.color = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('color')

    def is_set_color(self) -> bool:
        """Check if color was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'color' in self._pending_field_updates)

    def get_tagline(self) -> str:
        """Get the value of tagline."""
        return self.tagline

    def set_tagline(self, value: str):
        """Set the value of tagline."""
        self.tagline = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tagline')

    def is_set_tagline(self) -> bool:
        """Check if tagline was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tagline' in self._pending_field_updates)

    def get_project_summary(self) -> str:
        """Get the value of project_summary."""
        return self.project_summary

    def set_project_summary(self, value: str):
        """Set the value of project_summary."""
        self.project_summary = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('project_summary')

    def is_set_project_summary(self) -> bool:
        """Check if project_summary was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'project_summary' in self._pending_field_updates)

    def get_project_description(self) -> str:
        """Get the value of project_description."""
        return self.project_description

    def set_project_description(self, value: str):
        """Set the value of project_description."""
        self.project_description = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('project_description')

    def is_set_project_description(self) -> bool:
        """Check if project_description was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'project_description' in self._pending_field_updates)

    def get_status(self) -> str:
        """Get the value of status."""
        return self.status

    def set_status(self, value: str):
        """Set the value of status."""
        self.status = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('status')

    def is_set_status(self) -> bool:
        """Check if status was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'status' in self._pending_field_updates)

    def get_is_default(self) -> bool:
        """Get the value of is_default."""
        return self.is_default

    def set_is_default(self, value: bool):
        """Set the value of is_default."""
        self.is_default = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('is_default')

    def is_set_is_default(self) -> bool:
        """Check if is_default was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'is_default' in self._pending_field_updates)

    def get_project_type(self) -> str:
        """Get the value of project_type."""
        return self.project_type

    def set_project_type(self, value: str):
        """Set the value of project_type."""
        self.project_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('project_type')

    def is_set_project_type(self) -> bool:
        """Check if project_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'project_type' in self._pending_field_updates)

    def get_owner_email(self) -> str:
        """Get the value of owner_email."""
        return self.owner_email

    def set_owner_email(self, value: str):
        """Set the value of owner_email."""
        self.owner_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('owner_email')

    def is_set_owner_email(self) -> bool:
        """Check if owner_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'owner_email' in self._pending_field_updates)

    def get_category(self) -> str:
        """Get the value of category."""
        return self.category

    def set_category(self, value: str):
        """Set the value of category."""
        self.category = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('category')

    def is_set_category(self) -> bool:
        """Check if category was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'category' in self._pending_field_updates)

    def get_expected_scale(self) -> str:
        """Get the value of expected_scale."""
        return self.expected_scale

    def set_expected_scale(self, value: str):
        """Set the value of expected_scale."""
        self.expected_scale = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('expected_scale')

    def is_set_expected_scale(self) -> bool:
        """Check if expected_scale was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'expected_scale' in self._pending_field_updates)

    def get_is_multi_tenant(self) -> bool:
        """Get the value of is_multi_tenant."""
        return self.is_multi_tenant

    def set_is_multi_tenant(self, value: bool):
        """Set the value of is_multi_tenant."""
        self.is_multi_tenant = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('is_multi_tenant')

    def is_set_is_multi_tenant(self) -> bool:
        """Check if is_multi_tenant was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'is_multi_tenant' in self._pending_field_updates)

    def get_primary_users(self) -> List[str]:
        """Get the value of primary_users."""
        return self.primary_users

    def set_primary_users(self, value: List[str]):
        """Set the value of primary_users."""
        self.primary_users = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('primary_users')

    def add_primary_users(self, item: str):
        """Add an item to primary_users."""
        if self.primary_users is None:
            self.primary_users = []
        self.primary_users.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('primary_users')

    def del_primary_users(self, item: str):
        """Remove an item from primary_users."""
        if self.primary_users and item in self.primary_users:
            self.primary_users.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('primary_users')

    def del_primary_users_by_index(self, index: int):
        """Remove an item from primary_users by index."""
        if self.primary_users and 0 <= index < len(self.primary_users):
            del self.primary_users[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('primary_users')

    def is_set_primary_users(self) -> bool:
        """Check if primary_users was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'primary_users' in self._pending_field_updates)

    def get_entities(self) -> List[str]:
        """Get the value of entities."""
        return self.entities

    def set_entities(self, value: List[str]):
        """Set the value of entities."""
        self.entities = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('entities')

    def add_entities(self, item: str):
        """Add an item to entities."""
        if self.entities is None:
            self.entities = []
        self.entities.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('entities')

    def del_entities(self, item: str):
        """Remove an item from entities."""
        if self.entities and item in self.entities:
            self.entities.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('entities')

    def del_entities_by_index(self, index: int):
        """Remove an item from entities by index."""
        if self.entities and 0 <= index < len(self.entities):
            del self.entities[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('entities')

    def is_set_entities(self) -> bool:
        """Check if entities was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'entities' in self._pending_field_updates)

    def get_central_entity(self) -> str:
        """Get the value of central_entity."""
        return self.central_entity

    def set_central_entity(self, value: str):
        """Set the value of central_entity."""
        self.central_entity = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('central_entity')

    def is_set_central_entity(self) -> bool:
        """Check if central_entity was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'central_entity' in self._pending_field_updates)

    def get_relationships(self) -> List[EntityRelationship]:
        """Get the value of relationships."""
        return self.relationships

    def set_relationships(self, value: List[EntityRelationship]):
        """Set the value of relationships."""
        self.relationships = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('relationships')

    def add_relationships(self, item: EntityRelationship):
        """Add an item to relationships."""
        if self.relationships is None:
            self.relationships = []
        self.relationships.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('relationships')

    def del_relationships(self, item: EntityRelationship):
        """Remove an item from relationships."""
        if self.relationships and item in self.relationships:
            self.relationships.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('relationships')

    def del_relationships_by_index(self, index: int):
        """Remove an item from relationships by index."""
        if self.relationships and 0 <= index < len(self.relationships):
            del self.relationships[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('relationships')

    def is_set_relationships(self) -> bool:
        """Check if relationships was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'relationships' in self._pending_field_updates)

    def get_status_workflows(self) -> List[StatusWorkflow]:
        """Get the value of status_workflows."""
        return self.status_workflows

    def set_status_workflows(self, value: List[StatusWorkflow]):
        """Set the value of status_workflows."""
        self.status_workflows = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('status_workflows')

    def add_status_workflows(self, item: StatusWorkflow):
        """Add an item to status_workflows."""
        if self.status_workflows is None:
            self.status_workflows = []
        self.status_workflows.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('status_workflows')

    def del_status_workflows(self, item: StatusWorkflow):
        """Remove an item from status_workflows."""
        if self.status_workflows and item in self.status_workflows:
            self.status_workflows.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('status_workflows')

    def del_status_workflows_by_index(self, index: int):
        """Remove an item from status_workflows by index."""
        if self.status_workflows and 0 <= index < len(self.status_workflows):
            del self.status_workflows[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('status_workflows')

    def is_set_status_workflows(self) -> bool:
        """Check if status_workflows was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'status_workflows' in self._pending_field_updates)

    def get_embedded_data_notes(self) -> str:
        """Get the value of embedded_data_notes."""
        return self.embedded_data_notes

    def set_embedded_data_notes(self, value: str):
        """Set the value of embedded_data_notes."""
        self.embedded_data_notes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('embedded_data_notes')

    def is_set_embedded_data_notes(self) -> bool:
        """Check if embedded_data_notes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'embedded_data_notes' in self._pending_field_updates)

    def get_database_preference(self) -> str:
        """Get the value of database_preference."""
        return self.database_preference

    def set_database_preference(self, value: str):
        """Set the value of database_preference."""
        self.database_preference = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('database_preference')

    def is_set_database_preference(self) -> bool:
        """Check if database_preference was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'database_preference' in self._pending_field_updates)

    def get_include_streaming(self) -> bool:
        """Get the value of include_streaming."""
        return self.include_streaming

    def set_include_streaming(self, value: bool):
        """Set the value of include_streaming."""
        self.include_streaming = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('include_streaming')

    def is_set_include_streaming(self) -> bool:
        """Check if include_streaming was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'include_streaming' in self._pending_field_updates)

    def get_include_cache(self) -> bool:
        """Get the value of include_cache."""
        return self.include_cache

    def set_include_cache(self, value: bool):
        """Set the value of include_cache."""
        self.include_cache = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('include_cache')

    def is_set_include_cache(self) -> bool:
        """Check if include_cache was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'include_cache' in self._pending_field_updates)

    def get_include_vector_db(self) -> bool:
        """Get the value of include_vector_db."""
        return self.include_vector_db

    def set_include_vector_db(self, value: bool):
        """Set the value of include_vector_db."""
        self.include_vector_db = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('include_vector_db')

    def is_set_include_vector_db(self) -> bool:
        """Check if include_vector_db was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'include_vector_db' in self._pending_field_updates)

    def get_compliance_standards(self) -> List[str]:
        """Get the value of compliance_standards."""
        return self.compliance_standards

    def set_compliance_standards(self, value: List[str]):
        """Set the value of compliance_standards."""
        self.compliance_standards = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('compliance_standards')

    def add_compliance_standards(self, item: str):
        """Add an item to compliance_standards."""
        if self.compliance_standards is None:
            self.compliance_standards = []
        self.compliance_standards.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('compliance_standards')

    def del_compliance_standards(self, item: str):
        """Remove an item from compliance_standards."""
        if self.compliance_standards and item in self.compliance_standards:
            self.compliance_standards.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('compliance_standards')

    def del_compliance_standards_by_index(self, index: int):
        """Remove an item from compliance_standards by index."""
        if self.compliance_standards and 0 <= index < len(self.compliance_standards):
            del self.compliance_standards[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('compliance_standards')

    def is_set_compliance_standards(self) -> bool:
        """Check if compliance_standards was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'compliance_standards' in self._pending_field_updates)

    def get_sensitive_data_types(self) -> List[str]:
        """Get the value of sensitive_data_types."""
        return self.sensitive_data_types

    def set_sensitive_data_types(self, value: List[str]):
        """Set the value of sensitive_data_types."""
        self.sensitive_data_types = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sensitive_data_types')

    def add_sensitive_data_types(self, item: str):
        """Add an item to sensitive_data_types."""
        if self.sensitive_data_types is None:
            self.sensitive_data_types = []
        self.sensitive_data_types.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sensitive_data_types')

    def del_sensitive_data_types(self, item: str):
        """Remove an item from sensitive_data_types."""
        if self.sensitive_data_types and item in self.sensitive_data_types:
            self.sensitive_data_types.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('sensitive_data_types')

    def del_sensitive_data_types_by_index(self, index: int):
        """Remove an item from sensitive_data_types by index."""
        if self.sensitive_data_types and 0 <= index < len(self.sensitive_data_types):
            del self.sensitive_data_types[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('sensitive_data_types')

    def is_set_sensitive_data_types(self) -> bool:
        """Check if sensitive_data_types was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sensitive_data_types' in self._pending_field_updates)

    def get_audit_requirements(self) -> List[str]:
        """Get the value of audit_requirements."""
        return self.audit_requirements

    def set_audit_requirements(self, value: List[str]):
        """Set the value of audit_requirements."""
        self.audit_requirements = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('audit_requirements')

    def add_audit_requirements(self, item: str):
        """Add an item to audit_requirements."""
        if self.audit_requirements is None:
            self.audit_requirements = []
        self.audit_requirements.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('audit_requirements')

    def del_audit_requirements(self, item: str):
        """Remove an item from audit_requirements."""
        if self.audit_requirements and item in self.audit_requirements:
            self.audit_requirements.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('audit_requirements')

    def del_audit_requirements_by_index(self, index: int):
        """Remove an item from audit_requirements by index."""
        if self.audit_requirements and 0 <= index < len(self.audit_requirements):
            del self.audit_requirements[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('audit_requirements')

    def is_set_audit_requirements(self) -> bool:
        """Check if audit_requirements was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'audit_requirements' in self._pending_field_updates)

    def get_additional_requirements(self) -> str:
        """Get the value of additional_requirements."""
        return self.additional_requirements

    def set_additional_requirements(self, value: str):
        """Set the value of additional_requirements."""
        self.additional_requirements = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('additional_requirements')

    def is_set_additional_requirements(self) -> bool:
        """Check if additional_requirements was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'additional_requirements' in self._pending_field_updates)

    def get_schema_count(self) -> int:
        """Get the value of schema_count."""
        return self.schema_count

    def set_schema_count(self, value: int):
        """Set the value of schema_count."""
        self.schema_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('schema_count')

    def is_set_schema_count(self) -> bool:
        """Check if schema_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'schema_count' in self._pending_field_updates)

    def get_deployment_status(self) -> str:
        """Get the value of deployment_status."""
        return self.deployment_status

    def set_deployment_status(self, value: str):
        """Set the value of deployment_status."""
        self.deployment_status = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('deployment_status')

    def is_set_deployment_status(self) -> bool:
        """Check if deployment_status was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'deployment_status' in self._pending_field_updates)

    def get_discovery_completed(self) -> bool:
        """Get the value of discovery_completed."""
        return self.discovery_completed

    def set_discovery_completed(self, value: bool):
        """Set the value of discovery_completed."""
        self.discovery_completed = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discovery_completed')

    def is_set_discovery_completed(self) -> bool:
        """Check if discovery_completed was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discovery_completed' in self._pending_field_updates)

    def get_discovery_completed_at(self) -> str:
        """Get the value of discovery_completed_at."""
        return self.discovery_completed_at

    def set_discovery_completed_at(self, value: str):
        """Set the value of discovery_completed_at."""
        self.discovery_completed_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discovery_completed_at')

    def is_set_discovery_completed_at(self) -> bool:
        """Check if discovery_completed_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discovery_completed_at' in self._pending_field_updates)

    def get_archived_at(self) -> str:
        """Get the value of archived_at."""
        return self.archived_at

    def set_archived_at(self, value: str):
        """Set the value of archived_at."""
        self.archived_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('archived_at')

    def is_set_archived_at(self) -> bool:
        """Check if archived_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'archived_at' in self._pending_field_updates)

    def get_archived_by(self) -> str:
        """Get the value of archived_by."""
        return self.archived_by

    def set_archived_by(self, value: str):
        """Set the value of archived_by."""
        self.archived_by = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('archived_by')

    def is_set_archived_by(self) -> bool:
        """Check if archived_by was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'archived_by' in self._pending_field_updates)

    def get_tags(self) -> List[str]:
        """Get the value of tags."""
        return self.tags

    def set_tags(self, value: List[str]):
        """Set the value of tags."""
        self.tags = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tags')

    def add_tags(self, item: str):
        """Add an item to tags."""
        if self.tags is None:
            self.tags = []
        self.tags.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tags')

    def del_tags(self, item: str):
        """Remove an item from tags."""
        if self.tags and item in self.tags:
            self.tags.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('tags')

    def del_tags_by_index(self, index: int):
        """Remove an item from tags by index."""
        if self.tags and 0 <= index < len(self.tags):
            del self.tags[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('tags')

    def is_set_tags(self) -> bool:
        """Check if tags was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tags' in self._pending_field_updates)

    def get_schema_registry_refs(self) -> List[Dict[str, Any]]:
        """Get the references to SchemaRegistry."""
        return self.schema_registry_refs

    def set_schema_registry_refs(self, value: List[Dict[str, Any]]):
        """Set the references to SchemaRegistry."""
        self.schema_registry_refs = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('schema_registry_refs')

    def add_schema_registry_ref(self, uuid: str = None, fq_name: List[str] = None,
                                 ref_or_target=None, link_data: Dict[str, Any] = None):
        """
        Add a reference to a SchemaRegistry.
        
        Args:
            uuid: UUID of target (if not using ref_or_target)
            fq_name: FQ name of target (if not using ref_or_target)
            ref_or_target: Target object instance
            link_data: Optional dict with relationship metadata (role, allocation, etc.)
        
        Examples:
            # Method 1: Direct uuid/fq_name with link_data
            obj.add_schema_registry_ref(
                uuid='user-123',
                fq_name=['users', 'alice'],
                link_data={'role': 'lead', 'allocation': 1.0}
            )
            
            # Method 2: Pass target object with link_data
            target = SchemaRegistry.find_one(name='alice')
            obj.add_schema_registry_ref(
                ref_or_target=target,
                link_data={'role': 'lead', 'allocation': 1.0}
            )
        """
        # Handle target object
        if ref_or_target is not None:
            uuid = getattr(ref_or_target, 'uuid', uuid)
            fq_name = getattr(ref_or_target, 'fq_name', fq_name)
        
        # Create reference dict
        ref_dict = {
            'uuid': uuid,
            'fq_name': fq_name,
        }
        
        # Add to refs list if not duplicate
        if not any(r['uuid'] == uuid for r in self.schema_registry_refs):
            self.schema_registry_refs.append(ref_dict)
            
            # Store link_data separately if provided
            if link_data:
                if not hasattr(self, '_ref_link_data'):
                    self._ref_link_data = {}
                self._ref_link_data[uuid] = link_data
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('schema_registry_refs')

    def del_schema_registry_ref(self, uuid: str):
        """Delete a reference to a SchemaRegistry object by UUID."""
        self.schema_registry_refs = [r for r in self.schema_registry_refs if r['uuid'] != uuid]
        # Clean up link_data
        if hasattr(self, '_ref_link_data') and uuid in self._ref_link_data:
            del self._ref_link_data[uuid]
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('schema_registry_refs')

    def get_schema_registry_objects(self) -> 'List[SchemaRegistry]':
        """
        Get actual SchemaRegistry objects from references.
        
        Returns:
            List of SchemaRegistry objects
        
        Note:
            Access link_data separately via obj._ref_link_data[uuid]
        
        Examples:
            # Get objects and access link_data
            for target in obj.get_schema_registry_objects():
                link_data = obj._ref_link_data.get(target.uuid, {})
                print(target.name, link_data.get('role'))
        """
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from . import schema_registry
        import importlib
        
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.schema_registry'
        try:
            module = importlib.import_module(module_name)
            SchemaRegistry = getattr(module, 'SchemaRegistry')
            
            result = []
            for ref_dict in self.schema_registry_refs:
                # Create object from dict
                target = SchemaRegistry.from_dict(ref_dict)
                if target:
                    result.append(target)
            
            return result
        except (ImportError, AttributeError):
            return []

    def is_set_schema_registry_refs(self) -> bool:
        """Check if schema_registry was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'schema_registry_refs' in self._pending_field_updates)

    def get_tenants(self) -> 'List[Tenant]':
        """Get all Tenant objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.tenant import Tenant
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.tenant'
        try:
            module = importlib.import_module(module_name)
            Tenant = getattr(module, 'Tenant')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def tenants(self) -> 'List[Tenant]':
        """Property to access Tenant children."""
        return self.get_tenants()

    def get_gatekeepers(self) -> 'List[Gatekeeper]':
        """Get all Gatekeeper objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.gatekeeper import Gatekeeper
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.gatekeeper'
        try:
            module = importlib.import_module(module_name)
            Gatekeeper = getattr(module, 'Gatekeeper')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def gatekeepers(self) -> 'List[Gatekeeper]':
        """Property to access Gatekeeper children."""
        return self.get_gatekeepers()


    # ========================================================================
    # END-POINTS QUERY METHODS
    # ========================================================================

    @classmethod
    def get_end_points(cls):
        """Get all configured end_points for this object type."""
        return [ep.copy() for ep in cls._end_points]

    @classmethod
    def get_end_point(cls, type=None, name=None, cloud=None, operation=None, enabled_only=True):
        """
        Query specific end-point by criteria.
        
        Args:
            type: End-point type (database, streaming, cache, search, blob-storage, vector-db)
            name: Technology name (mongo, kafka, redis, pinecone, etc.)
            cloud: Cloud environment (private, platform, public, hybrid)
            operation: Operation name (create, read, update, delete, search, similarity_search)
            enabled_only: Only return enabled end_points
        
        Returns:
            Matching end-point dict or None
        """
        for ep in cls._end_points:
            if enabled_only and not ep.get('enabled', True):
                continue
            if type and ep.get('type') != type:
                continue
            if name and ep.get('name') != name:
                continue
            if cloud and cloud not in ep.get('cloud', []):
                continue
            if operation and operation not in ep.get('operations', []):
                continue
            return ep.copy()
        return None

    @classmethod
    def get_end_points_by_type(cls, ep_type, enabled_only=True):
        """Get all end_points of a specific type."""
        return [
            ep.copy() for ep in cls._end_points 
            if ep.get('type') == ep_type and (not enabled_only or ep.get('enabled', True))
        ]

    @classmethod
    def get_end_points_by_cloud(cls, cloud, enabled_only=True):
        """Get all end_points available in a specific cloud."""
        return [
            ep.copy() for ep in cls._end_points 
            if cloud in ep.get('cloud', []) and (not enabled_only or ep.get('enabled', True))
        ]

    @classmethod
    def supports_operation(cls, operation, ep_type=None):
        """Check if this object type supports an operation."""
        for ep in cls._end_points:
            if not ep.get('enabled', True):
                continue
            if ep_type and ep.get('type') != ep_type:
                continue
            if operation in ep.get('operations', []):
                return True
        return False

    @classmethod
    def get_primary_end_point(cls, ep_type=None):
        """Get the primary (highest priority) end-point of a type."""
        candidates = cls._end_points
        if ep_type:
            candidates = [ep for ep in candidates if ep.get('type') == ep_type]
        
        candidates = [ep for ep in candidates if ep.get('enabled', True)]
        
        if not candidates:
            return None
        
        # Sort by priority (lower number = higher priority)
        candidates.sort(key=lambda x: x.get('priority', 999))
        return candidates[0].copy()

    @classmethod
    def supports_vector_search(cls):
        """Check if this object type has vector database support."""
        return cls.get_end_point(type="vector-db") is not None

    @classmethod
    def get_vector_config(cls):
        """Get vector database configuration."""
        vector_ep = cls.get_end_point(type="vector-db")
        return vector_ep.get('config', {}) if vector_ep else {}

    # ========================================================================
    # INDEX QUERY METHODS
    # ========================================================================

    @classmethod
    def get_indexes(cls):
        """Get all index definitions for this object type."""
        return {k: v.copy() for k, v in cls._indexes.items()}

    @classmethod
    def get_index(cls, name):
        """Get specific index definition by name."""
        idx = cls._indexes.get(name)
        return idx.copy() if idx else None

    @classmethod
    def get_index_names(cls):
        """Get all index names."""
        return list(cls._indexes.keys())

    @classmethod
    def get_indexes_for_attribute(cls, attr_name):
        """Get all indexes that include a specific attribute."""
        result = []
        for idx_name, idx_def in cls._indexes.items():
            fields = idx_def.get('fields', [])
            if any(f.get('name') == attr_name for f in fields):
                result.append(idx_name)
        return result

    @classmethod
    def get_compound_indexes(cls):
        """Get all compound indexes (indexes with multiple fields)."""
        return {
            k: v.copy() for k, v in cls._indexes.items()
            if v.get('type') == 'compound'
        }

    @classmethod
    def get_simple_indexes(cls):
        """Get all simple indexes (single field)."""
        return {
            k: v.copy() for k, v in cls._indexes.items()
            if v.get('type') == 'simple'
        }

    # ========================================================================
    # INSTANCE ROUTING METHODS
    # ========================================================================

    def get_routing_info(self):
        """
        Get routing information for this instance.
        Useful for sharding, partitioning, cloud selection.
        """
        return {
            'object_type': getattr(self, 'obj_type', self.__class__.__name__),
            'uuid': getattr(self, 'uuid', None),
            'cloud': self._determine_cloud(),
            'partition_key': self._get_partition_key(),
            'endpoints': self.get_end_points()
        }

    def _determine_cloud(self):
        """Determine cloud environment based on instance data."""
        if hasattr(self, 'country'):
            country = getattr(self, 'country')
            if country in ['US', 'Canada']:
                return 'private'
        return 'platform'

    def _get_partition_key(self):
        """Get partition key value for this instance."""
        for ep in self._end_points:
            partition_key_name = ep.get('config', {}).get('partition_key')
            if partition_key_name:
                return getattr(self, partition_key_name, getattr(self, 'uuid', ''))
        return getattr(self, 'uuid', '')

    # ========================================================================
    # PENDING FIELD TRACKING METHODS
    # ========================================================================

    def disable_pending_tracking(self):
        """Temporarily disable pending field tracking."""
        self._tracking_disabled = True
    
    def enable_pending_tracking(self):
        """Re-enable pending field tracking."""
        self._tracking_disabled = False
    
    def is_pending_tracking_enabled(self):
        """Check if pending field tracking is currently enabled."""
        return (hasattr(self, '_pending_field_updates') and 
                not getattr(self, '_initializing', False) and
                not getattr(self, '_tracking_disabled', False))

    def clear_pending_updates(self):
        """Clear the pending field updates set."""
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.clear()
    
    def get_pending_updates(self):
        """Get the set of pending field updates."""
        return getattr(self, '_pending_field_updates', set()).copy()
    
    def has_pending_updates(self):
        """Check if there are any pending updates."""
        return bool(getattr(self, '_pending_field_updates', set()))

    # ========================================================================
    # SERIALIZATION METHODS
    # ========================================================================

    @staticmethod
    def _parse_datetime(value):
        """Parse a datetime string or return datetime object as-is."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    return value
        return value

    @staticmethod
    def _format_datetime(value):
        """Format a datetime object to ISO string."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def to_dict(self, include_all_fields=True, validate=False):
        """
        Converts the object to a dictionary, including nested objects.
        ENHANCED: Automatically converts datetime objects to ISO strings.
        
        Args:
            include_all_fields: If True, include all non-None fields. 
                              If False, only include pending field updates + mandatory system fields
        """
        data = {}
        
        if include_all_fields or not hasattr(self, '_pending_field_updates'):
            for py_key, json_key in self._py_to_json_map.items():
                value = getattr(self, py_key, None)
                if value is not None:
                    if hasattr(value, 'to_dict'):
                        data[json_key] = value.to_dict()
                    elif isinstance(value, datetime):
                        data[json_key] = self._format_datetime(value)
                    elif isinstance(value, list):
                        converted_list = []
                        for item in value:
                            if hasattr(item, 'to_dict'):
                                converted_list.append(item.to_dict())
                            elif isinstance(item, datetime):
                                converted_list.append(self._format_datetime(item))
                            else:
                                converted_list.append(item)
                        data[json_key] = converted_list
                    else:
                        data[json_key] = value
        else:
            fields_to_include = set(self._pending_field_updates)
            mandatory_for_updates = {'uuid', 'name', 'fq_name', 'parent_uuid', 'obj_type', 'parent_type'}
            
            for field in mandatory_for_updates:
                if field in self._py_to_json_map:
                    value = getattr(self, field, None)
                    if value is not None:
                        if field == 'parent_uuid' or (value and value != ''):
                            fields_to_include.add(field)
            
            for py_key in fields_to_include:
                if py_key in self._py_to_json_map:
                    json_key = self._py_to_json_map[py_key]
                    value = getattr(self, py_key, None)
                    
                    if hasattr(value, 'to_dict'):
                        data[json_key] = value.to_dict()
                    elif isinstance(value, datetime):
                        data[json_key] = self._format_datetime(value)
                    elif isinstance(value, list):
                        converted_list = []
                        for item in value:
                            if hasattr(item, 'to_dict'):
                                converted_list.append(item.to_dict())
                            elif isinstance(item, datetime):
                                converted_list.append(self._format_datetime(item))
                            else:
                                converted_list.append(item)
                        data[json_key] = converted_list
                    else:
                        data[json_key] = value
        
        # NEW: Embed link_data into references before returning
        if hasattr(self, '_ref_link_data') and self._ref_link_data:
            for py_key, json_key in self._py_to_json_map.items():
                if py_key.endswith('_refs') and json_key in data:
                    # Get the refs list from data
                    refs = data[json_key]
                    if isinstance(refs, list):
                        # Embed link_data into each reference
                        refs_with_link_data = []
                        for ref in refs:
                            if isinstance(ref, dict):
                                ref_copy = ref.copy()
                                uuid = ref_copy.get('uuid')
                                if uuid and uuid in self._ref_link_data:
                                    ref_copy['link_data'] = self._ref_link_data[uuid]
                                refs_with_link_data.append(ref_copy)
                            else:
                                refs_with_link_data.append(ref)
                        data[json_key] = refs_with_link_data
        
        if validate:
            self._validate_mandatory_fields()
        
        return data 

    def to_dict_for_update(self):
        """Converts only the modified fields + mandatory system fields to a dictionary for partial updates."""
        return self.to_dict(include_all_fields=False)

    def _validate_mandatory_fields(self):
        """
        Validate that all mandatory fields are set with non-None values.
        
        Called by to_dict(validate=True) before CREATE operations.
        
        Raises:
            ValueError: If any mandatory fields are missing or None
        """
        missing = []
        
        # Check each field in type metadata
        if hasattr(self, '_type_metadata'):
            for field_name, metadata in self._type_metadata.items():
                if metadata.get('mandatory'):
                    value = getattr(self, field_name, None)
                    
                    # Check if value is None or empty
                    if value is None:
                        missing.append(field_name)
                    # For strings, check if empty
                    elif isinstance(value, str) and not value.strip():
                        missing.append(field_name)
        
        # Raise error if any mandatory fields are missing
        if missing:
            raise ValueError(
                f"Cannot serialize {self.__class__.__name__}: "
                f"Missing mandatory fields: {', '.join(missing)}. "
                f"Please set these fields before calling to_dict(validate=True)."
            )

    @classmethod
    def _get_type_for_attribute(cls, py_key):
        """Get the type class for a given attribute."""
        type_info = cls._type_metadata.get(py_key)
        if not type_info:
            return None, False, False
            
        type_name = type_info.get('type')
        is_list = type_info.get('is_list', False)
        
        if not type_name:
            return None, False, False
            
        builtin_types = {
            'string': str, 'str': str, 'int': int, 'integer': int,
            'float': float, 'bool': bool, 'boolean': bool,
            'list': list, 'dict': dict, 'uuid': str, 'date': str, 'datetime': str
        }
        
        if type_name.lower() in builtin_types:
            return builtin_types[type_name.lower()], is_list, False
            
        try:
            import inflection
            import importlib
            snake_type_name = inflection.underscore(type_name)
            
            import_paths = [
                f'pymodel.enums.{snake_type_name}',
                f'pymodel.types.{snake_type_name}',
                f'pymodel.objects.{snake_type_name}',
            ]
            
            for i, import_path in enumerate(import_paths):
                try:
                    module = importlib.import_module(import_path)
                    type_class = getattr(module, type_name, None)
                    if type_class:
                        is_enum = (i == 0)
                        return type_class, is_list, is_enum
                except (ImportError, AttributeError):
                    continue
                    
        except Exception:
            pass
            
        return None, is_list, False

    @classmethod
    def _deserialize_value(cls, value, target_type, is_list=False, is_enum=False, field_name="unknown", type_name="unknown"):
        """Deserialize a value to the target type with STRICT type checking and datetime support."""
        if value is None:
            return [] if is_list else None
        
        if type_name.lower() in ['datetime', 'date']:
            if is_list:
                if not isinstance(value, list):
                    raise ObjectDeserializationError(
                        f"Expected list for datetime field '{field_name}', got {type(value).__name__}",
                        obj_type=cls.__name__, attribute=field_name, value=value
                    )
                return [cls._parse_datetime(item) for item in value]
            else:
                return cls._parse_datetime(value)
            
        builtin_types = {str, int, float, bool, list, dict}
        
        if is_list:
            if not isinstance(value, list):
                raise ObjectDeserializationError(
                    f"Expected list for field '{field_name}', got {type(value).__name__}",
                    obj_type=cls.__name__, attribute=field_name, value=value
                )
                
            if not value:
                return []
                
            if target_type is None:
                import inflection
                raise ObjectDeserializationError(
                    f"CRITICAL: Cannot deserialize list field '{field_name}' - type '{type_name}' not found. "
                    f"Check if pymodel.types.{inflection.underscore(type_name)}.py exists with class {type_name}.",
                    obj_type=cls.__name__, attribute=field_name, value=f"List with {len(value)} items"
                )
            
            if target_type in builtin_types:
                return value
            elif hasattr(target_type, 'from_dict'):
                deserialized_items = []
                for i, item in enumerate(value):
                    try:
                        if is_enum:
                            if isinstance(item, str):
                                deserialized_items.append(target_type(item))
                            else:
                                raise ObjectDeserializationError(
                                    f"Expected string for enum list item {i} in field '{field_name}', got {type(item).__name__}",
                                    obj_type=cls.__name__, attribute=f"{field_name}[{i}]", value=item
                                )
                        else:
                            if isinstance(item, dict):
                                deserialized_items.append(target_type.from_dict(item))
                            else:
                                raise ObjectDeserializationError(
                                    f"Expected dict for custom type list item {i} in field '{field_name}', got {type(item).__name__}",
                                    obj_type=cls.__name__, attribute=f"{field_name}[{i}]", value=item
                                )
                    except Exception as e:
                        raise ObjectDeserializationError(
                            f"Failed to deserialize list item {i} in field '{field_name}' to {target_type.__name__}: {str(e)}",
                            obj_type=cls.__name__, attribute=f"{field_name}[{i}]", value=item, original_error=e
                        )
                return deserialized_items
            else:
                raise ObjectDeserializationError(
                    f"CRITICAL: Type '{type_name}' found for field '{field_name}' but has no from_dict() method.",
                    obj_type=cls.__name__, attribute=field_name, value=f"Type: {target_type}"
                )
        else:
            if target_type is None:
                if type_name not in ['string', 'int', 'bool', 'float']:
                    try:
                        import logging
                        logging.getLogger(__name__).warning(
                            f"Could not find type '{type_name}' for field '{field_name}' in {cls.__name__}."
                        )
                    except:
                        pass
                return value
                
            if target_type in builtin_types:
                return value
            elif hasattr(target_type, 'from_dict'):
                try:
                    if is_enum:
                        if isinstance(value, str):
                            return target_type(value)
                        else:
                            raise ObjectDeserializationError(
                                f"Expected string for enum field '{field_name}', got {type(value).__name__}",
                                obj_type=cls.__name__, attribute=field_name, value=value
                            )
                    else:
                        if isinstance(value, dict):
                            return target_type.from_dict(value)
                        else:
                            raise ObjectDeserializationError(
                                f"Expected dict for custom type field '{field_name}', got {type(value).__name__}",
                                obj_type=cls.__name__, attribute=field_name, value=value
                            )
                except Exception as e:
                    raise ObjectDeserializationError(
                        f"Failed to deserialize field '{field_name}' to {target_type.__name__}: {str(e)}",
                        obj_type=cls.__name__, attribute=field_name, value=value, original_error=e
                    )
            else:
                return value

    @classmethod
    def _find_field_value(cls, py_key, data):
        """Find a field value in data using multiple naming conventions."""
        import inflection
        field_variations = [
            py_key,
            py_key.replace('_', '-'),
            inflection.dasherize(py_key),
            inflection.underscore(py_key),
        ]
        
        field_variations = list(dict.fromkeys(field_variations))
        
        for variation in field_variations:
            if variation in data:
                return variation, data[variation]
        
        return None, None

    @classmethod
    def from_dict(cls, data):
        """
        Creates an instance from a dictionary, handling nested objects.
        ENHANCED: Automatically converts datetime strings to datetime objects.
        ENHANCED: Derives name from fq_name if missing, validates if both present.
        FLEXIBLE MODE: Accepts multiple field naming conventions.
        """
        if data is None:
            return cls.from_empty()
            
        if not isinstance(data, dict):
            raise ObjectDeserializationError(
                f"Expected dict or None for {cls.__name__} deserialization, got {type(data).__name__}",
                obj_type=cls.__name__, value=data
            )

        if not data:
            return cls.from_empty()

        # NEW: Auto-derive name from fq_name if missing, or validate if both present
        if 'fq_name' in data:
            fq_name = data.get('fq_name')
            if fq_name and isinstance(fq_name, list) and len(fq_name) > 0:
                expected_name = fq_name[-1]
                
                if 'name' in data:
                    # Both present - validate they match
                    provided_name = data['name']
                    if provided_name != expected_name:
                        raise ObjectDeserializationError(
                            f"Name mismatch in {cls.__name__}: 'name' field is '{provided_name}' but "
                            f"fq_name[-1] is '{expected_name}'. They must match.",
                            obj_type=cls.__name__, value=data
                        )
                else:
                    # Only fq_name present - auto-derive name
                    data = data.copy()  # Don't modify original
                    data['name'] = expected_name

        temp_instance = cls.from_empty()
        init_args = {}
        back_refs = {}
        ref_link_data = {}  # NEW: Store extracted link_data
        
        processed_fields = set()
        deserialization_failures = []
        
        for json_key, value in data.items():
            try:
                # NEW: Extract link_data from references
                if json_key.endswith('_refs') or json_key.endswith('-refs'):
                    if isinstance(value, list):
                        # Check each reference for link_data
                        clean_refs = []
                        for ref in value:
                            if isinstance(ref, dict):
                                ref_copy = ref.copy()
                                # Extract and store link_data
                                if 'link_data' in ref_copy:
                                    uuid = ref_copy.get('uuid')
                                    if uuid:
                                        ref_link_data[uuid] = ref_copy.pop('link_data')
                                clean_refs.append(ref_copy)
                            else:
                                clean_refs.append(ref)
                        value = clean_refs
                
                if (json_key.endswith('_back_refs') or json_key.endswith('_refs') or '_back_refs' in json_key):
                    back_refs[json_key] = value
                    continue
                    
                py_key = None
                py_key = temp_instance._json_to_py_map.get(json_key)
                
                if not py_key:
                    import inflection
                    potential_py_key = inflection.underscore(json_key)
                    if potential_py_key in cls._type_metadata:
                        py_key = potential_py_key
                
                if not py_key and json_key in cls._type_metadata:
                    py_key = json_key
                
                if not py_key:
                    for metadata_py_key in cls._type_metadata.keys():
                        field_name_found, _ = cls._find_field_value(metadata_py_key, {json_key: value})
                        if field_name_found:
                            py_key = metadata_py_key
                            break
                
                if py_key in ['parent_type', 'obj_type']:
                    continue
                
                if py_key in processed_fields:
                    continue
                    
                if py_key:
                    processed_fields.add(py_key)
                    
                    type_info = cls._get_type_for_attribute(py_key)
                    if type_info:
                        target_type, is_list, is_enum = type_info
                        original_type_name = cls._type_metadata.get(py_key, {}).get('type', 'unknown')
                        try:
                            deserialized_value = cls._deserialize_value(
                                value, target_type, is_list, is_enum,
                                field_name=json_key, type_name=original_type_name
                            )
                            init_args[py_key] = deserialized_value
                        except Exception as e:
                            deserialization_failures.append(f"Field '{json_key}' (Python: '{py_key}'): {str(e)}")
                    else:
                        init_args[py_key] = value
                    
            except Exception:
                pass

        if deserialization_failures:
            detailed_error = (
                f"DESERIALIZATION FAILED for {cls.__name__}: Field conversion errors: "
                f"{'; '.join(deserialization_failures)}."
            )
            raise ObjectDeserializationError(
                detailed_error, obj_type=cls.__name__,
                attribute=deserialization_failures[0].split("'")[1] if deserialization_failures else None,
                value=data, original_error=Exception("Field conversion failures")
            )

        try:
            instance = cls(**init_args)
        except TypeError as e:
            detailed_error = (
                f"OBJECT CONSTRUCTION FAILED for {cls.__name__}: Constructor rejected arguments. "
                f"Provided args: {list(init_args.keys())}. Error: {str(e)}."
            )
            raise ObjectDeserializationError(
                detailed_error, obj_type=cls.__name__, value=init_args, original_error=e
            )
        except Exception as e:
            detailed_error = f"OBJECT CONSTRUCTION FAILED for {cls.__name__}: {str(e)}"
            raise ObjectDeserializationError(
                detailed_error, obj_type=cls.__name__, value=init_args, original_error=e
            )
        
        # NEW: Attach extracted link_data to instance
        if ref_link_data:
            instance._ref_link_data = ref_link_data
        
        for ref_name, ref_value in back_refs.items():
            try:
                setattr(instance, ref_name, ref_value)
            except Exception:
                pass


        # Update pending field updates for all fields present in the data
        for json_key, value in data.items():
            py_key = instance._json_to_py_map.get(json_key)
            if py_key and py_key not in ['parent_type', 'obj_type']:
                instance._pending_field_updates.add(py_key)

        return instance

    @classmethod
    def from_mandatory(cls, name: str):
        """Creates an instance with only mandatory fields."""
        mandatory_args = {k: v for k, v in locals().items() if k != 'cls'}
        return cls(**mandatory_args)

    @classmethod
    def from_empty(cls):
        """Creates an empty instance with no fields set, providing defaults for mandatory fields."""
        return cls(name="", uuid=None, fq_name=None, parent_uuid=None, display_name=None, description=None, created_by=None, created_at=None, updated_at=None, icon=None, color=None, tagline=None, project_summary=None, project_description=None, status=None, is_default=None, project_type=None, owner_email=None, category=None, expected_scale=None, is_multi_tenant=None, primary_users=None, entities=None, central_entity=None, relationships=None, status_workflows=None, embedded_data_notes=None, database_preference=None, include_streaming=None, include_cache=None, include_vector_db=None, compliance_standards=None, sensitive_data_types=None, audit_requirements=None, additional_requirements=None, schema_count=None, deployment_status=None, discovery_completed=None, discovery_completed_at=None, archived_at=None, archived_by=None, tags=None)

project=Project
Project=Project
Project=Project
project=Project
