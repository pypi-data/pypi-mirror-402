"""
API Key Authentication - Usage Examples

This file demonstrates all the ways to use API keys with the enhanced api_lib.
Exceptions are now imported from py_api_lib.exceptions
"""

# ==============================================================================
# EXAMPLE 1: NO CHANGES - Existing Code Works (if server allows)
# ==============================================================================

from py_api_lib import ApiLib

# OLD CODE - Still works if server has REQUIRE_API_AUTH=false
api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082"
)

domain = api_lib.domain_create("ecommerce")
project = api_lib.project_create(name="web-app", parent=domain)
print(f"Created project: {project.uuid}")


# ==============================================================================
# EXAMPLE 2: Environment Variable (RECOMMENDED for production)
# ==============================================================================

# Step 1: Set environment variable
# export API_KEY="ak_stores_prod_a1b2c3d4e5f6g7h8..."

# Step 2: Use existing code - NO CHANGES NEEDED!
api_lib = ApiLib.from_config()  # Automatically reads API_KEY from env

domain = api_lib.domain_create("ecommerce")
print(f"Created domain: {domain.uuid}")


# ==============================================================================
# EXAMPLE 3: Explicit API Key Parameter
# ==============================================================================

api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
)

domain = api_lib.domain_create("ecommerce")
project = api_lib.project_create(name="web-app", parent=domain)


# ==============================================================================
# EXAMPLE 4: Configuration File
# ==============================================================================

# Create config file: api_config.yaml
"""
api_lib:
  api_server_host: "localhost"
  api_server_port: "8082"
  api_key: "ak_stores_prod_a1b2c3d4..."
  timeout: 30
  max_retries: 3
"""

# Load from config
api_lib = ApiLib.from_config("api_config.yaml")
domain = api_lib.domain_create("ecommerce")


# ==============================================================================
# EXAMPLE 5: Runtime Key Management (Multi-tenant)
# ==============================================================================

# Initialize without key
api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082"
)

# Switch to tenant A
api_lib.set_api_key("ak_tenantA_prod_abc123...")
tenant_a_domain = api_lib.domain_create("tenant-a")
print(f"Created for tenant A: {tenant_a_domain.uuid}")

# Switch to tenant B
api_lib.set_api_key("ak_tenantB_prod_xyz789...")
tenant_b_domain = api_lib.domain_create("tenant-b")
print(f"Created for tenant B: {tenant_b_domain.uuid}")

# Check current key (masked)
print(f"Current key: {api_lib.get_api_key()}")  # "ak_tenantB_prod_***"

# Clear key
api_lib.clear_api_key()


# ==============================================================================
# EXAMPLE 6: Error Handling - Authentication Failed
# ==============================================================================

from py_api_lib.exceptions import AuthenticationError

try:
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="invalid_key_12345"
    )
    domain = api_lib.domain_create("test")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Output:
    # API key authentication failed: Invalid API key
    # Current key: ***
    # Hint: Check your API key or use set_api_key() to update it


# ==============================================================================
# EXAMPLE 7: Error Handling - Authorization Failed (Missing Scope)
# ==============================================================================

from py_api_lib.exceptions import AuthorizationError

try:
    # This key only has 'read' scope, trying to create (needs 'write')
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_readonly_key123..."
    )
    domain = api_lib.domain_create("test")  # Requires 'write' scope
except AuthorizationError as e:
    print(f"Authorization failed: {e}")
    # Output:
    # API key lacks required permissions: Missing scope 'write'
    # Current key: ak_stores_prod_***
    # Hint: Check API key scopes (read, write, delete, admin)


# ==============================================================================
# EXAMPLE 8: Error Handling - Rate Limit Exceeded
# ==============================================================================

from py_api_lib.exceptions import RateLimitError

try:
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
    )
    
    # Make too many requests
    for i in range(10000):
        domain = api_lib.domain_read(uuid="some-uuid")
        
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    print(f"Retry after: {e.retry_after} seconds")
    # Output:
    # Rate limit exceeded: 1000 requests/hour limit reached
    # Retry after: 3456 seconds


# ==============================================================================
# EXAMPLE 9: Error Handling - Encryption Required
# ==============================================================================

from py_api_lib.exceptions import EncryptionRequiredError

try:
    # Try to read encrypted object without encryption enabled
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
        # enable_encryption=False (default)
    )
    
    # This object has encrypted fields
    domain = api_lib.domain_read(uuid="encrypted-domain-uuid")
    
except EncryptionRequiredError as e:
    print(f"Encryption required: {e}")
    # Output:
    # Object domain/uuid contains encrypted data.
    # Encrypted fields: ['description', 'metadata']
    
    # Fix: Enable encryption
    api_lib_encrypted = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123...",
        enable_encryption=True,
        encryption_key=b"your-32-byte-encryption-key-here"
    )
    domain = api_lib_encrypted.domain_read(uuid="encrypted-domain-uuid")


# ==============================================================================
# EXAMPLE 10: Comprehensive Error Handling
# ==============================================================================

from py_api_lib.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    EncryptionRequiredError
)

def safe_create_domain(api_lib, name):
    """Example of comprehensive error handling"""
    try:
        domain = api_lib.domain_create(name)
        return domain
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Action: Check your API key or regenerate it")
        return None
        
    except AuthorizationError as e:
        print(f"❌ Authorization failed: {e}")
        print("💡 Action: Request a key with 'write' scope")
        return None
        
    except RateLimitError as e:
        print(f"❌ Rate limit exceeded: {e}")
        print(f"💡 Action: Wait {e.retry_after} seconds or request higher limit")
        return None
        
    except EncryptionRequiredError as e:
        print(f"❌ Encryption required: {e}")
        print("💡 Action: Enable encryption with encryption_key parameter")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

# Usage
api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_key123..."
)

domain = safe_create_domain(api_lib, "ecommerce")
if domain:
    print(f"✅ Created domain: {domain.uuid}")


# ==============================================================================
# EXAMPLE 11: Generate API Key (Admin Only)
# ==============================================================================

# Use admin API key to create new keys
admin_api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_admin_supersecret123..."
)

# Get domain UUID
domain = admin_api_lib.domain_read(fq_name=["stores"])

# Create new API key for UI server
response = admin_api_lib.api_key_create(
    name="ui-server-prod-key",
    parent_uuid=domain.uuid,
    description="Production UI server API key",
    scopes=["read", "write", "delete"],  # NOT admin
    rate_limit_per_hour=10000,
    expires_days=365
)

# SAVE THIS - Only shown once!
plaintext_key = response['plaintext_api_key']
print(f"New API key: {plaintext_key}")
# Example: ak_stores_prod_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Save to secrets manager
import boto3
secrets_client = boto3.client('secretsmanager')
secrets_client.create_secret(
    Name='ui-server-api-key',
    SecretString=plaintext_key
)


# ==============================================================================
# EXAMPLE 12: List API Keys (Admin)
# ==============================================================================

admin_api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_admin_key..."
)

# Get domain
domain = admin_api_lib.domain_read(fq_name=["stores"])

# List all keys for this domain
keys = admin_api_lib.api_keys_list(parent_id=domain.uuid)

for key in keys:
    print(f"Key: {key.key_prefix}")
    print(f"  Description: {key.description}")
    print(f"  Scopes: {key.scopes}")
    print(f"  Enabled: {key.enabled}")
    print(f"  Last used: {key.last_used_at}")
    print(f"  Request count: {key.request_count}")
    print()


# ==============================================================================
# EXAMPLE 13: Revoke API Key (Admin)
# ==============================================================================

admin_api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_admin_key..."
)

# Revoke a compromised key
admin_api_lib.api_key_update(
    uuid="key-uuid-to-revoke",
    enabled=False
)

print("API key revoked successfully")


# ==============================================================================
# EXAMPLE 14: Check Rate Limit Status
# ==============================================================================

api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_key123..."
)

# Get current rate limit status (requires admin scope or own key)
stats = api_lib.rate_limit_status_get(
    key_prefix="ak_stores_prod_***"
)

print(f"Current usage: {stats['current_usage']}/{stats['rate_limit']}")
print(f"Remaining: {stats['remaining']}")
print(f"Window: {stats['window_seconds']} seconds")


# ==============================================================================
# EXAMPLE 15: Context Manager Usage
# ==============================================================================

from py_api_lib.exceptions import AuthenticationError

try:
    with ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
    ) as api_lib:
        domain = api_lib.domain_create("ecommerce")
        project = api_lib.project_create(name="web-app", parent=domain)
        print(f"Created project: {project.uuid}")
    # Connection automatically closed
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")


# ==============================================================================
# EXAMPLE 16: Singleton Pattern
# ==============================================================================

from py_api_lib import ApiLibSingleton
from py_api_lib.exceptions import AuthenticationError

try:
    # Initialize once
    ApiLibSingleton.initialize(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
    )
    
    # Use anywhere in your application
    def create_domain(name):
        api_lib = ApiLibSingleton.get_instance()
        return api_lib.domain_create(name)
    
    def create_project(name, domain):
        api_lib = ApiLibSingleton.get_instance()
        return api_lib.project_create(name=name, parent=domain)
    
    domain = create_domain("ecommerce")
    project = create_project("web-app", domain)
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")


# ==============================================================================
# EXAMPLE 17: Combined with Encryption
# ==============================================================================

import base64
from py_api_lib.exceptions import EncryptionRequiredError

api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_key123...",
    enable_encryption=True,
    encryption_key=base64.b64decode("your-base64-encryption-key"),
    domain_name="stores"
)

# Objects will be encrypted before sending to server
domain = api_lib.domain_create("ecommerce")
project = api_lib.project_create(
    name="web-app",
    parent=domain,
    project_description="Sensitive data here"  # Will be encrypted
)


# ==============================================================================
# EXAMPLE 18: Health Check with Authentication
# ==============================================================================

from py_api_lib.exceptions import AuthenticationError

try:
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
    )
    
    if api_lib.health_check():
        print("Server is healthy and authenticated!")
    else:
        print("Health check failed - check server or API key")
        
except AuthenticationError as e:
    print(f"Authentication failed during health check: {e}")


# ==============================================================================
# EXAMPLE 19: Migration from No Auth to Auth
# ==============================================================================

# Phase 1: Development (no auth)
# Server: REQUIRE_API_AUTH=false
api_lib_dev = ApiLib(
    api_server_host="localhost",
    api_server_port="8082"
    # No api_key needed
)

# Phase 2: Add key via environment variable (no code changes!)
# export API_KEY="ak_stores_prod_key123..."
api_lib_prod = ApiLib.from_config()  # Reads from env

# Phase 3: Explicit key in production config
api_lib_prod = ApiLib.from_config("production_config.yaml")


# ==============================================================================
# EXAMPLE 20: Different Keys for Different Operations
# ==============================================================================

from py_api_lib.exceptions import AuthorizationError

# Read-only operations with read-only key
readonly_api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_readonly_key123..."
)

domains = readonly_api_lib.domains_list(detail=True)
for domain in domains:
    print(f"Domain: {domain.name}")

# Write operations with full-access key
fullaccess_api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_fullaccess_key123..."
)

try:
    new_domain = fullaccess_api_lib.domain_create("new-tenant")
except AuthorizationError as e:
    print(f"Authorization failed: {e}")


# ==============================================================================
# EXAMPLE 21: Debugging Authentication Issues
# ==============================================================================

import logging
from py_api_lib.exceptions import AuthenticationError

# Enable debug logging
logging.getLogger('api_lib').setLevel(logging.DEBUG)
logging.getLogger('api_client').setLevel(logging.DEBUG)

try:
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
    )
    
    # You'll see detailed logs:
    # DEBUG: Authorization: Bearer ak_stores_prod_***
    # DEBUG: POST /domain - Status: 201
    
    domain = api_lib.domain_create("test")
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")


# ==============================================================================
# EXAMPLE 22: Best Practice - Load from Secrets Manager
# ==============================================================================

import boto3
import json
from py_api_lib.exceptions import AuthenticationError

def get_api_key_from_secrets():
    """Load API key from AWS Secrets Manager"""
    secrets_client = boto3.client('secretsmanager')
    response = secrets_client.get_secret_value(SecretId='ui-server-api-key')
    return response['SecretString']

# Use in application
try:
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key=get_api_key_from_secrets()
    )
    
    domain = api_lib.domain_create("ecommerce")
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    print("Check secrets manager configuration")


# ==============================================================================
# EXAMPLE 23: Retry Logic for Rate Limits
# ==============================================================================

import time
from py_api_lib.exceptions import RateLimitError

def create_domain_with_retry(api_lib, name, max_retries=3):
    """Create domain with automatic retry on rate limit"""
    for attempt in range(max_retries):
        try:
            return api_lib.domain_create(name)
            
        except RateLimitError as e:
            if attempt < max_retries - 1:
                print(f"Rate limited. Waiting {e.retry_after}s before retry {attempt + 2}/{max_retries}")
                time.sleep(e.retry_after)
            else:
                print(f"Failed after {max_retries} attempts")
                raise
    
    return None

# Usage
api_lib = ApiLib(
    api_server_host="localhost",
    api_server_port="8082",
    api_key="ak_stores_prod_key123..."
)

domain = create_domain_with_retry(api_lib, "ecommerce")


# ==============================================================================
# EXAMPLE 24: Exception Hierarchy
# ==============================================================================

from py_api_lib.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    EncryptionRequiredError
)

# All custom exceptions can be caught individually or together
try:
    api_lib = ApiLib(
        api_server_host="localhost",
        api_server_port="8082",
        api_key="ak_stores_prod_key123..."
    )
    domain = api_lib.domain_create("test")
    
except (AuthenticationError, AuthorizationError) as e:
    # Handle auth-related errors together
    print(f"Authentication/Authorization error: {e}")
    
except RateLimitError as e:
    # Handle rate limit separately
    print(f"Rate limit error: {e}")
    print(f"Retry after: {e.retry_after}s")
    
except EncryptionRequiredError as e:
    # Handle encryption separately
    print(f"Encryption error: {e}")
    
except Exception as e:
    # Catch-all for other errors
    print(f"Unexpected error: {e}")
