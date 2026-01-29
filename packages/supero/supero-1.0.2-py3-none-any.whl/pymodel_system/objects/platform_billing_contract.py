# File: pymodel_system/objects/platform_billing_contract.py
"""
This file was generated from the platform_billing_contract.json schema.
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

class PlatformBillingContract:
    """
    Represents a PlatformBillingContract instance.
    
    This class is auto-generated and includes:
    - Standard CRUD operations
    - Fluent API methods (when used with Supero)
    - Smart reference management with link data support
    - Parent-child hierarchy navigation
    """
    
    _OBJ_TYPE = "platform_billing_contract"
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
    'contract_number': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_number',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'contract_status': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_status',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'base_plan_code': {
        'type': 'str',
        'is_list': False,
        'json_name': 'base_plan_code',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'contract_start_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_start_date',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'contract_end_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_end_date',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'contract_term_months': {
        'type': 'int',
        'is_list': False,
        'json_name': 'contract_term_months',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'auto_renewal': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'auto_renewal',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'renewal_notice_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'renewal_notice_days',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'renewal_term_months': {
        'type': 'int',
        'is_list': False,
        'json_name': 'renewal_term_months',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'pricing_model': {
        'type': 'str',
        'is_list': False,
        'json_name': 'pricing_model',
        'original_type': 'string',
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
    'annual_contract_value_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'annual_contract_value_cents',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'monthly_base_fee_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'monthly_base_fee_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'per_unit_fee_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'per_unit_fee_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'included_units': {
        'type': 'int',
        'is_list': False,
        'json_name': 'included_units',
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
    'support_fee_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'support_fee_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'professional_services_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'professional_services_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'billing_frequency': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_frequency',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'payment_terms_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'payment_terms_days',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'payment_method': {
        'type': 'str',
        'is_list': False,
        'json_name': 'payment_method',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'custom_limits': {
        'type': 'str',
        'is_list': False,
        'json_name': 'custom_limits',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'custom_features': {
        'type': 'str',
        'is_list': True,
        'json_name': 'custom_features',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'disabled_features': {
        'type': 'str',
        'is_list': True,
        'json_name': 'disabled_features',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'custom_sla_uptime_percent': {
        'type': 'float',
        'is_list': False,
        'json_name': 'custom_sla_uptime_percent',
        'original_type': 'float',
        'mandatory': False,
        'static': False,
    },
    'custom_support_level': {
        'type': 'str',
        'is_list': False,
        'json_name': 'custom_support_level',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'custom_data_retention_days': {
        'type': 'int',
        'is_list': False,
        'json_name': 'custom_data_retention_days',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'deployment_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'deployment_type',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'deployment_region': {
        'type': 'str',
        'is_list': False,
        'json_name': 'deployment_region',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'data_residency_requirements': {
        'type': 'str',
        'is_list': True,
        'json_name': 'data_residency_requirements',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'compliance_frameworks': {
        'type': 'str',
        'is_list': True,
        'json_name': 'compliance_frameworks',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'security_requirements': {
        'type': 'str',
        'is_list': False,
        'json_name': 'security_requirements',
        'original_type': 'json',
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
    'overage_cap_percent': {
        'type': 'int',
        'is_list': False,
        'json_name': 'overage_cap_percent',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'overage_rates': {
        'type': 'str',
        'is_list': False,
        'json_name': 'overage_rates',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'legal_entity_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'legal_entity_name',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'billing_address': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_address',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'tax_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'tax_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'tax_exempt': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'tax_exempt',
        'original_type': 'bool',
        'mandatory': False,
        'static': False,
    },
    'po_number': {
        'type': 'str',
        'is_list': False,
        'json_name': 'po_number',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'po_required': {
        'type': 'bool',
        'is_list': False,
        'json_name': 'po_required',
        'original_type': 'bool',
        'mandatory': True,
        'static': False,
    },
    'primary_contact_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'primary_contact_name',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'primary_contact_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'primary_contact_email',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'primary_contact_phone': {
        'type': 'str',
        'is_list': False,
        'json_name': 'primary_contact_phone',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'primary_contact_title': {
        'type': 'str',
        'is_list': False,
        'json_name': 'primary_contact_title',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'billing_contact_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_contact_name',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'billing_contact_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_contact_email',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'technical_contact_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'technical_contact_name',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'technical_contact_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'technical_contact_email',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'executive_sponsor_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'executive_sponsor_name',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'executive_sponsor_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'executive_sponsor_email',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'sales_rep_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'sales_rep_name',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'sales_rep_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'sales_rep_email',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'customer_success_manager': {
        'type': 'str',
        'is_list': False,
        'json_name': 'customer_success_manager',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'solutions_architect': {
        'type': 'str',
        'is_list': False,
        'json_name': 'solutions_architect',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'signed_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'signed_date',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'signed_by_customer': {
        'type': 'str',
        'is_list': False,
        'json_name': 'signed_by_customer',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'signed_by_customer_title': {
        'type': 'str',
        'is_list': False,
        'json_name': 'signed_by_customer_title',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'signed_by_supero': {
        'type': 'str',
        'is_list': False,
        'json_name': 'signed_by_supero',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'contract_document_url': {
        'type': 'str',
        'is_list': False,
        'json_name': 'contract_document_url',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'sow_document_url': {
        'type': 'str',
        'is_list': False,
        'json_name': 'sow_document_url',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'amendments': {
        'type': 'str',
        'is_list': False,
        'json_name': 'amendments',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'renewal_history': {
        'type': 'str',
        'is_list': False,
        'json_name': 'renewal_history',
        'original_type': 'json',
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
    'special_terms': {
        'type': 'str',
        'is_list': False,
        'json_name': 'special_terms',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'termination_clause': {
        'type': 'str',
        'is_list': False,
        'json_name': 'termination_clause',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'crm_opportunity_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'crm_opportunity_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'crm_account_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'crm_account_id',
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
        'contract_term_months': {
            'min-value': 1,
            'type': 'integer',
        },
        'renewal_notice_days': {
            'min-value': 0,
            'type': 'integer',
        },
        'annual_contract_value_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'monthly_base_fee_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'per_unit_fee_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'included_units': {
            'min-value': 0,
            'type': 'integer',
        },
        'setup_fee_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'support_fee_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'professional_services_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'payment_terms_days': {
            'min-value': 0,
            'type': 'integer',
        },
        'custom_sla_uptime_percent': {
            'min-value': 0,
            'max-value': 100,
            'type': 'float',
        },
        'custom_data_retention_days': {
            'min-value': -1,
            'type': 'integer',
        },
        'overage_cap_percent': {
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
        contract_number: Optional[str] = None,
        contract_status: Optional[str] = None,
        base_plan_code: Optional[str] = None,
        contract_start_date: Optional[str] = None,
        contract_end_date: Optional[str] = None,
        contract_term_months: Optional[int] = None,
        auto_renewal: Optional[bool] = None,
        renewal_notice_days: Optional[int] = None,
        renewal_term_months: Optional[int] = None,
        pricing_model: Optional[str] = None,
        pricing_currency: Optional[str] = None,
        annual_contract_value_cents: Optional[int] = None,
        monthly_base_fee_cents: Optional[int] = None,
        per_unit_fee_cents: Optional[int] = None,
        included_units: Optional[int] = None,
        setup_fee_cents: Optional[int] = None,
        support_fee_cents: Optional[int] = None,
        professional_services_cents: Optional[int] = None,
        billing_frequency: Optional[str] = None,
        payment_terms_days: Optional[int] = None,
        payment_method: Optional[str] = None,
        custom_limits: Optional[str] = None,
        custom_features: Optional[List[str]] = None,
        disabled_features: Optional[List[str]] = None,
        custom_sla_uptime_percent: Optional[float] = None,
        custom_support_level: Optional[str] = None,
        custom_data_retention_days: Optional[int] = None,
        deployment_type: Optional[str] = None,
        deployment_region: Optional[str] = None,
        data_residency_requirements: Optional[List[str]] = None,
        compliance_frameworks: Optional[List[str]] = None,
        security_requirements: Optional[str] = None,
        overage_handling: Optional[str] = None,
        overage_cap_percent: Optional[int] = None,
        overage_rates: Optional[str] = None,
        legal_entity_name: Optional[str] = None,
        billing_address: Optional[str] = None,
        tax_id: Optional[str] = None,
        tax_exempt: Optional[bool] = None,
        po_number: Optional[str] = None,
        po_required: Optional[bool] = None,
        primary_contact_name: Optional[str] = None,
        primary_contact_email: Optional[str] = None,
        primary_contact_phone: Optional[str] = None,
        primary_contact_title: Optional[str] = None,
        billing_contact_name: Optional[str] = None,
        billing_contact_email: Optional[str] = None,
        technical_contact_name: Optional[str] = None,
        technical_contact_email: Optional[str] = None,
        executive_sponsor_name: Optional[str] = None,
        executive_sponsor_email: Optional[str] = None,
        sales_rep_name: Optional[str] = None,
        sales_rep_email: Optional[str] = None,
        customer_success_manager: Optional[str] = None,
        solutions_architect: Optional[str] = None,
        signed_date: Optional[str] = None,
        signed_by_customer: Optional[str] = None,
        signed_by_customer_title: Optional[str] = None,
        signed_by_supero: Optional[str] = None,
        contract_document_url: Optional[str] = None,
        sow_document_url: Optional[str] = None,
        amendments: Optional[str] = None,
        renewal_history: Optional[str] = None,
        notes: Optional[str] = None,
        special_terms: Optional[str] = None,
        termination_clause: Optional[str] = None,
        crm_opportunity_id: Optional[str] = None,
        crm_account_id: Optional[str] = None
    ):
        # Set initialization flag to prevent tracking during __init__
        self._initializing = True
        
        self.obj_type = "platform_billing_contract"
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
    'contract_number': 'contract_number',
    'contract_status': 'contract_status',
    'base_plan_code': 'base_plan_code',
    'contract_start_date': 'contract_start_date',
    'contract_end_date': 'contract_end_date',
    'contract_term_months': 'contract_term_months',
    'auto_renewal': 'auto_renewal',
    'renewal_notice_days': 'renewal_notice_days',
    'renewal_term_months': 'renewal_term_months',
    'pricing_model': 'pricing_model',
    'pricing_currency': 'pricing_currency',
    'annual_contract_value_cents': 'annual_contract_value_cents',
    'monthly_base_fee_cents': 'monthly_base_fee_cents',
    'per_unit_fee_cents': 'per_unit_fee_cents',
    'included_units': 'included_units',
    'setup_fee_cents': 'setup_fee_cents',
    'support_fee_cents': 'support_fee_cents',
    'professional_services_cents': 'professional_services_cents',
    'billing_frequency': 'billing_frequency',
    'payment_terms_days': 'payment_terms_days',
    'payment_method': 'payment_method',
    'custom_limits': 'custom_limits',
    'custom_features': 'custom_features',
    'disabled_features': 'disabled_features',
    'custom_sla_uptime_percent': 'custom_sla_uptime_percent',
    'custom_support_level': 'custom_support_level',
    'custom_data_retention_days': 'custom_data_retention_days',
    'deployment_type': 'deployment_type',
    'deployment_region': 'deployment_region',
    'data_residency_requirements': 'data_residency_requirements',
    'compliance_frameworks': 'compliance_frameworks',
    'security_requirements': 'security_requirements',
    'overage_handling': 'overage_handling',
    'overage_cap_percent': 'overage_cap_percent',
    'overage_rates': 'overage_rates',
    'legal_entity_name': 'legal_entity_name',
    'billing_address': 'billing_address',
    'tax_id': 'tax_id',
    'tax_exempt': 'tax_exempt',
    'po_number': 'po_number',
    'po_required': 'po_required',
    'primary_contact_name': 'primary_contact_name',
    'primary_contact_email': 'primary_contact_email',
    'primary_contact_phone': 'primary_contact_phone',
    'primary_contact_title': 'primary_contact_title',
    'billing_contact_name': 'billing_contact_name',
    'billing_contact_email': 'billing_contact_email',
    'technical_contact_name': 'technical_contact_name',
    'technical_contact_email': 'technical_contact_email',
    'executive_sponsor_name': 'executive_sponsor_name',
    'executive_sponsor_email': 'executive_sponsor_email',
    'sales_rep_name': 'sales_rep_name',
    'sales_rep_email': 'sales_rep_email',
    'customer_success_manager': 'customer_success_manager',
    'solutions_architect': 'solutions_architect',
    'signed_date': 'signed_date',
    'signed_by_customer': 'signed_by_customer',
    'signed_by_customer_title': 'signed_by_customer_title',
    'signed_by_supero': 'signed_by_supero',
    'contract_document_url': 'contract_document_url',
    'sow_document_url': 'sow_document_url',
    'amendments': 'amendments',
    'renewal_history': 'renewal_history',
    'notes': 'notes',
    'special_terms': 'special_terms',
    'termination_clause': 'termination_clause',
    'crm_opportunity_id': 'crm_opportunity_id',
    'crm_account_id': 'crm_account_id'
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
    'contract_number': 'contract_number',
    'contract_status': 'contract_status',
    'base_plan_code': 'base_plan_code',
    'contract_start_date': 'contract_start_date',
    'contract_end_date': 'contract_end_date',
    'contract_term_months': 'contract_term_months',
    'auto_renewal': 'auto_renewal',
    'renewal_notice_days': 'renewal_notice_days',
    'renewal_term_months': 'renewal_term_months',
    'pricing_model': 'pricing_model',
    'pricing_currency': 'pricing_currency',
    'annual_contract_value_cents': 'annual_contract_value_cents',
    'monthly_base_fee_cents': 'monthly_base_fee_cents',
    'per_unit_fee_cents': 'per_unit_fee_cents',
    'included_units': 'included_units',
    'setup_fee_cents': 'setup_fee_cents',
    'support_fee_cents': 'support_fee_cents',
    'professional_services_cents': 'professional_services_cents',
    'billing_frequency': 'billing_frequency',
    'payment_terms_days': 'payment_terms_days',
    'payment_method': 'payment_method',
    'custom_limits': 'custom_limits',
    'custom_features': 'custom_features',
    'disabled_features': 'disabled_features',
    'custom_sla_uptime_percent': 'custom_sla_uptime_percent',
    'custom_support_level': 'custom_support_level',
    'custom_data_retention_days': 'custom_data_retention_days',
    'deployment_type': 'deployment_type',
    'deployment_region': 'deployment_region',
    'data_residency_requirements': 'data_residency_requirements',
    'compliance_frameworks': 'compliance_frameworks',
    'security_requirements': 'security_requirements',
    'overage_handling': 'overage_handling',
    'overage_cap_percent': 'overage_cap_percent',
    'overage_rates': 'overage_rates',
    'legal_entity_name': 'legal_entity_name',
    'billing_address': 'billing_address',
    'tax_id': 'tax_id',
    'tax_exempt': 'tax_exempt',
    'po_number': 'po_number',
    'po_required': 'po_required',
    'primary_contact_name': 'primary_contact_name',
    'primary_contact_email': 'primary_contact_email',
    'primary_contact_phone': 'primary_contact_phone',
    'primary_contact_title': 'primary_contact_title',
    'billing_contact_name': 'billing_contact_name',
    'billing_contact_email': 'billing_contact_email',
    'technical_contact_name': 'technical_contact_name',
    'technical_contact_email': 'technical_contact_email',
    'executive_sponsor_name': 'executive_sponsor_name',
    'executive_sponsor_email': 'executive_sponsor_email',
    'sales_rep_name': 'sales_rep_name',
    'sales_rep_email': 'sales_rep_email',
    'customer_success_manager': 'customer_success_manager',
    'solutions_architect': 'solutions_architect',
    'signed_date': 'signed_date',
    'signed_by_customer': 'signed_by_customer',
    'signed_by_customer_title': 'signed_by_customer_title',
    'signed_by_supero': 'signed_by_supero',
    'contract_document_url': 'contract_document_url',
    'sow_document_url': 'sow_document_url',
    'amendments': 'amendments',
    'renewal_history': 'renewal_history',
    'notes': 'notes',
    'special_terms': 'special_terms',
    'termination_clause': 'termination_clause',
    'crm_opportunity_id': 'crm_opportunity_id',
    'crm_account_id': 'crm_account_id'
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
        self.contract_number = contract_number
        self.contract_status = contract_status
        self.base_plan_code = base_plan_code
        self.contract_start_date = contract_start_date
        self.contract_end_date = contract_end_date
        self.contract_term_months = contract_term_months
        self.auto_renewal = auto_renewal
        self.renewal_notice_days = renewal_notice_days
        self.renewal_term_months = renewal_term_months
        self.pricing_model = pricing_model
        self.pricing_currency = pricing_currency
        self.annual_contract_value_cents = annual_contract_value_cents
        self.monthly_base_fee_cents = monthly_base_fee_cents
        self.per_unit_fee_cents = per_unit_fee_cents
        self.included_units = included_units
        self.setup_fee_cents = setup_fee_cents
        self.support_fee_cents = support_fee_cents
        self.professional_services_cents = professional_services_cents
        self.billing_frequency = billing_frequency
        self.payment_terms_days = payment_terms_days
        self.payment_method = payment_method
        self.custom_limits = custom_limits
        self.custom_features = custom_features if custom_features is not None else []
        self.disabled_features = disabled_features if disabled_features is not None else []
        self.custom_sla_uptime_percent = custom_sla_uptime_percent
        self.custom_support_level = custom_support_level
        self.custom_data_retention_days = custom_data_retention_days
        self.deployment_type = deployment_type
        self.deployment_region = deployment_region
        self.data_residency_requirements = data_residency_requirements if data_residency_requirements is not None else []
        self.compliance_frameworks = compliance_frameworks if compliance_frameworks is not None else []
        self.security_requirements = security_requirements
        self.overage_handling = overage_handling
        self.overage_cap_percent = overage_cap_percent
        self.overage_rates = overage_rates
        self.legal_entity_name = legal_entity_name
        self.billing_address = billing_address
        self.tax_id = tax_id
        self.tax_exempt = tax_exempt
        self.po_number = po_number
        self.po_required = po_required
        self.primary_contact_name = primary_contact_name
        self.primary_contact_email = primary_contact_email
        self.primary_contact_phone = primary_contact_phone
        self.primary_contact_title = primary_contact_title
        self.billing_contact_name = billing_contact_name
        self.billing_contact_email = billing_contact_email
        self.technical_contact_name = technical_contact_name
        self.technical_contact_email = technical_contact_email
        self.executive_sponsor_name = executive_sponsor_name
        self.executive_sponsor_email = executive_sponsor_email
        self.sales_rep_name = sales_rep_name
        self.sales_rep_email = sales_rep_email
        self.customer_success_manager = customer_success_manager
        self.solutions_architect = solutions_architect
        self.signed_date = signed_date
        self.signed_by_customer = signed_by_customer
        self.signed_by_customer_title = signed_by_customer_title
        self.signed_by_supero = signed_by_supero
        self.contract_document_url = contract_document_url
        self.sow_document_url = sow_document_url
        self.amendments = amendments
        self.renewal_history = renewal_history
        self.notes = notes
        self.special_terms = special_terms
        self.termination_clause = termination_clause
        self.crm_opportunity_id = crm_opportunity_id
        self.crm_account_id = crm_account_id


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
        self._pending_field_updates.add('contract_number')
        self._pending_field_updates.add('contract_status')
        self._pending_field_updates.add('base_plan_code')
        self._pending_field_updates.add('contract_start_date')
        self._pending_field_updates.add('contract_end_date')
        self._pending_field_updates.add('contract_term_months')
        self._pending_field_updates.add('auto_renewal')
        if renewal_notice_days != 30:
            self._pending_field_updates.add('renewal_notice_days')
        if renewal_term_months != 12:
            self._pending_field_updates.add('renewal_term_months')
        self._pending_field_updates.add('pricing_model')
        self._pending_field_updates.add('pricing_currency')
        self._pending_field_updates.add('annual_contract_value_cents')
        if monthly_base_fee_cents is not None:
            self._pending_field_updates.add('monthly_base_fee_cents')
        if per_unit_fee_cents is not None:
            self._pending_field_updates.add('per_unit_fee_cents')
        if included_units is not None:
            self._pending_field_updates.add('included_units')
        if setup_fee_cents != 0:
            self._pending_field_updates.add('setup_fee_cents')
        if support_fee_cents != 0:
            self._pending_field_updates.add('support_fee_cents')
        if professional_services_cents != 0:
            self._pending_field_updates.add('professional_services_cents')
        self._pending_field_updates.add('billing_frequency')
        self._pending_field_updates.add('payment_terms_days')
        self._pending_field_updates.add('payment_method')
        if custom_limits is not None:
            self._pending_field_updates.add('custom_limits')
        if custom_features is not None:
            self._pending_field_updates.add('custom_features')
        if disabled_features is not None:
            self._pending_field_updates.add('disabled_features')
        if custom_sla_uptime_percent is not None:
            self._pending_field_updates.add('custom_sla_uptime_percent')
        if custom_support_level is not None:
            self._pending_field_updates.add('custom_support_level')
        if custom_data_retention_days is not None:
            self._pending_field_updates.add('custom_data_retention_days')
        self._pending_field_updates.add('deployment_type')
        if deployment_region is not None:
            self._pending_field_updates.add('deployment_region')
        if data_residency_requirements is not None:
            self._pending_field_updates.add('data_residency_requirements')
        if compliance_frameworks is not None:
            self._pending_field_updates.add('compliance_frameworks')
        if security_requirements is not None:
            self._pending_field_updates.add('security_requirements')
        self._pending_field_updates.add('overage_handling')
        if overage_cap_percent is not None:
            self._pending_field_updates.add('overage_cap_percent')
        if overage_rates is not None:
            self._pending_field_updates.add('overage_rates')
        self._pending_field_updates.add('legal_entity_name')
        if billing_address is not None:
            self._pending_field_updates.add('billing_address')
        if tax_id is not None:
            self._pending_field_updates.add('tax_id')
        if tax_exempt != False:
            self._pending_field_updates.add('tax_exempt')
        if po_number is not None:
            self._pending_field_updates.add('po_number')
        self._pending_field_updates.add('po_required')
        self._pending_field_updates.add('primary_contact_name')
        self._pending_field_updates.add('primary_contact_email')
        if primary_contact_phone is not None:
            self._pending_field_updates.add('primary_contact_phone')
        if primary_contact_title is not None:
            self._pending_field_updates.add('primary_contact_title')
        if billing_contact_name is not None:
            self._pending_field_updates.add('billing_contact_name')
        if billing_contact_email is not None:
            self._pending_field_updates.add('billing_contact_email')
        if technical_contact_name is not None:
            self._pending_field_updates.add('technical_contact_name')
        if technical_contact_email is not None:
            self._pending_field_updates.add('technical_contact_email')
        if executive_sponsor_name is not None:
            self._pending_field_updates.add('executive_sponsor_name')
        if executive_sponsor_email is not None:
            self._pending_field_updates.add('executive_sponsor_email')
        if sales_rep_name is not None:
            self._pending_field_updates.add('sales_rep_name')
        if sales_rep_email is not None:
            self._pending_field_updates.add('sales_rep_email')
        if customer_success_manager is not None:
            self._pending_field_updates.add('customer_success_manager')
        if solutions_architect is not None:
            self._pending_field_updates.add('solutions_architect')
        if signed_date is not None:
            self._pending_field_updates.add('signed_date')
        if signed_by_customer is not None:
            self._pending_field_updates.add('signed_by_customer')
        if signed_by_customer_title is not None:
            self._pending_field_updates.add('signed_by_customer_title')
        if signed_by_supero is not None:
            self._pending_field_updates.add('signed_by_supero')
        if contract_document_url is not None:
            self._pending_field_updates.add('contract_document_url')
        if sow_document_url is not None:
            self._pending_field_updates.add('sow_document_url')
        if amendments is not None:
            self._pending_field_updates.add('amendments')
        if renewal_history is not None:
            self._pending_field_updates.add('renewal_history')
        if notes is not None:
            self._pending_field_updates.add('notes')
        if special_terms is not None:
            self._pending_field_updates.add('special_terms')
        if termination_clause is not None:
            self._pending_field_updates.add('termination_clause')
        if crm_opportunity_id is not None:
            self._pending_field_updates.add('crm_opportunity_id')
        if crm_account_id is not None:
            self._pending_field_updates.add('crm_account_id')
        
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

    def get_contract_number(self) -> str:
        """Get the value of contract_number."""
        return self.contract_number

    def set_contract_number(self, value: str):
        """Set the value of contract_number."""
        self.contract_number = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_number')

    def is_set_contract_number(self) -> bool:
        """Check if contract_number was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_number' in self._pending_field_updates)

    def get_contract_status(self) -> str:
        """Get the value of contract_status."""
        return self.contract_status

    def set_contract_status(self, value: str):
        """Set the value of contract_status."""
        self.contract_status = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_status')

    def is_set_contract_status(self) -> bool:
        """Check if contract_status was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_status' in self._pending_field_updates)

    def get_base_plan_code(self) -> str:
        """Get the value of base_plan_code."""
        return self.base_plan_code

    def set_base_plan_code(self, value: str):
        """Set the value of base_plan_code."""
        self.base_plan_code = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('base_plan_code')

    def is_set_base_plan_code(self) -> bool:
        """Check if base_plan_code was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'base_plan_code' in self._pending_field_updates)

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

    def get_contract_term_months(self) -> int:
        """Get the value of contract_term_months."""
        return self.contract_term_months

    def set_contract_term_months(self, value: int):
        """Set the value of contract_term_months."""
        self.contract_term_months = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_term_months')

    def is_set_contract_term_months(self) -> bool:
        """Check if contract_term_months was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_term_months' in self._pending_field_updates)

    def get_auto_renewal(self) -> bool:
        """Get the value of auto_renewal."""
        return self.auto_renewal

    def set_auto_renewal(self, value: bool):
        """Set the value of auto_renewal."""
        self.auto_renewal = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('auto_renewal')

    def is_set_auto_renewal(self) -> bool:
        """Check if auto_renewal was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'auto_renewal' in self._pending_field_updates)

    def get_renewal_notice_days(self) -> int:
        """Get the value of renewal_notice_days."""
        return self.renewal_notice_days

    def set_renewal_notice_days(self, value: int):
        """Set the value of renewal_notice_days."""
        self.renewal_notice_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('renewal_notice_days')

    def is_set_renewal_notice_days(self) -> bool:
        """Check if renewal_notice_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'renewal_notice_days' in self._pending_field_updates)

    def get_renewal_term_months(self) -> int:
        """Get the value of renewal_term_months."""
        return self.renewal_term_months

    def set_renewal_term_months(self, value: int):
        """Set the value of renewal_term_months."""
        self.renewal_term_months = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('renewal_term_months')

    def is_set_renewal_term_months(self) -> bool:
        """Check if renewal_term_months was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'renewal_term_months' in self._pending_field_updates)

    def get_pricing_model(self) -> str:
        """Get the value of pricing_model."""
        return self.pricing_model

    def set_pricing_model(self, value: str):
        """Set the value of pricing_model."""
        self.pricing_model = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('pricing_model')

    def is_set_pricing_model(self) -> bool:
        """Check if pricing_model was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'pricing_model' in self._pending_field_updates)

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

    def get_annual_contract_value_cents(self) -> int:
        """Get the value of annual_contract_value_cents."""
        return self.annual_contract_value_cents

    def set_annual_contract_value_cents(self, value: int):
        """Set the value of annual_contract_value_cents."""
        self.annual_contract_value_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('annual_contract_value_cents')

    def is_set_annual_contract_value_cents(self) -> bool:
        """Check if annual_contract_value_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'annual_contract_value_cents' in self._pending_field_updates)

    def get_monthly_base_fee_cents(self) -> int:
        """Get the value of monthly_base_fee_cents."""
        return self.monthly_base_fee_cents

    def set_monthly_base_fee_cents(self, value: int):
        """Set the value of monthly_base_fee_cents."""
        self.monthly_base_fee_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('monthly_base_fee_cents')

    def is_set_monthly_base_fee_cents(self) -> bool:
        """Check if monthly_base_fee_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'monthly_base_fee_cents' in self._pending_field_updates)

    def get_per_unit_fee_cents(self) -> int:
        """Get the value of per_unit_fee_cents."""
        return self.per_unit_fee_cents

    def set_per_unit_fee_cents(self, value: int):
        """Set the value of per_unit_fee_cents."""
        self.per_unit_fee_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('per_unit_fee_cents')

    def is_set_per_unit_fee_cents(self) -> bool:
        """Check if per_unit_fee_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'per_unit_fee_cents' in self._pending_field_updates)

    def get_included_units(self) -> int:
        """Get the value of included_units."""
        return self.included_units

    def set_included_units(self, value: int):
        """Set the value of included_units."""
        self.included_units = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('included_units')

    def is_set_included_units(self) -> bool:
        """Check if included_units was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'included_units' in self._pending_field_updates)

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

    def get_support_fee_cents(self) -> int:
        """Get the value of support_fee_cents."""
        return self.support_fee_cents

    def set_support_fee_cents(self, value: int):
        """Set the value of support_fee_cents."""
        self.support_fee_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('support_fee_cents')

    def is_set_support_fee_cents(self) -> bool:
        """Check if support_fee_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'support_fee_cents' in self._pending_field_updates)

    def get_professional_services_cents(self) -> int:
        """Get the value of professional_services_cents."""
        return self.professional_services_cents

    def set_professional_services_cents(self, value: int):
        """Set the value of professional_services_cents."""
        self.professional_services_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('professional_services_cents')

    def is_set_professional_services_cents(self) -> bool:
        """Check if professional_services_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'professional_services_cents' in self._pending_field_updates)

    def get_billing_frequency(self) -> str:
        """Get the value of billing_frequency."""
        return self.billing_frequency

    def set_billing_frequency(self, value: str):
        """Set the value of billing_frequency."""
        self.billing_frequency = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_frequency')

    def is_set_billing_frequency(self) -> bool:
        """Check if billing_frequency was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_frequency' in self._pending_field_updates)

    def get_payment_terms_days(self) -> int:
        """Get the value of payment_terms_days."""
        return self.payment_terms_days

    def set_payment_terms_days(self, value: int):
        """Set the value of payment_terms_days."""
        self.payment_terms_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('payment_terms_days')

    def is_set_payment_terms_days(self) -> bool:
        """Check if payment_terms_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'payment_terms_days' in self._pending_field_updates)

    def get_payment_method(self) -> str:
        """Get the value of payment_method."""
        return self.payment_method

    def set_payment_method(self, value: str):
        """Set the value of payment_method."""
        self.payment_method = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('payment_method')

    def is_set_payment_method(self) -> bool:
        """Check if payment_method was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'payment_method' in self._pending_field_updates)

    def get_custom_limits(self) -> str:
        """Get the value of custom_limits."""
        return self.custom_limits

    def set_custom_limits(self, value: str):
        """Set the value of custom_limits."""
        self.custom_limits = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('custom_limits')

    def is_set_custom_limits(self) -> bool:
        """Check if custom_limits was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'custom_limits' in self._pending_field_updates)

    def get_custom_features(self) -> List[str]:
        """Get the value of custom_features."""
        return self.custom_features

    def set_custom_features(self, value: List[str]):
        """Set the value of custom_features."""
        self.custom_features = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('custom_features')

    def add_custom_features(self, item: str):
        """Add an item to custom_features."""
        if self.custom_features is None:
            self.custom_features = []
        self.custom_features.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('custom_features')

    def del_custom_features(self, item: str):
        """Remove an item from custom_features."""
        if self.custom_features and item in self.custom_features:
            self.custom_features.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('custom_features')

    def del_custom_features_by_index(self, index: int):
        """Remove an item from custom_features by index."""
        if self.custom_features and 0 <= index < len(self.custom_features):
            del self.custom_features[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('custom_features')

    def is_set_custom_features(self) -> bool:
        """Check if custom_features was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'custom_features' in self._pending_field_updates)

    def get_disabled_features(self) -> List[str]:
        """Get the value of disabled_features."""
        return self.disabled_features

    def set_disabled_features(self, value: List[str]):
        """Set the value of disabled_features."""
        self.disabled_features = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('disabled_features')

    def add_disabled_features(self, item: str):
        """Add an item to disabled_features."""
        if self.disabled_features is None:
            self.disabled_features = []
        self.disabled_features.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('disabled_features')

    def del_disabled_features(self, item: str):
        """Remove an item from disabled_features."""
        if self.disabled_features and item in self.disabled_features:
            self.disabled_features.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('disabled_features')

    def del_disabled_features_by_index(self, index: int):
        """Remove an item from disabled_features by index."""
        if self.disabled_features and 0 <= index < len(self.disabled_features):
            del self.disabled_features[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('disabled_features')

    def is_set_disabled_features(self) -> bool:
        """Check if disabled_features was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'disabled_features' in self._pending_field_updates)

    def get_custom_sla_uptime_percent(self) -> float:
        """Get the value of custom_sla_uptime_percent."""
        return self.custom_sla_uptime_percent

    def set_custom_sla_uptime_percent(self, value: float):
        """Set the value of custom_sla_uptime_percent."""
        self.custom_sla_uptime_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('custom_sla_uptime_percent')

    def is_set_custom_sla_uptime_percent(self) -> bool:
        """Check if custom_sla_uptime_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'custom_sla_uptime_percent' in self._pending_field_updates)

    def get_custom_support_level(self) -> str:
        """Get the value of custom_support_level."""
        return self.custom_support_level

    def set_custom_support_level(self, value: str):
        """Set the value of custom_support_level."""
        self.custom_support_level = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('custom_support_level')

    def is_set_custom_support_level(self) -> bool:
        """Check if custom_support_level was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'custom_support_level' in self._pending_field_updates)

    def get_custom_data_retention_days(self) -> int:
        """Get the value of custom_data_retention_days."""
        return self.custom_data_retention_days

    def set_custom_data_retention_days(self, value: int):
        """Set the value of custom_data_retention_days."""
        self.custom_data_retention_days = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('custom_data_retention_days')

    def is_set_custom_data_retention_days(self) -> bool:
        """Check if custom_data_retention_days was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'custom_data_retention_days' in self._pending_field_updates)

    def get_deployment_type(self) -> str:
        """Get the value of deployment_type."""
        return self.deployment_type

    def set_deployment_type(self, value: str):
        """Set the value of deployment_type."""
        self.deployment_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('deployment_type')

    def is_set_deployment_type(self) -> bool:
        """Check if deployment_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'deployment_type' in self._pending_field_updates)

    def get_deployment_region(self) -> str:
        """Get the value of deployment_region."""
        return self.deployment_region

    def set_deployment_region(self, value: str):
        """Set the value of deployment_region."""
        self.deployment_region = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('deployment_region')

    def is_set_deployment_region(self) -> bool:
        """Check if deployment_region was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'deployment_region' in self._pending_field_updates)

    def get_data_residency_requirements(self) -> List[str]:
        """Get the value of data_residency_requirements."""
        return self.data_residency_requirements

    def set_data_residency_requirements(self, value: List[str]):
        """Set the value of data_residency_requirements."""
        self.data_residency_requirements = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('data_residency_requirements')

    def add_data_residency_requirements(self, item: str):
        """Add an item to data_residency_requirements."""
        if self.data_residency_requirements is None:
            self.data_residency_requirements = []
        self.data_residency_requirements.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('data_residency_requirements')

    def del_data_residency_requirements(self, item: str):
        """Remove an item from data_residency_requirements."""
        if self.data_residency_requirements and item in self.data_residency_requirements:
            self.data_residency_requirements.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('data_residency_requirements')

    def del_data_residency_requirements_by_index(self, index: int):
        """Remove an item from data_residency_requirements by index."""
        if self.data_residency_requirements and 0 <= index < len(self.data_residency_requirements):
            del self.data_residency_requirements[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('data_residency_requirements')

    def is_set_data_residency_requirements(self) -> bool:
        """Check if data_residency_requirements was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'data_residency_requirements' in self._pending_field_updates)

    def get_compliance_frameworks(self) -> List[str]:
        """Get the value of compliance_frameworks."""
        return self.compliance_frameworks

    def set_compliance_frameworks(self, value: List[str]):
        """Set the value of compliance_frameworks."""
        self.compliance_frameworks = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('compliance_frameworks')

    def add_compliance_frameworks(self, item: str):
        """Add an item to compliance_frameworks."""
        if self.compliance_frameworks is None:
            self.compliance_frameworks = []
        self.compliance_frameworks.append(item)
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('compliance_frameworks')

    def del_compliance_frameworks(self, item: str):
        """Remove an item from compliance_frameworks."""
        if self.compliance_frameworks and item in self.compliance_frameworks:
            self.compliance_frameworks.remove(item)
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('compliance_frameworks')

    def del_compliance_frameworks_by_index(self, index: int):
        """Remove an item from compliance_frameworks by index."""
        if self.compliance_frameworks and 0 <= index < len(self.compliance_frameworks):
            del self.compliance_frameworks[index]
            if hasattr(self, '_pending_field_updates'):
                self._pending_field_updates.add('compliance_frameworks')

    def is_set_compliance_frameworks(self) -> bool:
        """Check if compliance_frameworks was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'compliance_frameworks' in self._pending_field_updates)

    def get_security_requirements(self) -> str:
        """Get the value of security_requirements."""
        return self.security_requirements

    def set_security_requirements(self, value: str):
        """Set the value of security_requirements."""
        self.security_requirements = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('security_requirements')

    def is_set_security_requirements(self) -> bool:
        """Check if security_requirements was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'security_requirements' in self._pending_field_updates)

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

    def get_overage_cap_percent(self) -> int:
        """Get the value of overage_cap_percent."""
        return self.overage_cap_percent

    def set_overage_cap_percent(self, value: int):
        """Set the value of overage_cap_percent."""
        self.overage_cap_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_cap_percent')

    def is_set_overage_cap_percent(self) -> bool:
        """Check if overage_cap_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_cap_percent' in self._pending_field_updates)

    def get_overage_rates(self) -> str:
        """Get the value of overage_rates."""
        return self.overage_rates

    def set_overage_rates(self, value: str):
        """Set the value of overage_rates."""
        self.overage_rates = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('overage_rates')

    def is_set_overage_rates(self) -> bool:
        """Check if overage_rates was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'overage_rates' in self._pending_field_updates)

    def get_legal_entity_name(self) -> str:
        """Get the value of legal_entity_name."""
        return self.legal_entity_name

    def set_legal_entity_name(self, value: str):
        """Set the value of legal_entity_name."""
        self.legal_entity_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('legal_entity_name')

    def is_set_legal_entity_name(self) -> bool:
        """Check if legal_entity_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'legal_entity_name' in self._pending_field_updates)

    def get_billing_address(self) -> str:
        """Get the value of billing_address."""
        return self.billing_address

    def set_billing_address(self, value: str):
        """Set the value of billing_address."""
        self.billing_address = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_address')

    def is_set_billing_address(self) -> bool:
        """Check if billing_address was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_address' in self._pending_field_updates)

    def get_tax_id(self) -> str:
        """Get the value of tax_id."""
        return self.tax_id

    def set_tax_id(self, value: str):
        """Set the value of tax_id."""
        self.tax_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tax_id')

    def is_set_tax_id(self) -> bool:
        """Check if tax_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tax_id' in self._pending_field_updates)

    def get_tax_exempt(self) -> bool:
        """Get the value of tax_exempt."""
        return self.tax_exempt

    def set_tax_exempt(self, value: bool):
        """Set the value of tax_exempt."""
        self.tax_exempt = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tax_exempt')

    def is_set_tax_exempt(self) -> bool:
        """Check if tax_exempt was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tax_exempt' in self._pending_field_updates)

    def get_po_number(self) -> str:
        """Get the value of po_number."""
        return self.po_number

    def set_po_number(self, value: str):
        """Set the value of po_number."""
        self.po_number = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('po_number')

    def is_set_po_number(self) -> bool:
        """Check if po_number was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'po_number' in self._pending_field_updates)

    def get_po_required(self) -> bool:
        """Get the value of po_required."""
        return self.po_required

    def set_po_required(self, value: bool):
        """Set the value of po_required."""
        self.po_required = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('po_required')

    def is_set_po_required(self) -> bool:
        """Check if po_required was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'po_required' in self._pending_field_updates)

    def get_primary_contact_name(self) -> str:
        """Get the value of primary_contact_name."""
        return self.primary_contact_name

    def set_primary_contact_name(self, value: str):
        """Set the value of primary_contact_name."""
        self.primary_contact_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('primary_contact_name')

    def is_set_primary_contact_name(self) -> bool:
        """Check if primary_contact_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'primary_contact_name' in self._pending_field_updates)

    def get_primary_contact_email(self) -> str:
        """Get the value of primary_contact_email."""
        return self.primary_contact_email

    def set_primary_contact_email(self, value: str):
        """Set the value of primary_contact_email."""
        self.primary_contact_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('primary_contact_email')

    def is_set_primary_contact_email(self) -> bool:
        """Check if primary_contact_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'primary_contact_email' in self._pending_field_updates)

    def get_primary_contact_phone(self) -> str:
        """Get the value of primary_contact_phone."""
        return self.primary_contact_phone

    def set_primary_contact_phone(self, value: str):
        """Set the value of primary_contact_phone."""
        self.primary_contact_phone = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('primary_contact_phone')

    def is_set_primary_contact_phone(self) -> bool:
        """Check if primary_contact_phone was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'primary_contact_phone' in self._pending_field_updates)

    def get_primary_contact_title(self) -> str:
        """Get the value of primary_contact_title."""
        return self.primary_contact_title

    def set_primary_contact_title(self, value: str):
        """Set the value of primary_contact_title."""
        self.primary_contact_title = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('primary_contact_title')

    def is_set_primary_contact_title(self) -> bool:
        """Check if primary_contact_title was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'primary_contact_title' in self._pending_field_updates)

    def get_billing_contact_name(self) -> str:
        """Get the value of billing_contact_name."""
        return self.billing_contact_name

    def set_billing_contact_name(self, value: str):
        """Set the value of billing_contact_name."""
        self.billing_contact_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_contact_name')

    def is_set_billing_contact_name(self) -> bool:
        """Check if billing_contact_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_contact_name' in self._pending_field_updates)

    def get_billing_contact_email(self) -> str:
        """Get the value of billing_contact_email."""
        return self.billing_contact_email

    def set_billing_contact_email(self, value: str):
        """Set the value of billing_contact_email."""
        self.billing_contact_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_contact_email')

    def is_set_billing_contact_email(self) -> bool:
        """Check if billing_contact_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_contact_email' in self._pending_field_updates)

    def get_technical_contact_name(self) -> str:
        """Get the value of technical_contact_name."""
        return self.technical_contact_name

    def set_technical_contact_name(self, value: str):
        """Set the value of technical_contact_name."""
        self.technical_contact_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('technical_contact_name')

    def is_set_technical_contact_name(self) -> bool:
        """Check if technical_contact_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'technical_contact_name' in self._pending_field_updates)

    def get_technical_contact_email(self) -> str:
        """Get the value of technical_contact_email."""
        return self.technical_contact_email

    def set_technical_contact_email(self, value: str):
        """Set the value of technical_contact_email."""
        self.technical_contact_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('technical_contact_email')

    def is_set_technical_contact_email(self) -> bool:
        """Check if technical_contact_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'technical_contact_email' in self._pending_field_updates)

    def get_executive_sponsor_name(self) -> str:
        """Get the value of executive_sponsor_name."""
        return self.executive_sponsor_name

    def set_executive_sponsor_name(self, value: str):
        """Set the value of executive_sponsor_name."""
        self.executive_sponsor_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('executive_sponsor_name')

    def is_set_executive_sponsor_name(self) -> bool:
        """Check if executive_sponsor_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'executive_sponsor_name' in self._pending_field_updates)

    def get_executive_sponsor_email(self) -> str:
        """Get the value of executive_sponsor_email."""
        return self.executive_sponsor_email

    def set_executive_sponsor_email(self, value: str):
        """Set the value of executive_sponsor_email."""
        self.executive_sponsor_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('executive_sponsor_email')

    def is_set_executive_sponsor_email(self) -> bool:
        """Check if executive_sponsor_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'executive_sponsor_email' in self._pending_field_updates)

    def get_sales_rep_name(self) -> str:
        """Get the value of sales_rep_name."""
        return self.sales_rep_name

    def set_sales_rep_name(self, value: str):
        """Set the value of sales_rep_name."""
        self.sales_rep_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sales_rep_name')

    def is_set_sales_rep_name(self) -> bool:
        """Check if sales_rep_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sales_rep_name' in self._pending_field_updates)

    def get_sales_rep_email(self) -> str:
        """Get the value of sales_rep_email."""
        return self.sales_rep_email

    def set_sales_rep_email(self, value: str):
        """Set the value of sales_rep_email."""
        self.sales_rep_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sales_rep_email')

    def is_set_sales_rep_email(self) -> bool:
        """Check if sales_rep_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sales_rep_email' in self._pending_field_updates)

    def get_customer_success_manager(self) -> str:
        """Get the value of customer_success_manager."""
        return self.customer_success_manager

    def set_customer_success_manager(self, value: str):
        """Set the value of customer_success_manager."""
        self.customer_success_manager = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('customer_success_manager')

    def is_set_customer_success_manager(self) -> bool:
        """Check if customer_success_manager was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'customer_success_manager' in self._pending_field_updates)

    def get_solutions_architect(self) -> str:
        """Get the value of solutions_architect."""
        return self.solutions_architect

    def set_solutions_architect(self, value: str):
        """Set the value of solutions_architect."""
        self.solutions_architect = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('solutions_architect')

    def is_set_solutions_architect(self) -> bool:
        """Check if solutions_architect was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'solutions_architect' in self._pending_field_updates)

    def get_signed_date(self) -> str:
        """Get the value of signed_date."""
        return self.signed_date

    def set_signed_date(self, value: str):
        """Set the value of signed_date."""
        self.signed_date = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('signed_date')

    def is_set_signed_date(self) -> bool:
        """Check if signed_date was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'signed_date' in self._pending_field_updates)

    def get_signed_by_customer(self) -> str:
        """Get the value of signed_by_customer."""
        return self.signed_by_customer

    def set_signed_by_customer(self, value: str):
        """Set the value of signed_by_customer."""
        self.signed_by_customer = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('signed_by_customer')

    def is_set_signed_by_customer(self) -> bool:
        """Check if signed_by_customer was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'signed_by_customer' in self._pending_field_updates)

    def get_signed_by_customer_title(self) -> str:
        """Get the value of signed_by_customer_title."""
        return self.signed_by_customer_title

    def set_signed_by_customer_title(self, value: str):
        """Set the value of signed_by_customer_title."""
        self.signed_by_customer_title = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('signed_by_customer_title')

    def is_set_signed_by_customer_title(self) -> bool:
        """Check if signed_by_customer_title was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'signed_by_customer_title' in self._pending_field_updates)

    def get_signed_by_supero(self) -> str:
        """Get the value of signed_by_supero."""
        return self.signed_by_supero

    def set_signed_by_supero(self, value: str):
        """Set the value of signed_by_supero."""
        self.signed_by_supero = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('signed_by_supero')

    def is_set_signed_by_supero(self) -> bool:
        """Check if signed_by_supero was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'signed_by_supero' in self._pending_field_updates)

    def get_contract_document_url(self) -> str:
        """Get the value of contract_document_url."""
        return self.contract_document_url

    def set_contract_document_url(self, value: str):
        """Set the value of contract_document_url."""
        self.contract_document_url = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('contract_document_url')

    def is_set_contract_document_url(self) -> bool:
        """Check if contract_document_url was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'contract_document_url' in self._pending_field_updates)

    def get_sow_document_url(self) -> str:
        """Get the value of sow_document_url."""
        return self.sow_document_url

    def set_sow_document_url(self, value: str):
        """Set the value of sow_document_url."""
        self.sow_document_url = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('sow_document_url')

    def is_set_sow_document_url(self) -> bool:
        """Check if sow_document_url was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'sow_document_url' in self._pending_field_updates)

    def get_amendments(self) -> str:
        """Get the value of amendments."""
        return self.amendments

    def set_amendments(self, value: str):
        """Set the value of amendments."""
        self.amendments = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('amendments')

    def is_set_amendments(self) -> bool:
        """Check if amendments was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'amendments' in self._pending_field_updates)

    def get_renewal_history(self) -> str:
        """Get the value of renewal_history."""
        return self.renewal_history

    def set_renewal_history(self, value: str):
        """Set the value of renewal_history."""
        self.renewal_history = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('renewal_history')

    def is_set_renewal_history(self) -> bool:
        """Check if renewal_history was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'renewal_history' in self._pending_field_updates)

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

    def get_special_terms(self) -> str:
        """Get the value of special_terms."""
        return self.special_terms

    def set_special_terms(self, value: str):
        """Set the value of special_terms."""
        self.special_terms = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('special_terms')

    def is_set_special_terms(self) -> bool:
        """Check if special_terms was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'special_terms' in self._pending_field_updates)

    def get_termination_clause(self) -> str:
        """Get the value of termination_clause."""
        return self.termination_clause

    def set_termination_clause(self, value: str):
        """Set the value of termination_clause."""
        self.termination_clause = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('termination_clause')

    def is_set_termination_clause(self) -> bool:
        """Check if termination_clause was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'termination_clause' in self._pending_field_updates)

    def get_crm_opportunity_id(self) -> str:
        """Get the value of crm_opportunity_id."""
        return self.crm_opportunity_id

    def set_crm_opportunity_id(self, value: str):
        """Set the value of crm_opportunity_id."""
        self.crm_opportunity_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('crm_opportunity_id')

    def is_set_crm_opportunity_id(self) -> bool:
        """Check if crm_opportunity_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'crm_opportunity_id' in self._pending_field_updates)

    def get_crm_account_id(self) -> str:
        """Get the value of crm_account_id."""
        return self.crm_account_id

    def set_crm_account_id(self, value: str):
        """Set the value of crm_account_id."""
        self.crm_account_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('crm_account_id')

    def is_set_crm_account_id(self) -> bool:
        """Check if crm_account_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'crm_account_id' in self._pending_field_updates)



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
        return cls(name="", uuid=None, fq_name=None, parent_uuid=None, display_name=None, description=None, created_by=None, created_at=None, updated_at=None, contract_number=None, contract_status=None, base_plan_code=None, contract_start_date=None, contract_end_date=None, contract_term_months=None, auto_renewal=None, renewal_notice_days=None, renewal_term_months=None, pricing_model=None, pricing_currency=None, annual_contract_value_cents=None, monthly_base_fee_cents=None, per_unit_fee_cents=None, included_units=None, setup_fee_cents=None, support_fee_cents=None, professional_services_cents=None, billing_frequency=None, payment_terms_days=None, payment_method=None, custom_limits=None, custom_features=None, disabled_features=None, custom_sla_uptime_percent=None, custom_support_level=None, custom_data_retention_days=None, deployment_type=None, deployment_region=None, data_residency_requirements=None, compliance_frameworks=None, security_requirements=None, overage_handling=None, overage_cap_percent=None, overage_rates=None, legal_entity_name=None, billing_address=None, tax_id=None, tax_exempt=None, po_number=None, po_required=None, primary_contact_name=None, primary_contact_email=None, primary_contact_phone=None, primary_contact_title=None, billing_contact_name=None, billing_contact_email=None, technical_contact_name=None, technical_contact_email=None, executive_sponsor_name=None, executive_sponsor_email=None, sales_rep_name=None, sales_rep_email=None, customer_success_manager=None, solutions_architect=None, signed_date=None, signed_by_customer=None, signed_by_customer_title=None, signed_by_supero=None, contract_document_url=None, sow_document_url=None, amendments=None, renewal_history=None, notes=None, special_terms=None, termination_clause=None, crm_opportunity_id=None, crm_account_id=None)

platform_billing_contract=PlatformBillingContract
PlatformBillingContract=PlatformBillingContract
PlatformBillingContract=PlatformBillingContract
platform_billing_contract=PlatformBillingContract
