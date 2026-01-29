# File: pymodel_system/objects/platform_billing_plan.py
"""
This file was generated from the platform_billing_plan.json schema.
ENHANCED: Proper datetime handling with automatic string<->datetime conversion.
ENHANCED: Supero fluent API support with smart reference management.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import importlib
import uuid
import inflection
from pymodel_system.enums.billing_plan_types import BillingPlanTypes
from datetime import datetime

from ..serialization_errors import ObjectDeserializationError, InvalidParentError
from datetime import datetime
import re

class PlatformBillingPlan:
    """
    Represents a PlatformBillingPlan instance.
    
    This class is auto-generated and includes:
    - Standard CRUD operations
    - Fluent API methods (when used with Supero)
    - Smart reference management with link data support
    - Parent-child hierarchy navigation
    """
    
    _OBJ_TYPE = "platform_billing_plan"
    _PARENT_TYPE = "config_root"

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
    'plan_code': {
        'type': 'billing_plan_types',
        'is_list': False,
        'json_name': 'plan_code',
        'original_type': 'billing_plan_types',
        'mandatory': True,
        'static': False,
    },
    'plan_version': {
        'type': 'int',
        'is_list': False,
        'json_name': 'plan_version',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'tier_level': {
        'type': 'int',
        'is_list': False,
        'json_name': 'tier_level',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'pricing_currency': {
        'type': 'str',
        'is_list': False,
        'json_name': 'pricing_currency',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'monthly_price_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'monthly_price_cents',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'annual_price_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'annual_price_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'setup_fee_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'setup_fee_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_schemas': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_schemas',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'max_api_requests_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_api_requests_monthly',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'max_api_requests_per_second': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_api_requests_per_second',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_storage_bytes',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'max_db_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_db_storage_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_blob_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_blob_storage_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_vector_storage_bytes': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_vector_storage_bytes',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_team_members': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_team_members',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'max_projects': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_projects',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'max_api_keys_per_project': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_api_keys_per_project',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_plugins': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_plugins',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_plugin_invocations_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_plugin_invocations_monthly',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'allowed_plugin_types': {
        'type': 'str',
        'is_list': True,
        'json_name': 'allowed_plugin_types',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'max_kafka_topics': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_kafka_topics',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_kafka_messages_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_kafka_messages_monthly',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_kafka_partitions_per_topic': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_kafka_partitions_per_topic',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_vectors_stored': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_vectors_stored',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_vector_queries_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_vector_queries_monthly',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_vector_dimensions': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_vector_dimensions',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_sdk_generations_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_sdk_generations_monthly',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_workflow_executions_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_workflow_executions_monthly',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_bandwidth_bytes_monthly': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_bandwidth_bytes_monthly',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'features': {
        'type': 'str',
        'is_list': True,
        'json_name': 'features',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'sdk_languages': {
        'type': 'str',
        'is_list': True,
        'json_name': 'sdk_languages',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'support_level': {
        'type': 'str',
        'is_list': False,
        'json_name': 'support_level',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'sla_uptime_percent': {
        'type': 'float',
        'is_list': False,
        'json_name': 'sla_uptime_percent',
        'original_type': 'float',
        'mandatory': False,
        'static': False,
    },
    'data_retention_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'data_retention_days',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'audit_log_retention_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'audit_log_retention_days',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'backup_frequency': {
        'type': 'str',
        'is_list': False,
        'json_name': 'backup_frequency',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'overage_handling': {
        'type': 'str',
        'is_list': False,
        'json_name': 'overage_handling',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'overage_grace_percent': {
        'type': 'int',
        'is_list': False,
        'json_name': 'overage_grace_percent',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'overage_api_request_price_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'overage_api_request_price_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'overage_storage_price_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'overage_storage_price_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'overage_vector_query_price_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'overage_vector_query_price_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'version_policy': {
        'type': 'str',
        'is_list': False,
        'json_name': 'version_policy',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'previous_version_uuid': {
        'type': 'str',
        'is_list': False,
        'json_name': 'previous_version_uuid',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'sunset_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'sunset_date',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'migration_target_plan_code': {
        'type': 'str',
        'is_list': False,
        'json_name': 'migration_target_plan_code',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'is_public': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'is_public',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'is_active': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'is_active',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'trial_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'trial_days',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'requires_payment_method': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'requires_payment_method',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'requires_approval': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'requires_approval',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'minimum_commitment_months': {
        'type': 'int',
        'is_list': False,
        'json_name': 'minimum_commitment_months',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    }
}
    
    # Infrastructure end_points metadata
    _end_points = []
    
    # Index definitions
    _indexes = {}

    _CONSTRAINTS = {
        'plan_version': {
            'min-value': 1,
            'type': 'integer',
        },
        'tier_level': {
            'min-value': 0,
            'max-value': 100,
            'type': 'integer',
        },
        'monthly_price_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'max_schemas': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_api_requests_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_api_requests_per_second': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_storage_bytes': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_db_storage_bytes': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_blob_storage_bytes': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_vector_storage_bytes': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_team_members': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_projects': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_api_keys_per_project': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_plugins': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_plugin_invocations_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_kafka_topics': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_kafka_messages_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_kafka_partitions_per_topic': {
            'min-value': 1,
            'type': 'integer',
        },
        'max_vectors_stored': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_vector_queries_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_sdk_generations_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_workflow_executions_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'max_bandwidth_bytes_monthly': {
            'min-value': -1,
            'type': 'integer',
        },
        'data_retention_days': {
            'min-value': -1,
            'type': 'integer',
        },
        'overage_grace_percent': {
            'min-value': 0,
            'max-value': 100,
            'type': 'integer',
        },
        'trial_days': {
            'min-value': 0,
            'type': 'integer',
        },
        'minimum_commitment_months': {
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
        plan_code: Optional[BillingPlanTypes] = None,
        plan_version: Optional[int] = None,
        tier_level: Optional[int] = None,
        pricing_currency: Optional[str] = None,
        monthly_price_cents: Optional[int] = None,
        annual_price_cents: Optional[int] = None,
        setup_fee_cents: Optional[int] = None,
        max_schemas: Optional[int] = None,
        max_api_requests_monthly: Optional[int] = None,
        max_api_requests_per_second: Optional[int] = None,
        max_storage_bytes: Optional[int] = None,
        max_db_storage_bytes: Optional[int] = None,
        max_blob_storage_bytes: Optional[int] = None,
        max_vector_storage_bytes: Optional[int] = None,
        max_team_members: Optional[int] = None,
        max_projects: Optional[int] = None,
        max_api_keys_per_project: Optional[int] = None,
        max_plugins: Optional[int] = None,
        max_plugin_invocations_monthly: Optional[int] = None,
        allowed_plugin_types: Optional[List[str]] = None,
        max_kafka_topics: Optional[int] = None,
        max_kafka_messages_monthly: Optional[int] = None,
        max_kafka_partitions_per_topic: Optional[int] = None,
        max_vectors_stored: Optional[int] = None,
        max_vector_queries_monthly: Optional[int] = None,
        max_vector_dimensions: Optional[int] = None,
        max_sdk_generations_monthly: Optional[int] = None,
        max_workflow_executions_monthly: Optional[int] = None,
        max_bandwidth_bytes_monthly: Optional[int] = None,
        features: Optional[List[str]] = None,
        sdk_languages: Optional[List[str]] = None,
        support_level: Optional[str] = None,
        sla_uptime_percent: Optional[float] = None,
        data_retention_days: Optional[int] = None,
        audit_log_retention_days: Optional[int] = None,
        backup_frequency: Optional[str] = None,
        overage_handling: Optional[str] = None,
        overage_grace_percent: Optional[int] = None,
        overage_api_request_price_cents: Optional[int] = None,
        overage_storage_price_cents: Optional[int] = None,
        overage_vector_query_price_cents: Optional[int] = None,
        version_policy: Optional[str] = None,
        previous_version_uuid: Optional[str] = None,
        sunset_date: Optional[str] = None,
        migration_target_plan_code: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_active: Optional[bool] = None,
        trial_days: Optional[int] = None,
        requires_payment_method: Optional[bool] = None,
        requires_approval: Optional[bool] = None,
        minimum_commitment_months: Optional[int] = None
    ):
        # Set initialization flag to prevent tracking during __init__
        self._initializing = True
        
        self.obj_type = "platform_billing_plan"
        self.parent_type = "config_root"
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
    'plan_code': 'plan_code',
    'plan_version': 'plan_version',
    'tier_level': 'tier_level',
    'pricing_currency': 'pricing_currency',
    'monthly_price_cents': 'monthly_price_cents',
    'annual_price_cents': 'annual_price_cents',
    'setup_fee_cents': 'setup_fee_cents',
    'max_schemas': 'max_schemas',
    'max_api_requests_monthly': 'max_api_requests_monthly',
    'max_api_requests_per_second': 'max_api_requests_per_second',
    'max_storage_bytes': 'max_storage_bytes',
    'max_db_storage_bytes': 'max_db_storage_bytes',
    'max_blob_storage_bytes': 'max_blob_storage_bytes',
    'max_vector_storage_bytes': 'max_vector_storage_bytes',
    'max_team_members': 'max_team_members',
    'max_projects': 'max_projects',
    'max_api_keys_per_project': 'max_api_keys_per_project',
    'max_plugins': 'max_plugins',
    'max_plugin_invocations_monthly': 'max_plugin_invocations_monthly',
    'allowed_plugin_types': 'allowed_plugin_types',
    'max_kafka_topics': 'max_kafka_topics',
    'max_kafka_messages_monthly': 'max_kafka_messages_monthly',
    'max_kafka_partitions_per_topic': 'max_kafka_partitions_per_topic',
    'max_vectors_stored': 'max_vectors_stored',
    'max_vector_queries_monthly': 'max_vector_queries_monthly',
    'max_vector_dimensions': 'max_vector_dimensions',
    'max_sdk_generations_monthly': 'max_sdk_generations_monthly',
    'max_workflow_executions_monthly': 'max_workflow_executions_monthly',
    'max_bandwidth_bytes_monthly': 'max_bandwidth_bytes_monthly',
    'features': 'features',
    'sdk_languages': 'sdk_languages',
    'support_level': 'support_level',
    'sla_uptime_percent': 'sla_uptime_percent',
    'data_retention_days': 'data_retention_days',
    'audit_log_retention_days': 'audit_log_retention_days',
    'backup_frequency': 'backup_frequency',
    'overage_handling': 'overage_handling',
    'overage_grace_percent': 'overage_grace_percent',
    'overage_api_request_price_cents': 'overage_api_request_price_cents',
    'overage_storage_price_cents': 'overage_storage_price_cents',
    'overage_vector_query_price_cents': 'overage_vector_query_price_cents',
    'version_policy': 'version_policy',
    'previous_version_uuid': 'previous_version_uuid',
    'sunset_date': 'sunset_date',
    'migration_target_plan_code': 'migration_target_plan_code',
    'is_public': 'is_public',
    'is_active': 'is_active',
    'trial_days': 'trial_days',
    'requires_payment_method': 'requires_payment_method',
    'requires_approval': 'requires_approval',
    'minimum_commitment_months': 'minimum_commitment_months'
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
    'plan_code': 'plan_code',
    'plan_version': 'plan_version',
    'tier_level': 'tier_level',
    'pricing_currency': 'pricing_currency',
    'monthly_price_cents': 'monthly_price_cents',
    'annual_price_cents': 'annual_price_cents',
    'setup_fee_cents': 'setup_fee_cents',
    'max_schemas': 'max_schemas',
    'max_api_requests_monthly': 'max_api_requests_monthly',
    'max_api_requests_per_second': 'max_api_requests_per_second',
    'max_storage_bytes': 'max_storage_bytes',
    'max_db_storage_bytes': 'max_db_storage_bytes',
    'max_blob_storage_bytes': 'max_blob_storage_bytes',
    'max_vector_storage_bytes': 'max_vector_storage_bytes',
    'max_team_members': 'max_team_members',
    'max_projects': 'max_projects',
    'max_api_keys_per_project': 'max_api_keys_per_project',
    'max_plugins': 'max_plugins',
    'max_plugin_invocations_monthly': 'max_plugin_invocations_monthly',
    'allowed_plugin_types': 'allowed_plugin_types',
    'max_kafka_topics': 'max_kafka_topics',
    'max_kafka_messages_monthly': 'max_kafka_messages_monthly',
    'max_kafka_partitions_per_topic': 'max_kafka_partitions_per_topic',
    'max_vectors_stored': 'max_vectors_stored',
    'max_vector_queries_monthly': 'max_vector_queries_monthly',
    'max_vector_dimensions': 'max_vector_dimensions',
    'max_sdk_generations_monthly': 'max_sdk_generations_monthly',
    'max_workflow_executions_monthly': 'max_workflow_executions_monthly',
    'max_bandwidth_bytes_monthly': 'max_bandwidth_bytes_monthly',
    'features': 'features',
    'sdk_languages': 'sdk_languages',
    'support_level': 'support_level',
    'sla_uptime_percent': 'sla_uptime_percent',
    'data_retention_days': 'data_retention_days',
    'audit_log_retention_days': 'audit_log_retention_days',
    'backup_frequency': 'backup_frequency',
    'overage_handling': 'overage_handling',
    'overage_grace_percent': 'overage_grace_percent',
    'overage_api_request_price_cents': 'overage_api_request_price_cents',
    'overage_storage_price_cents': 'overage_storage_price_cents',
    'overage_vector_query_price_cents': 'overage_vector_query_price_cents',
    'version_policy': 'version_policy',
    'previous_version_uuid': 'previous_version_uuid',
    'sunset_date': 'sunset_date',
    'migration_target_plan_code': 'migration_target_plan_code',
    'is_public': 'is_public',
    'is_active': 'is_active',
    'trial_days': 'trial_days',
    'requires_payment_method': 'requires_payment_method',
    'requires_approval': 'requires_approval',
    'minimum_commitment_months': 'minimum_commitment_months'
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
        self.plan_code = plan_code
        self.plan_version = plan_version
        self.tier_level = tier_level
        self.pricing_currency = pricing_currency
        self.monthly_price_cents = monthly_price_cents
        self.annual_price_cents = annual_price_cents
        self.setup_fee_cents = setup_fee_cents
        self.max_schemas = max_schemas
        self.max_api_requests_monthly = max_api_requests_monthly
        self.max_api_requests_per_second = max_api_requests_per_second
        self.max_storage_bytes = max_storage_bytes
        self.max_db_storage_bytes = max_db_storage_bytes
        self.max_blob_storage_bytes = max_blob_storage_bytes
        self.max_vector_storage_bytes = max_vector_storage_bytes
        self.max_team_members = max_team_members
        self.max_projects = max_projects
        self.max_api_keys_per_project = max_api_keys_per_project
        self.max_plugins = max_plugins
        self.max_plugin_invocations_monthly = max_plugin_invocations_monthly
        self.allowed_plugin_types = allowed_plugin_types if allowed_plugin_types is not None else []
        self.max_kafka_topics = max_kafka_topics
        self.max_kafka_messages_monthly = max_kafka_messages_monthly
        self.max_kafka_partitions_per_topic = max_kafka_partitions_per_topic
        self.max_vectors_stored = max_vectors_stored
        self.max_vector_queries_monthly = max_vector_queries_monthly
        self.max_vector_dimensions = max_vector_dimensions
        self.max_sdk_generations_monthly = max_sdk_generations_monthly
        self.max_workflow_executions_monthly = max_workflow_executions_monthly
        self.max_bandwidth_bytes_monthly = max_bandwidth_bytes_monthly
        self.features = features if features is not None else []
        self.sdk_languages = sdk_languages if sdk_languages is not None else []
        self.support_level = support_level
        self.sla_uptime_percent = sla_uptime_percent
        self.data_retention_days = data_retention_days
        self.audit_log_retention_days = audit_log_retention_days
        self.backup_frequency = backup_frequency
        self.overage_handling = overage_handling
        self.overage_grace_percent = overage_grace_percent
        self.overage_api_request_price_cents = overage_api_request_price_cents
        self.overage_storage_price_cents = overage_storage_price_cents
        self.overage_vector_query_price_cents = overage_vector_query_price_cents
        self.version_policy = version_policy
        self.previous_version_uuid = previous_version_uuid
        self.sunset_date = sunset_date
        self.migration_target_plan_code = migration_target_plan_code
        self.is_public = is_public
        self.is_active = is_active
        self.trial_days = trial_days
        self.requires_payment_method = requires_payment_method
        self.requires_approval = requires_approval
        self.minimum_commitment_months = minimum_commitment_months


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
        self._pending_field_updates.add('plan_code')
        self._pending_field_updates.add('plan_version')
        self._pending_field_updates.add('tier_level')
        self._pending_field_updates.add('pricing_currency')
        self._pending_field_updates.add('monthly_price_cents')
        if annual_price_cents is not None:
            self._pending_field_updates.add('annual_price_cents')
        if setup_fee_cents != 0:
            self._pending_field_updates.add('setup_fee_cents')
        self._pending_field_updates.add('max_schemas')
        self._pending_field_updates.add('max_api_requests_monthly')
        if max_api_requests_per_second != 10:
            self._pending_field_updates.add('max_api_requests_per_second')
        self._pending_field_updates.add('max_storage_bytes')
        if max_db_storage_bytes != -1:
            self._pending_field_updates.add('max_db_storage_bytes')
        if max_blob_storage_bytes != -1:
            self._pending_field_updates.add('max_blob_storage_bytes')
        if max_vector_storage_bytes != -1:
            self._pending_field_updates.add('max_vector_storage_bytes')
        self._pending_field_updates.add('max_team_members')
        self._pending_field_updates.add('max_projects')
        if max_api_keys_per_project != 5:
            self._pending_field_updates.add('max_api_keys_per_project')
        if max_plugins != 0:
            self._pending_field_updates.add('max_plugins')
        if max_plugin_invocations_monthly != 0:
            self._pending_field_updates.add('max_plugin_invocations_monthly')
        if allowed_plugin_types is not None:
            self._pending_field_updates.add('allowed_plugin_types')
        if max_kafka_topics != 0:
            self._pending_field_updates.add('max_kafka_topics')
        if max_kafka_messages_monthly != 0:
            self._pending_field_updates.add('max_kafka_messages_monthly')
        if max_kafka_partitions_per_topic != 3:
            self._pending_field_updates.add('max_kafka_partitions_per_topic')
        if max_vectors_stored != 0:
            self._pending_field_updates.add('max_vectors_stored')
        if max_vector_queries_monthly != 0:
            self._pending_field_updates.add('max_vector_queries_monthly')
        if max_vector_dimensions != 1536:
            self._pending_field_updates.add('max_vector_dimensions')
        if max_sdk_generations_monthly != -1:
            self._pending_field_updates.add('max_sdk_generations_monthly')
        if max_workflow_executions_monthly != 0:
            self._pending_field_updates.add('max_workflow_executions_monthly')
        if max_bandwidth_bytes_monthly != -1:
            self._pending_field_updates.add('max_bandwidth_bytes_monthly')
        if features is not None:
            self._pending_field_updates.add('features')
        if sdk_languages is not None:
            self._pending_field_updates.add('sdk_languages')
        self._pending_field_updates.add('support_level')
        if sla_uptime_percent is not None:
            self._pending_field_updates.add('sla_uptime_percent')
        if data_retention_days != 30:
            self._pending_field_updates.add('data_retention_days')
        if audit_log_retention_days != 7:
            self._pending_field_updates.add('audit_log_retention_days')
        if backup_frequency != 'none':
            self._pending_field_updates.add('backup_frequency')
        self._pending_field_updates.add('overage_handling')
        if overage_grace_percent != 10:
            self._pending_field_updates.add('overage_grace_percent')
        if overage_api_request_price_cents is not None:
            self._pending_field_updates.add('overage_api_request_price_cents')
        if overage_storage_price_cents is not None:
            self._pending_field_updates.add('overage_storage_price_cents')
        if overage_vector_query_price_cents is not None:
            self._pending_field_updates.add('overage_vector_query_price_cents')
        self._pending_field_updates.add('version_policy')
        if previous_version_uuid is not None:
            self._pending_field_updates.add('previous_version_uuid')
        if sunset_date is not None:
            self._pending_field_updates.add('sunset_date')
        if migration_target_plan_code is not None:
            self._pending_field_updates.add('migration_target_plan_code')
        self._pending_field_updates.add('is_public')
        self._pending_field_updates.add('is_active')
        if trial_days != 0:
            self._pending_field_updates.add('trial_days')
        self._pending_field_updates.add('requires_payment_method')
        self._pending_field_updates.add('requires_approval')
        if minimum_commitment_months != 0:
            self._pending_field_updates.add('minimum_commitment_months')
        
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

    def get_plan_code(self) -> str:
        """Get the value of plan_code as base type value."""
        return self.plan_code.value if hasattr(self.plan_code, 'value') else self.plan_code

    def set_plan_code(self, value: str):
        """Set the value of plan_code (accepts base type value)."""
        if value is None:
            self.plan_code = None
        elif hasattr(value, 'value'):
            self.plan_code = value
        else:
            try:
                import importlib
                package_base = self.__module__.split('.')[0]
                module_name = f'{package_base}.enums.billing_plan_types'
                enum_module = importlib.import_module(module_name)
                enum_class = getattr(enum_module, 'BillingPlanTypes')
                self.plan_code = enum_class(value)
            except Exception as e:
                raise ValueError(f'Cannot convert {value} to BillingPlanTypes enum: {e}')
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plan_code')

    def is_set_plan_code(self) -> bool:
        """Check if plan_code was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plan_code' in self._pending_field_updates)

    def get_plan_version(self) -> int:
        """Get the value of plan_version."""
        return self.plan_version

    def set_plan_version(self, value: int):
        """Set the value of plan_version."""
        self.plan_version = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plan_version')

    def is_set_plan_version(self) -> bool:
        """Check if plan_version was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plan_version' in self._pending_field_updates)

    def get_tier_level(self) -> int:
        """Get the value of tier_level."""
        return self.tier_level

    def set_tier_level(self, value: int):
        """Set the value of tier_level."""
        self.tier_level = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tier_level')

    def is_set_tier_level(self) -> bool:
        """Check if tier_level was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tier_level' in self._pending_field_updates)

    def get_pricing_currency(self) -> str:
        """Get the value of pricing_currency."""
        return self.pricing_currency

    def set_pricing_currency(self, value: str):
        """Set the value of pricing_currency."""
        self.pricing_currency = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('pricing_currency')

    def is_set_pricing_currency(self) -> bool:
        """Check if pricing_currency was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'pricing_currency' in self._pending_field_updates)

    def get_monthly_price_cents(self) -> int:
        """Get the value of monthly_price_cents."""
        return self.monthly_price_cents

    def set_monthly_price_cents(self, value: int):
        """Set the value of monthly_price_cents."""
        self.monthly_price_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('monthly_price_cents')

    def is_set_monthly_price_cents(self) -> bool:
        """Check if monthly_price_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'monthly_price_cents' in self._pending_field_updates)

    def get_annual_price_cents(self) -> int:
        """Get the value of annual_price_cents."""
        return self.annual_price_cents

    def set_annual_price_cents(self, value: int):
        """Set the value of annual_price_cents."""
        self.annual_price_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('annual_price_cents')

    def is_set_annual_price_cents(self) -> bool:
        """Check if annual_price_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'annual_price_cents' in self._pending_field_updates)

    def get_setup_fee_cents(self) -> int:
        """Get the value of setup_fee_cents."""
        return self.setup_fee_cents

    def set_setup_fee_cents(self, value: int):
        """Set the value of setup_fee_cents."""
        self.setup_fee_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('setup_fee_cents')

    def is_set_setup_fee_cents(self) -> bool:
        """Check if setup_fee_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'setup_fee_cents' in self._pending_field_updates)

    def get_max_schemas(self) -> int:
        """Get the value of max_schemas."""
        return self.max_schemas

    def set_max_schemas(self, value: int):
        """Set the value of max_schemas."""
        self.max_schemas = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_schemas')

    def is_set_max_schemas(self) -> bool:
        """Check if max_schemas was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_schemas' in self._pending_field_updates)

    def get_max_api_requests_monthly(self) -> int:
        """Get the value of max_api_requests_monthly."""
        return self.max_api_requests_monthly

    def set_max_api_requests_monthly(self, value: int):
        """Set the value of max_api_requests_monthly."""
        self.max_api_requests_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_api_requests_monthly')

    def is_set_max_api_requests_monthly(self) -> bool:
        """Check if max_api_requests_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_api_requests_monthly' in self._pending_field_updates)

    def get_max_api_requests_per_second(self) -> int:
        """Get the value of max_api_requests_per_second."""
        return self.max_api_requests_per_second

    def set_max_api_requests_per_second(self, value: int):
        """Set the value of max_api_requests_per_second."""
        self.max_api_requests_per_second = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_api_requests_per_second')

    def is_set_max_api_requests_per_second(self) -> bool:
        """Check if max_api_requests_per_second was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_api_requests_per_second' in self._pending_field_updates)

    def get_max_storage_bytes(self) -> int:
        """Get the value of max_storage_bytes."""
        return self.max_storage_bytes

    def set_max_storage_bytes(self, value: int):
        """Set the value of max_storage_bytes."""
        self.max_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_storage_bytes')

    def is_set_max_storage_bytes(self) -> bool:
        """Check if max_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_storage_bytes' in self._pending_field_updates)

    def get_max_db_storage_bytes(self) -> int:
        """Get the value of max_db_storage_bytes."""
        return self.max_db_storage_bytes

    def set_max_db_storage_bytes(self, value: int):
        """Set the value of max_db_storage_bytes."""
        self.max_db_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_db_storage_bytes')

    def is_set_max_db_storage_bytes(self) -> bool:
        """Check if max_db_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_db_storage_bytes' in self._pending_field_updates)

    def get_max_blob_storage_bytes(self) -> int:
        """Get the value of max_blob_storage_bytes."""
        return self.max_blob_storage_bytes

    def set_max_blob_storage_bytes(self, value: int):
        """Set the value of max_blob_storage_bytes."""
        self.max_blob_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_blob_storage_bytes')

    def is_set_max_blob_storage_bytes(self) -> bool:
        """Check if max_blob_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_blob_storage_bytes' in self._pending_field_updates)

    def get_max_vector_storage_bytes(self) -> int:
        """Get the value of max_vector_storage_bytes."""
        return self.max_vector_storage_bytes

    def set_max_vector_storage_bytes(self, value: int):
        """Set the value of max_vector_storage_bytes."""
        self.max_vector_storage_bytes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_vector_storage_bytes')

    def is_set_max_vector_storage_bytes(self) -> bool:
        """Check if max_vector_storage_bytes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_vector_storage_bytes' in self._pending_field_updates)

    def get_max_team_members(self) -> int:
        """Get the value of max_team_members."""
        return self.max_team_members

    def set_max_team_members(self, value: int):
        """Set the value of max_team_members."""
        self.max_team_members = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_team_members')

    def is_set_max_team_members(self) -> bool:
        """Check if max_team_members was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_team_members' in self._pending_field_updates)

    def get_max_projects(self) -> int:
        """Get the value of max_projects."""
        return self.max_projects

    def set_max_projects(self, value: int):
        """Set the value of max_projects."""
        self.max_projects = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_projects')

    def is_set_max_projects(self) -> bool:
        """Check if max_projects was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_projects' in self._pending_field_updates)

    def get_max_api_keys_per_project(self) -> int:
        """Get the value of max_api_keys_per_project."""
        return self.max_api_keys_per_project

    def set_max_api_keys_per_project(self, value: int):
        """Set the value of max_api_keys_per_project."""
        self.max_api_keys_per_project = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_api_keys_per_project')

    def is_set_max_api_keys_per_project(self) -> bool:
        """Check if max_api_keys_per_project was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_api_keys_per_project' in self._pending_field_updates)

    def get_max_plugins(self) -> int:
        """Get the value of max_plugins."""
        return self.max_plugins

    def set_max_plugins(self, value: int):
        """Set the value of max_plugins."""
        self.max_plugins = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_plugins')

    def is_set_max_plugins(self) -> bool:
        """Check if max_plugins was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_plugins' in self._pending_field_updates)

    def get_max_plugin_invocations_monthly(self) -> int:
        """Get the value of max_plugin_invocations_monthly."""
        return self.max_plugin_invocations_monthly

    def set_max_plugin_invocations_monthly(self, value: int):
        """Set the value of max_plugin_invocations_monthly."""
        self.max_plugin_invocations_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_plugin_invocations_monthly')

    def is_set_max_plugin_invocations_monthly(self) -> bool:
        """Check if max_plugin_invocations_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_plugin_invocations_monthly' in self._pending_field_updates)

    def get_allowed_plugin_types(self) -> List[str]:
        """Get the value of allowed_plugin_types."""
        return self.allowed_plugin_types

    def set_allowed_plugin_types(self, value: List[str]):
        """Set the value of allowed_plugin_types."""
        self.allowed_plugin_types = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('allowed_plugin_types')

    def add_allowed_plugin_types(self, item: str):
        """Add an item to allowed_plugin_types."""
        if self.allowed_plugin_types is None:
            self.allowed_plugin_types = []
        self.allowed_plugin_types.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('allowed_plugin_types')

    def del_allowed_plugin_types(self, item: str):
        """Remove an item from allowed_plugin_types."""
        if self.allowed_plugin_types and item in self.allowed_plugin_types:
            self.allowed_plugin_types.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('allowed_plugin_types')

    def del_allowed_plugin_types_by_index(self, index: int):
        """Remove an item from allowed_plugin_types by index."""
        if self.allowed_plugin_types and 0 <= index < len(self.allowed_plugin_types):
            del self.allowed_plugin_types[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('allowed_plugin_types')

    def is_set_allowed_plugin_types(self) -> bool:
        """Check if allowed_plugin_types was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'allowed_plugin_types' in self._pending_field_updates)

    def get_max_kafka_topics(self) -> int:
        """Get the value of max_kafka_topics."""
        return self.max_kafka_topics

    def set_max_kafka_topics(self, value: int):
        """Set the value of max_kafka_topics."""
        self.max_kafka_topics = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_kafka_topics')

    def is_set_max_kafka_topics(self) -> bool:
        """Check if max_kafka_topics was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_kafka_topics' in self._pending_field_updates)

    def get_max_kafka_messages_monthly(self) -> int:
        """Get the value of max_kafka_messages_monthly."""
        return self.max_kafka_messages_monthly

    def set_max_kafka_messages_monthly(self, value: int):
        """Set the value of max_kafka_messages_monthly."""
        self.max_kafka_messages_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_kafka_messages_monthly')

    def is_set_max_kafka_messages_monthly(self) -> bool:
        """Check if max_kafka_messages_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_kafka_messages_monthly' in self._pending_field_updates)

    def get_max_kafka_partitions_per_topic(self) -> int:
        """Get the value of max_kafka_partitions_per_topic."""
        return self.max_kafka_partitions_per_topic

    def set_max_kafka_partitions_per_topic(self, value: int):
        """Set the value of max_kafka_partitions_per_topic."""
        self.max_kafka_partitions_per_topic = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_kafka_partitions_per_topic')

    def is_set_max_kafka_partitions_per_topic(self) -> bool:
        """Check if max_kafka_partitions_per_topic was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_kafka_partitions_per_topic' in self._pending_field_updates)

    def get_max_vectors_stored(self) -> int:
        """Get the value of max_vectors_stored."""
        return self.max_vectors_stored

    def set_max_vectors_stored(self, value: int):
        """Set the value of max_vectors_stored."""
        self.max_vectors_stored = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_vectors_stored')

    def is_set_max_vectors_stored(self) -> bool:
        """Check if max_vectors_stored was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_vectors_stored' in self._pending_field_updates)

    def get_max_vector_queries_monthly(self) -> int:
        """Get the value of max_vector_queries_monthly."""
        return self.max_vector_queries_monthly

    def set_max_vector_queries_monthly(self, value: int):
        """Set the value of max_vector_queries_monthly."""
        self.max_vector_queries_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_vector_queries_monthly')

    def is_set_max_vector_queries_monthly(self) -> bool:
        """Check if max_vector_queries_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_vector_queries_monthly' in self._pending_field_updates)

    def get_max_vector_dimensions(self) -> int:
        """Get the value of max_vector_dimensions."""
        return self.max_vector_dimensions

    def set_max_vector_dimensions(self, value: int):
        """Set the value of max_vector_dimensions."""
        self.max_vector_dimensions = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_vector_dimensions')

    def is_set_max_vector_dimensions(self) -> bool:
        """Check if max_vector_dimensions was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_vector_dimensions' in self._pending_field_updates)

    def get_max_sdk_generations_monthly(self) -> int:
        """Get the value of max_sdk_generations_monthly."""
        return self.max_sdk_generations_monthly

    def set_max_sdk_generations_monthly(self, value: int):
        """Set the value of max_sdk_generations_monthly."""
        self.max_sdk_generations_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_sdk_generations_monthly')

    def is_set_max_sdk_generations_monthly(self) -> bool:
        """Check if max_sdk_generations_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_sdk_generations_monthly' in self._pending_field_updates)

    def get_max_workflow_executions_monthly(self) -> int:
        """Get the value of max_workflow_executions_monthly."""
        return self.max_workflow_executions_monthly

    def set_max_workflow_executions_monthly(self, value: int):
        """Set the value of max_workflow_executions_monthly."""
        self.max_workflow_executions_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_workflow_executions_monthly')

    def is_set_max_workflow_executions_monthly(self) -> bool:
        """Check if max_workflow_executions_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_workflow_executions_monthly' in self._pending_field_updates)

    def get_max_bandwidth_bytes_monthly(self) -> int:
        """Get the value of max_bandwidth_bytes_monthly."""
        return self.max_bandwidth_bytes_monthly

    def set_max_bandwidth_bytes_monthly(self, value: int):
        """Set the value of max_bandwidth_bytes_monthly."""
        self.max_bandwidth_bytes_monthly = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_bandwidth_bytes_monthly')

    def is_set_max_bandwidth_bytes_monthly(self) -> bool:
        """Check if max_bandwidth_bytes_monthly was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_bandwidth_bytes_monthly' in self._pending_field_updates)

    def get_features(self) -> List[str]:
        """Get the value of features."""
        return self.features

    def set_features(self, value: List[str]):
        """Set the value of features."""
        self.features = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('features')

    def add_features(self, item: str):
        """Add an item to features."""
        if self.features is None:
            self.features = []
        self.features.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('features')

    def del_features(self, item: str):
        """Remove an item from features."""
        if self.features and item in self.features:
            self.features.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('features')

    def del_features_by_index(self, index: int):
        """Remove an item from features by index."""
        if self.features and 0 <= index < len(self.features):
            del self.features[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('features')

    def is_set_features(self) -> bool:
        """Check if features was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'features' in self._pending_field_updates)

    def get_sdk_languages(self) -> List[str]:
        """Get the value of sdk_languages."""
        return self.sdk_languages

    def set_sdk_languages(self, value: List[str]):
        """Set the value of sdk_languages."""
        self.sdk_languages = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sdk_languages')

    def add_sdk_languages(self, item: str):
        """Add an item to sdk_languages."""
        if self.sdk_languages is None:
            self.sdk_languages = []
        self.sdk_languages.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sdk_languages')

    def del_sdk_languages(self, item: str):
        """Remove an item from sdk_languages."""
        if self.sdk_languages and item in self.sdk_languages:
            self.sdk_languages.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('sdk_languages')

    def del_sdk_languages_by_index(self, index: int):
        """Remove an item from sdk_languages by index."""
        if self.sdk_languages and 0 <= index < len(self.sdk_languages):
            del self.sdk_languages[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('sdk_languages')

    def is_set_sdk_languages(self) -> bool:
        """Check if sdk_languages was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sdk_languages' in self._pending_field_updates)

    def get_support_level(self) -> str:
        """Get the value of support_level."""
        return self.support_level

    def set_support_level(self, value: str):
        """Set the value of support_level."""
        self.support_level = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('support_level')

    def is_set_support_level(self) -> bool:
        """Check if support_level was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'support_level' in self._pending_field_updates)

    def get_sla_uptime_percent(self) -> float:
        """Get the value of sla_uptime_percent."""
        return self.sla_uptime_percent

    def set_sla_uptime_percent(self, value: float):
        """Set the value of sla_uptime_percent."""
        self.sla_uptime_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sla_uptime_percent')

    def is_set_sla_uptime_percent(self) -> bool:
        """Check if sla_uptime_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sla_uptime_percent' in self._pending_field_updates)

    def get_data_retention_days(self) -> int:
        """Get the value of data_retention_days."""
        return self.data_retention_days

    def set_data_retention_days(self, value: int):
        """Set the value of data_retention_days."""
        self.data_retention_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('data_retention_days')

    def is_set_data_retention_days(self) -> bool:
        """Check if data_retention_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'data_retention_days' in self._pending_field_updates)

    def get_audit_log_retention_days(self) -> int:
        """Get the value of audit_log_retention_days."""
        return self.audit_log_retention_days

    def set_audit_log_retention_days(self, value: int):
        """Set the value of audit_log_retention_days."""
        self.audit_log_retention_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('audit_log_retention_days')

    def is_set_audit_log_retention_days(self) -> bool:
        """Check if audit_log_retention_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'audit_log_retention_days' in self._pending_field_updates)

    def get_backup_frequency(self) -> str:
        """Get the value of backup_frequency."""
        return self.backup_frequency

    def set_backup_frequency(self, value: str):
        """Set the value of backup_frequency."""
        self.backup_frequency = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('backup_frequency')

    def is_set_backup_frequency(self) -> bool:
        """Check if backup_frequency was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'backup_frequency' in self._pending_field_updates)

    def get_overage_handling(self) -> str:
        """Get the value of overage_handling."""
        return self.overage_handling

    def set_overage_handling(self, value: str):
        """Set the value of overage_handling."""
        self.overage_handling = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_handling')

    def is_set_overage_handling(self) -> bool:
        """Check if overage_handling was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_handling' in self._pending_field_updates)

    def get_overage_grace_percent(self) -> int:
        """Get the value of overage_grace_percent."""
        return self.overage_grace_percent

    def set_overage_grace_percent(self, value: int):
        """Set the value of overage_grace_percent."""
        self.overage_grace_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_grace_percent')

    def is_set_overage_grace_percent(self) -> bool:
        """Check if overage_grace_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_grace_percent' in self._pending_field_updates)

    def get_overage_api_request_price_cents(self) -> int:
        """Get the value of overage_api_request_price_cents."""
        return self.overage_api_request_price_cents

    def set_overage_api_request_price_cents(self, value: int):
        """Set the value of overage_api_request_price_cents."""
        self.overage_api_request_price_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_api_request_price_cents')

    def is_set_overage_api_request_price_cents(self) -> bool:
        """Check if overage_api_request_price_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_api_request_price_cents' in self._pending_field_updates)

    def get_overage_storage_price_cents(self) -> int:
        """Get the value of overage_storage_price_cents."""
        return self.overage_storage_price_cents

    def set_overage_storage_price_cents(self, value: int):
        """Set the value of overage_storage_price_cents."""
        self.overage_storage_price_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_storage_price_cents')

    def is_set_overage_storage_price_cents(self) -> bool:
        """Check if overage_storage_price_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_storage_price_cents' in self._pending_field_updates)

    def get_overage_vector_query_price_cents(self) -> int:
        """Get the value of overage_vector_query_price_cents."""
        return self.overage_vector_query_price_cents

    def set_overage_vector_query_price_cents(self, value: int):
        """Set the value of overage_vector_query_price_cents."""
        self.overage_vector_query_price_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_vector_query_price_cents')

    def is_set_overage_vector_query_price_cents(self) -> bool:
        """Check if overage_vector_query_price_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_vector_query_price_cents' in self._pending_field_updates)

    def get_version_policy(self) -> str:
        """Get the value of version_policy."""
        return self.version_policy

    def set_version_policy(self, value: str):
        """Set the value of version_policy."""
        self.version_policy = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('version_policy')

    def is_set_version_policy(self) -> bool:
        """Check if version_policy was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'version_policy' in self._pending_field_updates)

    def get_previous_version_uuid(self) -> str:
        """Get the value of previous_version_uuid."""
        return self.previous_version_uuid

    def set_previous_version_uuid(self, value: str):
        """Set the value of previous_version_uuid."""
        self.previous_version_uuid = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('previous_version_uuid')

    def is_set_previous_version_uuid(self) -> bool:
        """Check if previous_version_uuid was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'previous_version_uuid' in self._pending_field_updates)

    def get_sunset_date(self) -> str:
        """Get the value of sunset_date."""
        return self.sunset_date

    def set_sunset_date(self, value: str):
        """Set the value of sunset_date."""
        self.sunset_date = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sunset_date')

    def is_set_sunset_date(self) -> bool:
        """Check if sunset_date was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sunset_date' in self._pending_field_updates)

    def get_migration_target_plan_code(self) -> str:
        """Get the value of migration_target_plan_code."""
        return self.migration_target_plan_code

    def set_migration_target_plan_code(self, value: str):
        """Set the value of migration_target_plan_code."""
        self.migration_target_plan_code = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('migration_target_plan_code')

    def is_set_migration_target_plan_code(self) -> bool:
        """Check if migration_target_plan_code was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'migration_target_plan_code' in self._pending_field_updates)

    def get_is_public(self) -> bool:
        """Get the value of is_public."""
        return self.is_public

    def set_is_public(self, value: bool):
        """Set the value of is_public."""
        self.is_public = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('is_public')

    def is_set_is_public(self) -> bool:
        """Check if is_public was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'is_public' in self._pending_field_updates)

    def get_is_active(self) -> bool:
        """Get the value of is_active."""
        return self.is_active

    def set_is_active(self, value: bool):
        """Set the value of is_active."""
        self.is_active = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('is_active')

    def is_set_is_active(self) -> bool:
        """Check if is_active was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'is_active' in self._pending_field_updates)

    def get_trial_days(self) -> int:
        """Get the value of trial_days."""
        return self.trial_days

    def set_trial_days(self, value: int):
        """Set the value of trial_days."""
        self.trial_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('trial_days')

    def is_set_trial_days(self) -> bool:
        """Check if trial_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'trial_days' in self._pending_field_updates)

    def get_requires_payment_method(self) -> bool:
        """Get the value of requires_payment_method."""
        return self.requires_payment_method

    def set_requires_payment_method(self, value: bool):
        """Set the value of requires_payment_method."""
        self.requires_payment_method = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('requires_payment_method')

    def is_set_requires_payment_method(self) -> bool:
        """Check if requires_payment_method was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'requires_payment_method' in self._pending_field_updates)

    def get_requires_approval(self) -> bool:
        """Get the value of requires_approval."""
        return self.requires_approval

    def set_requires_approval(self, value: bool):
        """Set the value of requires_approval."""
        self.requires_approval = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('requires_approval')

    def is_set_requires_approval(self) -> bool:
        """Check if requires_approval was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'requires_approval' in self._pending_field_updates)

    def get_minimum_commitment_months(self) -> int:
        """Get the value of minimum_commitment_months."""
        return self.minimum_commitment_months

    def set_minimum_commitment_months(self, value: int):
        """Set the value of minimum_commitment_months."""
        self.minimum_commitment_months = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('minimum_commitment_months')

    def is_set_minimum_commitment_months(self) -> bool:
        """Check if minimum_commitment_months was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'minimum_commitment_months' in self._pending_field_updates)

    @classmethod
    def getbilling_plan_typesStrings(cls):
        """Legacy method for billing_plan_types backward compatibility."""
        try:
            import importlib
            package_base = cls.__module__.split('.')[0] if hasattr(cls, '__module__') else 'pymodel'
            enum_snake_name = normalize_name_consistent('billing_plan_types')
            module_name = f'{package_base}.enums.{enum_snake_name}'
            enum_module = importlib.import_module(module_name)
            enum_class = getattr(enum_module, 'billing_plan_types')
            return enum_class.get_all_values()
        except Exception:
            return []



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
        return cls(name="", uuid=None, fq_name=None, parent_uuid=None, display_name=None, description=None, created_by=None, created_at=None, updated_at=None, plan_code=None, plan_version=None, tier_level=None, pricing_currency=None, monthly_price_cents=None, annual_price_cents=None, setup_fee_cents=None, max_schemas=None, max_api_requests_monthly=None, max_api_requests_per_second=None, max_storage_bytes=None, max_db_storage_bytes=None, max_blob_storage_bytes=None, max_vector_storage_bytes=None, max_team_members=None, max_projects=None, max_api_keys_per_project=None, max_plugins=None, max_plugin_invocations_monthly=None, allowed_plugin_types=None, max_kafka_topics=None, max_kafka_messages_monthly=None, max_kafka_partitions_per_topic=None, max_vectors_stored=None, max_vector_queries_monthly=None, max_vector_dimensions=None, max_sdk_generations_monthly=None, max_workflow_executions_monthly=None, max_bandwidth_bytes_monthly=None, features=None, sdk_languages=None, support_level=None, sla_uptime_percent=None, data_retention_days=None, audit_log_retention_days=None, backup_frequency=None, overage_handling=None, overage_grace_percent=None, overage_api_request_price_cents=None, overage_storage_price_cents=None, overage_vector_query_price_cents=None, version_policy=None, previous_version_uuid=None, sunset_date=None, migration_target_plan_code=None, is_public=None, is_active=None, trial_days=None, requires_payment_method=None, requires_approval=None, minimum_commitment_months=None)

platform_billing_plan=PlatformBillingPlan
PlatformBillingPlan=PlatformBillingPlan
PlatformBillingPlan=PlatformBillingPlan
platform_billing_plan=PlatformBillingPlan
