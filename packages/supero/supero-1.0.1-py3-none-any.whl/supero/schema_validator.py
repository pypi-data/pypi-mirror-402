#!/usr/bin/env python3
"""
Schema Validator - Validates schema structure before resolution.

Catches common errors:
- Missing required fields
- Invalid extends format (dot notation instead of colon)
- Missing attribute types
- Invalid enum structures
- System attribute TYPE MISMATCH (allows matching types)
- Unknown attribute types (types that don't exist)
- Invalid reference names and types
"""
from typing import Dict, List, Set, Optional
import re


class SchemaValidationError(Exception):
    """Schema validation error with context"""
    def __init__(self, message: str, schema_name: str = None, 
                 file_path: str = None, field: str = None):
        self.schema_name = schema_name
        self.file_path = file_path
        self.field = field
        
        context = []
        if file_path:
            context.append(f"File: {file_path}")
        if schema_name:
            context.append(f"Schema: {schema_name}")
        if field:
            context.append(f"Field: {field}")
        
        full_message = f"{message}"
        if context:
            full_message += "\n" + "\n".join(f"  {c}" for c in context)
        
        super().__init__(full_message)


class SchemaValidator:
    """Validates schema structure and catches common errors"""
    
    # =========================================================================
    # SYSTEM ATTRIBUTES WITH EXPECTED TYPES
    # =========================================================================
    # Allows user to define system attributes IF type matches.
    # Only type mismatch causes validation error.
    # =========================================================================
    SYSTEM_ATTRIBUTES = {
        # Required system attributes
        'name': {'type': 'string', 'required': True},
        'uuid': {'type': 'string', 'required': True, 'compatible': ['uuid']},
        'fq_name': {'type': 'list', 'required': True, 'compatible': ['array']},
        'parent_type': {'type': 'string', 'required': True},
        'parent_uuid': {'type': 'string', 'required': True, 'compatible': ['uuid']},
        'obj_type': {'type': 'string', 'required': True},
        
        # Optional system attributes
        'display_name': {'type': 'string', 'required': False},
        'description': {'type': 'string', 'required': False},
        'created_by': {'type': 'string', 'required': False},
        'created_at': {'type': 'datetime', 'required': False, 'compatible': ['string', 'timestamp']},
        'updated_at': {'type': 'datetime', 'required': False, 'compatible': ['string', 'timestamp']},
        
        # Legacy/deprecated (still reserved)
        'last_modified': {'type': 'datetime', 'required': False, 'compatible': ['string', 'timestamp']},
        'id': {'type': 'string', 'required': False, 'compatible': ['uuid', 'int', 'integer']},
        'perms2': {'type': 'object', 'required': False, 'compatible': ['dict', 'json']},
        'owner': {'type': 'string', 'required': False},
    }
    
    # Keep set for backwards compatibility
    RESERVED_ATTRIBUTES = set(SYSTEM_ATTRIBUTES.keys())

    def __init__(self):
        self.builtin_types = {
            'string', 'int', 'integer', 'float', 'double', 'boolean', 'bool',
            'datetime', 'date', 'time', 'timestamp', 'uuid', 'json', 'object', 
            'array', 'list', 'dict', 'number', 'null', 'any', 'bytes', 'binary'
        }

    def _is_type_compatible(self, user_type: str, system_type: str, 
                           compatible_types: list = None) -> bool:
        """
        Check if user-defined type is compatible with system attribute type.
        
        Args:
            user_type: Type specified by user in schema
            system_type: Expected system attribute type
            compatible_types: List of additional compatible types
            
        Returns:
            True if types are compatible
        """
        if not user_type:
            return True  # No type specified, will use system default
            
        user_type = user_type.lower().strip()
        system_type = system_type.lower().strip()
        
        # Exact match
        if user_type == system_type:
            return True
        
        # Check compatible types
        if compatible_types and user_type in [t.lower() for t in compatible_types]:
            return True
        
        # Common type aliases
        type_aliases = {
            'str': 'string',
            'int': 'integer',
            'bool': 'boolean',
            'dict': 'object',
            'list': 'array',
            'float': 'number',
            'double': 'number',
        }
        
        normalized_user = type_aliases.get(user_type, user_type)
        normalized_system = type_aliases.get(system_type, system_type)
        
        return normalized_user == normalized_system

    def _validate_reserved_attributes(self, schema: Dict, schema_name: str, 
                                     file_path: str) -> List[str]:
        """
        Validate system attributes in OBJECT schemas.
        
        NEW BEHAVIOR (allows matching types):
        - System attribute with MATCHING type → ALLOWED ✓
        - System attribute with MISMATCHING type → ERROR ✗
        - Compatible types allowed (e.g., string/datetime for timestamps)
        
        This allows users to:
        - Add description to system attributes
        - Add constraints (min-length, pattern, etc.)
        - Customize behavior while keeping correct type
        """
        errors = []
        attributes = schema.get('attributes', [])
        
        # Handle both list and dict format
        attr_map = {}
        if isinstance(attributes, list):
            for attr in attributes:
                if isinstance(attr, dict) and 'name' in attr:
                    attr_map[attr['name']] = attr
        elif isinstance(attributes, dict):
            attr_map = attributes
        
        # Check each attribute against system attributes
        for attr_name, attr_details in attr_map.items():
            if attr_name not in self.SYSTEM_ATTRIBUTES:
                continue  # Not a system attribute, skip validation
            
            # It's a system attribute - check type compatibility
            system_attr = self.SYSTEM_ATTRIBUTES[attr_name]
            system_type = system_attr['type']
            compatible = system_attr.get('compatible', [])
            
            # Get user-specified type
            user_type = None
            if isinstance(attr_details, dict):
                user_type = attr_details.get('type')
            
            if not user_type:
                # No type specified - OK, system will provide default type
                continue
            
            # Check type compatibility
            if not self._is_type_compatible(user_type, system_type, compatible):
                compatible_str = f" (or: {', '.join(compatible)})" if compatible else ""
                errors.append(self._error(
                    f"❌ SYSTEM ATTRIBUTE TYPE MISMATCH: '{attr_name}'\n"
                    f"\n"
                    f"You defined '{attr_name}' with type '{user_type}', but the system\n"
                    f"requires type '{system_type}'{compatible_str}.\n"
                    f"\n"
                    f"💡 SOLUTIONS:\n"
                    f"   1. Change type to '{system_type}'\n"
                    f"   2. Remove the attribute (system will provide it)\n"
                    f"   3. Use a different attribute name\n"
                    f"\n"
                    f"✓ TIP: You CAN define system attributes to add constraints\n"
                    f"  (description, min-length, etc.) - just keep the correct type.",
                    schema_name, file_path, f'attributes.{attr_name}'
                ))
        
        return errors
    
    def _normalize_type_name(self, type_name: str) -> str:
        """
        Normalize type name for comparison.
        Handles: PascalCase, snake_case, kebab-case
        
        Examples:
            OrderLineItem -> orderlineitem
            order_line_item -> orderlineitem
            order-line-item -> orderlineitem
        """
        return type_name.lower().replace('_', '').replace('-', '')
    
    def _normalize_reference_name(self, ref_name: str) -> str:
        """
        Normalize reference name for comparison.
        Handles: PascalCase, snake_case, camelCase, kebab-case
        
        Examples:
            TeamMembers -> teammembers
            team_members -> teammembers
            teamMembers -> teammembers
            team-members -> teammembers
        """
        return ref_name.lower().replace('_', '').replace('-', '')
    
    def _is_valid_reference_name(self, ref_name: str) -> bool:
        """
        Validate reference name allows multiple naming conventions:
        - snake_case: team_members, user_account
        - PascalCase: TeamMembers, UserAccount  
        - camelCase: teamMembers, userAccount
        - kebab-case: team-members (also supported)
        
        Pattern: starts with letter or underscore, contains letters, numbers, underscores, hyphens
        """
        if not ref_name or not isinstance(ref_name, str):
            return False
        # Allow: snake_case, PascalCase, camelCase, kebab-case
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', ref_name))
    
    def _validate_attribute_types_exist(self, schema: Dict, schema_name: str,
                                        file_path: str, 
                                        known_schemas: Dict[str, Dict]) -> List[str]:
        """
        Validate that all attribute types reference existing schemas.
        
        This catches errors like:
        - {"name": "line_items", "type": "order_line_item"} 
          when the actual schema is named "OrderLineItem"
        
        Args:
            schema: Schema to validate
            schema_name: Name of the schema
            file_path: File path for context
            known_schemas: Dict of all known schemas {name: schema}
            
        Returns:
            List of error messages
        """
        errors = []
        attributes = schema.get('attributes', [])
        
        if not known_schemas:
            return errors  # Can't validate without schema context
        
        # Build normalized name lookup
        # normalized_name -> actual_name
        normalized_to_actual = {}
        for name in known_schemas.keys():
            normalized = self._normalize_type_name(name)
            normalized_to_actual[normalized] = name
        
        # Get list of attributes
        attr_list = []
        if isinstance(attributes, list):
            attr_list = attributes
        elif isinstance(attributes, dict):
            attr_list = [{'name': k, **v} for k, v in attributes.items()]
        
        for attr in attr_list:
            if not isinstance(attr, dict):
                continue
                
            attr_name = attr.get('name', 'unknown')
            attr_type = attr.get('type', '')
            
            if not attr_type:
                continue
            
            # Skip builtin types
            if attr_type.lower() in self.builtin_types:
                continue
            
            # Skip cross-namespace references (e.g., "general:TimeZones", "system:AuditInfo")
            # These reference types in other namespaces that we can't validate here
            if ':' in attr_type:
                continue
            
            # Check if type exists (with normalization)
            normalized_type = self._normalize_type_name(attr_type)
            
            if normalized_type not in normalized_to_actual:
                # Type doesn't exist at all
                # Check if it might be a typo - find similar names
                suggestions = self._find_similar_types(attr_type, known_schemas.keys())
                suggestion_str = ""
                if suggestions:
                    suggestion_str = f"\n\n💡 Did you mean: {', '.join(suggestions)}?"
                
                errors.append(self._error(
                    f"❌ UNKNOWN TYPE: '{attr_type}'\n"
                    f"\n"
                    f"Attribute '{attr_name}' references type '{attr_type}' which doesn't exist.\n"
                    f"\n"
                    f"💡 SOLUTIONS:\n"
                    f"   1. Create a TYPE schema named '{attr_type}'\n"
                    f"   2. Check spelling of the type name\n"
                    f"   3. Use a builtin type: string, integer, boolean, etc."
                    f"{suggestion_str}",
                    schema_name, file_path, f'attributes.{attr_name}'
                ))
            # NOTE: If normalized names match, we do NOT report a mismatch.
            # PascalCase and snake_case are equivalent naming conventions:
            # - TimeZones == time_zones (both valid)
            # - OrderLineItem == order_line_item (both valid)
        
        return errors
    
    def _find_similar_types(self, type_name: str, known_types: List[str], 
                           max_suggestions: int = 3) -> List[str]:
        """Find similar type names for suggestions (simple substring matching)"""
        suggestions = []
        type_lower = type_name.lower()
        
        for known in known_types:
            known_lower = known.lower()
            # Check if any word in type_name appears in known type
            words = type_lower.replace('_', ' ').replace('-', ' ').split()
            for word in words:
                if len(word) > 2 and word in known_lower:
                    suggestions.append(known)
                    break
        
        return suggestions[:max_suggestions]
    
    def _validate_type_vs_object_usage(self, schema: Dict, schema_name: str,
                                       file_path: str,
                                       known_schemas: Dict[str, Dict]) -> List[str]:
        """
        Validate that OBJECTs aren't used as attribute types.
        
        Rules:
        - Attribute types can be: primitives, TYPEs, or ENUMs
        - OBJECTs must be referenced via 'references' array
        
        Args:
            schema: Schema to validate
            schema_name: Name of the schema
            file_path: File path for context
            known_schemas: Dict of all known schemas
            
        Returns:
            List of error messages
        """
        errors = []
        attributes = schema.get('attributes', [])
        
        if not known_schemas:
            return errors
        
        # Build normalized lookup
        normalized_to_schema = {}
        for name, s in known_schemas.items():
            normalized = self._normalize_type_name(name)
            normalized_to_schema[normalized] = (name, s)
        
        # Get attribute list
        attr_list = []
        if isinstance(attributes, list):
            attr_list = attributes
        elif isinstance(attributes, dict):
            attr_list = [{'name': k, **v} for k, v in attributes.items()]
        
        for attr in attr_list:
            if not isinstance(attr, dict):
                continue
            
            attr_name = attr.get('name', 'unknown')
            attr_type = attr.get('type', '')
            
            if not attr_type or attr_type.lower() in self.builtin_types:
                continue
            
            # Skip cross-namespace references (e.g., "general:TimeZones", "system:AuditInfo")
            # These reference types in other namespaces that we can't validate here
            if ':' in attr_type:
                continue
            
            normalized_type = self._normalize_type_name(attr_type)
            
            if normalized_type in normalized_to_schema:
                actual_name, referenced_schema = normalized_to_schema[normalized_type]
                
                # Check if the referenced schema is an OBJECT (has parent_type)
                has_parent_type = 'parent_type' in referenced_schema
                is_enum = referenced_schema.get('enum') or 'values' in referenced_schema
                
                if has_parent_type and not is_enum:
                    errors.append(self._error(
                        f"❌ OBJECT USED AS TYPE: '{actual_name}'\n"
                        f"\n"
                        f"Attribute '{attr_name}' uses '{actual_name}' as its type,\n"
                        f"but '{actual_name}' is an OBJECT (has parent_type).\n"
                        f"\n"
                        f"OBJECTs cannot be used as attribute types.\n"
                        f"\n"
                        f"💡 SOLUTIONS:\n"
                        f"   1. Convert '{actual_name}' to a TYPE (remove parent_type)\n"
                        f"   2. Use 'references' array instead:\n"
                        f"      \"references\": [{{\"type\": \"{actual_name}\"}}]\n"
                        f"   3. Create a separate TYPE for embedded data",
                        schema_name, file_path, f'attributes.{attr_name}'
                    ))
        
        return errors
    
    def _validate_reference_types_exist(self, schema: Dict, schema_name: str,
                                        file_path: str, 
                                        known_schemas: Dict[str, Dict]) -> List[str]:
        """
        Validate that all reference types exist in known schemas.
        
        Allows multiple naming conventions for type references:
        - PascalCase: TeamMember
        - snake_case: team_member
        - camelCase: teamMember
        """
        errors = []
        references = schema.get('references', [])
        
        if not references or not known_schemas:
            return errors
        
        # Build normalized name lookup
        normalized_to_actual = {}
        for name in known_schemas.keys():
            normalized = self._normalize_type_name(name)
            normalized_to_actual[normalized] = name
        
        for i, ref in enumerate(references):
            if not isinstance(ref, dict):
                continue
            
            ref_type = ref.get('type')
            ref_name = ref.get('name', f'ref_{i}')
            
            if not ref_type:
                # If no type specified, name is used as type
                ref_type = ref_name
            
            if not ref_type:
                continue
            
            # Skip cross-namespace references (e.g., "general:Project")
            if ':' in ref_type:
                continue
            
            # Check if type exists (with normalization)
            normalized_type = self._normalize_type_name(ref_type)
            
            if normalized_type not in normalized_to_actual:
                # Type doesn't exist - find suggestions
                suggestions = self._find_similar_types(ref_type, known_schemas.keys())
                suggestion_str = ""
                if suggestions:
                    suggestion_str = f"\n\n💡 Did you mean: {', '.join(suggestions)}?"
                
                errors.append(self._error(
                    f"❌ UNKNOWN REFERENCE TYPE: '{ref_type}'\n"
                    f"\n"
                    f"Reference '{ref_name}' targets type '{ref_type}' which doesn't exist.\n"
                    f"\n"
                    f"💡 SOLUTIONS:\n"
                    f"   1. Create an OBJECT schema named '{ref_type}'\n"
                    f"   2. Check spelling of the type name\n"
                    f"   3. Use namespace prefix for external types (e.g., 'general:Project')"
                    f"{suggestion_str}",
                    schema_name, file_path, f'references[{i}].type'
                ))
            
            # Validate 'attr' type exists (should be TYPE or ENUM, not OBJECT)
            attr_type = ref.get('attr')
            if attr_type:
                if ':' in attr_type:
                    continue  # Skip cross-namespace
                
                normalized_attr = self._normalize_type_name(attr_type)
                
                if normalized_attr not in normalized_to_actual:
                    suggestions = self._find_similar_types(attr_type, known_schemas.keys())
                    suggestion_str = ""
                    if suggestions:
                        suggestion_str = f"\n\n💡 Did you mean: {', '.join(suggestions)}?"
                    
                    errors.append(self._error(
                        f"❌ UNKNOWN LINK DATA TYPE: '{attr_type}'\n"
                        f"\n"
                        f"Reference '{ref_name}' uses '{attr_type}' for link data,\n"
                        f"but this type doesn't exist.\n"
                        f"\n"
                        f"💡 SOLUTIONS:\n"
                        f"   1. Create a TYPE schema named '{attr_type}'\n"
                        f"   2. Create an ENUM schema named '{attr_type}'\n"
                        f"   3. Check spelling of the type name"
                        f"{suggestion_str}",
                        schema_name, file_path, f'references[{i}].attr'
                    ))
                else:
                    # Check that attr is a TYPE or ENUM, not an OBJECT
                    actual_name = normalized_to_actual.get(normalized_attr)
                    attr_schema = known_schemas.get(actual_name) if actual_name else None
                    
                    if attr_schema:
                        has_parent_type = 'parent_type' in attr_schema
                        is_enum = attr_schema.get('enum') or 'values' in attr_schema
                        
                        if has_parent_type and not is_enum:
                            errors.append(self._error(
                                f"❌ OBJECT USED AS LINK DATA: '{actual_name}'\n"
                                f"\n"
                                f"Reference '{ref_name}' uses '{actual_name}' for link data (attr),\n"
                                f"but '{actual_name}' is an OBJECT (has parent_type).\n"
                                f"\n"
                                f"Link data must be a TYPE or ENUM, not an OBJECT.\n"
                                f"\n"
                                f"💡 SOLUTIONS:\n"
                                f"   1. Create a TYPE schema for link metadata\n"
                                f"   2. Use an ENUM for simple link attributes\n"
                                f"   3. Remove 'attr' if no link data needed",
                                schema_name, file_path, f'references[{i}].attr'
                            ))
        
        return errors
    
    def validate_schema(self, schema: Dict, schema_name: str = None, 
                       file_path: str = None,
                       known_schemas: Dict[str, Dict] = None) -> List[str]:
        """
        Validate a single schema and return list of error messages.
        
        Args:
            schema: Schema dictionary to validate
            schema_name: Name of the schema (for context)
            file_path: File path (for context)
            known_schemas: Dict of all known schemas (for type validation)
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        schema_name = schema_name or schema.get('name', 'unknown')
        
        # Check required fields
        if 'name' not in schema:
            errors.append(self._error("Missing required field: 'name'", 
                                     schema_name, file_path))
        
        # Validate name format
        if 'name' in schema:
            name = schema['name']
            if not name or not isinstance(name, str):
                errors.append(self._error("Schema 'name' must be a non-empty string", 
                                         schema_name, file_path, 'name'))
        
        # Validate extends format
        if 'extends' in schema:
            errors.extend(self._validate_extends(schema, schema_name, file_path))
        
        # Validate reserved/system attributes (only for object schemas)
        if 'attributes' in schema:
            is_object_schema = self._is_object_schema(schema, file_path)
            if is_object_schema:
                errors.extend(self._validate_reserved_attributes(schema, schema_name, file_path))

        # Validate attributes structure
        if 'attributes' in schema:
            errors.extend(self._validate_attributes(schema, schema_name, file_path))
        
        # Validate attribute types exist
        if 'attributes' in schema and known_schemas:
            errors.extend(self._validate_attribute_types_exist(
                schema, schema_name, file_path, known_schemas
            ))
            errors.extend(self._validate_type_vs_object_usage(
                schema, schema_name, file_path, known_schemas
            ))
        
        # Validate references
        if 'references' in schema:
            errors.extend(self._validate_references(schema, schema_name, file_path))
        
        # Validate reference types exist (with naming convention flexibility)
        if 'references' in schema and known_schemas:
            errors.extend(self._validate_reference_types_exist(
                schema, schema_name, file_path, known_schemas
            ))
        
        # Validate enum structure
        if schema.get('enum') or 'values' in schema:
            errors.extend(self._validate_enum(schema, schema_name, file_path))
        
        # Validate no conflicting keys
        if schema.get('enum') and 'attributes' in schema:
            errors.append(self._error(
                "Schema cannot be both an enum and have attributes",
                schema_name, file_path
            ))
        
        return errors
    
    def _validate_extends(self, schema: Dict, schema_name: str, 
                         file_path: str) -> List[str]:
        """Validate extends field - STRICT MODE: subdomain required"""
        errors = []
        extends = schema['extends']
        
        if not isinstance(extends, str):
            errors.append(self._error(
                f"'extends' must be a string, got {type(extends).__name__}",
                schema_name, file_path, 'extends'
            ))
            return errors
        
        # Check for incorrect dot notation
        if '.' in extends:
            errors.append(self._error(
                f"Invalid extends format: '{extends}'. "
                f"Use colon notation (e.g., 'subdomain:ClassName') not dot notation",
                schema_name, file_path, 'extends'
            ))
        
        # ✅ STRICT: Require subdomain prefix
        if ':' not in extends:
            errors.append(self._error(
                f"Invalid extends format: '{extends}'. "
                f"Subdomain prefix is required. Use 'subdomain:ClassName' format.\n"
                f"Examples:\n"
                f"  - 'general:Project' (from public/general)\n"
                f"  - 'healthcare:Patient' (from public/healthcare)\n"
                f"  - 'tenant:{extends}' (from tenant's own schemas)",
                schema_name, file_path, 'extends'
            ))
            return errors
        
        # Check for multiple colons
        if extends.count(':') > 1:
            errors.append(self._error(
                f"Invalid extends format: '{extends}'. "
                f"Use exactly one colon (e.g., 'subdomain:ClassName')",
                schema_name, file_path, 'extends'
            ))
        
        # Validate subdomain and class name
        parts = extends.split(':', 1)
        subdomain = parts[0]
        class_name = parts[1]
        
        if not subdomain:
            errors.append(self._error(
                f"Empty subdomain in extends: '{extends}'",
                schema_name, file_path, 'extends'
            ))
        
        if not class_name:
            errors.append(self._error(
                f"Empty class name in extends: '{extends}'",
                schema_name, file_path, 'extends'
            ))
        
        # Validate subdomain is not empty and class name is valid identifier
        if subdomain and not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', subdomain):
            errors.append(self._error(
                f"Invalid subdomain name: '{subdomain}'. "
                f"Must start with letter and contain only letters, numbers, hyphens, underscores",
                schema_name, file_path, 'extends'
            ))
        
        if class_name and not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
            errors.append(self._error(
                f"Invalid class name: '{class_name}'. "
                f"Must be PascalCase (start with uppercase letter)",
                schema_name, file_path, 'extends'
            ))
        
        return errors

    def _validate_attributes(self, schema: Dict, schema_name: str, 
                            file_path: str) -> List[str]:
        """Validate attributes structure"""
        errors = []
        attributes = schema['attributes']
        
        if isinstance(attributes, dict):
            # Dict format: {attr_name: {type: ..., ...}}
            for attr_name, attr_details in attributes.items():
                if not isinstance(attr_details, dict):
                    errors.append(self._error(
                        f"Attribute '{attr_name}' must be a dict with 'type' field",
                        schema_name, file_path, f'attributes.{attr_name}'
                    ))
                    continue
                
                if 'type' not in attr_details:
                    # Allow system attributes without type (system provides it)
                    if attr_name not in self.SYSTEM_ATTRIBUTES:
                        errors.append(self._error(
                            f"Attribute '{attr_name}' missing required field: 'type'",
                            schema_name, file_path, f'attributes.{attr_name}'
                        ))
        
        elif isinstance(attributes, list):
            # List format: [{name: ..., type: ..., ...}, ...]
            seen_names = set()
            
            for i, attr in enumerate(attributes):
                if not isinstance(attr, dict):
                    errors.append(self._error(
                        f"Attribute at index {i} must be a dict",
                        schema_name, file_path, f'attributes[{i}]'
                    ))
                    continue
                
                if 'name' not in attr:
                    errors.append(self._error(
                        f"Attribute at index {i} missing required field: 'name'",
                        schema_name, file_path, f'attributes[{i}]'
                    ))
                else:
                    attr_name = attr['name']
                    
                    # Check for duplicates
                    if attr_name in seen_names:
                        errors.append(self._error(
                            f"Duplicate attribute name: '{attr_name}'",
                            schema_name, file_path, f'attributes[{i}]'
                        ))
                    seen_names.add(attr_name)
                
                if 'type' not in attr:
                    attr_name = attr.get('name', f'index_{i}')
                    # Allow system attributes without type (system provides it)
                    if attr_name not in self.SYSTEM_ATTRIBUTES:
                        errors.append(self._error(
                            f"Attribute '{attr_name}' missing required field: 'type'",
                            schema_name, file_path, f'attributes[{i}]'
                        ))
        else:
            errors.append(self._error(
                f"'attributes' must be a list or dict, got {type(attributes).__name__}",
                schema_name, file_path, 'attributes'
            ))
        
        return errors
    
    def _is_object_schema(self, schema: Dict, file_path: str = None) -> bool:
        """
        Determine if this is an object schema (vs custom type or enum).

        Object schemas:
        - Become database entities with UUIDs, timestamps, etc.
        - System attributes apply

        Custom types:
        - Just data structures (like structs)
        - Can use any attribute names

        Enums:
        - Value lists
        - Don't have attributes

        Detection logic:
        1. Check explicit schema type/category field
        2. Check for enum indicators (values, enum: true)
        3. Check file path (objects/, types/, enums/)
        4. Default to object if ambiguous (safer)
        """
        # 1. Check explicit type field
        schema_type = schema.get('schema_type')
        if schema_type:
            return schema_type.lower() in ['object']

        # 2. If it's an enum, it's not an object
        if schema.get('enum') or 'values' in schema:
            return False
        
        # 3. If no parent_type, it's likely a TYPE not an OBJECT
        if 'parent_type' not in schema:
            return False

        # 4. Check file path hints
        if file_path:
            path_lower = file_path.lower()

            # Explicit type indicators
            if '/types/' in path_lower:
                return False

            if '/enums/' in path_lower:
                return False

            # Explicit object indicators
            if '/objects/' in path_lower:
                return True

        # 5. Has parent_type = likely an object
        return True
    
    def _validate_references(self, schema: Dict, schema_name: str, 
                            file_path: str) -> List[str]:
        """Validate references structure and naming conventions"""
        errors = []
        references = schema['references']
        
        if not isinstance(references, list):
            errors.append(self._error(
                f"'references' must be a list, got {type(references).__name__}",
                schema_name, file_path, 'references'
            ))
            return errors
        
        seen_names = set()
        seen_normalized_names = {}  # normalized_name -> original_name
        
        for i, ref in enumerate(references):
            if not isinstance(ref, dict):
                errors.append(self._error(
                    f"Reference at index {i} must be a dict",
                    schema_name, file_path, f'references[{i}]'
                ))
                continue
            
            # Check for 'name' or 'type' field
            if 'name' not in ref and 'type' not in ref:
                errors.append(self._error(
                    f"Reference at index {i} must have 'name' or 'type' field",
                    schema_name, file_path, f'references[{i}]'
                ))
                continue
            
            # Get reference name (defaults to type if name not provided)
            ref_name = ref.get('name') or ref.get('type')
            
            # Validate reference name format - allow multiple conventions
            if ref_name and not self._is_valid_reference_name(ref_name):
                errors.append(self._error(
                    f"Invalid reference name: '{ref_name}'\n"
                    f"\n"
                    f"Reference names must:\n"
                    f"  - Start with a letter or underscore\n"
                    f"  - Contain only letters, numbers, underscores, or hyphens\n"
                    f"\n"
                    f"✅ Allowed formats:\n"
                    f"   - snake_case: team_members, user_account\n"
                    f"   - PascalCase: TeamMembers, UserAccount\n"
                    f"   - camelCase: teamMembers, userAccount\n"
                    f"   - kebab-case: team-members",
                    schema_name, file_path, f'references[{i}].name'
                ))
                continue
            
            # Check for duplicate reference names (exact match)
            if ref_name in seen_names:
                errors.append(self._error(
                    f"Duplicate reference name: '{ref_name}'",
                    schema_name, file_path, f'references[{i}]'
                ))
            seen_names.add(ref_name)
            
            # Check for normalized name collisions (different cases of same name)
            if ref_name:
                normalized = self._normalize_reference_name(ref_name)
                if normalized in seen_normalized_names:
                    original = seen_normalized_names[normalized]
                    if original != ref_name:
                        errors.append(self._error(
                            f"⚠️ Reference name collision: '{ref_name}' and '{original}'\n"
                            f"\n"
                            f"These names normalize to the same identifier and will\n"
                            f"conflict in generated code.\n"
                            f"\n"
                            f"💡 Use distinct names to avoid collisions.",
                            schema_name, file_path, f'references[{i}].name'
                        ))
                else:
                    seen_normalized_names[normalized] = ref_name
            
            # Validate 'attr' field if present (must be TYPE or ENUM, not OBJECT)
            if 'attr' in ref:
                attr_type = ref['attr']
                if attr_type and not isinstance(attr_type, str):
                    errors.append(self._error(
                        f"Reference 'attr' must be a string (TYPE or ENUM name), got {type(attr_type).__name__}",
                        schema_name, file_path, f'references[{i}].attr'
                    ))
            
            # Validate 'cardinality' if present
            if 'cardinality' in ref:
                cardinality = ref['cardinality']
                if cardinality not in ('one', 'many'):
                    errors.append(self._error(
                        f"Reference 'cardinality' must be 'one' or 'many', got '{cardinality}'",
                        schema_name, file_path, f'references[{i}].cardinality'
                    ))
            
            # Validate 'type' field format if present
            ref_type = ref.get('type')
            if ref_type and not isinstance(ref_type, str):
                errors.append(self._error(
                    f"Reference 'type' must be a string, got {type(ref_type).__name__}",
                    schema_name, file_path, f'references[{i}].type'
                ))
            elif ref_type and not self._is_valid_reference_name(ref_type) and ':' not in ref_type:
                # Allow namespace:type format (e.g., "general:Project")
                errors.append(self._error(
                    f"Invalid reference type: '{ref_type}'\n"
                    f"\n"
                    f"Reference types must:\n"
                    f"  - Start with a letter or underscore\n"
                    f"  - Contain only letters, numbers, underscores, or hyphens\n"
                    f"  - Or use namespace:type format (e.g., 'general:Project')\n"
                    f"\n"
                    f"✅ Allowed formats:\n"
                    f"   - snake_case: team_member, user_account\n"
                    f"   - PascalCase: TeamMember, UserAccount\n"
                    f"   - camelCase: teamMember, userAccount\n"
                    f"   - Namespaced: general:Project, healthcare:Patient",
                    schema_name, file_path, f'references[{i}].type'
                ))
        
        return errors
    
    def _validate_enum(self, schema: Dict, schema_name: str, 
                      file_path: str) -> List[str]:
        """Validate enum structure"""
        errors = []
        
        if 'values' not in schema:
            errors.append(self._error(
                "Enum must have 'values' field",
                schema_name, file_path, 'values'
            ))
            return errors
        
        values = schema['values']
        
        if not isinstance(values, list):
            errors.append(self._error(
                f"Enum 'values' must be a list, got {type(values).__name__}",
                schema_name, file_path, 'values'
            ))
            return errors
        
        if len(values) == 0:
            errors.append(self._error(
                "Enum 'values' cannot be empty",
                schema_name, file_path, 'values'
            ))
        
        # Check for duplicates
        seen = set()
        for val in values:
            if val in seen:
                errors.append(self._error(
                    f"Duplicate enum value: '{val}'",
                    schema_name, file_path, 'values'
                ))
            seen.add(val)
        
        # Validate type field if present
        if 'type' in schema:
            enum_type = schema['type']
            if enum_type not in ['string', 'int', 'integer', 'float']:
                errors.append(self._error(
                    f"Enum 'type' must be string, int, or float, got '{enum_type}'",
                    schema_name, file_path, 'type'
                ))
        
        return errors
    
    def _error(self, message: str, schema_name: str = None, 
               file_path: str = None, field: str = None) -> str:
        """Format error message with context"""
        context = []
        if file_path:
            context.append(f"File: {file_path}")
        if schema_name:
            context.append(f"Schema: {schema_name}")
        if field:
            context.append(f"Field: {field}")
        
        if context:
            return f"{message}\n  " + "\n  ".join(context)
        return message
    
    def validate_all_schemas(self, schemas: Dict[str, Dict], 
                            base_path: str = None) -> Dict[str, List[str]]:
        """
        Validate multiple schemas with cross-schema type checking.
        
        Args:
            schemas: Dict of {schema_name: schema_content}
            base_path: Base path for file context
            
        Returns:
            Dict of {schema_name: [error_messages]} for schemas with errors
        """
        all_errors = {}
        
        for schema_name, schema in schemas.items():
            file_path = None
            if base_path:
                # Try to construct file path
                category = schema.get('_category', 'object')
                file_path = f"{base_path}/{category}/{schema.get('name', schema_name)}.json"
            
            # Pass all schemas for cross-schema validation
            errors = self.validate_schema(schema, schema_name, file_path, 
                                         known_schemas=schemas)
            if errors:
                all_errors[schema_name] = errors
        
        return all_errors
    
    def validate_schema_batch(self, schemas: List[Dict], 
                             base_path: str = None) -> Dict[str, List[str]]:
        """
        Validate a batch of schemas (list format) with cross-schema type checking.
        
        Args:
            schemas: List of schema dictionaries
            base_path: Base path for file context
            
        Returns:
            Dict of {schema_name: [error_messages]} for schemas with errors
        """
        # Convert list to dict for cross-schema validation
        schema_dict = {}
        for schema in schemas:
            name = schema.get('name', f'unknown_{len(schema_dict)}')
            schema_dict[name] = schema
        
        return self.validate_all_schemas(schema_dict, base_path)
    
    def format_validation_report(self, all_errors: Dict[str, List[str]]) -> str:
        """Format validation errors into a readable report"""
        if not all_errors:
            return "✓ All schemas valid"
        
        report = [f"✗ Found {len(all_errors)} schema(s) with errors:\n"]
        
        for schema_name, errors in all_errors.items():
            report.append(f"Schema '{schema_name}':")
            for error in errors:
                # Indent error messages
                for line in error.split('\n'):
                    report.append(f"  {line}")
            report.append("")  # Blank line between schemas
        
        return "\n".join(report)


def validate_schemas_before_resolution(tenant_schemas: Dict[str, Dict],
                                       public_schemas: Dict[str, Dict],
                                       tenant_path: str = None) -> None:
    """
    Validate all schemas before resolution.
    
    Raises SchemaValidationError if validation fails.
    """
    validator = SchemaValidator()
    
    # Combine all schemas for cross-schema validation
    all_schemas = {**public_schemas, **tenant_schemas}
    
    # Validate tenant schemas (with access to public schemas for type lookup)
    tenant_errors = {}
    for name, schema in tenant_schemas.items():
        errors = validator.validate_schema(schema, name, 
                                          known_schemas=all_schemas)
        if errors:
            tenant_errors[name] = errors
    
    if tenant_errors:
        report = validator.format_validation_report(tenant_errors)
        raise SchemaValidationError(
            f"Schema validation failed:\n\n{report}"
        )


if __name__ == '__main__':
    # Test the validator
    validator = SchemaValidator()
    
    # Test cases including reference naming conventions
    test_schemas = {
        'OrderLineItem': {
            'name': 'OrderLineItem',
            'parent_type': 'order',  # This makes it an OBJECT
            'attributes': [
                {'name': 'product_name', 'type': 'string'},
                {'name': 'quantity', 'type': 'integer'},
            ]
        },
        'Order': {
            'name': 'Order',
            'parent_type': 'project',
            'attributes': [
                {'name': 'order_number', 'type': 'string'},
                # This should ERROR: OrderLineItem is an OBJECT, not a TYPE
                {'name': 'line_items', 'type': 'order_line_item', 'list': True},
            ]
        },
        'Address': {
            'name': 'Address',
            # No parent_type = TYPE
            'attributes': [
                {'name': 'street', 'type': 'string'},
                {'name': 'city', 'type': 'string'},
            ]
        },
        'Customer': {
            'name': 'Customer',
            'parent_type': 'project',
            'attributes': [
                {'name': 'name', 'type': 'string'},
                # This should be OK: Address is a TYPE
                {'name': 'billing_address', 'type': 'Address'},
                # This should ERROR: unknown type
                {'name': 'payment_info', 'type': 'PaymentDetails'},
            ]
        },
        'RoleAssignment': {
            'name': 'RoleAssignment',
            # No parent_type = TYPE (for link data)
            'attributes': [
                {'name': 'role', 'type': 'string'},
                {'name': 'assigned_at', 'type': 'datetime'},
            ]
        },
        'TeamMember': {
            'name': 'TeamMember',
            'parent_type': 'project',
            'attributes': [
                {'name': 'email', 'type': 'string'},
            ]
        },
        'Project': {
            'name': 'Project',
            'parent_type': 'domain',
            'attributes': [
                {'name': 'title', 'type': 'string'},
            ],
            # Test various reference naming conventions
            'references': [
                # snake_case - should be valid
                {'name': 'team_members', 'type': 'TeamMember', 'cardinality': 'many'},
                # PascalCase - should be valid
                {'name': 'Lead', 'type': 'TeamMember', 'cardinality': 'one'},
                # camelCase - should be valid
                {'name': 'projectOwner', 'type': 'TeamMember', 'cardinality': 'one'},
                # With link data (attr) - should be valid
                {'name': 'assigned_members', 'type': 'TeamMember', 'attr': 'RoleAssignment', 'cardinality': 'many'},
            ]
        },
    }
    
    print("=" * 60)
    print("SCHEMA VALIDATION TEST")
    print("=" * 60)
    
    errors = validator.validate_all_schemas(test_schemas)
    print(validator.format_validation_report(errors))
    
    print("\n" + "=" * 60)
    print("REFERENCE NAMING CONVENTION TEST")
    print("=" * 60)
    
    # Test reference name validation
    test_names = [
        'team_members',      # snake_case
        'TeamMembers',       # PascalCase
        'teamMembers',       # camelCase
        'team-members',      # kebab-case
        '_private_ref',      # underscore prefix
        'ref123',            # with numbers
        '123invalid',        # invalid: starts with number
        'invalid name',      # invalid: contains space
        'invalid@name',      # invalid: contains @
    ]
    
    print("\nReference name validation results:")
    for name in test_names:
        valid = validator._is_valid_reference_name(name)
        status = "✅ VALID" if valid else "❌ INVALID"
        print(f"  {name:20} -> {status}")
