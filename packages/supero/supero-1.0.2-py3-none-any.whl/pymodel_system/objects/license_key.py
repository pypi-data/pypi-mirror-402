# File: pymodel_system/objects/license_key.py
"""
This file was generated from the LicenseKey.json schema.
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

class LicenseKey:
    """
    Represents a LicenseKey instance.
    
    This class is auto-generated and includes:
    - Standard CRUD operations
    - Fluent API methods (when used with Supero)
    - Smart reference management with link data support
    - Parent-child hierarchy navigation
    """
    
    _OBJ_TYPE = "license_key"
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
    'key': {
        'type': 'str',
        'is_list': False,
        'json_name': 'key',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'license_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'license_type',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'admin_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'admin_email',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'tier': {
        'type': 'str',
        'is_list': False,
        'json_name': 'tier',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'offline_pack': {
        'type': 'str',
        'is_list': False,
        'json_name': 'offline_pack',
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
    'issued_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'issued_at',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'expires_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'expires_at',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'grace_period_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'grace_period_days',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'billing_cycle': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_cycle',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'features': {
        'type': 'str',
        'is_list': True,
        'json_name': 'features',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'included_projects': {
        'type': 'int',
        'is_list': False,
        'json_name': 'included_projects',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'included_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'included_tenants',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'included_servers': {
        'type': 'int',
        'is_list': False,
        'json_name': 'included_servers',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'max_projects': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_projects',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'max_servers': {
        'type': 'int',
        'is_list': False,
        'json_name': 'max_servers',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'per_extra_project': {
        'type': 'int',
        'is_list': False,
        'json_name': 'per_extra_project',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'per_extra_100_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'per_extra_100_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'per_extra_server': {
        'type': 'int',
        'is_list': False,
        'json_name': 'per_extra_server',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'ai_agent_enabled': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'ai_agent_enabled',
        'original_type': 'boolean',
        'mandatory': False,
        'static': False,
    },
    'ai_agent_included_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'ai_agent_included_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'ai_agent_max_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'ai_agent_max_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'per_extra_100_ai_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'per_extra_100_ai_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'discount_percent': {
        'type': 'int',
        'is_list': False,
        'json_name': 'discount_percent',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'discount_base_percent': {
        'type': 'int',
        'is_list': False,
        'json_name': 'discount_base_percent',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'discount_overage_percent': {
        'type': 'int',
        'is_list': False,
        'json_name': 'discount_overage_percent',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'discount_ai_percent': {
        'type': 'int',
        'is_list': False,
        'json_name': 'discount_ai_percent',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'discount_code': {
        'type': 'str',
        'is_list': False,
        'json_name': 'discount_code',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'discount_expires_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'discount_expires_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'discount_note': {
        'type': 'str',
        'is_list': False,
        'json_name': 'discount_note',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'hardware_ids': {
        'type': 'str',
        'is_list': True,
        'json_name': 'hardware_ids',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'signature': {
        'type': 'str',
        'is_list': False,
        'json_name': 'signature',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'public_key_version': {
        'type': 'str',
        'is_list': False,
        'json_name': 'public_key_version',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'stripe_customer_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'stripe_customer_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'stripe_subscription_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'stripe_subscription_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'stripe_ai_subscription_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'stripe_ai_subscription_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'contract_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'contract_start_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_start_date',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'contract_end_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_end_date',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'contract_value': {
        'type': 'int',
        'is_list': False,
        'json_name': 'contract_value',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'last_heartbeat_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'last_heartbeat_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'heartbeat_failures': {
        'type': 'int',
        'is_list': False,
        'json_name': 'heartbeat_failures',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'reported_projects': {
        'type': 'int',
        'is_list': False,
        'json_name': 'reported_projects',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'reported_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'reported_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'reported_servers': {
        'type': 'int',
        'is_list': False,
        'json_name': 'reported_servers',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'reported_ai_tenants': {
        'type': 'int',
        'is_list': False,
        'json_name': 'reported_ai_tenants',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'renewal_reminder_sent': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'renewal_reminder_sent',
        'original_type': 'boolean',
        'mandatory': False,
        'static': False,
    },
    'auto_renew': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'auto_renew',
        'original_type': 'boolean',
        'mandatory': False,
        'static': False,
    },
    'notes': {
        'type': 'str',
        'is_list': False,
        'json_name': 'notes',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'metadata': {
        'type': 'str',
        'is_list': False,
        'json_name': 'metadata',
        'original_type': 'json',
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
            'enabled': True,
            'config': {'indexes': ['idx_key', 'idx_status', 'idx_type', 'idx_tier']},
            'operations': ['create', 'read', 'update', 'delete'],
        }
    ]
    
    # Index definitions
    _indexes = {
        'idx_key': {
            'name': 'idx_key',
            'type': 'simple',
            'fields': [
                {'name': 'key', 'sort': 'asc'}
            ],
            'unique': False,
            'sparse': False
        },
        'idx_type': {
            'name': 'idx_type',
            'type': 'simple',
            'fields': [
                {'name': 'license_type', 'sort': 'asc'}
            ],
            'unique': False,
            'sparse': False
        },
        'idx_tier': {
            'name': 'idx_tier',
            'type': 'simple',
            'fields': [
                {'name': 'tier', 'sort': 'asc'}
            ],
            'unique': False,
            'sparse': False
        },
        'idx_status': {
            'name': 'idx_status',
            'type': 'simple',
            'fields': [
                {'name': 'status', 'sort': 'asc'}
            ],
            'unique': False,
            'sparse': False
        }
    }

    _CONSTRAINTS = {
        'included_projects': {
            'min-value': 1,
            'type': 'integer',
        },
        'included_tenants': {
            'min-value': 1,
            'type': 'integer',
        },
        'included_servers': {
            'min-value': 1,
            'type': 'integer',
        },
        'discount_percent': {
            'min-value': 0,
            'max-value': 100,
            'type': 'integer',
        },
        'discount_base_percent': {
            'min-value': 0,
            'max-value': 100,
            'type': 'integer',
        },
        'discount_overage_percent': {
            'min-value': 0,
            'max-value': 100,
            'type': 'integer',
        },
        'discount_ai_percent': {
            'min-value': 0,
            'max-value': 100,
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
        key: Optional[str] = None,
        license_type: Optional[str] = None,
        admin_email: Optional[str] = None,
        tier: Optional[str] = None,
        offline_pack: Optional[str] = None,
        status: Optional[str] = None,
        issued_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        grace_period_days: Optional[int] = None,
        billing_cycle: Optional[str] = None,
        features: Optional[List[str]] = None,
        included_projects: Optional[int] = None,
        included_tenants: Optional[int] = None,
        included_servers: Optional[int] = None,
        max_projects: Optional[int] = None,
        max_tenants: Optional[int] = None,
        max_servers: Optional[int] = None,
        per_extra_project: Optional[int] = None,
        per_extra_100_tenants: Optional[int] = None,
        per_extra_server: Optional[int] = None,
        ai_agent_enabled: Optional[bool] = None,
        ai_agent_included_tenants: Optional[int] = None,
        ai_agent_max_tenants: Optional[int] = None,
        per_extra_100_ai_tenants: Optional[int] = None,
        discount_percent: Optional[int] = None,
        discount_base_percent: Optional[int] = None,
        discount_overage_percent: Optional[int] = None,
        discount_ai_percent: Optional[int] = None,
        discount_code: Optional[str] = None,
        discount_expires_at: Optional[str] = None,
        discount_note: Optional[str] = None,
        hardware_ids: Optional[List[str]] = None,
        signature: Optional[str] = None,
        public_key_version: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        stripe_ai_subscription_id: Optional[str] = None,
        contract_id: Optional[str] = None,
        contract_start_date: Optional[str] = None,
        contract_end_date: Optional[str] = None,
        contract_value: Optional[int] = None,
        last_heartbeat_at: Optional[str] = None,
        heartbeat_failures: Optional[int] = None,
        reported_projects: Optional[int] = None,
        reported_tenants: Optional[int] = None,
        reported_servers: Optional[int] = None,
        reported_ai_tenants: Optional[int] = None,
        renewal_reminder_sent: Optional[bool] = None,
        auto_renew: Optional[bool] = None,
        notes: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        # Set initialization flag to prevent tracking during __init__
        self._initializing = True
        
        self.obj_type = "license_key"
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
    'key': 'key',
    'license_type': 'license_type',
    'admin_email': 'admin_email',
    'tier': 'tier',
    'offline_pack': 'offline_pack',
    'status': 'status',
    'issued_at': 'issued_at',
    'expires_at': 'expires_at',
    'grace_period_days': 'grace_period_days',
    'billing_cycle': 'billing_cycle',
    'features': 'features',
    'included_projects': 'included_projects',
    'included_tenants': 'included_tenants',
    'included_servers': 'included_servers',
    'max_projects': 'max_projects',
    'max_tenants': 'max_tenants',
    'max_servers': 'max_servers',
    'per_extra_project': 'per_extra_project',
    'per_extra_100_tenants': 'per_extra_100_tenants',
    'per_extra_server': 'per_extra_server',
    'ai_agent_enabled': 'ai_agent_enabled',
    'ai_agent_included_tenants': 'ai_agent_included_tenants',
    'ai_agent_max_tenants': 'ai_agent_max_tenants',
    'per_extra_100_ai_tenants': 'per_extra_100_ai_tenants',
    'discount_percent': 'discount_percent',
    'discount_base_percent': 'discount_base_percent',
    'discount_overage_percent': 'discount_overage_percent',
    'discount_ai_percent': 'discount_ai_percent',
    'discount_code': 'discount_code',
    'discount_expires_at': 'discount_expires_at',
    'discount_note': 'discount_note',
    'hardware_ids': 'hardware_ids',
    'signature': 'signature',
    'public_key_version': 'public_key_version',
    'stripe_customer_id': 'stripe_customer_id',
    'stripe_subscription_id': 'stripe_subscription_id',
    'stripe_ai_subscription_id': 'stripe_ai_subscription_id',
    'contract_id': 'contract_id',
    'contract_start_date': 'contract_start_date',
    'contract_end_date': 'contract_end_date',
    'contract_value': 'contract_value',
    'last_heartbeat_at': 'last_heartbeat_at',
    'heartbeat_failures': 'heartbeat_failures',
    'reported_projects': 'reported_projects',
    'reported_tenants': 'reported_tenants',
    'reported_servers': 'reported_servers',
    'reported_ai_tenants': 'reported_ai_tenants',
    'renewal_reminder_sent': 'renewal_reminder_sent',
    'auto_renew': 'auto_renew',
    'notes': 'notes',
    'metadata': 'metadata'
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
    'key': 'key',
    'license_type': 'license_type',
    'admin_email': 'admin_email',
    'tier': 'tier',
    'offline_pack': 'offline_pack',
    'status': 'status',
    'issued_at': 'issued_at',
    'expires_at': 'expires_at',
    'grace_period_days': 'grace_period_days',
    'billing_cycle': 'billing_cycle',
    'features': 'features',
    'included_projects': 'included_projects',
    'included_tenants': 'included_tenants',
    'included_servers': 'included_servers',
    'max_projects': 'max_projects',
    'max_tenants': 'max_tenants',
    'max_servers': 'max_servers',
    'per_extra_project': 'per_extra_project',
    'per_extra_100_tenants': 'per_extra_100_tenants',
    'per_extra_server': 'per_extra_server',
    'ai_agent_enabled': 'ai_agent_enabled',
    'ai_agent_included_tenants': 'ai_agent_included_tenants',
    'ai_agent_max_tenants': 'ai_agent_max_tenants',
    'per_extra_100_ai_tenants': 'per_extra_100_ai_tenants',
    'discount_percent': 'discount_percent',
    'discount_base_percent': 'discount_base_percent',
    'discount_overage_percent': 'discount_overage_percent',
    'discount_ai_percent': 'discount_ai_percent',
    'discount_code': 'discount_code',
    'discount_expires_at': 'discount_expires_at',
    'discount_note': 'discount_note',
    'hardware_ids': 'hardware_ids',
    'signature': 'signature',
    'public_key_version': 'public_key_version',
    'stripe_customer_id': 'stripe_customer_id',
    'stripe_subscription_id': 'stripe_subscription_id',
    'stripe_ai_subscription_id': 'stripe_ai_subscription_id',
    'contract_id': 'contract_id',
    'contract_start_date': 'contract_start_date',
    'contract_end_date': 'contract_end_date',
    'contract_value': 'contract_value',
    'last_heartbeat_at': 'last_heartbeat_at',
    'heartbeat_failures': 'heartbeat_failures',
    'reported_projects': 'reported_projects',
    'reported_tenants': 'reported_tenants',
    'reported_servers': 'reported_servers',
    'reported_ai_tenants': 'reported_ai_tenants',
    'renewal_reminder_sent': 'renewal_reminder_sent',
    'auto_renew': 'auto_renew',
    'notes': 'notes',
    'metadata': 'metadata'
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
        self.key = key
        self.license_type = license_type
        self.admin_email = admin_email
        self.tier = tier
        self.offline_pack = offline_pack
        self.status = status
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.grace_period_days = grace_period_days
        self.billing_cycle = billing_cycle
        self.features = features if features is not None else []
        self.included_projects = included_projects
        self.included_tenants = included_tenants
        self.included_servers = included_servers
        self.max_projects = max_projects
        self.max_tenants = max_tenants
        self.max_servers = max_servers
        self.per_extra_project = per_extra_project
        self.per_extra_100_tenants = per_extra_100_tenants
        self.per_extra_server = per_extra_server
        self.ai_agent_enabled = ai_agent_enabled
        self.ai_agent_included_tenants = ai_agent_included_tenants
        self.ai_agent_max_tenants = ai_agent_max_tenants
        self.per_extra_100_ai_tenants = per_extra_100_ai_tenants
        self.discount_percent = discount_percent
        self.discount_base_percent = discount_base_percent
        self.discount_overage_percent = discount_overage_percent
        self.discount_ai_percent = discount_ai_percent
        self.discount_code = discount_code
        self.discount_expires_at = discount_expires_at
        self.discount_note = discount_note
        self.hardware_ids = hardware_ids if hardware_ids is not None else []
        self.signature = signature
        self.public_key_version = public_key_version
        self.stripe_customer_id = stripe_customer_id
        self.stripe_subscription_id = stripe_subscription_id
        self.stripe_ai_subscription_id = stripe_ai_subscription_id
        self.contract_id = contract_id
        self.contract_start_date = contract_start_date
        self.contract_end_date = contract_end_date
        self.contract_value = contract_value
        self.last_heartbeat_at = last_heartbeat_at
        self.heartbeat_failures = heartbeat_failures
        self.reported_projects = reported_projects
        self.reported_tenants = reported_tenants
        self.reported_servers = reported_servers
        self.reported_ai_tenants = reported_ai_tenants
        self.renewal_reminder_sent = renewal_reminder_sent
        self.auto_renew = auto_renew
        self.notes = notes
        self.metadata = metadata


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
        self._pending_field_updates.add('key')
        self._pending_field_updates.add('license_type')
        if admin_email is not None:
            self._pending_field_updates.add('admin_email')
        self._pending_field_updates.add('tier')
        if offline_pack is not None:
            self._pending_field_updates.add('offline_pack')
        self._pending_field_updates.add('status')
        self._pending_field_updates.add('issued_at')
        self._pending_field_updates.add('expires_at')
        if grace_period_days != 7:
            self._pending_field_updates.add('grace_period_days')
        if billing_cycle != 'monthly':
            self._pending_field_updates.add('billing_cycle')
        self._pending_field_updates.add('features')
        self._pending_field_updates.add('included_projects')
        self._pending_field_updates.add('included_tenants')
        self._pending_field_updates.add('included_servers')
        if max_projects is not None:
            self._pending_field_updates.add('max_projects')
        if max_tenants is not None:
            self._pending_field_updates.add('max_tenants')
        if max_servers is not None:
            self._pending_field_updates.add('max_servers')
        if per_extra_project != 99:
            self._pending_field_updates.add('per_extra_project')
        if per_extra_100_tenants != 25:
            self._pending_field_updates.add('per_extra_100_tenants')
        if per_extra_server != 49:
            self._pending_field_updates.add('per_extra_server')
        if ai_agent_enabled != False:
            self._pending_field_updates.add('ai_agent_enabled')
        if ai_agent_included_tenants != 0:
            self._pending_field_updates.add('ai_agent_included_tenants')
        if ai_agent_max_tenants is not None:
            self._pending_field_updates.add('ai_agent_max_tenants')
        if per_extra_100_ai_tenants != 19:
            self._pending_field_updates.add('per_extra_100_ai_tenants')
        if discount_percent != 0:
            self._pending_field_updates.add('discount_percent')
        if discount_base_percent != 0:
            self._pending_field_updates.add('discount_base_percent')
        if discount_overage_percent != 0:
            self._pending_field_updates.add('discount_overage_percent')
        if discount_ai_percent != 0:
            self._pending_field_updates.add('discount_ai_percent')
        if discount_code is not None:
            self._pending_field_updates.add('discount_code')
        if discount_expires_at is not None:
            self._pending_field_updates.add('discount_expires_at')
        if discount_note is not None:
            self._pending_field_updates.add('discount_note')
        if hardware_ids is not None:
            self._pending_field_updates.add('hardware_ids')
        if signature is not None:
            self._pending_field_updates.add('signature')
        if public_key_version != 'v1':
            self._pending_field_updates.add('public_key_version')
        if stripe_customer_id is not None:
            self._pending_field_updates.add('stripe_customer_id')
        if stripe_subscription_id is not None:
            self._pending_field_updates.add('stripe_subscription_id')
        if stripe_ai_subscription_id is not None:
            self._pending_field_updates.add('stripe_ai_subscription_id')
        if contract_id is not None:
            self._pending_field_updates.add('contract_id')
        if contract_start_date is not None:
            self._pending_field_updates.add('contract_start_date')
        if contract_end_date is not None:
            self._pending_field_updates.add('contract_end_date')
        if contract_value is not None:
            self._pending_field_updates.add('contract_value')
        if last_heartbeat_at is not None:
            self._pending_field_updates.add('last_heartbeat_at')
        if heartbeat_failures != 0:
            self._pending_field_updates.add('heartbeat_failures')
        if reported_projects != 0:
            self._pending_field_updates.add('reported_projects')
        if reported_tenants != 0:
            self._pending_field_updates.add('reported_tenants')
        if reported_servers != 0:
            self._pending_field_updates.add('reported_servers')
        if reported_ai_tenants != 0:
            self._pending_field_updates.add('reported_ai_tenants')
        if renewal_reminder_sent != False:
            self._pending_field_updates.add('renewal_reminder_sent')
        if auto_renew != True:
            self._pending_field_updates.add('auto_renew')
        if notes is not None:
            self._pending_field_updates.add('notes')
        if metadata is not None:
            self._pending_field_updates.add('metadata')
        
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

    def get_key(self) -> str:
        """Get the value of key."""
        return self.key

    def set_key(self, value: str):
        """Set the value of key."""
        self.key = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('key')

    def is_set_key(self) -> bool:
        """Check if key was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'key' in self._pending_field_updates)

    def get_license_type(self) -> str:
        """Get the value of license_type."""
        return self.license_type

    def set_license_type(self, value: str):
        """Set the value of license_type."""
        self.license_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('license_type')

    def is_set_license_type(self) -> bool:
        """Check if license_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'license_type' in self._pending_field_updates)

    def get_admin_email(self) -> str:
        """Get the value of admin_email."""
        return self.admin_email

    def set_admin_email(self, value: str):
        """Set the value of admin_email."""
        self.admin_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('admin_email')

    def is_set_admin_email(self) -> bool:
        """Check if admin_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'admin_email' in self._pending_field_updates)

    def get_tier(self) -> str:
        """Get the value of tier."""
        return self.tier

    def set_tier(self, value: str):
        """Set the value of tier."""
        self.tier = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tier')

    def is_set_tier(self) -> bool:
        """Check if tier was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tier' in self._pending_field_updates)

    def get_offline_pack(self) -> str:
        """Get the value of offline_pack."""
        return self.offline_pack

    def set_offline_pack(self, value: str):
        """Set the value of offline_pack."""
        self.offline_pack = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('offline_pack')

    def is_set_offline_pack(self) -> bool:
        """Check if offline_pack was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'offline_pack' in self._pending_field_updates)

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

    def get_issued_at(self) -> str:
        """Get the value of issued_at."""
        return self.issued_at

    def set_issued_at(self, value: str):
        """Set the value of issued_at."""
        self.issued_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('issued_at')

    def is_set_issued_at(self) -> bool:
        """Check if issued_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'issued_at' in self._pending_field_updates)

    def get_expires_at(self) -> str:
        """Get the value of expires_at."""
        return self.expires_at

    def set_expires_at(self, value: str):
        """Set the value of expires_at."""
        self.expires_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('expires_at')

    def is_set_expires_at(self) -> bool:
        """Check if expires_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'expires_at' in self._pending_field_updates)

    def get_grace_period_days(self) -> int:
        """Get the value of grace_period_days."""
        return self.grace_period_days

    def set_grace_period_days(self, value: int):
        """Set the value of grace_period_days."""
        self.grace_period_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('grace_period_days')

    def is_set_grace_period_days(self) -> bool:
        """Check if grace_period_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'grace_period_days' in self._pending_field_updates)

    def get_billing_cycle(self) -> str:
        """Get the value of billing_cycle."""
        return self.billing_cycle

    def set_billing_cycle(self, value: str):
        """Set the value of billing_cycle."""
        self.billing_cycle = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_cycle')

    def is_set_billing_cycle(self) -> bool:
        """Check if billing_cycle was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_cycle' in self._pending_field_updates)

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

    def get_included_projects(self) -> int:
        """Get the value of included_projects."""
        return self.included_projects

    def set_included_projects(self, value: int):
        """Set the value of included_projects."""
        self.included_projects = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('included_projects')

    def is_set_included_projects(self) -> bool:
        """Check if included_projects was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'included_projects' in self._pending_field_updates)

    def get_included_tenants(self) -> int:
        """Get the value of included_tenants."""
        return self.included_tenants

    def set_included_tenants(self, value: int):
        """Set the value of included_tenants."""
        self.included_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('included_tenants')

    def is_set_included_tenants(self) -> bool:
        """Check if included_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'included_tenants' in self._pending_field_updates)

    def get_included_servers(self) -> int:
        """Get the value of included_servers."""
        return self.included_servers

    def set_included_servers(self, value: int):
        """Set the value of included_servers."""
        self.included_servers = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('included_servers')

    def is_set_included_servers(self) -> bool:
        """Check if included_servers was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'included_servers' in self._pending_field_updates)

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

    def get_max_tenants(self) -> int:
        """Get the value of max_tenants."""
        return self.max_tenants

    def set_max_tenants(self, value: int):
        """Set the value of max_tenants."""
        self.max_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_tenants')

    def is_set_max_tenants(self) -> bool:
        """Check if max_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_tenants' in self._pending_field_updates)

    def get_max_servers(self) -> int:
        """Get the value of max_servers."""
        return self.max_servers

    def set_max_servers(self, value: int):
        """Set the value of max_servers."""
        self.max_servers = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('max_servers')

    def is_set_max_servers(self) -> bool:
        """Check if max_servers was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'max_servers' in self._pending_field_updates)

    def get_per_extra_project(self) -> int:
        """Get the value of per_extra_project."""
        return self.per_extra_project

    def set_per_extra_project(self, value: int):
        """Set the value of per_extra_project."""
        self.per_extra_project = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('per_extra_project')

    def is_set_per_extra_project(self) -> bool:
        """Check if per_extra_project was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'per_extra_project' in self._pending_field_updates)

    def get_per_extra_100_tenants(self) -> int:
        """Get the value of per_extra_100_tenants."""
        return self.per_extra_100_tenants

    def set_per_extra_100_tenants(self, value: int):
        """Set the value of per_extra_100_tenants."""
        self.per_extra_100_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('per_extra_100_tenants')

    def is_set_per_extra_100_tenants(self) -> bool:
        """Check if per_extra_100_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'per_extra_100_tenants' in self._pending_field_updates)

    def get_per_extra_server(self) -> int:
        """Get the value of per_extra_server."""
        return self.per_extra_server

    def set_per_extra_server(self, value: int):
        """Set the value of per_extra_server."""
        self.per_extra_server = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('per_extra_server')

    def is_set_per_extra_server(self) -> bool:
        """Check if per_extra_server was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'per_extra_server' in self._pending_field_updates)

    def get_ai_agent_enabled(self) -> bool:
        """Get the value of ai_agent_enabled."""
        return self.ai_agent_enabled

    def set_ai_agent_enabled(self, value: bool):
        """Set the value of ai_agent_enabled."""
        self.ai_agent_enabled = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('ai_agent_enabled')

    def is_set_ai_agent_enabled(self) -> bool:
        """Check if ai_agent_enabled was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'ai_agent_enabled' in self._pending_field_updates)

    def get_ai_agent_included_tenants(self) -> int:
        """Get the value of ai_agent_included_tenants."""
        return self.ai_agent_included_tenants

    def set_ai_agent_included_tenants(self, value: int):
        """Set the value of ai_agent_included_tenants."""
        self.ai_agent_included_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('ai_agent_included_tenants')

    def is_set_ai_agent_included_tenants(self) -> bool:
        """Check if ai_agent_included_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'ai_agent_included_tenants' in self._pending_field_updates)

    def get_ai_agent_max_tenants(self) -> int:
        """Get the value of ai_agent_max_tenants."""
        return self.ai_agent_max_tenants

    def set_ai_agent_max_tenants(self, value: int):
        """Set the value of ai_agent_max_tenants."""
        self.ai_agent_max_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('ai_agent_max_tenants')

    def is_set_ai_agent_max_tenants(self) -> bool:
        """Check if ai_agent_max_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'ai_agent_max_tenants' in self._pending_field_updates)

    def get_per_extra_100_ai_tenants(self) -> int:
        """Get the value of per_extra_100_ai_tenants."""
        return self.per_extra_100_ai_tenants

    def set_per_extra_100_ai_tenants(self, value: int):
        """Set the value of per_extra_100_ai_tenants."""
        self.per_extra_100_ai_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('per_extra_100_ai_tenants')

    def is_set_per_extra_100_ai_tenants(self) -> bool:
        """Check if per_extra_100_ai_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'per_extra_100_ai_tenants' in self._pending_field_updates)

    def get_discount_percent(self) -> int:
        """Get the value of discount_percent."""
        return self.discount_percent

    def set_discount_percent(self, value: int):
        """Set the value of discount_percent."""
        self.discount_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_percent')

    def is_set_discount_percent(self) -> bool:
        """Check if discount_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_percent' in self._pending_field_updates)

    def get_discount_base_percent(self) -> int:
        """Get the value of discount_base_percent."""
        return self.discount_base_percent

    def set_discount_base_percent(self, value: int):
        """Set the value of discount_base_percent."""
        self.discount_base_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_base_percent')

    def is_set_discount_base_percent(self) -> bool:
        """Check if discount_base_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_base_percent' in self._pending_field_updates)

    def get_discount_overage_percent(self) -> int:
        """Get the value of discount_overage_percent."""
        return self.discount_overage_percent

    def set_discount_overage_percent(self, value: int):
        """Set the value of discount_overage_percent."""
        self.discount_overage_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_overage_percent')

    def is_set_discount_overage_percent(self) -> bool:
        """Check if discount_overage_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_overage_percent' in self._pending_field_updates)

    def get_discount_ai_percent(self) -> int:
        """Get the value of discount_ai_percent."""
        return self.discount_ai_percent

    def set_discount_ai_percent(self, value: int):
        """Set the value of discount_ai_percent."""
        self.discount_ai_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_ai_percent')

    def is_set_discount_ai_percent(self) -> bool:
        """Check if discount_ai_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_ai_percent' in self._pending_field_updates)

    def get_discount_code(self) -> str:
        """Get the value of discount_code."""
        return self.discount_code

    def set_discount_code(self, value: str):
        """Set the value of discount_code."""
        self.discount_code = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_code')

    def is_set_discount_code(self) -> bool:
        """Check if discount_code was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_code' in self._pending_field_updates)

    def get_discount_expires_at(self) -> str:
        """Get the value of discount_expires_at."""
        return self.discount_expires_at

    def set_discount_expires_at(self, value: str):
        """Set the value of discount_expires_at."""
        self.discount_expires_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_expires_at')

    def is_set_discount_expires_at(self) -> bool:
        """Check if discount_expires_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_expires_at' in self._pending_field_updates)

    def get_discount_note(self) -> str:
        """Get the value of discount_note."""
        return self.discount_note

    def set_discount_note(self, value: str):
        """Set the value of discount_note."""
        self.discount_note = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_note')

    def is_set_discount_note(self) -> bool:
        """Check if discount_note was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_note' in self._pending_field_updates)

    def get_hardware_ids(self) -> List[str]:
        """Get the value of hardware_ids."""
        return self.hardware_ids

    def set_hardware_ids(self, value: List[str]):
        """Set the value of hardware_ids."""
        self.hardware_ids = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('hardware_ids')

    def add_hardware_ids(self, item: str):
        """Add an item to hardware_ids."""
        if self.hardware_ids is None:
            self.hardware_ids = []
        self.hardware_ids.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('hardware_ids')

    def del_hardware_ids(self, item: str):
        """Remove an item from hardware_ids."""
        if self.hardware_ids and item in self.hardware_ids:
            self.hardware_ids.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('hardware_ids')

    def del_hardware_ids_by_index(self, index: int):
        """Remove an item from hardware_ids by index."""
        if self.hardware_ids and 0 <= index < len(self.hardware_ids):
            del self.hardware_ids[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('hardware_ids')

    def is_set_hardware_ids(self) -> bool:
        """Check if hardware_ids was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'hardware_ids' in self._pending_field_updates)

    def get_signature(self) -> str:
        """Get the value of signature."""
        return self.signature

    def set_signature(self, value: str):
        """Set the value of signature."""
        self.signature = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('signature')

    def is_set_signature(self) -> bool:
        """Check if signature was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'signature' in self._pending_field_updates)

    def get_public_key_version(self) -> str:
        """Get the value of public_key_version."""
        return self.public_key_version

    def set_public_key_version(self, value: str):
        """Set the value of public_key_version."""
        self.public_key_version = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('public_key_version')

    def is_set_public_key_version(self) -> bool:
        """Check if public_key_version was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'public_key_version' in self._pending_field_updates)

    def get_stripe_customer_id(self) -> str:
        """Get the value of stripe_customer_id."""
        return self.stripe_customer_id

    def set_stripe_customer_id(self, value: str):
        """Set the value of stripe_customer_id."""
        self.stripe_customer_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('stripe_customer_id')

    def is_set_stripe_customer_id(self) -> bool:
        """Check if stripe_customer_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'stripe_customer_id' in self._pending_field_updates)

    def get_stripe_subscription_id(self) -> str:
        """Get the value of stripe_subscription_id."""
        return self.stripe_subscription_id

    def set_stripe_subscription_id(self, value: str):
        """Set the value of stripe_subscription_id."""
        self.stripe_subscription_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('stripe_subscription_id')

    def is_set_stripe_subscription_id(self) -> bool:
        """Check if stripe_subscription_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'stripe_subscription_id' in self._pending_field_updates)

    def get_stripe_ai_subscription_id(self) -> str:
        """Get the value of stripe_ai_subscription_id."""
        return self.stripe_ai_subscription_id

    def set_stripe_ai_subscription_id(self, value: str):
        """Set the value of stripe_ai_subscription_id."""
        self.stripe_ai_subscription_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('stripe_ai_subscription_id')

    def is_set_stripe_ai_subscription_id(self) -> bool:
        """Check if stripe_ai_subscription_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'stripe_ai_subscription_id' in self._pending_field_updates)

    def get_contract_id(self) -> str:
        """Get the value of contract_id."""
        return self.contract_id

    def set_contract_id(self, value: str):
        """Set the value of contract_id."""
        self.contract_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_id')

    def is_set_contract_id(self) -> bool:
        """Check if contract_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_id' in self._pending_field_updates)

    def get_contract_start_date(self) -> str:
        """Get the value of contract_start_date."""
        return self.contract_start_date

    def set_contract_start_date(self, value: str):
        """Set the value of contract_start_date."""
        self.contract_start_date = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_start_date')

    def is_set_contract_start_date(self) -> bool:
        """Check if contract_start_date was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_start_date' in self._pending_field_updates)

    def get_contract_end_date(self) -> str:
        """Get the value of contract_end_date."""
        return self.contract_end_date

    def set_contract_end_date(self, value: str):
        """Set the value of contract_end_date."""
        self.contract_end_date = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_end_date')

    def is_set_contract_end_date(self) -> bool:
        """Check if contract_end_date was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_end_date' in self._pending_field_updates)

    def get_contract_value(self) -> int:
        """Get the value of contract_value."""
        return self.contract_value

    def set_contract_value(self, value: int):
        """Set the value of contract_value."""
        self.contract_value = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_value')

    def is_set_contract_value(self) -> bool:
        """Check if contract_value was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_value' in self._pending_field_updates)

    def get_last_heartbeat_at(self) -> str:
        """Get the value of last_heartbeat_at."""
        return self.last_heartbeat_at

    def set_last_heartbeat_at(self, value: str):
        """Set the value of last_heartbeat_at."""
        self.last_heartbeat_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('last_heartbeat_at')

    def is_set_last_heartbeat_at(self) -> bool:
        """Check if last_heartbeat_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'last_heartbeat_at' in self._pending_field_updates)

    def get_heartbeat_failures(self) -> int:
        """Get the value of heartbeat_failures."""
        return self.heartbeat_failures

    def set_heartbeat_failures(self, value: int):
        """Set the value of heartbeat_failures."""
        self.heartbeat_failures = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('heartbeat_failures')

    def is_set_heartbeat_failures(self) -> bool:
        """Check if heartbeat_failures was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'heartbeat_failures' in self._pending_field_updates)

    def get_reported_projects(self) -> int:
        """Get the value of reported_projects."""
        return self.reported_projects

    def set_reported_projects(self, value: int):
        """Set the value of reported_projects."""
        self.reported_projects = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('reported_projects')

    def is_set_reported_projects(self) -> bool:
        """Check if reported_projects was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'reported_projects' in self._pending_field_updates)

    def get_reported_tenants(self) -> int:
        """Get the value of reported_tenants."""
        return self.reported_tenants

    def set_reported_tenants(self, value: int):
        """Set the value of reported_tenants."""
        self.reported_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('reported_tenants')

    def is_set_reported_tenants(self) -> bool:
        """Check if reported_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'reported_tenants' in self._pending_field_updates)

    def get_reported_servers(self) -> int:
        """Get the value of reported_servers."""
        return self.reported_servers

    def set_reported_servers(self, value: int):
        """Set the value of reported_servers."""
        self.reported_servers = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('reported_servers')

    def is_set_reported_servers(self) -> bool:
        """Check if reported_servers was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'reported_servers' in self._pending_field_updates)

    def get_reported_ai_tenants(self) -> int:
        """Get the value of reported_ai_tenants."""
        return self.reported_ai_tenants

    def set_reported_ai_tenants(self, value: int):
        """Set the value of reported_ai_tenants."""
        self.reported_ai_tenants = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('reported_ai_tenants')

    def is_set_reported_ai_tenants(self) -> bool:
        """Check if reported_ai_tenants was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'reported_ai_tenants' in self._pending_field_updates)

    def get_renewal_reminder_sent(self) -> bool:
        """Get the value of renewal_reminder_sent."""
        return self.renewal_reminder_sent

    def set_renewal_reminder_sent(self, value: bool):
        """Set the value of renewal_reminder_sent."""
        self.renewal_reminder_sent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('renewal_reminder_sent')

    def is_set_renewal_reminder_sent(self) -> bool:
        """Check if renewal_reminder_sent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'renewal_reminder_sent' in self._pending_field_updates)

    def get_auto_renew(self) -> bool:
        """Get the value of auto_renew."""
        return self.auto_renew

    def set_auto_renew(self, value: bool):
        """Set the value of auto_renew."""
        self.auto_renew = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('auto_renew')

    def is_set_auto_renew(self) -> bool:
        """Check if auto_renew was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'auto_renew' in self._pending_field_updates)

    def get_notes(self) -> str:
        """Get the value of notes."""
        return self.notes

    def set_notes(self, value: str):
        """Set the value of notes."""
        self.notes = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('notes')

    def is_set_notes(self) -> bool:
        """Check if notes was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'notes' in self._pending_field_updates)

    def get_metadata(self) -> str:
        """Get the value of metadata."""
        return self.metadata

    def set_metadata(self, value: str):
        """Set the value of metadata."""
        self.metadata = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('metadata')

    def is_set_metadata(self) -> bool:
        """Check if metadata was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'metadata' in self._pending_field_updates)

    def get_license_payments(self) -> 'List[LicensePayment]':
        """Get all LicensePayment objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.license_payment import LicensePayment
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.license_payment'
        try:
            module = importlib.import_module(module_name)
            LicensePayment = getattr(module, 'LicensePayment')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def license_payments(self) -> 'List[LicensePayment]':
        """Property to access LicensePayment children."""
        return self.get_license_payments()

    def get_license_usages(self) -> 'List[LicenseUsage]':
        """Get all LicenseUsage objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.license_usage import LicenseUsage
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.license_usage'
        try:
            module = importlib.import_module(module_name)
            LicenseUsage = getattr(module, 'LicenseUsage')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def license_usages(self) -> 'List[LicenseUsage]':
        """Property to access LicenseUsage children."""
        return self.get_license_usages()

    def get_license_payments(self) -> 'List[LicensePayment]':
        """Get all LicensePayment objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.license_payment import LicensePayment
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.license_payment'
        try:
            module = importlib.import_module(module_name)
            LicensePayment = getattr(module, 'LicensePayment')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def license_payments(self) -> 'List[LicensePayment]':
        """Property to access LicensePayment children."""
        return self.get_license_payments()

    def get_license_activations(self) -> 'List[LicenseActivation]':
        """Get all LicenseActivation objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.license_activation import LicenseActivation
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.license_activation'
        try:
            module = importlib.import_module(module_name)
            LicenseActivation = getattr(module, 'LicenseActivation')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def license_activations(self) -> 'List[LicenseActivation]':
        """Property to access LicenseActivation children."""
        return self.get_license_activations()

    def get_license_activations(self) -> 'List[LicenseActivation]':
        """Get all LicenseActivation objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.license_activation import LicenseActivation
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.license_activation'
        try:
            module = importlib.import_module(module_name)
            LicenseActivation = getattr(module, 'LicenseActivation')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def license_activations(self) -> 'List[LicenseActivation]':
        """Property to access LicenseActivation children."""
        return self.get_license_activations()

    def get_license_usages(self) -> 'List[LicenseUsage]':
        """Get all LicenseUsage objects that are children of this object."""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from ..objects.license_usage import LicenseUsage
        import importlib
        module_name = f'{self.__module__.rsplit(".", 1)[0]}.license_usage'
        try:
            module = importlib.import_module(module_name)
            LicenseUsage = getattr(module, 'LicenseUsage')
            children = []
            return children
        except (ImportError, AttributeError):
            return []

    @property
    def license_usages(self) -> 'List[LicenseUsage]':
        """Property to access LicenseUsage children."""
        return self.get_license_usages()


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
        return cls(name="", uuid=None, fq_name=None, parent_uuid=None, display_name=None, description=None, created_by=None, created_at=None, updated_at=None, key=None, license_type=None, admin_email=None, tier=None, offline_pack=None, status=None, issued_at=None, expires_at=None, grace_period_days=None, billing_cycle=None, features=None, included_projects=None, included_tenants=None, included_servers=None, max_projects=None, max_tenants=None, max_servers=None, per_extra_project=None, per_extra_100_tenants=None, per_extra_server=None, ai_agent_enabled=None, ai_agent_included_tenants=None, ai_agent_max_tenants=None, per_extra_100_ai_tenants=None, discount_percent=None, discount_base_percent=None, discount_overage_percent=None, discount_ai_percent=None, discount_code=None, discount_expires_at=None, discount_note=None, hardware_ids=None, signature=None, public_key_version=None, stripe_customer_id=None, stripe_subscription_id=None, stripe_ai_subscription_id=None, contract_id=None, contract_start_date=None, contract_end_date=None, contract_value=None, last_heartbeat_at=None, heartbeat_failures=None, reported_projects=None, reported_tenants=None, reported_servers=None, reported_ai_tenants=None, renewal_reminder_sent=None, auto_renew=None, notes=None, metadata=None)

LicenseKey=LicenseKey
LicenseKey=LicenseKey
LicenseKey=LicenseKey
license_key=LicenseKey
