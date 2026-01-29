"""
User Management - Handle user operations for domains.

Manages:
- User creation and registration
- User listing and retrieval
- User updates and removal
- Current user profile operations

REFACTORED v4.0 (Context-Aware Architecture):
- ✅ Context-aware: Gets domain/project/tenant from PlatformClient
- ✅ Single source of truth: No redundant domain parameters
- ✅ Cleaner API: Fewer parameters needed
- ✅ Full multi-tenant hierarchy support (domain → project → tenant → user)
- ✅ RBAC support: api_key parameter in all methods
- ✅ Optional overrides: Can override project/tenant if needed
"""

from typing import Dict, List, Any, Optional
import logging


class UserManager:
    """
    Manages user operations for a domain with full multi-tenant support.
    
    Handles:
    - User CRUD operations (admin)
    - User listing and filtering (with tenant isolation)
    - Profile operations (current user)
    - Password management
    
    Version 4.0 Refactored Architecture:
    - Context-aware: Gets domain/project/tenant from PlatformClient JWT
    - Single source of truth: PlatformClient owns all context
    - Cleaner initialization: No redundant domain parameters
    - Optional overrides: Can override project/tenant when needed
    - RBAC support: api_key parameter for per-call authorization
    - Tenant filtering for proper isolation
    """
    
    def __init__(
        self,
        platform_client,
        logger: logging.Logger = None,
        domain_uuid: str = None,
        project_uuid: str = None,
        tenant_uuid: str = None
    ):
        """
        Initialize UserManager with context-aware client.
        
        Args:
            platform_client: PlatformClient instance (contains domain/project/tenant context)
            logger: Logger instance (creates new if None)
            project_uuid: Project UUID override (uses client.project_uuid if None)
            tenant_uuid: Tenant UUID override (uses client.tenant_uuid if None)
        
        Example:
            >>> # Simple - context from client (recommended)
            >>> user_mgr = UserManager(platform_client=client, logger=logger)
            >>> print(user_mgr.domain_name)  # From client.domain_name
            >>> 
            >>> # Override context if needed
            >>> user_mgr = UserManager(
            ...     platform_client=client,
            ...     project_uuid='other-project',  # Override
            ...     tenant_uuid='other-tenant'     # Override
            ... )
            >>> 
            >>> # Operations use context automatically
            >>> user = user_mgr.add_user(
            ...     email='dev@acme.com',
            ...     password='Pass123!'
            ...     # domain/project/tenant automatically included!
            ... )
        """
        self.client = platform_client
        self.logger = logger or logging.getLogger(__name__)
        
        # ✅ REFACTORED: Extract from client, allow overrides
        self.domain_name = platform_client.domain_name
        self.domain_uuid = platform_client.domain_uuid
        self.project_uuid = project_uuid or platform_client.project_uuid
        self.tenant_uuid = tenant_uuid or platform_client.tenant_uuid
        
        if domain_uuid or project_uuid or tenant_uuid:
            context_parts = []
            if domain_uuid:
                context_parts.append(f"domain={domain_uuid[:8]}")
            if project_uuid:
                context_parts.append(f"project={project_uuid[:8]}")
            if tenant_uuid:
                context_parts.append(f"tenant={tenant_uuid[:8]}")
            
            self.logger.debug(
                f"UserManager initialized with context: {', '.join(context_parts)}"
            )
    
    # ============================================
    # USER MANAGEMENT (Admin Operations)
    # ============================================
    
    def add_user(
        self,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        role: str = 'developer',
        permissions: List[str] = None,
        domain_uuid: str = None,
        project_uuid: str = None,
        tenant_uuid: str = None,   # ✅ NEW
        api_key: str = None        # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Add user to this domain/project/tenant.
        
        Requires admin permissions.
        
        Args:
            email: User email (unique within domain)
            password: User password
            first_name: User first name
            last_name: User last name
            role: User role (e.g., 'tenant_admin', 'developer', 'viewer')
            permissions: List of permissions (e.g., ['read', 'write', 'admin'])
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            tenant_uuid: Tenant UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'user_uuid': 'uuid',
                'email': 'user@example.com',
                'first_name': 'John',
                'last_name': 'Developer',
                'role': 'developer',
                'domain_uuid': 'domain-uuid',
                'project_uuid': 'project-uuid',
                'tenant_uuid': 'tenant-uuid',
                'created_at': '2025-01-01T00:00:00Z'
            }
        
        Example:
            >>> # With instance context (recommended)
            >>> user = user_mgr.add_user(
            ...     email='dev@acme.com',
            ...     password='SecurePass123!',
            ...     first_name='John',
            ...     last_name='Developer',
            ...     role='developer'
            ... )
            >>> 
            >>> # With explicit context (override)
            >>> user = user_mgr.add_user(
            ...     domain_uuid='other-domain',
            ...     project_uuid='other-project',
            ...     tenant_uuid='other-tenant',
            ...     email='dev@acme.com',
            ...     password='SecurePass123!'
            ... )
            >>> 
            >>> # With RBAC override
            >>> user = user_mgr.add_user(
            ...     email='dev@acme.com',
            ...     password='SecurePass123!',
            ...     api_key=admin_api_key  # Use different API key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        tenant_uuid = tenant_uuid or self.tenant_uuid
        
        if not domain_uuid:
            raise ValueError(
                "domain_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., domain_uuid='...')\n"
                "  2. In method call: add_user(domain_uuid='...', ...)"
            )
        
        if not project_uuid:
            raise ValueError(
                "project_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., project_uuid='...')\n"
                "  2. In method call: add_user(project_uuid='...', ...)"
            )
        
        if not tenant_uuid:
            raise ValueError(
                "tenant_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., tenant_uuid='...')\n"
                "  2. In method call: add_user(tenant_uuid='...', ...)"
            )

        if not email or not email.strip():
            raise ValueError("email is required and cannot be empty")

        if not password or not password.strip():
            raise ValueError("password is required and cannot be empty")


        payload = {
            'domain_name': self.domain_name,
            'domain_uuid': domain_uuid,
            'project_uuid': project_uuid,  # ✅ Always included now
            'tenant_uuid': tenant_uuid,    # ✅ NEW
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'permissions': permissions or []
        }
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key
        
        result = self.client.post('/users/register', **kwargs)
        self.logger.info(f"✓ Added user: {email} (role: {role}, tenant: {tenant_uuid[:8]})")
        return result
    
    def list_users(
        self,
        role: str = None,
        status: str = 'active',
        limit: int = None,
        offset: int = None,
        domain_uuid: str = None,
        project_uuid: str = None,   # ✅ NEW
        tenant_uuid: str = None,    # ✅ NEW
        api_key: str = None         # ✅ NEW (RBAC)
    ) -> List[Dict[str, Any]]:
        """
        List users in this domain/project/tenant.
        
        Args:
            role: Filter by role (None = all roles)
            status: Filter by status (default: 'active')
            limit: Maximum number of results
            offset: Number of results to skip (for pagination)
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            tenant_uuid: Tenant UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            List of user info dicts
        
        Example:
            >>> # All active users in instance context (uses defaults)
            >>> all_users = user_mgr.list_users()
            >>> 
            >>> # Only admins in specific tenant
            >>> admins = user_mgr.list_users(
            ...     role='tenant_admin',
            ...     tenant_uuid='tenant-123'
            ... )
            >>> 
            >>> # Paginated results with RBAC
            >>> page1 = user_mgr.list_users(
            ...     limit=10,
            ...     offset=0,
            ...     api_key=user_api_key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        tenant_uuid = tenant_uuid or self.tenant_uuid
        
        if not domain_uuid:
            raise ValueError(
                "domain_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., domain_uuid='...')\n"
                "  2. In method call: list_users(domain_uuid='...', ...)"
            )
        
        params = {}
        
        # ✅ Add project/tenant filters for proper isolation
        if project_uuid:
            params['project_uuid'] = project_uuid
        if tenant_uuid:
            params['tenant_uuid'] = tenant_uuid
        
        if role:
            params['role'] = role
        if status:
            params['status'] = status
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get(f'/domains/{domain_uuid}/users', **kwargs)
    
    def get_user(
        self,
        user_uuid: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Get user details by UUID.
        
        Args:
            user_uuid: User UUID
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            User info dict
        
        Example:
            >>> user = user_mgr.get_user('user-uuid-123')
            >>> print(f"Name: {user['first_name']} {user['last_name']}")
            >>> print(f"Role: {user['role']}")
            >>> print(f"Tenant: {user['tenant_uuid']}")
            >>> 
            >>> # With RBAC override
            >>> user = user_mgr.get_user('user-uuid-123', api_key=admin_key)
        """
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get(f'/users/{user_uuid}', **kwargs)
    
    def update_user(
        self,
        user_uuid: str,
        api_key: str = None,  # ✅ NEW (RBAC)
        **updates
    ) -> Dict[str, Any]:
        """
        Update user role and permissions.
        
        Requires admin permissions.
        
        Args:
            user_uuid: User UUID
            api_key: API key for RBAC (optional, overrides instance default)
            **updates: Fields to update (role, permissions, etc.)
        
        Returns:
            Updated user info dict
        
        Example:
            >>> # Promote user to admin
            >>> user_mgr.update_user(
            ...     user_uuid='user-123',
            ...     role='tenant_admin',
            ...     permissions=['user:create', 'user:read', 'user:update']
            ... )
            >>> 
            >>> # With RBAC override
            >>> user_mgr.update_user(
            ...     user_uuid='user-123',
            ...     api_key=domain_admin_key,
            ...     role='tenant_admin'
            ... )
        """
        # Create copy to avoid side effects
        payload = dict(updates)
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key
        
        result = self.client.put(f'/users/{user_uuid}/role', **kwargs)
        self.logger.info(f"✓ Updated user: {user_uuid}")
        return result
    
    def disable_user(
        self,
        user_uuid: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> bool:
        """
        Disable user account (soft delete).
        
        Requires admin permissions.
        User can be re-enabled later with enable_user().
        
        Args:
            user_uuid: User UUID
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            True if successful
        
        Example:
            >>> user_mgr.disable_user('user-123')
            >>> # With RBAC override
            >>> user_mgr.disable_user('user-123', api_key=admin_key)
        """
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        response = self.client.put(f'/users/{user_uuid}/disable', **kwargs)
        
        if response.get('success', False):
            self.logger.info(f"✓ User disabled: {user_uuid}")
        
        return response.get('success', False)
    
    def enable_user(
        self,
        user_uuid: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> bool:
        """
        Enable a disabled user account.
        
        Requires admin permissions.
        
        Args:
            user_uuid: User UUID
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            True if successful
        
        Example:
            >>> user_mgr.enable_user('user-123')
            >>> # With RBAC override
            >>> user_mgr.enable_user('user-123', api_key=admin_key)
        """
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        response = self.client.put(f'/users/{user_uuid}/enable', **kwargs)
        
        if response.get('success', False):
            self.logger.info(f"✓ User enabled: {user_uuid}")
        
        return response.get('success', False)
    
    def remove_user(
        self,
        user_uuid: str,
        permanent: bool = False,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> bool:
        """
        Remove user from this domain/tenant.
        
        Requires admin permissions.
        
        Args:
            user_uuid: User UUID
            permanent: If True, permanently delete. If False, disable (default)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            True if successful
        
        Warning:
            Permanent deletion cannot be undone!
        
        Example:
            >>> # Disable user (can be re-enabled)
            >>> user_mgr.remove_user('user-123')
            >>> 
            >>> # Permanently delete with RBAC
            >>> user_mgr.remove_user(
            ...     'user-123',
            ...     permanent=True,
            ...     api_key=domain_admin_key
            ... )
        """
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        if permanent:
            # Permanent deletion
            response = self.client.delete(f'/users/{user_uuid}', **kwargs)
            action = "deleted"
        else:
            # Disable user account
            response = self.client.put(f'/users/{user_uuid}/disable', **kwargs)
            action = "disabled"
        
        if response.get('success', False):
            self.logger.info(f"✓ User {action}: {user_uuid}")
        
        return response.get('success', False)
    
    def search_users(
        self,
        query: str,
        fields: List[str] = None,
        limit: int = 20,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        tenant_uuid: str = None,   # ✅ NEW
        api_key: str = None        # ✅ NEW (RBAC)
    ) -> List[Dict[str, Any]]:
        """
        Search users by query string.
        
        WARNING: This endpoint is documented but not verified by test client.
        May not be implemented in all Platform UI versions.
        
        Args:
            query: Search query
            fields: Fields to search in (default: ['first_name', 'last_name', 'email'])
            limit: Maximum results
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            tenant_uuid: Tenant UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            List of matching user dicts
        
        Example:
            >>> # Search in instance context (uses defaults)
            >>> users = user_mgr.search_users(query='john')
            >>> 
            >>> # Search specific fields in specific tenant
            >>> users = user_mgr.search_users(
            ...     query='developer',
            ...     fields=['role', 'first_name'],
            ...     tenant_uuid='tenant-123'
            ... )
            >>> 
            >>> # With RBAC override
            >>> users = user_mgr.search_users(
            ...     query='john',
            ...     api_key=user_api_key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        tenant_uuid = tenant_uuid or self.tenant_uuid
        
        if not domain_uuid:
            raise ValueError(
                "domain_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., domain_uuid='...')\n"
                "  2. In method call: search_users(domain_uuid='...', ...)"
            )
        
        params = {
            'query': query,
            'limit': limit
        }
        
        # ✅ Add project/tenant filters for proper isolation
        if project_uuid:
            params['project_uuid'] = project_uuid
        if tenant_uuid:
            params['tenant_uuid'] = tenant_uuid
        
        if fields:
            params['fields'] = ','.join(fields)
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get('/users/search', **kwargs)
    
    # ============================================
    # USER ROLES & PERMISSIONS
    # ============================================
    
    def list_roles(
        self,
        domain_uuid: str = None,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> List[Dict[str, Any]]:
        """
        List available roles in this domain.
        
        WARNING: This endpoint is documented but not verified by test client.
        May not be implemented in all Platform UI versions.
        
        Args:
            domain_uuid: Domain UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            List of role definitions with permissions
        
        Example:
            >>> roles = user_mgr.list_roles()
            >>> for role in roles:
            ...     print(f"{role['name']}: {role['permissions']}")
            >>> 
            >>> # With RBAC override
            >>> roles = user_mgr.list_roles(api_key=admin_key)
        """
        # ✅ Use provided domain_uuid or fall back to instance variable
        domain_uuid = domain_uuid or self.domain_uuid
        
        if not domain_uuid:
            raise ValueError(
                "domain_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., domain_uuid='...')\n"
                "  2. In method call: list_roles(domain_uuid='...', ...)"
            )
        
        params = {'domain_uuid': domain_uuid}
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get('/roles', **kwargs)
    
    def assign_role(
        self,
        user_uuid: str,
        role: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Assign role to user.
        
        Args:
            user_uuid: User UUID
            role: Role name
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            Updated user info
        
        Example:
            >>> user_mgr.assign_role('user-123', 'tenant_admin')
            >>> # With RBAC override
            >>> user_mgr.assign_role('user-123', 'tenant_admin', api_key=admin_key)
        """
        return self.update_user(user_uuid, api_key=api_key, role=role)
    
    def grant_permissions(
        self,
        user_uuid: str,
        permissions: List[str],
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Grant additional permissions to user.
        
        Args:
            user_uuid: User UUID
            permissions: List of permissions to add
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            Updated user info
        
        Note:
            This method performs a GET followed by a PUT. In high-concurrency
            environments, permissions modified between these calls may be lost.
        
        Example:
            >>> user_mgr.grant_permissions('user-123', ['project:write'])
            >>> # With RBAC override
            >>> user_mgr.grant_permissions(
            ...     'user-123',
            ...     ['project:write'],
            ...     api_key=admin_key
            ... )
        """
        # Get current user (with RBAC)
        user = self.get_user(user_uuid, api_key=api_key)
        current_perms = set(user.get('permissions', []))
        
        # Add new permissions
        new_perms = current_perms.union(set(permissions))
        
        # Update user (with RBAC)
        return self.update_user(user_uuid, api_key=api_key, permissions=list(new_perms))
    
    def revoke_permissions(
        self,
        user_uuid: str,
        permissions: List[str],
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Revoke permissions from user.
        
        Args:
            user_uuid: User UUID
            permissions: List of permissions to remove
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            Updated user info
        
        Note:
            This method performs a GET followed by a PUT. In high-concurrency
            environments, permissions modified between these calls may be lost.
        
        Example:
            >>> user_mgr.revoke_permissions('user-123', ['project:write'])
            >>> # With RBAC override
            >>> user_mgr.revoke_permissions(
            ...     'user-123',
            ...     ['project:write'],
            ...     api_key=admin_key
            ... )
        """
        # Get current user (with RBAC)
        user = self.get_user(user_uuid, api_key=api_key)
        current_perms = set(user.get('permissions', []))
        
        # Remove permissions
        new_perms = current_perms - set(permissions)
        
        # Update user (with RBAC)
        return self.update_user(user_uuid, api_key=api_key, permissions=list(new_perms))
    
    # ============================================
    # CURRENT USER OPERATIONS (Profile)
    # ============================================
    
    def whoami(
        self,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Get current authenticated user info.
        
        Args:
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'user_uuid': 'user-uuid',
                'email': 'user@acme.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'developer',
                'permissions': ['project:read', 'project:write'],
                'domain_uuid': 'domain-uuid',
                'domain_name': 'acme-corp',
                'project_uuid': 'project-uuid',
                'tenant_uuid': 'tenant-uuid'
            }
        
        Example:
            >>> user = user_mgr.whoami()
            >>> print(f"Logged in as: {user['email']} ({user['role']})")
            >>> print(f"Tenant: {user['tenant_uuid']}")
            >>> 
            >>> # With RBAC override
            >>> user = user_mgr.whoami(api_key=user_api_key)
        """
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get('/auth/me', **kwargs)
    
    def update_profile(
        self,
        api_key: str = None,  # ✅ NEW (RBAC)
        **updates
    ) -> Dict[str, Any]:
        """
        Update current user's profile.
        
        Args:
            api_key: API key for RBAC (optional, overrides instance default)
            **updates: Profile fields to update (first_name, last_name, phone, etc.)
        
        Returns:
            Updated user info
        
        Note:
            Cannot update role or permissions through this method.
            Use update_user() with admin credentials instead.
        
        Example:
            >>> user_mgr.update_profile(
            ...     first_name='John',
            ...     last_name='Q. Developer',
            ...     phone='+1-555-0200'
            ... )
            >>> 
            >>> # With RBAC override
            >>> user_mgr.update_profile(
            ...     first_name='John',
            ...     api_key=user_api_key
            ... )
        """
        # Remove protected fields (create new dict)
        protected = ['role', 'permissions', 'email', 'domain_name', 'domain_uuid',
                     'project_uuid', 'tenant_uuid']  # ✅ Added new protected fields
        
        # Filter out protected fields
        filtered_updates = {
            k: v for k, v in updates.items()
            if k not in protected
        }
        
        # Warn about removed fields
        removed = set(updates.keys()) - set(filtered_updates.keys())
        for field in removed:
            self.logger.warning(f"Cannot update protected field: {field}")
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': filtered_updates}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.put('/auth/me', **kwargs)
    
    def change_password(
        self,
        old_password: str,
        new_password: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> bool:
        """
        Change current user's password.
        
        WARNING: This endpoint is documented but not verified by test client.
        May not be implemented in all Platform UI versions.
        
        Args:
            old_password: Current password (for verification)
            new_password: New password
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            True if successful
        
        Example:
            >>> success = user_mgr.change_password('OldPass123', 'NewPass456!')
            >>> # With RBAC override
            >>> success = user_mgr.change_password(
            ...     'OldPass123',
            ...     'NewPass456!',
            ...     api_key=user_api_key
            ... )
        """
        payload = {
            'old_password': old_password,
            'new_password': new_password
        }
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key
        
        response = self.client.post('/auth/change-password', **kwargs)
        
        if response.get('success', False):
            self.logger.info("✓ Password changed successfully")
        
        return response.get('success', False)
    
    def request_password_reset(
        self,
        email: str,
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> bool:
        """
        Request password reset for a user.
        
        WARNING: This endpoint is not documented in official API.
        May not be implemented in all Platform UI versions.
        
        Sends password reset email to user.
        
        Args:
            email: User email address
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            True if reset email sent
        
        Example:
            >>> user_mgr.request_password_reset('user@acme.com')
            >>> # With RBAC override
            >>> user_mgr.request_password_reset('user@acme.com', api_key=admin_key)
        """
        payload = {
            'email': email,
            'domain_name': self.domain_name
        }
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'json': payload}
        if api_key:
            kwargs['api_key'] = api_key
        
        response = self.client.post('/auth/password/reset/request', **kwargs)
        return response.get('success', False)
    
    # ============================================
    # BULK OPERATIONS
    # ============================================
    
    def bulk_add_users(
        self,
        users: List[Dict[str, Any]],
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        tenant_uuid: str = None,   # ✅ NEW
        api_key: str = None        # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Add multiple users in bulk.
        
        Args:
            users: List of user data dicts
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            tenant_uuid: Tenant UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'created': [user1, user2, ...],
                'failed': [{'email': 'x', 'error': 'msg'}, ...]
            }
        
        Example:
            >>> users = [
            ...     {
            ...         'email': 'dev1@acme.com',
            ...         'password': 'Pass123!',
            ...         'first_name': 'Developer',
            ...         'last_name': 'One',
            ...         'role': 'developer'
            ...     },
            ...     {
            ...         'email': 'dev2@acme.com',
            ...         'password': 'Pass456!',
            ...         'first_name': 'Developer',
            ...         'last_name': 'Two',
            ...         'role': 'developer'
            ...     }
            ... ]
            >>> # Uses instance context
            >>> result = user_mgr.bulk_add_users(users)
            >>> 
            >>> # With RBAC override
            >>> result = user_mgr.bulk_add_users(users, api_key=admin_key)
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        tenant_uuid = tenant_uuid or self.tenant_uuid
        
        if not domain_uuid:
            raise ValueError(
                "domain_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., domain_uuid='...')\n"
                "  2. In method call: bulk_add_users(domain_uuid='...', ...)"
            )
        
        if not project_uuid:
            raise ValueError(
                "project_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., project_uuid='...')\n"
                "  2. In method call: bulk_add_users(project_uuid='...', ...)"
            )
        
        if not tenant_uuid:
            raise ValueError(
                "tenant_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., tenant_uuid='...')\n"
                "  2. In method call: bulk_add_users(tenant_uuid='...', ...)"
            )
        
        created = []
        failed = []
        
        for user_data in users:
            try:
                # Ensure UUIDs are in each user data
                user_data['domain_uuid'] = domain_uuid
                user_data['project_uuid'] = project_uuid
                user_data['tenant_uuid'] = tenant_uuid
                
                # Add api_key if provided
                if api_key:
                    user_data['api_key'] = api_key
                
                result = self.add_user(**user_data)
                created.append(result)
            except Exception as e:
                failed.append({
                    'email': user_data.get('email'),
                    'error': str(e)
                })
                self.logger.error(f"  ✗ Failed to create {user_data.get('email')}: {e}")
        
        self.logger.info(
            f"Bulk user creation: {len(created)} created, {len(failed)} failed"
        )
        
        return {
            'created': created,
            'failed': failed
        }
    
    def bulk_update_users(
        self,
        updates: List[Dict[str, Any]],
        api_key: str = None  # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Update multiple users in bulk.
        
        Args:
            updates: List of update dicts with 'user_uuid' and update fields
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'updated': [user1, user2, ...],
                'failed': [{'user_uuid': 'x', 'error': 'msg'}, ...]
            }
        
        Example:
            >>> updates = [
            ...     {'user_uuid': 'user-1', 'role': 'tenant_admin'},
            ...     {'user_uuid': 'user-2', 'role': 'tenant_admin'}
            ... ]
            >>> result = user_mgr.bulk_update_users(updates)
            >>> 
            >>> # With RBAC override
            >>> result = user_mgr.bulk_update_users(updates, api_key=admin_key)
        """
        updated = []
        failed = []
        
        for update_data in updates:
            # Create a copy to avoid modifying original
            update_copy = update_data.copy()
            user_uuid = update_copy.pop('user_uuid', None)
            
            if not user_uuid:
                failed.append({'error': 'Missing user_uuid'})
                continue
            
            try:
                result = self.update_user(user_uuid, api_key=api_key, **update_copy)
                updated.append(result)
            except Exception as e:
                failed.append({
                    'user_uuid': user_uuid,
                    'error': str(e)
                })
                self.logger.error(f"  ✗ Failed to update {user_uuid}: {e}")
        
        self.logger.info(
            f"Bulk user update: {len(updated)} updated, {len(failed)} failed"
        )
        
        return {
            'updated': updated,
            'failed': failed
        }
    
    # ============================================
    # USER STATISTICS
    # ============================================
    
    def get_user_stats(
        self,
        domain_uuid: str = None,
        project_uuid: str = None,  # ✅ NEW
        tenant_uuid: str = None,   # ✅ NEW
        api_key: str = None        # ✅ NEW (RBAC)
    ) -> Dict[str, Any]:
        """
        Get user statistics for this domain/project/tenant.
        
        WARNING: This endpoint is not documented in official API.
        May not be implemented in all Platform UI versions.
        
        Args:
            domain_uuid: Domain UUID (optional if set at initialization)
            project_uuid: Project UUID (optional if set at initialization)
            tenant_uuid: Tenant UUID (optional if set at initialization)
            api_key: API key for RBAC (optional, overrides instance default)
        
        Returns:
            {
                'total_users': 50,
                'by_role': {
                    'tenant_admin': 5,
                    'developer': 20,
                    'viewer': 25
                },
                'by_status': {
                    'active': 45,
                    'inactive': 5
                },
                'recent_logins': 30  # Last 24 hours
            }
        
        Example:
            >>> # Uses instance context
            >>> stats = user_mgr.get_user_stats()
            >>> print(f"Total users: {stats['total_users']}")
            >>> 
            >>> # Stats for specific tenant with RBAC
            >>> stats = user_mgr.get_user_stats(
            ...     tenant_uuid='tenant-123',
            ...     api_key=admin_key
            ... )
        """
        # ✅ Use provided UUIDs or fall back to instance variables
        domain_uuid = domain_uuid or self.domain_uuid
        project_uuid = project_uuid or self.project_uuid
        tenant_uuid = tenant_uuid or self.tenant_uuid
        
        if not domain_uuid:
            raise ValueError(
                "domain_uuid is required. Provide it either:\n"
                "  1. At UserManager initialization: UserManager(..., domain_uuid='...')\n"
                "  2. In method call: get_user_stats(domain_uuid='...', ...)"
            )
        
        params = {'domain_uuid': domain_uuid}
        
        # ✅ Add project/tenant filters for proper scoping
        if project_uuid:
            params['project_uuid'] = project_uuid
        if tenant_uuid:
            params['tenant_uuid'] = tenant_uuid
        
        # ✅ RBAC: Pass api_key to client if provided
        kwargs = {'params': params}
        if api_key:
            kwargs['api_key'] = api_key
        
        return self.client.get('/users/stats', **kwargs)
