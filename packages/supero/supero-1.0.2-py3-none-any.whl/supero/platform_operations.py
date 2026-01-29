"""
Platform Operations - Module-level functions for platform management.

Handles:
- Tenant registration
- User registration (admin operation)
- Login and authentication
- High-level platform workflows

FIXED v3.0 - Multi-Tenant Hierarchy Support:
- Added tenant parameter to login()
- Added project_uuid and tenant_uuid to register_user()
- Extract and return project/tenant context from JWT
- Improved error messages with hierarchy context
"""

import os
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from .core import Supero

from .platform_client import (
    PlatformClient,
    AuthenticationError,
    AuthorizationError,
    RateLimitError
)

from .core import default_platform_core_host, default_platform_core_port
from .core import Supero

def _build_base_url(host: str, port: int) -> str:
    """Build base_url from host and port for v3.0 PlatformClient."""
    protocol = "https" if port == 443 else "http"
    return f"{protocol}://{host}:{port}/api/v1"

def register_domain(
    domain_name: str,
    admin_email: str,
    admin_password: str,
    domain_display_name: str = None,
    description: str = None,
    platform_core_host: str = None,
    platform_core_port: int = 443,
    self_registration: bool = True,
    **metadata
) -> 'Supero':
    """
    Register a new tenant organization and return connected instance.

    This is a platform operation that creates a new domain.

    For self-registration (default):
        - User must be logged in first
        - Creates tenant and promotes user to domain_admin
        - Returns connected Supero instance with updated JWT

    For admin registration:
        - System admin creates tenant for someone else
        - Admin user is created but separate login required
        - Returns Supero instance after automatic login

    Args:
        domain_name: Unique domain name (e.g., 'acme-corp')
        admin_email: Admin user email
        admin_password: Admin user password
        domain_display_name: Human-readable domain name (optional)
        description: Domain description (optional)
        platform_core_host: Platform Core host (default: from env or 'localhost')
        platform_core_port: Platform Core port (default: 443)
        self_registration: If True, expects user to be logged in (default: True)
        **metadata: Additional metadata

    Returns:
        Connected Supero instance with JWT token

    Raises:
        AuthenticationError: If registration fails or cannot login
        ConnectionError: If cannot connect to Platform Core
        ValueError: If required parameters missing

    Example:
        >>> import supero
        >>> # Self-registration (user creating their own tenant)
        >>> org = supero.register_domain(
        ...     domain_name='my-company',
        ...     admin_email='me@my-company.com',
        ...     admin_password='SecurePass123!',
        ...     domain_display_name='My Company'
        ... )
        >>>
        >>> # Admin registration (requires system admin token)
        >>> org = supero.register_domain(
        ...     domain_name='acme-corp',
        ...     admin_email='admin@acme.com',
        ...     admin_password='SecurePass123!',
        ...     self_registration=False
        ... )
    """
    # Import here to avoid circular dependency

    # Auto-detect platform-core host
    if platform_core_host is None:
        platform_core_host = default_platform_core_host

    # Create platform client (may have auth for self-registration)
    base_url = _build_base_url(platform_core_host, platform_core_port)
    client = PlatformClient(base_url=base_url)

    # Register tenant
    payload = {
        'domain_name': domain_name,
        'domain_display_name': domain_display_name or domain_name,
        'admin_email': admin_email,
        'admin_password': admin_password,
        'description': description or f"Tenant for {domain_name}"
    }

    try:
        result = client.post('/domains/register', json=payload)
    except ConnectionError as e:
        raise ConnectionError(
            f"Could not connect to Platform Core at "
            f"{platform_core_host}:{platform_core_port}. "
            f"Ensure Platform Core server is running. Error: {e}"
        )
    except AuthenticationError as e:
        raise AuthenticationError(f"Tenant registration failed: {e}")

    # Handle self-registration case (session updated)
    if self_registration and result.get('session_updated'):
        # User created their own tenant - new JWT tokens provided
        new_tokens = result.get('tokens', {})
        jwt_token = new_tokens.get('access_token')

        if not jwt_token:
            raise AuthenticationError(
                "Self-registration succeeded but no JWT token returned"
            )

        return Supero.quickstart(
            name=domain_name,
            jwt_token=jwt_token,
            platform_core_host=platform_core_host,
            platform_core_port=platform_core_port
        )

    # Handle admin registration case (no session update)
    # Admin created tenant for someone else - need to login separately
    try:
        return login(
            domain_name=domain_name,
            email=admin_email,
            password=admin_password,
            platform_core_host=platform_core_host,
            platform_core_port=platform_core_port
        )
    except Exception as e:
        raise AuthenticationError(
            f"Tenant registered successfully but login failed: {e}"
        )


def register_user(
    domain_uuid: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    role: str = 'developer',
    permissions: list = None,
    admin_token: str = None,
    project_uuid: str = None,  # ✅ NEW: Project context
    tenant_uuid: str = None,   # ✅ NEW: Tenant context
    platform_core_host: str = None,
    platform_core_port: int = 443
) -> dict:
    """
    Register a new user in an existing tenant.
    
    This is a platform operation that adds a user to a tenant.
    Requires admin authentication.
    
    Multi-Tenant Hierarchy (v3.0):
        Users are created under: domain → project → tenant → user
        
        - If tenant_uuid provided: Create user under that specific tenant
        - If only project_uuid provided: Create under project's default tenant
        - If neither provided: Create under domain's default project's default tenant
    
    Args:
        domain_uuid: Target domain UUID (required)
        email: User email
        password: User password
        first_name: User first name
        last_name: User last name
        role: User role (default: 'developer')
        permissions: List of permissions (optional)
        admin_token: Admin JWT token (required)
        project_uuid: Target project UUID (optional, uses 'default-project' if not provided)
        tenant_uuid: Target tenant UUID (optional, uses 'default-tenant' if not provided)
        platform_core_host: Platform Core host
        platform_core_port: Platform Core port
    
    Returns:
        User info dict with UUID and email
    
    Raises:
        ValueError: If admin_token or domain_uuid not provided
        AuthenticationError: If authentication fails
        AuthorizationError: If insufficient permissions
    
    Example:
        >>> import supero
        >>> # Create user in specific tenant
        >>> user = supero.register_user(
        ...     domain_uuid='domain-123',
        ...     project_uuid='project-456',
        ...     tenant_uuid='tenant-789',
        ...     email='developer@acme.com',
        ...     password='SecurePass123!',
        ...     first_name='John',
        ...     last_name='Developer',
        ...     role='developer',
        ...     permissions=['project:read', 'project:write'],
        ...     admin_token='eyJhbGc...'
        ... )
        >>> print(f"User created: {user['user_uuid']}")
        >>> 
        >>> # Create user in default project/tenant
        >>> user = supero.register_user(
        ...     domain_uuid='domain-123',
        ...     email='viewer@acme.com',
        ...     password='SecurePass123!',
        ...     role='viewer',
        ...     admin_token='eyJhbGc...'
        ... )
    """
    if not admin_token:
        raise ValueError("admin_token is required to register users")
    
    if not domain_uuid:
        raise ValueError("domain_uuid is required to register users")
    
    # Auto-detect platform-core host
    if platform_core_host is None:
        platform_core_host = default_platform_core_host
    
    base_url = _build_base_url(platform_core_host, platform_core_port)
    client = PlatformClient(base_url=base_url, jwt_token=admin_token)
    
    payload = {
        'domain_uuid': domain_uuid,
        'email': email,
        'password': password,
        'first_name': first_name,
        'last_name': last_name,
        'role': role,
        'permissions': permissions or []
    }
    
    # Add project/tenant context if provided
    if project_uuid:
        payload['project_uuid'] = project_uuid
    if tenant_uuid:
        payload['tenant_uuid'] = tenant_uuid
    
    try:
        return client.post('/users/register', json=payload)
    except ConnectionError as e:
        raise ConnectionError(
            f"Could not connect to Platform Core at "
            f"{platform_core_host}:{platform_core_port}. "
            f"Ensure Platform Core server is running. Error: {e}"
        )
    except AuthenticationError as e:
        raise AuthenticationError(
            f"User registration failed - authentication error. "
            f"Check admin_token is valid. Error: {e}"
        )
    except AuthorizationError as e:
        raise AuthorizationError(
            f"User registration failed - permission denied. "
            f"Ensure admin has user:create permission. Error: {e}"
        )


def login(
    domain_name: str,
    email: str,
    password: str,
    project: str = 'default-project',  # ✅ DEFAULT: 'default-project'
    tenant: str = 'default-tenant',    # ✅ DEFAULT: 'default-tenant'
    platform_core_host: str = None,
    platform_core_port: int = 443
) -> 'Supero':
    """
    Login to tenant and return connected Supero instance.
    
    Multi-Tenant Hierarchy (v3.0):
        Authentication flow: domain → project → tenant → user
        
        - If tenant specified: Login to specific tenant in project
        - If only project specified: Login to project's default tenant
        - If neither specified: Login to default project's default tenant
    
    Args:
        domain_name: Domain name (required)
        email: User email (required)
        password: User password (required)
        project: Project name (optional, defaults to 'default-project')
        tenant: Tenant name (optional, defaults to 'default-tenant')
        platform_core_host: Platform Core host
        platform_core_port: Platform Core port
    
    Returns:
        Connected Supero instance with JWT token and context
    
    Raises:
        AuthenticationError: If login fails or invalid credentials
        ConnectionError: If cannot connect to Platform Core
    
    Example:
        >>> import supero
        >>> 
        >>> # Login to default project/tenant
        >>> org = supero.login(
        ...     domain_name='acme-corp',
        ...     email='admin@acme.com',
        ...     password='password'
        ... )
        >>> 
        >>> # Login to specific project (default tenant)
        >>> org = supero.login(
        ...     domain_name='acme-corp',
        ...     email='developer@acme.com',
        ...     password='password',
        ...     project='my-project'
        ... )
        >>> 
        >>> # Login to specific project and tenant
        >>> org = supero.login(
        ...     domain_name='acme-corp',
        ...     email='user@acme.com',
        ...     password='password',
        ...     project='my-project',
        ...     tenant='my-tenant'
        ... )
        >>> 
        >>> # Access context after login
        >>> print(f"Logged in as: {org.user_email}")
        >>> print(f"Domain: {org.domain_name}")
        >>> print(f"Project: {org.project_name}")
        >>> print(f"Tenant: {org.tenant_name}")
    """
    # Import here to avoid circular dependency
    
    # Auto-detect platform-core host
    if platform_core_host is None:
        platform_core_host = default_platform_core_host
    
    base_url = _build_base_url(platform_core_host, platform_core_port)
    client = PlatformClient(base_url=base_url)

    payload = {
        'email': email,
        'password': password,
        'domain': domain_name
    }
    
    if project:
        payload['project'] = project
    
    if tenant:
        payload['tenant'] = tenant
    
    try:
        result = client.post('/auth/login', json=payload)
    except ConnectionError as e:
        raise ConnectionError(
            f"Could not connect to Platform Core at "
            f"{platform_core_host}:{platform_core_port}. "
            f"Ensure Platform Core server is running. Error: {e}"
        )
    except AuthenticationError as e:
        # ✅ IMPROVED: Include project/tenant in error message
        context = f"{email}@{domain_name}"
        if project:
            context += f"/{project}"
        if tenant:
            context += f"/{tenant}"
        raise AuthenticationError(
            f"Login failed for {context}. "
            f"Check credentials and ensure user has access to specified tenant. Error: {e}"
        )
    except AuthorizationError as e:
        context = f"{email}@{domain_name}"
        if project:
            context += f"/{project}"
        if tenant:
            context += f"/{tenant}"
        raise AuthorizationError(
            f"Login failed - permission denied for {context}. "
            f"User may be disabled or lack access to tenant. Error: {e}"
        )
    except Exception as e:
        raise ValueError(
            f"Unexpected error during login for {email}@{domain_name}: {e}"
        )
    
    # Extract JWT token from structured response
    auth_data = result.get('auth', {})
    jwt_token = auth_data.get('access_token')
    
    if not jwt_token:
        # Fallback: try old format
        jwt_token = result.get('token') or result.get('jwt_token')
    
    if not jwt_token:
        raise AuthenticationError(
            "Login succeeded but no JWT token returned. "
            "Response format may have changed. "
            f"Response keys: {list(result.keys())}"
        )
    
    # ✅ NEW: Extract context from response
    user_data = result.get('user', {})
    context_data = result.get('context', {})
    
    # Build full login context from response
    login_context = {
            'user_uuid': user_data.get('user_uuid'),
            'user_email': user_data.get('email') or user_data.get('username'),
            'username': user_data.get('username'),
            'role': user_data.get('role'),
            'domain_name': context_data.get('domain') or domain_name,
            'domain_uuid': context_data.get('domain_uuid'),
            'project_name': context_data.get('project') or project or 'default-project',
            'project_uuid': context_data.get('project_uuid'),
            'tenant_name': context_data.get('tenant') or tenant or 'default-tenant',
            'tenant_uuid': context_data.get('tenant_uuid'),
        }
    
    # Pass login_context to Supero - contains domain_uuid!
    supero_instance = Supero.quickstart(
            name=domain_name,
            jwt_token=jwt_token,
            platform_core_host=platform_core_host,
            platform_core_port=platform_core_port,
            login_context=login_context
        )
    
    return supero_instance


def signup(
    email: str,
    password: str,
    full_name: str,
    platform_core_host: str = None,
    platform_core_port: int = 443
) -> dict:
    """
    Self-service user signup (creates viewer account in default domain).
    
    New users start as 'viewer' in the default domain and can later
    create their own tenant using register_domain() with self_registration=True.
    
    Multi-Tenant Hierarchy (v3.0):
        New users are created under:
        default-domain → default-project → default-tenant → user
    
    Args:
        email: User email
        password: User password
        full_name: User full name
        platform_core_host: Platform Core host
        platform_core_port: Platform Core port
    
    Returns:
        User info dict
    
    Example:
        >>> import supero
        >>> # New user signs up
        >>> user = supero.signup(
        ...     email='newuser@example.com',
        ...     password='SecurePass123!',
        ...     full_name='New User'
        ... )
        >>> print(f"User created: {user['user_uuid']}")
        >>> 
        >>> # Now login (to default project/tenant)
        >>> org = supero.login(
        ...     domain_name='default-domain',
        ...     email='newuser@example.com',
        ...     password='SecurePass123!'
        ... )
    """
    # Auto-detect platform-core host
    if platform_core_host is None:
        platform_core_host = default_platform_core_host
    
    base_url = _build_base_url(platform_core_host, platform_core_port)
    client = PlatformClient(base_url=base_url)
    
    payload = {
        'email': email,
        'password': password,
        'full_name': full_name
    }
    
    try:
        return client.post('/auth/register', json=payload)
    except ConnectionError as e:
        raise ConnectionError(
            f"Could not connect to Platform Core at "
            f"{platform_core_host}:{platform_core_port}. "
            f"Ensure Platform Core server is running. Error: {e}"
        )
    except AuthenticationError as e:
        raise AuthenticationError(
            f"Signup failed for {email}. "
            f"Email may already be registered. Error: {e}"
        )
