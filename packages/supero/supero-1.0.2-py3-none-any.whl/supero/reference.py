"""
Reference class for managing object relationships with link data.

Supports adding metadata to references (e.g., role, permissions, allocation).
"""

from typing import Any, Dict, Optional


class Reference:
    """
    Represents a reference from one object to another with optional link data.
    
    Link data allows storing metadata about the relationship itself, not just
    the connection between objects.
    
    Example:
        # Create reference with link data
        ref = Reference(
            target=user,
            role="lead",
            permissions=["read", "write", "admin"],
            allocation=0.8
        )
        
        # Add to project
        project.add_user(ref)
        
        # Access target object
        print(ref.target.name)
        
        # Access link data
        print(ref.role)
        print(ref.allocation)
    """
    
    def __init__(self, target: Any, **link_data):
        """
        Initialize reference.
        
        Args:
            target: The referenced object (e.g., User, Project, etc.)
            **link_data: Arbitrary link data attributes (role, permissions, etc.)
        
        Example:
            >>> user = User.find_one(name="Alice")
            >>> ref = Reference(user, role="lead", allocation=1.0)
            >>> project.add_user(ref)
        """
        self._target = target
        self._link_data = link_data
        self._modified = False
    
    @property
    def target(self) -> Any:
        """
        Get the referenced object.
        
        Returns:
            The target object
            
        Example:
            >>> for user_ref in project.get_users(with_link_data=True):
            ...     print(user_ref.target.name)
        """
        return self._target
    
    @property
    def link_data(self) -> Dict[str, Any]:
        """
        Get all link data as dict.
        
        Returns:
            Copy of link data dictionary
            
        Example:
            >>> ref = Reference(user, role="lead", allocation=1.0)
            >>> print(ref.link_data)
            {'role': 'lead', 'allocation': 1.0}
        """
        return self._link_data.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get link data value with default.
        
        Args:
            key: Link data attribute name
            default: Default value if key not found
            
        Returns:
            Value or default
            
        Example:
            >>> role = ref.get('role', 'member')
            >>> allocation = ref.get('allocation', 0.5)
        """
        return self._link_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set link data value.
        
        Args:
            key: Link data attribute name
            value: Value to set
            
        Example:
            >>> ref.set('role', 'senior_lead')
            >>> ref.set('allocation', 1.0)
        """
        self._link_data[key] = value
        self._modified = True
    
    def update(self, **kwargs):
        """
        Update multiple link data values.
        
        Args:
            **kwargs: Link data attributes to update
            
        Example:
            >>> ref.update(role='senior_lead', allocation=1.0)
        """
        self._link_data.update(kwargs)
        self._modified = True
    
    def has(self, key: str) -> bool:
        """
        Check if link data has a key.
        
        Args:
            key: Link data attribute name
            
        Returns:
            True if key exists
            
        Example:
            >>> if ref.has('role'):
            ...     print(f"Role: {ref.role}")
        """
        return key in self._link_data
    
    def __getattr__(self, name: str) -> Any:
        """
        Allow accessing link data as attributes.
        
        Args:
            name: Attribute name
            
        Returns:
            Link data value
            
        Raises:
            AttributeError: If attribute not found
            
        Example:
            >>> print(ref.role)
            'lead'
            >>> print(ref.allocation)
            0.8
        """
        if name.startswith('_'):
            # Private attributes - use normal lookup
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        
        if name in self._link_data:
            return self._link_data[name]
        
        raise AttributeError(
            f"Reference has no link data attribute '{name}'. "
            f"Available: {list(self._link_data.keys())}"
        )
    
    def __setattr__(self, name: str, value: Any):
        """
        Allow setting link data as attributes.
        
        Args:
            name: Attribute name
            value: Value to set
            
        Example:
            >>> ref.role = "senior_lead"
            >>> ref.allocation = 1.0
        """
        if name.startswith('_'):
            # Private attributes - use normal assignment
            super().__setattr__(name, value)
        else:
            if not hasattr(self, '_link_data'):
                super().__setattr__('_link_data', {})
            if not hasattr(self, '_modified'):
                super().__setattr__('_modified', False)
            self._link_data[name] = value
            self._modified = True
    
    def is_modified(self) -> bool:
        """
        Check if link data has been modified.
        
        Returns:
            True if modified since creation
            
        Example:
            >>> ref = Reference(user, role="lead")
            >>> print(ref.is_modified())
            False
            >>> ref.role = "senior_lead"
            >>> print(ref.is_modified())
            True
        """
        return self._modified
    
    def save(self):
        """
        Save changes to link data (if context available).
        
        Note: This requires the parent object to be tracked.
        Implementation depends on how link data is stored.
        
        Example:
            >>> ref = project.get_user_ref(user)
            >>> ref.role = "senior_lead"
            >>> ref.save()
        """
        if self._modified:
            # This would need to trigger update on parent object
            # For now, this is a placeholder
            # Implementation would need parent object reference
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert reference to dictionary.
        
        Returns:
            Dict with target info and link data
            
        Example:
            >>> ref_dict = ref.to_dict()
            >>> print(ref_dict)
            {
                'target': {'uuid': '...', 'name': 'Alice'},
                'link_data': {'role': 'lead', 'allocation': 1.0}
            }
        """
        return {
            'target': {
                'uuid': getattr(self._target, 'uuid', None),
                'name': getattr(self._target, 'name', None),
                'obj_type': getattr(self._target, 'obj_type', None)
            },
            'link_data': self._link_data.copy()
        }
    
    def __repr__(self) -> str:
        """
        String representation of reference.
        
        Returns:
            Human-readable string
            
        Example:
            >>> print(ref)
            Reference(target=Alice, role='lead', allocation=1.0)
        """
        target_name = getattr(self._target, 'name', str(self._target))
        link_attrs = ', '.join(f"{k}={v!r}" for k, v in self._link_data.items())
        if link_attrs:
            return f"Reference(target={target_name}, {link_attrs})"
        return f"Reference(target={target_name})"
    
    def __eq__(self, other) -> bool:
        """
        Compare references by target UUID.
        
        Args:
            other: Another Reference object
            
        Returns:
            True if same target
            
        Example:
            >>> ref1 == ref2  # True if same target user
        """
        if not isinstance(other, Reference):
            return False
        
        self_uuid = getattr(self._target, 'uuid', None)
        other_uuid = getattr(other._target, 'uuid', None)
        
        return self_uuid == other_uuid if self_uuid and other_uuid else False
    
    def __hash__(self):
        """
        Hash by target UUID for use in sets/dicts.
        
        Returns:
            Hash value
        """
        target_uuid = getattr(self._target, 'uuid', None)
        return hash(target_uuid) if target_uuid else hash(id(self._target))


# Convenience function
def create_ref(target: Any, **link_data) -> Reference:
    """
    Convenience function to create a Reference.
    
    Args:
        target: Target object
        **link_data: Link data attributes
        
    Returns:
        Reference instance
        
    Example:
        >>> from supero.reference import create_ref
        >>> ref = create_ref(user, role="lead", allocation=1.0)
    """
    return Reference(target, **link_data)
