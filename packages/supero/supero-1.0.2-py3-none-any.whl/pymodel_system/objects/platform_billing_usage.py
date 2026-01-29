# File: pymodel_system/objects/platform_billing_usage.py
"""
This file was generated from the platform_billing_usage.json schema.
ENHANCED: Proper datetime handling with automatic string<->datetime conversion.
ENHANCED: Supero fluent API support with smart reference management.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import importlib
import uuid
import inflection
from datetime import datetime

from ..serialization_errors import ObjectDeserializationError, InvalidParentError
from datetime import datetime
import re

class PlatformBillingUsage:
    """
    Represents a PlatformBillingUsage instance.
    
    This class is auto-generated and includes:
    - Standard CRUD operations
    - Fluent API methods (when used with Supero)
    - Smart reference management with link data support
    - Parent-child hierarchy navigation
    """
    
    _OBJ_TYPE = "platform_billing_usage"
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
    'period_month': {
        'type': 'str',
        'is_list': False,
        'json_name': 'period_month',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'period_start': {
        'type': 'str',
        'is_list': False,
        'json_name': 'period_start',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'period_end': {
        'type': 'str',
        'is_list': False,
        'json_name': 'period_end',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'snapshot_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'snapshot_at',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'snapshot_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'snapshot_type',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'is_final': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'is_final',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'schema_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'schema_count',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'schema_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'schema_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'object_count_total': {
        'type': 'int',
        'is_list': False,
        'json_name': 'object_count_total',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'api_request_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'api_request_count',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'api_request_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'api_request_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'api_read_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'api_read_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'api_write_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'api_write_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'api_error_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'api_error_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'storage_bytes_total': {
        'type': 'int',
        'is_list': False,
        'json_name': 'storage_bytes_total',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'storage_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'storage_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'db_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'db_storage_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'blob_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'blob_storage_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'vector_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'vector_storage_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'team_member_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'team_member_count',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'team_member_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'team_member_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'project_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'project_count',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'project_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'project_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'api_key_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'api_key_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'plugin_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'plugin_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'plugin_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'plugin_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'plugin_invocation_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'plugin_invocation_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'plugin_invocation_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'plugin_invocation_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'kafka_topic_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'kafka_topic_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'kafka_message_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'kafka_message_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'kafka_message_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'kafka_message_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'vector_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'vector_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'vector_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'vector_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'vector_query_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'vector_query_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'vector_query_limit': {
        'type': 'int',
        'is_list': False,
        'json_name': 'vector_query_limit',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'sdk_generation_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'sdk_generation_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'workflow_execution_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'workflow_execution_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'bandwidth_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'bandwidth_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'usage_by_project': {
        'type': 'str',
        'is_list': False,
        'json_name': 'usage_by_project',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'usage_by_schema': {
        'type': 'str',
        'is_list': False,
        'json_name': 'usage_by_schema',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'peak_api_requests_per_second': {
        'type': 'int',
        'is_list': False,
        'json_name': 'peak_api_requests_per_second',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'overage_detected': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'overage_detected',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'exceeded_metrics': {
        'type': 'str',
        'is_list': True,
        'json_name': 'exceeded_metrics',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'overage_details': {
        'type': 'str',
        'is_list': False,
        'json_name': 'overage_details',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'overage_charges_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'overage_charges_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'alerts_triggered': {
        'type': 'str',
        'is_list': True,
        'json_name': 'alerts_triggered',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    }
}
    
    # Infrastructure end_points metadata
    _end_points = []
    
    # Index definitions
    _indexes = {}

    _CONSTRAINTS = {
        'period_month': {
            'pattern': '^\\d{4}-\\d{2}$',
            'type': 'string',
        },
        'schema_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'object_count_total': {
            'min-value': 0,
            'type': 'integer',
        },
        'api_request_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'api_read_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'api_write_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'api_error_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'storage_bytes_total': {
            'min-value': 0,
            'type': 'integer',
        },
        'db_storage_bytes': {
            'min-value': 0,
            'type': 'integer',
        },
        'blob_storage_bytes': {
            'min-value': 0,
            'type': 'integer',
        },
        'vector_storage_bytes': {
            'min-value': 0,
            'type': 'integer',
        },
        'team_member_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'project_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'api_key_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'plugin_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'plugin_invocation_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'kafka_topic_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'kafka_message_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'vector_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'vector_query_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'sdk_generation_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'workflow_execution_count': {
            'min-value': 0,
            'type': 'integer',
        },
        'bandwidth_bytes': {
            'min-value': 0,
            'type': 'integer',
        },
        'overage_charges_cents': {
            'min-value': 0,
            'type': 'integer',
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
        period_month: Optional[str] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        snapshot_at: Optional[str] = None,
        snapshot_type: Optional[str] = None,
        is_final: Optional[bool] = None,
        schema_count: Optional[int] = None,
        schema_limit: Optional[int] = None,
        object_count_total: Optional[int] = None,
        api_request_count: Optional[int] = None,
        api_request_limit: Optional[int] = None,
        api_read_count: Optional[int] = None,
        api_write_count: Optional[int] = None,
        api_error_count: Optional[int] = None,
        storage_bytes_total: Optional[int] = None,
        storage_limit: Optional[int] = None,
        db_storage_bytes: Optional[int] = None,
        blob_storage_bytes: Optional[int] = None,
        vector_storage_bytes: Optional[int] = None,
        team_member_count: Optional[int] = None,
        team_member_limit: Optional[int] = None,
        project_count: Optional[int] = None,
        project_limit: Optional[int] = None,
        api_key_count: Optional[int] = None,
        plugin_count: Optional[int] = None,
        plugin_limit: Optional[int] = None,
        plugin_invocation_count: Optional[int] = None,
        plugin_invocation_limit: Optional[int] = None,
        kafka_topic_count: Optional[int] = None,
        kafka_message_count: Optional[int] = None,
        kafka_message_limit: Optional[int] = None,
        vector_count: Optional[int] = None,
        vector_limit: Optional[int] = None,
        vector_query_count: Optional[int] = None,
        vector_query_limit: Optional[int] = None,
        sdk_generation_count: Optional[int] = None,
        workflow_execution_count: Optional[int] = None,
        bandwidth_bytes: Optional[int] = None,
        usage_by_project: Optional[str] = None,
        usage_by_schema: Optional[str] = None,
        peak_api_requests_per_second: Optional[int] = None,
        overage_detected: Optional[bool] = None,
        exceeded_metrics: Optional[List[str]] = None,
        overage_details: Optional[str] = None,
        overage_charges_cents: Optional[int] = None,
        alerts_triggered: Optional[List[str]] = None
    ):
        # Set initialization flag to prevent tracking during __init__
        self._initializing = True
        
        self.obj_type = "platform_billing_usage"
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
    'period_month': 'period_month',
    'period_start': 'period_start',
    'period_end': 'period_end',
    'snapshot_at': 'snapshot_at',
    'snapshot_type': 'snapshot_type',
    'is_final': 'is_final',
    'schema_count': 'schema_count',
    'schema_limit': 'schema_limit',
    'object_count_total': 'object_count_total',
    'api_request_count': 'api_request_count',
    'api_request_limit': 'api_request_limit',
    'api_read_count': 'api_read_count',
    'api_write_count': 'api_write_count',
    'api_error_count': 'api_error_count',
    'storage_bytes_total': 'storage_bytes_total',
    'storage_limit': 'storage_limit',
    'db_storage_bytes': 'db_storage_bytes',
    'blob_storage_bytes': 'blob_storage_bytes',
    'vector_storage_bytes': 'vector_storage_bytes',
    'team_member_count': 'team_member_count',
    'team_member_limit': 'team_member_limit',
    'project_count': 'project_count',
    'project_limit': 'project_limit',
    'api_key_count': 'api_key_count',
    'plugin_count': 'plugin_count',
    'plugin_limit': 'plugin_limit',
    'plugin_invocation_count': 'plugin_invocation_count',
    'plugin_invocation_limit': 'plugin_invocation_limit',
    'kafka_topic_count': 'kafka_topic_count',
    'kafka_message_count': 'kafka_message_count',
    'kafka_message_limit': 'kafka_message_limit',
    'vector_count': 'vector_count',
    'vector_limit': 'vector_limit',
    'vector_query_count': 'vector_query_count',
    'vector_query_limit': 'vector_query_limit',
    'sdk_generation_count': 'sdk_generation_count',
    'workflow_execution_count': 'workflow_execution_count',
    'bandwidth_bytes': 'bandwidth_bytes',
    'usage_by_project': 'usage_by_project',
    'usage_by_schema': 'usage_by_schema',
    'peak_api_requests_per_second': 'peak_api_requests_per_second',
    'overage_detected': 'overage_detected',
    'exceeded_metrics': 'exceeded_metrics',
    'overage_details': 'overage_details',
    'overage_charges_cents': 'overage_charges_cents',
    'alerts_triggered': 'alerts_triggered'
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
    'period_month': 'period_month',
    'period_start': 'period_start',
    'period_end': 'period_end',
    'snapshot_at': 'snapshot_at',
    'snapshot_type': 'snapshot_type',
    'is_final': 'is_final',
    'schema_count': 'schema_count',
    'schema_limit': 'schema_limit',
    'object_count_total': 'object_count_total',
    'api_request_count': 'api_request_count',
    'api_request_limit': 'api_request_limit',
    'api_read_count': 'api_read_count',
    'api_write_count': 'api_write_count',
    'api_error_count': 'api_error_count',
    'storage_bytes_total': 'storage_bytes_total',
    'storage_limit': 'storage_limit',
    'db_storage_bytes': 'db_storage_bytes',
    'blob_storage_bytes': 'blob_storage_bytes',
    'vector_storage_bytes': 'vector_storage_bytes',
    'team_member_count': 'team_member_count',
    'team_member_limit': 'team_member_limit',
    'project_count': 'project_count',
    'project_limit': 'project_limit',
    'api_key_count': 'api_key_count',
    'plugin_count': 'plugin_count',
    'plugin_limit': 'plugin_limit',
    'plugin_invocation_count': 'plugin_invocation_count',
    'plugin_invocation_limit': 'plugin_invocation_limit',
    'kafka_topic_count': 'kafka_topic_count',
    'kafka_message_count': 'kafka_message_count',
    'kafka_message_limit': 'kafka_message_limit',
    'vector_count': 'vector_count',
    'vector_limit': 'vector_limit',
    'vector_query_count': 'vector_query_count',
    'vector_query_limit': 'vector_query_limit',
    'sdk_generation_count': 'sdk_generation_count',
    'workflow_execution_count': 'workflow_execution_count',
    'bandwidth_bytes': 'bandwidth_bytes',
    'usage_by_project': 'usage_by_project',
    'usage_by_schema': 'usage_by_schema',
    'peak_api_requests_per_second': 'peak_api_requests_per_second',
    'overage_detected': 'overage_detected',
    'exceeded_metrics': 'exceeded_metrics',
    'overage_details': 'overage_details',
    'overage_charges_cents': 'overage_charges_cents',
    'alerts_triggered': 'alerts_triggered'
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
        self.period_month = period_month
        self.period_start = period_start
        self.period_end = period_end
        self.snapshot_at = snapshot_at
        self.snapshot_type = snapshot_type
        self.is_final = is_final
        self.schema_count = schema_count
        self.schema_limit = schema_limit
        self.object_count_total = object_count_total
        self.api_request_count = api_request_count
        self.api_request_limit = api_request_limit
        self.api_read_count = api_read_count
        self.api_write_count = api_write_count
        self.api_error_count = api_error_count
        self.storage_bytes_total = storage_bytes_total
        self.storage_limit = storage_limit
        self.db_storage_bytes = db_storage_bytes
        self.blob_storage_bytes = blob_storage_bytes
        self.vector_storage_bytes = vector_storage_bytes
        self.team_member_count = team_member_count
        self.team_member_limit = team_member_limit
        self.project_count = project_count
        self.project_limit = project_limit
        self.api_key_count = api_key_count
        self.plugin_count = plugin_count
        self.plugin_limit = plugin_limit
        self.plugin_invocation_count = plugin_invocation_count
        self.plugin_invocation_limit = plugin_invocation_limit
        self.kafka_topic_count = kafka_topic_count
        self.kafka_message_count = kafka_message_count
        self.kafka_message_limit = kafka_message_limit
        self.vector_count = vector_count
        self.vector_limit = vector_limit
        self.vector_query_count = vector_query_count
        self.vector_query_limit = vector_query_limit
        self.sdk_generation_count = sdk_generation_count
        self.workflow_execution_count = workflow_execution_count
        self.bandwidth_bytes = bandwidth_bytes
        self.usage_by_project = usage_by_project
        self.usage_by_schema = usage_by_schema
        self.peak_api_requests_per_second = peak_api_requests_per_second
        self.overage_detected = overage_detected
        self.exceeded_metrics = exceeded_metrics if exceeded_metrics is not None else []
        self.overage_details = overage_details
        self.overage_charges_cents = overage_charges_cents
        self.alerts_triggered = alerts_triggered if alerts_triggered is not None else []


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
        self._pending_field_updates.add('period_month')
        self._pending_field_updates.add('period_start')
        self._pending_field_updates.add('period_end')
        self._pending_field_updates.add('snapshot_at')
        self._pending_field_updates.add('snapshot_type')
        self._pending_field_updates.add('is_final')
        self._pending_field_updates.add('schema_count')
        if schema_limit is not None:
            self._pending_field_updates.add('schema_limit')
        if object_count_total != 0:
            self._pending_field_updates.add('object_count_total')
        self._pending_field_updates.add('api_request_count')
        if api_request_limit is not None:
            self._pending_field_updates.add('api_request_limit')
        if api_read_count != 0:
            self._pending_field_updates.add('api_read_count')
        if api_write_count != 0:
            self._pending_field_updates.add('api_write_count')
        if api_error_count != 0:
            self._pending_field_updates.add('api_error_count')
        self._pending_field_updates.add('storage_bytes_total')
        if storage_limit is not None:
            self._pending_field_updates.add('storage_limit')
        if db_storage_bytes != 0:
            self._pending_field_updates.add('db_storage_bytes')
        if blob_storage_bytes != 0:
            self._pending_field_updates.add('blob_storage_bytes')
        if vector_storage_bytes != 0:
            self._pending_field_updates.add('vector_storage_bytes')
        self._pending_field_updates.add('team_member_count')
        if team_member_limit is not None:
            self._pending_field_updates.add('team_member_limit')
        self._pending_field_updates.add('project_count')
        if project_limit is not None:
            self._pending_field_updates.add('project_limit')
        if api_key_count != 0:
            self._pending_field_updates.add('api_key_count')
        if plugin_count != 0:
            self._pending_field_updates.add('plugin_count')
        if plugin_limit is not None:
            self._pending_field_updates.add('plugin_limit')
        if plugin_invocation_count != 0:
            self._pending_field_updates.add('plugin_invocation_count')
        if plugin_invocation_limit is not None:
            self._pending_field_updates.add('plugin_invocation_limit')
        if kafka_topic_count != 0:
            self._pending_field_updates.add('kafka_topic_count')
        if kafka_message_count != 0:
            self._pending_field_updates.add('kafka_message_count')
        if kafka_message_limit is not None:
            self._pending_field_updates.add('kafka_message_limit')
        if vector_count != 0:
            self._pending_field_updates.add('vector_count')
        if vector_limit is not None:
            self._pending_field_updates.add('vector_limit')
        if vector_query_count != 0:
            self._pending_field_updates.add('vector_query_count')
        if vector_query_limit is not None:
            self._pending_field_updates.add('vector_query_limit')
        if sdk_generation_count != 0:
            self._pending_field_updates.add('sdk_generation_count')
        if workflow_execution_count != 0:
            self._pending_field_updates.add('workflow_execution_count')
        if bandwidth_bytes != 0:
            self._pending_field_updates.add('bandwidth_bytes')
        if usage_by_project is not None:
            self._pending_field_updates.add('usage_by_project')
        if usage_by_schema is not None:
            self._pending_field_updates.add('usage_by_schema')
        if peak_api_requests_per_second != 0:
            self._pending_field_updates.add('peak_api_requests_per_second')
        self._pending_field_updates.add('overage_detected')
        if exceeded_metrics is not None:
            self._pending_field_updates.add('exceeded_metrics')
        if overage_details is not None:
            self._pending_field_updates.add('overage_details')
        if overage_charges_cents != 0:
            self._pending_field_updates.add('overage_charges_cents')
        if alerts_triggered is not None:
            self._pending_field_updates.add('alerts_triggered')
        
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

    def get_period_month(self) -> str:
        """Get the value of period_month."""
        return self.period_month

    def set_period_month(self, value: str):
        """Set the value of period_month."""
        self.period_month = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('period_month')

    def is_set_period_month(self) -> bool:
        """Check if period_month was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'period_month' in self._pending_field_updates)

    def get_period_start(self) -> str:
        """Get the value of period_start."""
        return self.period_start

    def set_period_start(self, value: str):
        """Set the value of period_start."""
        self.period_start = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('period_start')

    def is_set_period_start(self) -> bool:
        """Check if period_start was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'period_start' in self._pending_field_updates)

    def get_period_end(self) -> str:
        """Get the value of period_end."""
        return self.period_end

    def set_period_end(self, value: str):
        """Set the value of period_end."""
        self.period_end = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('period_end')

    def is_set_period_end(self) -> bool:
        """Check if period_end was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'period_end' in self._pending_field_updates)

    def get_snapshot_at(self) -> str:
        """Get the value of snapshot_at."""
        return self.snapshot_at

    def set_snapshot_at(self, value: str):
        """Set the value of snapshot_at."""
        self.snapshot_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('snapshot_at')

    def is_set_snapshot_at(self) -> bool:
        """Check if snapshot_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'snapshot_at' in self._pending_field_updates)

    def get_snapshot_type(self) -> str:
        """Get the value of snapshot_type."""
        return self.snapshot_type

    def set_snapshot_type(self, value: str):
        """Set the value of snapshot_type."""
        self.snapshot_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('snapshot_type')

    def is_set_snapshot_type(self) -> bool:
        """Check if snapshot_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'snapshot_type' in self._pending_field_updates)

    def get_is_final(self) -> bool:
        """Get the value of is_final."""
        return self.is_final

    def set_is_final(self, value: bool):
        """Set the value of is_final."""
        self.is_final = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('is_final')

    def is_set_is_final(self) -> bool:
        """Check if is_final was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'is_final' in self._pending_field_updates)

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

    def get_schema_limit(self) -> int:
        """Get the value of schema_limit."""
        return self.schema_limit

    def set_schema_limit(self, value: int):
        """Set the value of schema_limit."""
        self.schema_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('schema_limit')

    def is_set_schema_limit(self) -> bool:
        """Check if schema_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'schema_limit' in self._pending_field_updates)

    def get_object_count_total(self) -> int:
        """Get the value of object_count_total."""
        return self.object_count_total

    def set_object_count_total(self, value: int):
        """Set the value of object_count_total."""
        self.object_count_total = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('object_count_total')

    def is_set_object_count_total(self) -> bool:
        """Check if object_count_total was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'object_count_total' in self._pending_field_updates)

    def get_api_request_count(self) -> int:
        """Get the value of api_request_count."""
        return self.api_request_count

    def set_api_request_count(self, value: int):
        """Set the value of api_request_count."""
        self.api_request_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('api_request_count')

    def is_set_api_request_count(self) -> bool:
        """Check if api_request_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'api_request_count' in self._pending_field_updates)

    def get_api_request_limit(self) -> int:
        """Get the value of api_request_limit."""
        return self.api_request_limit

    def set_api_request_limit(self, value: int):
        """Set the value of api_request_limit."""
        self.api_request_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('api_request_limit')

    def is_set_api_request_limit(self) -> bool:
        """Check if api_request_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'api_request_limit' in self._pending_field_updates)

    def get_api_read_count(self) -> int:
        """Get the value of api_read_count."""
        return self.api_read_count

    def set_api_read_count(self, value: int):
        """Set the value of api_read_count."""
        self.api_read_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('api_read_count')

    def is_set_api_read_count(self) -> bool:
        """Check if api_read_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'api_read_count' in self._pending_field_updates)

    def get_api_write_count(self) -> int:
        """Get the value of api_write_count."""
        return self.api_write_count

    def set_api_write_count(self, value: int):
        """Set the value of api_write_count."""
        self.api_write_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('api_write_count')

    def is_set_api_write_count(self) -> bool:
        """Check if api_write_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'api_write_count' in self._pending_field_updates)

    def get_api_error_count(self) -> int:
        """Get the value of api_error_count."""
        return self.api_error_count

    def set_api_error_count(self, value: int):
        """Set the value of api_error_count."""
        self.api_error_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('api_error_count')

    def is_set_api_error_count(self) -> bool:
        """Check if api_error_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'api_error_count' in self._pending_field_updates)

    def get_storage_bytes_total(self) -> int:
        """Get the value of storage_bytes_total."""
        return self.storage_bytes_total

    def set_storage_bytes_total(self, value: int):
        """Set the value of storage_bytes_total."""
        self.storage_bytes_total = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('storage_bytes_total')

    def is_set_storage_bytes_total(self) -> bool:
        """Check if storage_bytes_total was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'storage_bytes_total' in self._pending_field_updates)

    def get_storage_limit(self) -> int:
        """Get the value of storage_limit."""
        return self.storage_limit

    def set_storage_limit(self, value: int):
        """Set the value of storage_limit."""
        self.storage_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('storage_limit')

    def is_set_storage_limit(self) -> bool:
        """Check if storage_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'storage_limit' in self._pending_field_updates)

    def get_db_storage_bytes(self) -> int:
        """Get the value of db_storage_bytes."""
        return self.db_storage_bytes

    def set_db_storage_bytes(self, value: int):
        """Set the value of db_storage_bytes."""
        self.db_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('db_storage_bytes')

    def is_set_db_storage_bytes(self) -> bool:
        """Check if db_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'db_storage_bytes' in self._pending_field_updates)

    def get_blob_storage_bytes(self) -> int:
        """Get the value of blob_storage_bytes."""
        return self.blob_storage_bytes

    def set_blob_storage_bytes(self, value: int):
        """Set the value of blob_storage_bytes."""
        self.blob_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('blob_storage_bytes')

    def is_set_blob_storage_bytes(self) -> bool:
        """Check if blob_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'blob_storage_bytes' in self._pending_field_updates)

    def get_vector_storage_bytes(self) -> int:
        """Get the value of vector_storage_bytes."""
        return self.vector_storage_bytes

    def set_vector_storage_bytes(self, value: int):
        """Set the value of vector_storage_bytes."""
        self.vector_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('vector_storage_bytes')

    def is_set_vector_storage_bytes(self) -> bool:
        """Check if vector_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'vector_storage_bytes' in self._pending_field_updates)

    def get_team_member_count(self) -> int:
        """Get the value of team_member_count."""
        return self.team_member_count

    def set_team_member_count(self, value: int):
        """Set the value of team_member_count."""
        self.team_member_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('team_member_count')

    def is_set_team_member_count(self) -> bool:
        """Check if team_member_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'team_member_count' in self._pending_field_updates)

    def get_team_member_limit(self) -> int:
        """Get the value of team_member_limit."""
        return self.team_member_limit

    def set_team_member_limit(self, value: int):
        """Set the value of team_member_limit."""
        self.team_member_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('team_member_limit')

    def is_set_team_member_limit(self) -> bool:
        """Check if team_member_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'team_member_limit' in self._pending_field_updates)

    def get_project_count(self) -> int:
        """Get the value of project_count."""
        return self.project_count

    def set_project_count(self, value: int):
        """Set the value of project_count."""
        self.project_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('project_count')

    def is_set_project_count(self) -> bool:
        """Check if project_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'project_count' in self._pending_field_updates)

    def get_project_limit(self) -> int:
        """Get the value of project_limit."""
        return self.project_limit

    def set_project_limit(self, value: int):
        """Set the value of project_limit."""
        self.project_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('project_limit')

    def is_set_project_limit(self) -> bool:
        """Check if project_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'project_limit' in self._pending_field_updates)

    def get_api_key_count(self) -> int:
        """Get the value of api_key_count."""
        return self.api_key_count

    def set_api_key_count(self, value: int):
        """Set the value of api_key_count."""
        self.api_key_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('api_key_count')

    def is_set_api_key_count(self) -> bool:
        """Check if api_key_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'api_key_count' in self._pending_field_updates)

    def get_plugin_count(self) -> int:
        """Get the value of plugin_count."""
        return self.plugin_count

    def set_plugin_count(self, value: int):
        """Set the value of plugin_count."""
        self.plugin_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plugin_count')

    def is_set_plugin_count(self) -> bool:
        """Check if plugin_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plugin_count' in self._pending_field_updates)

    def get_plugin_limit(self) -> int:
        """Get the value of plugin_limit."""
        return self.plugin_limit

    def set_plugin_limit(self, value: int):
        """Set the value of plugin_limit."""
        self.plugin_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plugin_limit')

    def is_set_plugin_limit(self) -> bool:
        """Check if plugin_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plugin_limit' in self._pending_field_updates)

    def get_plugin_invocation_count(self) -> int:
        """Get the value of plugin_invocation_count."""
        return self.plugin_invocation_count

    def set_plugin_invocation_count(self, value: int):
        """Set the value of plugin_invocation_count."""
        self.plugin_invocation_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plugin_invocation_count')

    def is_set_plugin_invocation_count(self) -> bool:
        """Check if plugin_invocation_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plugin_invocation_count' in self._pending_field_updates)

    def get_plugin_invocation_limit(self) -> int:
        """Get the value of plugin_invocation_limit."""
        return self.plugin_invocation_limit

    def set_plugin_invocation_limit(self, value: int):
        """Set the value of plugin_invocation_limit."""
        self.plugin_invocation_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plugin_invocation_limit')

    def is_set_plugin_invocation_limit(self) -> bool:
        """Check if plugin_invocation_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plugin_invocation_limit' in self._pending_field_updates)

    def get_kafka_topic_count(self) -> int:
        """Get the value of kafka_topic_count."""
        return self.kafka_topic_count

    def set_kafka_topic_count(self, value: int):
        """Set the value of kafka_topic_count."""
        self.kafka_topic_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('kafka_topic_count')

    def is_set_kafka_topic_count(self) -> bool:
        """Check if kafka_topic_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'kafka_topic_count' in self._pending_field_updates)

    def get_kafka_message_count(self) -> int:
        """Get the value of kafka_message_count."""
        return self.kafka_message_count

    def set_kafka_message_count(self, value: int):
        """Set the value of kafka_message_count."""
        self.kafka_message_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('kafka_message_count')

    def is_set_kafka_message_count(self) -> bool:
        """Check if kafka_message_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'kafka_message_count' in self._pending_field_updates)

    def get_kafka_message_limit(self) -> int:
        """Get the value of kafka_message_limit."""
        return self.kafka_message_limit

    def set_kafka_message_limit(self, value: int):
        """Set the value of kafka_message_limit."""
        self.kafka_message_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('kafka_message_limit')

    def is_set_kafka_message_limit(self) -> bool:
        """Check if kafka_message_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'kafka_message_limit' in self._pending_field_updates)

    def get_vector_count(self) -> int:
        """Get the value of vector_count."""
        return self.vector_count

    def set_vector_count(self, value: int):
        """Set the value of vector_count."""
        self.vector_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('vector_count')

    def is_set_vector_count(self) -> bool:
        """Check if vector_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'vector_count' in self._pending_field_updates)

    def get_vector_limit(self) -> int:
        """Get the value of vector_limit."""
        return self.vector_limit

    def set_vector_limit(self, value: int):
        """Set the value of vector_limit."""
        self.vector_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('vector_limit')

    def is_set_vector_limit(self) -> bool:
        """Check if vector_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'vector_limit' in self._pending_field_updates)

    def get_vector_query_count(self) -> int:
        """Get the value of vector_query_count."""
        return self.vector_query_count

    def set_vector_query_count(self, value: int):
        """Set the value of vector_query_count."""
        self.vector_query_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('vector_query_count')

    def is_set_vector_query_count(self) -> bool:
        """Check if vector_query_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'vector_query_count' in self._pending_field_updates)

    def get_vector_query_limit(self) -> int:
        """Get the value of vector_query_limit."""
        return self.vector_query_limit

    def set_vector_query_limit(self, value: int):
        """Set the value of vector_query_limit."""
        self.vector_query_limit = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('vector_query_limit')

    def is_set_vector_query_limit(self) -> bool:
        """Check if vector_query_limit was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'vector_query_limit' in self._pending_field_updates)

    def get_sdk_generation_count(self) -> int:
        """Get the value of sdk_generation_count."""
        return self.sdk_generation_count

    def set_sdk_generation_count(self, value: int):
        """Set the value of sdk_generation_count."""
        self.sdk_generation_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sdk_generation_count')

    def is_set_sdk_generation_count(self) -> bool:
        """Check if sdk_generation_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sdk_generation_count' in self._pending_field_updates)

    def get_workflow_execution_count(self) -> int:
        """Get the value of workflow_execution_count."""
        return self.workflow_execution_count

    def set_workflow_execution_count(self, value: int):
        """Set the value of workflow_execution_count."""
        self.workflow_execution_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('workflow_execution_count')

    def is_set_workflow_execution_count(self) -> bool:
        """Check if workflow_execution_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'workflow_execution_count' in self._pending_field_updates)

    def get_bandwidth_bytes(self) -> int:
        """Get the value of bandwidth_bytes."""
        return self.bandwidth_bytes

    def set_bandwidth_bytes(self, value: int):
        """Set the value of bandwidth_bytes."""
        self.bandwidth_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('bandwidth_bytes')

    def is_set_bandwidth_bytes(self) -> bool:
        """Check if bandwidth_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'bandwidth_bytes' in self._pending_field_updates)

    def get_usage_by_project(self) -> str:
        """Get the value of usage_by_project."""
        return self.usage_by_project

    def set_usage_by_project(self, value: str):
        """Set the value of usage_by_project."""
        self.usage_by_project = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('usage_by_project')

    def is_set_usage_by_project(self) -> bool:
        """Check if usage_by_project was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'usage_by_project' in self._pending_field_updates)

    def get_usage_by_schema(self) -> str:
        """Get the value of usage_by_schema."""
        return self.usage_by_schema

    def set_usage_by_schema(self, value: str):
        """Set the value of usage_by_schema."""
        self.usage_by_schema = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('usage_by_schema')

    def is_set_usage_by_schema(self) -> bool:
        """Check if usage_by_schema was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'usage_by_schema' in self._pending_field_updates)

    def get_peak_api_requests_per_second(self) -> int:
        """Get the value of peak_api_requests_per_second."""
        return self.peak_api_requests_per_second

    def set_peak_api_requests_per_second(self, value: int):
        """Set the value of peak_api_requests_per_second."""
        self.peak_api_requests_per_second = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('peak_api_requests_per_second')

    def is_set_peak_api_requests_per_second(self) -> bool:
        """Check if peak_api_requests_per_second was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'peak_api_requests_per_second' in self._pending_field_updates)

    def get_overage_detected(self) -> bool:
        """Get the value of overage_detected."""
        return self.overage_detected

    def set_overage_detected(self, value: bool):
        """Set the value of overage_detected."""
        self.overage_detected = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_detected')

    def is_set_overage_detected(self) -> bool:
        """Check if overage_detected was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_detected' in self._pending_field_updates)

    def get_exceeded_metrics(self) -> List[str]:
        """Get the value of exceeded_metrics."""
        return self.exceeded_metrics

    def set_exceeded_metrics(self, value: List[str]):
        """Set the value of exceeded_metrics."""
        self.exceeded_metrics = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('exceeded_metrics')

    def add_exceeded_metrics(self, item: str):
        """Add an item to exceeded_metrics."""
        if self.exceeded_metrics is None:
            self.exceeded_metrics = []
        self.exceeded_metrics.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('exceeded_metrics')

    def del_exceeded_metrics(self, item: str):
        """Remove an item from exceeded_metrics."""
        if self.exceeded_metrics and item in self.exceeded_metrics:
            self.exceeded_metrics.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('exceeded_metrics')

    def del_exceeded_metrics_by_index(self, index: int):
        """Remove an item from exceeded_metrics by index."""
        if self.exceeded_metrics and 0 <= index < len(self.exceeded_metrics):
            del self.exceeded_metrics[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('exceeded_metrics')

    def is_set_exceeded_metrics(self) -> bool:
        """Check if exceeded_metrics was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'exceeded_metrics' in self._pending_field_updates)

    def get_overage_details(self) -> str:
        """Get the value of overage_details."""
        return self.overage_details

    def set_overage_details(self, value: str):
        """Set the value of overage_details."""
        self.overage_details = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_details')

    def is_set_overage_details(self) -> bool:
        """Check if overage_details was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_details' in self._pending_field_updates)

    def get_overage_charges_cents(self) -> int:
        """Get the value of overage_charges_cents."""
        return self.overage_charges_cents

    def set_overage_charges_cents(self, value: int):
        """Set the value of overage_charges_cents."""
        self.overage_charges_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_charges_cents')

    def is_set_overage_charges_cents(self) -> bool:
        """Check if overage_charges_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_charges_cents' in self._pending_field_updates)

    def get_alerts_triggered(self) -> List[str]:
        """Get the value of alerts_triggered."""
        return self.alerts_triggered

    def set_alerts_triggered(self, value: List[str]):
        """Set the value of alerts_triggered."""
        self.alerts_triggered = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('alerts_triggered')

    def add_alerts_triggered(self, item: str):
        """Add an item to alerts_triggered."""
        if self.alerts_triggered is None:
            self.alerts_triggered = []
        self.alerts_triggered.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('alerts_triggered')

    def del_alerts_triggered(self, item: str):
        """Remove an item from alerts_triggered."""
        if self.alerts_triggered and item in self.alerts_triggered:
            self.alerts_triggered.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('alerts_triggered')

    def del_alerts_triggered_by_index(self, index: int):
        """Remove an item from alerts_triggered by index."""
        if self.alerts_triggered and 0 <= index < len(self.alerts_triggered):
            del self.alerts_triggered[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('alerts_triggered')

    def is_set_alerts_triggered(self) -> bool:
        """Check if alerts_triggered was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'alerts_triggered' in self._pending_field_updates)



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
        return cls(name="", uuid=None, fq_name=None, parent_uuid=None, display_name=None, description=None, created_by=None, created_at=None, updated_at=None, period_month=None, period_start=None, period_end=None, snapshot_at=None, snapshot_type=None, is_final=None, schema_count=None, schema_limit=None, object_count_total=None, api_request_count=None, api_request_limit=None, api_read_count=None, api_write_count=None, api_error_count=None, storage_bytes_total=None, storage_limit=None, db_storage_bytes=None, blob_storage_bytes=None, vector_storage_bytes=None, team_member_count=None, team_member_limit=None, project_count=None, project_limit=None, api_key_count=None, plugin_count=None, plugin_limit=None, plugin_invocation_count=None, plugin_invocation_limit=None, kafka_topic_count=None, kafka_message_count=None, kafka_message_limit=None, vector_count=None, vector_limit=None, vector_query_count=None, vector_query_limit=None, sdk_generation_count=None, workflow_execution_count=None, bandwidth_bytes=None, usage_by_project=None, usage_by_schema=None, peak_api_requests_per_second=None, overage_detected=None, exceeded_metrics=None, overage_details=None, overage_charges_cents=None, alerts_triggered=None)

platform_billing_usage=PlatformBillingUsage
PlatformBillingUsage=PlatformBillingUsage
PlatformBillingUsage=PlatformBillingUsage
platform_billing_usage=PlatformBillingUsage
