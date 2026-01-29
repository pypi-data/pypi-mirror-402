"""
Schema naming utilities for the Supero Platform
Handles normalization, validation, and storage filename generation
"""
import re
from typing import Tuple, Dict, Any

def normalize_schema_name(name: str) -> str:
    """
    Normalize schema name to snake_case.
    
    Handles acronyms intelligently using a two-pass approach:
    - Pass 1: Standard CamelCase boundaries (acronym followed by uppercase or end)
    - Pass 2: Compound words (acronym followed by lowercase/digits)
    
    Examples:
        >>> normalize_schema_name("UserAccount")
        'user_account'
        >>> normalize_schema_name("SDKBuildRequest")
        'sdk_build_request'
        >>> normalize_schema_name("HTTPv2Server")
        'httpv2_server'
        >>> normalize_schema_name("HTTPSAPIEndpoint")
        'https_api_endpoint'
        >>> normalize_schema_name("ConfigHTTPServer")
        'config_http_server'
    
    Args:
        name: Original schema name (can be CamelCase, snake_case, etc.)
        
    Returns:
        Normalized snake_case name
    """
    if not name:
        return name
    
    # Remove .json extension if present
    name = name.replace('.json', '')
    
    # CRITICAL: Order matters! Longer acronyms MUST come first
    # to prevent partial matches (e.g., HTTPS before HTTP, UUID before ID)
    acronym_map = [
        # Network/Protocol (longest first)
        ('HTTPS', 'Https'),
        ('HTTP', 'Http'),
        ('SFTP', 'Sftp'),
        ('FTP', 'Ftp'),
        ('SSH', 'Ssh'),
        
        # Cloud services
        ('AWS', 'Aws'),
        
        # Authentication
        ('OAuth', 'Oauth'),
        ('JWT', 'Jwt'),
        
        # Data formats
        ('JSON', 'Json'),
        ('XML', 'Xml'),
        ('HTML', 'Html'),
        
        # API/SDK
        ('REST', 'Rest'),
        ('SOAP', 'Soap'),
        ('CRUD', 'Crud'),
        ('API', 'Api'),
        ('SDK', 'Sdk'),
        ('CLI', 'Cli'),
        
        # Database
        ('NoSQL', 'Nosql'),
        ('SQL', 'Sql'),
        
        # Network
        ('TCP', 'Tcp'),
        ('UDP', 'Udp'),
        ('DNS', 'Dns'),
        ('VPN', 'Vpn'),
        ('VPC', 'Vpc'),
        ('CDN', 'Cdn'),
        
        # Security
        ('SSL', 'Ssl'),
        ('TLS', 'Tls'),
        
        # Identifiers
        ('UUID', 'Uuid'),
        ('URL', 'Url'),
        ('URI', 'Uri'),
        
        # Communication
        ('SMS', 'Sms'),
        ('MMS', 'Mms'),
        
        # Technology
        ('IoT', 'Iot'),
        ('AI', 'Ai'),
        ('ML', 'Ml'),
        ('NLP', 'Nlp'),
        
        # Other (must be last to avoid conflicts)
        ('ID', 'Id'),
        ('UI', 'Ui'),
        ('S3', 'S3'),
        ('IP', 'Ip'),
    ]
    
    # PASS 1: Match acronyms followed by uppercase or end
    # Handles: SDKBuildRequest → SdkBuildRequest, HTTPServer → HttpServer
    for acronym, replacement in acronym_map:
        pattern = f'{acronym}(?=[A-Z]|$)'
        name = re.sub(pattern, replacement, name)
    
    # PASS 2: Match remaining all-caps acronyms followed by lowercase/digits
    # Handles: HTTPv2 → Httpv2, IPv4 → Ipv4
    # Only matches if acronym is still in all-caps (not already replaced)
    for acronym, replacement in acronym_map:
        pattern = f'{acronym}(?=[a-z0-9])'
        name = re.sub(pattern, replacement, name)
    
    # Convert CamelCase to snake_case
    # Insert underscore between lowercase/digit and uppercase
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    
    # Handle consecutive capitals (XMLParser → Xml_Parser)
    name = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    
    # Replace hyphens and spaces with underscores
    name = name.replace('-', '_').replace(' ', '_')
    
    # Lowercase everything
    name = name.lower()
    
    # Remove duplicate underscores
    name = re.sub('_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name


def validate_schema_name(name: str, raise_on_error: bool = True) -> Tuple[bool, str]:
    """
    Validate schema name according to platform rules.
    
    Rules:
    - Must not be empty
    - Must contain only lowercase letters, numbers, and underscores
    - Must start with a letter
    - Cannot be a Python reserved word
    
    Args:
        name: Schema name to validate
        raise_on_error: If True, raise ValueError on invalid name. 
                       If False, return (False, error_message)
    
    Returns:
        If raise_on_error=True: Returns (True, '') on success, raises on failure
        If raise_on_error=False: Returns (True, '') or (False, error_message)
    
    Raises:
        ValueError: If name is invalid and raise_on_error=True
    """
    # Check for empty name
    if not name or not name.strip():
        error_msg = "Schema name cannot be empty"
        if raise_on_error:
            raise ValueError(error_msg)
        return False, error_msg
    
    name = name.strip()
    
    # Check valid characters (lowercase letters, numbers, underscores only)
    if not re.match(r'^[a-z][a-z0-9_]*$', name):
        if not name[0].isalpha():
            error_msg = f"Schema name must start with a letter: '{name}'"
        elif name[0].isupper():
            error_msg = f"Schema name can only contain lowercase letters, numbers, and underscores: '{name}'"
        else:
            error_msg = f"Schema name can only contain lowercase letters, numbers, and underscores: '{name}'"
        
        if raise_on_error:
            raise ValueError(error_msg)
        return False, error_msg
    
    # Check for Python reserved words
    python_reserved = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
        'while', 'with', 'yield'
    }
    
    if name in python_reserved:
        error_msg = f"Schema name cannot be a Python reserved word: '{name}'"
        if raise_on_error:
            raise ValueError(error_msg)
        return False, error_msg
    
    return True, ''


def process_schema_upload(schema_content: Dict[str, Any], 
                          preserve_original_name: bool = True) -> Tuple[Dict[str, Any], str]:
    """
    Process uploaded schema content for storage.
    
    Steps:
    1. Validate schema has 'name' field
    2. Store original name as 'display_name' if not present
    3. Normalize the 'name' field to snake_case
    4. Generate storage filename
    
    Args:
        schema_content: Dictionary containing schema definition
        preserve_original_name: If True, preserve original casing in display_name
        
    Returns:
        Tuple of (processed_schema, storage_filename)
        
    Raises:
        ValueError: If schema is invalid
        
    Example:
        >>> schema = {"name": "SMSData", "attributes": []}
        >>> processed, filename = process_schema_upload(schema)
        >>> processed["name"]
        'sms_data'
        >>> processed["display_name"]
        'SMSData'
        >>> filename
        'sms_data.json'
    """
    if not isinstance(schema_content, dict):
        raise ValueError("Schema content must be a dictionary")
    
    if 'name' not in schema_content:
        raise ValueError("Schema must have a 'name' field")
    
    original_name = schema_content['name']
    
    if not original_name:
        raise ValueError("Schema 'name' field cannot be empty")
    
    # Preserve original casing in display_name if not already set
    if preserve_original_name and 'display_name' not in schema_content:
        schema_content['display_name'] = original_name
    
    # Normalize the name to snake_case
    normalized_name = normalize_schema_name(original_name)
    
    # Validate normalized name
    validate_schema_name(normalized_name, raise_on_error=True)
    
    # Update schema with normalized name
    schema_content['name'] = normalized_name
    
    # Generate storage filename
    storage_filename = get_storage_filename(normalized_name)
    
    return schema_content, storage_filename


def get_storage_filename(schema_name: str) -> str:
    """
    Generate storage filename for a schema.
    
    Args:
        schema_name: Schema name (will be normalized if not already)
        
    Returns:
        Filename with .json extension
        
    Example:
        >>> get_storage_filename("user_account")
        'user_account.json'
        >>> get_storage_filename("UserAccount")
        'user_account.json'
    """
    # Normalize name if not already
    normalized = normalize_schema_name(schema_name)
    
    # Add .json extension if not present
    if not normalized.endswith('.json'):
        normalized += '.json'
    
    return normalized


def get_display_name(schema_name: str) -> str:
    """
    Generate a user-friendly display name from schema name.
    
    Converts snake_case to Title Case.
    
    Args:
        schema_name: Normalized schema name (snake_case)
        
    Returns:
        Display name in Title Case
        
    Example:
        >>> get_display_name("user_account")
        'User Account'
        >>> get_display_name("sms_data")
        'SMS Data'
    """
    # Split on underscores and capitalize each word
    words = schema_name.split('_')
    
    # Special handling for known acronyms
    acronyms = {'sms', 'api', 'http', 'https', 'xml', 'json', 'sql', 'url', 
                'uri', 'uuid', 'aws', 's3', 'sdk', 'id', 'ui', 'rest', 'crud',
                'tcp', 'udp', 'ip', 'dns', 'ssl', 'tls', 'vpn', 'cdn', 'iot',
                'ai', 'ml', 'nlp', 'jwt', 'oauth'}
    
    display_words = []
    for word in words:
        if word.lower() in acronyms:
            display_words.append(word.upper())
        else:
            display_words.append(word.capitalize())
    
    return ' '.join(display_words)
