# File: pymodel_system/objects/platform_billing_invoice.py
"""
This file was generated from the platform_billing_invoice.json schema.
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

class PlatformBillingInvoice:
    """
    Represents a PlatformBillingInvoice instance.
    
    This class is auto-generated and includes:
    - Standard CRUD operations
    - Fluent API methods (when used with Supero)
    - Smart reference management with link data support
    - Parent-child hierarchy navigation
    """
    
    _OBJ_TYPE = "platform_billing_invoice"
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
    'invoice_number': {
        'type': 'str',
        'is_list': False,
        'json_name': 'invoice_number',
        'original_type': 'string',
        'mandatory': True,
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
    'invoice_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'invoice_type',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'invoice_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'invoice_date',
        'original_type': 'datetime',
        'mandatory': True,
        'static': False,
    },
    'due_date': {
        'type': 'str',
        'is_list': False,
        'json_name': 'due_date',
        'original_type': 'datetime',
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
    'currency': {
        'type': 'str',
        'is_list': False,
        'json_name': 'currency',
        'original_type': 'string',
        'mandatory': True,
        'static': False,
    },
    'subtotal_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'subtotal_cents',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'discount_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'discount_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'tax_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'tax_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'tax_rate_percent': {
        'type': 'float',
        'is_list': False,
        'json_name': 'tax_rate_percent',
        'original_type': 'float',
        'mandatory': False,
        'static': False,
    },
    'total_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'total_cents',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'amount_paid_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'amount_paid_cents',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'amount_due_cents': {
        'type': 'int',
        'is_list': False,
        'json_name': 'amount_due_cents',
        'original_type': 'integer',
        'mandatory': True,
        'static': False,
    },
    'paid_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'paid_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'voided_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'voided_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'line_items': {
        'type': 'str',
        'is_list': False,
        'json_name': 'line_items',
        'original_type': 'json',
        'mandatory': False,
        'static': False,
    },
    'billing_reason': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_reason',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'plan_code': {
        'type': 'str',
        'is_list': False,
        'json_name': 'plan_code',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'stripe_invoice_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'stripe_invoice_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'stripe_payment_intent_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'stripe_payment_intent_id',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'stripe_charge_id': {
        'type': 'str',
        'is_list': False,
        'json_name': 'stripe_charge_id',
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
    'invoice_pdf_url': {
        'type': 'str',
        'is_list': False,
        'json_name': 'invoice_pdf_url',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'hosted_invoice_url': {
        'type': 'str',
        'is_list': False,
        'json_name': 'hosted_invoice_url',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'receipt_url': {
        'type': 'str',
        'is_list': False,
        'json_name': 'receipt_url',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'payment_method_type': {
        'type': 'str',
        'is_list': False,
        'json_name': 'payment_method_type',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'payment_method_last_four': {
        'type': 'str',
        'is_list': False,
        'json_name': 'payment_method_last_four',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'billing_name': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_name',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'billing_email': {
        'type': 'str',
        'is_list': False,
        'json_name': 'billing_email',
        'original_type': 'string',
        'mandatory': False,
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
    'attempt_count': {
        'type': 'int',
        'is_list': False,
        'json_name': 'attempt_count',
        'original_type': 'integer',
        'mandatory': False,
        'static': False,
    },
    'next_payment_attempt_at': {
        'type': 'str',
        'is_list': False,
        'json_name': 'next_payment_attempt_at',
        'original_type': 'datetime',
        'mandatory': False,
        'static': False,
    },
    'last_payment_error': {
        'type': 'str',
        'is_list': False,
        'json_name': 'last_payment_error',
        'original_type': 'string',
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
    'memo': {
        'type': 'str',
        'is_list': False,
        'json_name': 'memo',
        'original_type': 'string',
        'mandatory': False,
        'static': False,
    },
    'footer': {
        'type': 'str',
        'is_list': False,
        'json_name': 'footer',
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
    _end_points = []
    
    # Index definitions
    _indexes = {}

    _CONSTRAINTS = {
        'subtotal_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'discount_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'tax_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'total_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'amount_paid_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'amount_due_cents': {
            'min-value': 0,
            'type': 'integer',
        },
        'attempt_count': {
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
        invoice_number: Optional[str] = None,
        status: Optional[str] = None,
        invoice_type: Optional[str] = None,
        invoice_date: Optional[str] = None,
        due_date: Optional[str] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        currency: Optional[str] = None,
        subtotal_cents: Optional[int] = None,
        discount_cents: Optional[int] = None,
        tax_cents: Optional[int] = None,
        tax_rate_percent: Optional[float] = None,
        total_cents: Optional[int] = None,
        amount_paid_cents: Optional[int] = None,
        amount_due_cents: Optional[int] = None,
        paid_at: Optional[str] = None,
        voided_at: Optional[str] = None,
        line_items: Optional[str] = None,
        billing_reason: Optional[str] = None,
        plan_code: Optional[str] = None,
        stripe_invoice_id: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None,
        stripe_charge_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        invoice_pdf_url: Optional[str] = None,
        hosted_invoice_url: Optional[str] = None,
        receipt_url: Optional[str] = None,
        payment_method_type: Optional[str] = None,
        payment_method_last_four: Optional[str] = None,
        billing_name: Optional[str] = None,
        billing_email: Optional[str] = None,
        billing_address: Optional[str] = None,
        attempt_count: Optional[int] = None,
        next_payment_attempt_at: Optional[str] = None,
        last_payment_error: Optional[str] = None,
        notes: Optional[str] = None,
        memo: Optional[str] = None,
        footer: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        # Set initialization flag to prevent tracking during __init__
        self._initializing = True
        
        self.obj_type = "platform_billing_invoice"
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
    'invoice_number': 'invoice_number',
    'status': 'status',
    'invoice_type': 'invoice_type',
    'invoice_date': 'invoice_date',
    'due_date': 'due_date',
    'period_start': 'period_start',
    'period_end': 'period_end',
    'currency': 'currency',
    'subtotal_cents': 'subtotal_cents',
    'discount_cents': 'discount_cents',
    'tax_cents': 'tax_cents',
    'tax_rate_percent': 'tax_rate_percent',
    'total_cents': 'total_cents',
    'amount_paid_cents': 'amount_paid_cents',
    'amount_due_cents': 'amount_due_cents',
    'paid_at': 'paid_at',
    'voided_at': 'voided_at',
    'line_items': 'line_items',
    'billing_reason': 'billing_reason',
    'plan_code': 'plan_code',
    'stripe_invoice_id': 'stripe_invoice_id',
    'stripe_payment_intent_id': 'stripe_payment_intent_id',
    'stripe_charge_id': 'stripe_charge_id',
    'stripe_subscription_id': 'stripe_subscription_id',
    'invoice_pdf_url': 'invoice_pdf_url',
    'hosted_invoice_url': 'hosted_invoice_url',
    'receipt_url': 'receipt_url',
    'payment_method_type': 'payment_method_type',
    'payment_method_last_four': 'payment_method_last_four',
    'billing_name': 'billing_name',
    'billing_email': 'billing_email',
    'billing_address': 'billing_address',
    'attempt_count': 'attempt_count',
    'next_payment_attempt_at': 'next_payment_attempt_at',
    'last_payment_error': 'last_payment_error',
    'notes': 'notes',
    'memo': 'memo',
    'footer': 'footer',
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
    'invoice_number': 'invoice_number',
    'status': 'status',
    'invoice_type': 'invoice_type',
    'invoice_date': 'invoice_date',
    'due_date': 'due_date',
    'period_start': 'period_start',
    'period_end': 'period_end',
    'currency': 'currency',
    'subtotal_cents': 'subtotal_cents',
    'discount_cents': 'discount_cents',
    'tax_cents': 'tax_cents',
    'tax_rate_percent': 'tax_rate_percent',
    'total_cents': 'total_cents',
    'amount_paid_cents': 'amount_paid_cents',
    'amount_due_cents': 'amount_due_cents',
    'paid_at': 'paid_at',
    'voided_at': 'voided_at',
    'line_items': 'line_items',
    'billing_reason': 'billing_reason',
    'plan_code': 'plan_code',
    'stripe_invoice_id': 'stripe_invoice_id',
    'stripe_payment_intent_id': 'stripe_payment_intent_id',
    'stripe_charge_id': 'stripe_charge_id',
    'stripe_subscription_id': 'stripe_subscription_id',
    'invoice_pdf_url': 'invoice_pdf_url',
    'hosted_invoice_url': 'hosted_invoice_url',
    'receipt_url': 'receipt_url',
    'payment_method_type': 'payment_method_type',
    'payment_method_last_four': 'payment_method_last_four',
    'billing_name': 'billing_name',
    'billing_email': 'billing_email',
    'billing_address': 'billing_address',
    'attempt_count': 'attempt_count',
    'next_payment_attempt_at': 'next_payment_attempt_at',
    'last_payment_error': 'last_payment_error',
    'notes': 'notes',
    'memo': 'memo',
    'footer': 'footer',
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
        self.invoice_number = invoice_number
        self.status = status
        self.invoice_type = invoice_type
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.period_start = period_start
        self.period_end = period_end
        self.currency = currency
        self.subtotal_cents = subtotal_cents
        self.discount_cents = discount_cents
        self.tax_cents = tax_cents
        self.tax_rate_percent = tax_rate_percent
        self.total_cents = total_cents
        self.amount_paid_cents = amount_paid_cents
        self.amount_due_cents = amount_due_cents
        self.paid_at = paid_at
        self.voided_at = voided_at
        self.line_items = line_items
        self.billing_reason = billing_reason
        self.plan_code = plan_code
        self.stripe_invoice_id = stripe_invoice_id
        self.stripe_payment_intent_id = stripe_payment_intent_id
        self.stripe_charge_id = stripe_charge_id
        self.stripe_subscription_id = stripe_subscription_id
        self.invoice_pdf_url = invoice_pdf_url
        self.hosted_invoice_url = hosted_invoice_url
        self.receipt_url = receipt_url
        self.payment_method_type = payment_method_type
        self.payment_method_last_four = payment_method_last_four
        self.billing_name = billing_name
        self.billing_email = billing_email
        self.billing_address = billing_address
        self.attempt_count = attempt_count
        self.next_payment_attempt_at = next_payment_attempt_at
        self.last_payment_error = last_payment_error
        self.notes = notes
        self.memo = memo
        self.footer = footer
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
        self._pending_field_updates.add('invoice_number')
        self._pending_field_updates.add('status')
        self._pending_field_updates.add('invoice_type')
        self._pending_field_updates.add('invoice_date')
        self._pending_field_updates.add('due_date')
        self._pending_field_updates.add('period_start')
        self._pending_field_updates.add('period_end')
        self._pending_field_updates.add('currency')
        self._pending_field_updates.add('subtotal_cents')
        if discount_cents != 0:
            self._pending_field_updates.add('discount_cents')
        if tax_cents != 0:
            self._pending_field_updates.add('tax_cents')
        if tax_rate_percent is not None:
            self._pending_field_updates.add('tax_rate_percent')
        self._pending_field_updates.add('total_cents')
        if amount_paid_cents != 0:
            self._pending_field_updates.add('amount_paid_cents')
        self._pending_field_updates.add('amount_due_cents')
        if paid_at is not None:
            self._pending_field_updates.add('paid_at')
        if voided_at is not None:
            self._pending_field_updates.add('voided_at')
        if line_items is not None:
            self._pending_field_updates.add('line_items')
        if billing_reason is not None:
            self._pending_field_updates.add('billing_reason')
        if plan_code is not None:
            self._pending_field_updates.add('plan_code')
        if stripe_invoice_id is not None:
            self._pending_field_updates.add('stripe_invoice_id')
        if stripe_payment_intent_id is not None:
            self._pending_field_updates.add('stripe_payment_intent_id')
        if stripe_charge_id is not None:
            self._pending_field_updates.add('stripe_charge_id')
        if stripe_subscription_id is not None:
            self._pending_field_updates.add('stripe_subscription_id')
        if invoice_pdf_url is not None:
            self._pending_field_updates.add('invoice_pdf_url')
        if hosted_invoice_url is not None:
            self._pending_field_updates.add('hosted_invoice_url')
        if receipt_url is not None:
            self._pending_field_updates.add('receipt_url')
        if payment_method_type is not None:
            self._pending_field_updates.add('payment_method_type')
        if payment_method_last_four is not None:
            self._pending_field_updates.add('payment_method_last_four')
        if billing_name is not None:
            self._pending_field_updates.add('billing_name')
        if billing_email is not None:
            self._pending_field_updates.add('billing_email')
        if billing_address is not None:
            self._pending_field_updates.add('billing_address')
        if attempt_count != 0:
            self._pending_field_updates.add('attempt_count')
        if next_payment_attempt_at is not None:
            self._pending_field_updates.add('next_payment_attempt_at')
        if last_payment_error is not None:
            self._pending_field_updates.add('last_payment_error')
        if notes is not None:
            self._pending_field_updates.add('notes')
        if memo is not None:
            self._pending_field_updates.add('memo')
        if footer is not None:
            self._pending_field_updates.add('footer')
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

    def get_invoice_number(self) -> str:
        """Get the value of invoice_number."""
        return self.invoice_number

    def set_invoice_number(self, value: str):
        """Set the value of invoice_number."""
        self.invoice_number = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('invoice_number')

    def is_set_invoice_number(self) -> bool:
        """Check if invoice_number was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'invoice_number' in self._pending_field_updates)

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

    def get_invoice_type(self) -> str:
        """Get the value of invoice_type."""
        return self.invoice_type

    def set_invoice_type(self, value: str):
        """Set the value of invoice_type."""
        self.invoice_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('invoice_type')

    def is_set_invoice_type(self) -> bool:
        """Check if invoice_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'invoice_type' in self._pending_field_updates)

    def get_invoice_date(self) -> str:
        """Get the value of invoice_date."""
        return self.invoice_date

    def set_invoice_date(self, value: str):
        """Set the value of invoice_date."""
        self.invoice_date = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('invoice_date')

    def is_set_invoice_date(self) -> bool:
        """Check if invoice_date was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'invoice_date' in self._pending_field_updates)

    def get_due_date(self) -> str:
        """Get the value of due_date."""
        return self.due_date

    def set_due_date(self, value: str):
        """Set the value of due_date."""
        self.due_date = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('due_date')

    def is_set_due_date(self) -> bool:
        """Check if due_date was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'due_date' in self._pending_field_updates)

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

    def get_currency(self) -> str:
        """Get the value of currency."""
        return self.currency

    def set_currency(self, value: str):
        """Set the value of currency."""
        self.currency = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('currency')

    def is_set_currency(self) -> bool:
        """Check if currency was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'currency' in self._pending_field_updates)

    def get_subtotal_cents(self) -> int:
        """Get the value of subtotal_cents."""
        return self.subtotal_cents

    def set_subtotal_cents(self, value: int):
        """Set the value of subtotal_cents."""
        self.subtotal_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('subtotal_cents')

    def is_set_subtotal_cents(self) -> bool:
        """Check if subtotal_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'subtotal_cents' in self._pending_field_updates)

    def get_discount_cents(self) -> int:
        """Get the value of discount_cents."""
        return self.discount_cents

    def set_discount_cents(self, value: int):
        """Set the value of discount_cents."""
        self.discount_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('discount_cents')

    def is_set_discount_cents(self) -> bool:
        """Check if discount_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'discount_cents' in self._pending_field_updates)

    def get_tax_cents(self) -> int:
        """Get the value of tax_cents."""
        return self.tax_cents

    def set_tax_cents(self, value: int):
        """Set the value of tax_cents."""
        self.tax_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tax_cents')

    def is_set_tax_cents(self) -> bool:
        """Check if tax_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tax_cents' in self._pending_field_updates)

    def get_tax_rate_percent(self) -> float:
        """Get the value of tax_rate_percent."""
        return self.tax_rate_percent

    def set_tax_rate_percent(self, value: float):
        """Set the value of tax_rate_percent."""
        self.tax_rate_percent = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('tax_rate_percent')

    def is_set_tax_rate_percent(self) -> bool:
        """Check if tax_rate_percent was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'tax_rate_percent' in self._pending_field_updates)

    def get_total_cents(self) -> int:
        """Get the value of total_cents."""
        return self.total_cents

    def set_total_cents(self, value: int):
        """Set the value of total_cents."""
        self.total_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('total_cents')

    def is_set_total_cents(self) -> bool:
        """Check if total_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'total_cents' in self._pending_field_updates)

    def get_amount_paid_cents(self) -> int:
        """Get the value of amount_paid_cents."""
        return self.amount_paid_cents

    def set_amount_paid_cents(self, value: int):
        """Set the value of amount_paid_cents."""
        self.amount_paid_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('amount_paid_cents')

    def is_set_amount_paid_cents(self) -> bool:
        """Check if amount_paid_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'amount_paid_cents' in self._pending_field_updates)

    def get_amount_due_cents(self) -> int:
        """Get the value of amount_due_cents."""
        return self.amount_due_cents

    def set_amount_due_cents(self, value: int):
        """Set the value of amount_due_cents."""
        self.amount_due_cents = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('amount_due_cents')

    def is_set_amount_due_cents(self) -> bool:
        """Check if amount_due_cents was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'amount_due_cents' in self._pending_field_updates)

    def get_paid_at(self) -> str:
        """Get the value of paid_at."""
        return self.paid_at

    def set_paid_at(self, value: str):
        """Set the value of paid_at."""
        self.paid_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('paid_at')

    def is_set_paid_at(self) -> bool:
        """Check if paid_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'paid_at' in self._pending_field_updates)

    def get_voided_at(self) -> str:
        """Get the value of voided_at."""
        return self.voided_at

    def set_voided_at(self, value: str):
        """Set the value of voided_at."""
        self.voided_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('voided_at')

    def is_set_voided_at(self) -> bool:
        """Check if voided_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'voided_at' in self._pending_field_updates)

    def get_line_items(self) -> str:
        """Get the value of line_items."""
        return self.line_items

    def set_line_items(self, value: str):
        """Set the value of line_items."""
        self.line_items = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('line_items')

    def is_set_line_items(self) -> bool:
        """Check if line_items was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'line_items' in self._pending_field_updates)

    def get_billing_reason(self) -> str:
        """Get the value of billing_reason."""
        return self.billing_reason

    def set_billing_reason(self, value: str):
        """Set the value of billing_reason."""
        self.billing_reason = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_reason')

    def is_set_billing_reason(self) -> bool:
        """Check if billing_reason was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_reason' in self._pending_field_updates)

    def get_plan_code(self) -> str:
        """Get the value of plan_code."""
        return self.plan_code

    def set_plan_code(self, value: str):
        """Set the value of plan_code."""
        self.plan_code = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('plan_code')

    def is_set_plan_code(self) -> bool:
        """Check if plan_code was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'plan_code' in self._pending_field_updates)

    def get_stripe_invoice_id(self) -> str:
        """Get the value of stripe_invoice_id."""
        return self.stripe_invoice_id

    def set_stripe_invoice_id(self, value: str):
        """Set the value of stripe_invoice_id."""
        self.stripe_invoice_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('stripe_invoice_id')

    def is_set_stripe_invoice_id(self) -> bool:
        """Check if stripe_invoice_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'stripe_invoice_id' in self._pending_field_updates)

    def get_stripe_payment_intent_id(self) -> str:
        """Get the value of stripe_payment_intent_id."""
        return self.stripe_payment_intent_id

    def set_stripe_payment_intent_id(self, value: str):
        """Set the value of stripe_payment_intent_id."""
        self.stripe_payment_intent_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('stripe_payment_intent_id')

    def is_set_stripe_payment_intent_id(self) -> bool:
        """Check if stripe_payment_intent_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'stripe_payment_intent_id' in self._pending_field_updates)

    def get_stripe_charge_id(self) -> str:
        """Get the value of stripe_charge_id."""
        return self.stripe_charge_id

    def set_stripe_charge_id(self, value: str):
        """Set the value of stripe_charge_id."""
        self.stripe_charge_id = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('stripe_charge_id')

    def is_set_stripe_charge_id(self) -> bool:
        """Check if stripe_charge_id was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'stripe_charge_id' in self._pending_field_updates)

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

    def get_invoice_pdf_url(self) -> str:
        """Get the value of invoice_pdf_url."""
        return self.invoice_pdf_url

    def set_invoice_pdf_url(self, value: str):
        """Set the value of invoice_pdf_url."""
        self.invoice_pdf_url = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('invoice_pdf_url')

    def is_set_invoice_pdf_url(self) -> bool:
        """Check if invoice_pdf_url was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'invoice_pdf_url' in self._pending_field_updates)

    def get_hosted_invoice_url(self) -> str:
        """Get the value of hosted_invoice_url."""
        return self.hosted_invoice_url

    def set_hosted_invoice_url(self, value: str):
        """Set the value of hosted_invoice_url."""
        self.hosted_invoice_url = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('hosted_invoice_url')

    def is_set_hosted_invoice_url(self) -> bool:
        """Check if hosted_invoice_url was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'hosted_invoice_url' in self._pending_field_updates)

    def get_receipt_url(self) -> str:
        """Get the value of receipt_url."""
        return self.receipt_url

    def set_receipt_url(self, value: str):
        """Set the value of receipt_url."""
        self.receipt_url = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('receipt_url')

    def is_set_receipt_url(self) -> bool:
        """Check if receipt_url was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'receipt_url' in self._pending_field_updates)

    def get_payment_method_type(self) -> str:
        """Get the value of payment_method_type."""
        return self.payment_method_type

    def set_payment_method_type(self, value: str):
        """Set the value of payment_method_type."""
        self.payment_method_type = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('payment_method_type')

    def is_set_payment_method_type(self) -> bool:
        """Check if payment_method_type was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'payment_method_type' in self._pending_field_updates)

    def get_payment_method_last_four(self) -> str:
        """Get the value of payment_method_last_four."""
        return self.payment_method_last_four

    def set_payment_method_last_four(self, value: str):
        """Set the value of payment_method_last_four."""
        self.payment_method_last_four = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('payment_method_last_four')

    def is_set_payment_method_last_four(self) -> bool:
        """Check if payment_method_last_four was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'payment_method_last_four' in self._pending_field_updates)

    def get_billing_name(self) -> str:
        """Get the value of billing_name."""
        return self.billing_name

    def set_billing_name(self, value: str):
        """Set the value of billing_name."""
        self.billing_name = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_name')

    def is_set_billing_name(self) -> bool:
        """Check if billing_name was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_name' in self._pending_field_updates)

    def get_billing_email(self) -> str:
        """Get the value of billing_email."""
        return self.billing_email

    def set_billing_email(self, value: str):
        """Set the value of billing_email."""
        self.billing_email = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('billing_email')

    def is_set_billing_email(self) -> bool:
        """Check if billing_email was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'billing_email' in self._pending_field_updates)

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

    def get_attempt_count(self) -> int:
        """Get the value of attempt_count."""
        return self.attempt_count

    def set_attempt_count(self, value: int):
        """Set the value of attempt_count."""
        self.attempt_count = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('attempt_count')

    def is_set_attempt_count(self) -> bool:
        """Check if attempt_count was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'attempt_count' in self._pending_field_updates)

    def get_next_payment_attempt_at(self) -> str:
        """Get the value of next_payment_attempt_at."""
        return self.next_payment_attempt_at

    def set_next_payment_attempt_at(self, value: str):
        """Set the value of next_payment_attempt_at."""
        self.next_payment_attempt_at = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('next_payment_attempt_at')

    def is_set_next_payment_attempt_at(self) -> bool:
        """Check if next_payment_attempt_at was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'next_payment_attempt_at' in self._pending_field_updates)

    def get_last_payment_error(self) -> str:
        """Get the value of last_payment_error."""
        return self.last_payment_error

    def set_last_payment_error(self, value: str):
        """Set the value of last_payment_error."""
        self.last_payment_error = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('last_payment_error')

    def is_set_last_payment_error(self) -> bool:
        """Check if last_payment_error was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'last_payment_error' in self._pending_field_updates)

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

    def get_memo(self) -> str:
        """Get the value of memo."""
        return self.memo

    def set_memo(self, value: str):
        """Set the value of memo."""
        self.memo = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('memo')

    def is_set_memo(self) -> bool:
        """Check if memo was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'memo' in self._pending_field_updates)

    def get_footer(self) -> str:
        """Get the value of footer."""
        return self.footer

    def set_footer(self, value: str):
        """Set the value of footer."""
        self.footer = value
        if hasattr(self, '_pending_field_updates'):
            self._pending_field_updates.add('footer')

    def is_set_footer(self) -> bool:
        """Check if footer was explicitly set."""
        return (hasattr(self, '_pending_field_updates') and 
                'footer' in self._pending_field_updates)

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
        return cls(name="", uuid=None, fq_name=None, parent_uuid=None, display_name=None, description=None, created_by=None, created_at=None, updated_at=None, invoice_number=None, status=None, invoice_type=None, invoice_date=None, due_date=None, period_start=None, period_end=None, currency=None, subtotal_cents=None, discount_cents=None, tax_cents=None, tax_rate_percent=None, total_cents=None, amount_paid_cents=None, amount_due_cents=None, paid_at=None, voided_at=None, line_items=None, billing_reason=None, plan_code=None, stripe_invoice_id=None, stripe_payment_intent_id=None, stripe_charge_id=None, stripe_subscription_id=None, invoice_pdf_url=None, hosted_invoice_url=None, receipt_url=None, payment_method_type=None, payment_method_last_four=None, billing_name=None, billing_email=None, billing_address=None, attempt_count=None, next_payment_attempt_at=None, last_payment_error=None, notes=None, memo=None, footer=None, metadata=None)

platform_billing_invoice=PlatformBillingInvoice
PlatformBillingInvoice=PlatformBillingInvoice
PlatformBillingInvoice=PlatformBillingInvoice
platform_billing_invoice=PlatformBillingInvoice
