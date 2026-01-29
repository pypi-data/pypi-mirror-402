"""
Query Builder for advanced queries with Django-style lookups.

Provides fluent API for filtering, ordering, pagination, etc.

UPDATED v2.1: Added per-call api_key support for RBAC enforcement
"""

from typing import List, Dict, Any, Optional
import inflection


class QueryBuilder:
    """
    Fluent query builder with Django-style filters.
    
    Example:
        projects = (Project.query()
            .filter(status="active")
            .filter(priority__gte=5)
            .order_by("-created_at")
            .limit(10)
            .all())

    RBAC Example (v2.1):
        # Per-call API key for multi-user server scenarios
        projects = (Project.query()
            .filter(status="active")
            .with_api_key(user_api_key)  # ✅ RBAC override
            .all())
    """
    
    def __init__(self, obj_class, supero_context, api_key: str = None):
        """
        Initialize query builder.
        
        Args:
            obj_class: Object class to query
            supero_context: Supero context for API access
            api_key: Optional API key for RBAC (overrides instance default)

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        self.obj_class = obj_class
        self.context = supero_context
        self._filters = []
        self._order_by_fields = []
        self._limit_value = None
        self._offset_value = 0
        self._only_fields = None
        self._exclude_fields = None
        self._prefetch = []
        self._api_key = api_key  # ✅ NEW: Store API key for RBAC
    
    def with_api_key(self, api_key: str) -> 'QueryBuilder':
        """
        Set API key for RBAC enforcement.

        Use this in multi-user server scenarios where each request
        should use a different user's API key.

        Args:
            api_key: API key to use for this query

        Returns:
            Self for chaining

        Example:
            >>> # Multi-user server scenario
            >>> user_key = get_api_key_from_session(request)
            >>> projects = (Project.query()
            ...     .filter(status="active")
            ...     .with_api_key(user_key)
            ...     .all())

        ✅ NEW: Per-call api_key support for RBAC (v2.1)
        """
        self._api_key = api_key
        return self
    
    def filter(self, **kwargs) -> 'QueryBuilder':
        """
        Add filter conditions.
        
        Supports Django-style lookups:
        - exact: field=value
        - in: field__in=[values]
        - gt/gte: field__gt=value, field__gte=value
        - lt/lte: field__lt=value, field__lte=value
        - contains: field__contains=value
        - icontains: field__icontains=value (case-insensitive)
        - startswith: field__startswith=value
        - endswith: field__endswith=value
        - ne: field__ne=value (not equal)
        - isnull: field__isnull=True/False
        
        Args:
            **kwargs: Filter conditions
            
        Returns:
            Self for chaining
            
        Example:
            >>> query.filter(status="active")
            >>> query.filter(priority__gte=5)
            >>> query.filter(name__contains="Alpha")
        """
        for key, value in kwargs.items():
            self._filters.append((key, value))
        return self
    
    def order_by(self, *fields) -> 'QueryBuilder':
        """
        Order results by fields.
        
        Use '-' prefix for descending order.
        
        Args:
            *fields: Field names to order by
            
        Returns:
            Self for chaining
            
        Example:
            .order_by('name')           # Ascending
            .order_by('-created_at')    # Descending
            .order_by('priority', '-name')  # Multiple
        """
        self._order_by_fields.extend(fields)
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """
        Limit number of results.
        
        Args:
            count: Maximum number of results
            
        Returns:
            Self for chaining
        """
        self._limit_value = count
        return self
    
    def offset(self, count: int) -> 'QueryBuilder':
        """
        Skip first N results.
        
        Args:
            count: Number of results to skip
            
        Returns:
            Self for chaining
        """
        self._offset_value = count
        return self
    
    def paginate(self, page: int, per_page: int = 20) -> 'QueryBuilder':
        """
        Paginate results.
        
        Args:
            page: Page number (1-indexed)
            per_page: Results per page
        
        Returns:
            Self for chaining
            
        Example:
            >>> Project.query().paginate(page=1, per_page=10)
        """
        self._limit_value = per_page
        self._offset_value = (page - 1) * per_page
        return self
    
    def all(self) -> List:
        """
        Execute query and return all results.
        
        Returns:
            List of matching objects
            
        Example:
            >>> projects = Project.query().filter(status="active").all()

            # With RBAC override (v2.1)
            >>> projects = Project.query().with_api_key(user_key).all()
        """
        # Get object type
        obj_type = self.obj_class._OBJ_TYPE
        
        # ✅ RBAC: Pass api_key through to ApiLib
        # Build kwargs for _objects_list
        list_kwargs = {
            'detail': True
        }
        
        # Add domain_name if context has it
        if hasattr(self.context, 'domain_name'):
            list_kwargs['domain_name'] = self.context.domain_name
        
        # ✅ NEW: Add api_key for RBAC if set
        if self._api_key is not None:
            list_kwargs['api_key'] = self._api_key
        
        # Get all objects from API
        objects = self.context.api_lib._objects_list(obj_type, **list_kwargs)
        
        # Apply filters
        objects = self._apply_filters(objects)
        
        # Apply ordering
        objects = self._apply_ordering(objects)
        
        # Apply pagination
        objects = self._apply_pagination(objects)
        
        return objects
    
    def first(self) -> Optional[Any]:
        """
        Get first result or None.
        
        Returns:
            First matching object or None
            
        Example:
            >>> project = Project.query().filter(name="Alpha").first()

            # With RBAC override (v2.1)
            >>> project = Project.query().with_api_key(user_key).filter(name="Alpha").first()
        """
        results = self.limit(1).all()
        return results[0] if results else None
    
    def count(self) -> int:
        """
        Count results without loading objects.
        
        Returns:
            Number of matching objects
            
        Example:
            >>> count = Project.query().filter(status="active").count()

            # With RBAC override (v2.1)
            >>> count = Project.query().with_api_key(user_key).filter(status="active").count()
        """
        return len(self.all())
    
    def exists(self) -> bool:
        """
        Check if any results exist.
        
        Returns:
            True if at least one result exists
            
        Example:
            >>> has_active = Project.query().filter(status="active").exists()

            # With RBAC override (v2.1)
            >>> has_active = Project.query().with_api_key(user_key).filter(status="active").exists()
        """
        return self.limit(1).count() > 0
    
    def get(self, object_id: str) -> Optional[Any]:
        """
        Get a specific object by ID.

        Args:
            object_id: UUID of the object

        Returns:
            Object instance or None if not found

        Example:
            >>> project = Project.query().get("uuid-123")

            # With RBAC override (v2.1)
            >>> project = Project.query().with_api_key(user_key).get("uuid-123")

        ✅ NEW: Added in v2.1 for convenience
        """
        obj_type = self.obj_class._OBJ_TYPE

        # Build kwargs for _object_read
        read_kwargs = {
            'id': object_id
        }

        # Add domain_name if context has it
        if hasattr(self.context, 'domain_name'):
            read_kwargs['domain_name'] = self.context.domain_name

        # ✅ RBAC: Add api_key if set
        if self._api_key is not None:
            read_kwargs['api_key'] = self._api_key

        try:
            return self.context.api_lib._object_read(obj_type, **read_kwargs)
        except Exception:
            return None

    def get_by_fq_name(self, fq_name: List[str]) -> Optional[Any]:
        """
        Get a specific object by fully-qualified name.

        Args:
            fq_name: Fully-qualified name as list of strings

        Returns:
            Object instance or None if not found

        Example:
            >>> project = Project.query().get_by_fq_name(["acme-corp", "backend"])

            # With RBAC override (v2.1)
            >>> project = Project.query().with_api_key(user_key).get_by_fq_name(["acme-corp", "backend"])

        ✅ NEW: Added in v2.1 for convenience
        """
        obj_type = self.obj_class._OBJ_TYPE

        # Build kwargs for _object_read
        read_kwargs = {
            'fq_name': fq_name
        }

        # Add domain_name if context has it
        if hasattr(self.context, 'domain_name'):
            read_kwargs['domain_name'] = self.context.domain_name

        # ✅ RBAC: Add api_key if set
        if self._api_key is not None:
            read_kwargs['api_key'] = self._api_key

        try:
            return self.context.api_lib._object_read(obj_type, **read_kwargs)
        except Exception:
            return None

    def delete(self, object_id: str) -> bool:
        """
        Delete a specific object by ID.

        Args:
            object_id: UUID of the object to delete

        Returns:
            True if deletion succeeded

        Example:
            >>> Project.query().delete("uuid-123")

            # With RBAC override (v2.1)
            >>> Project.query().with_api_key(admin_key).delete("uuid-123")

        ✅ NEW: Added in v2.1 for convenience
        """
        obj_type = self.obj_class._OBJ_TYPE

        # Build kwargs for _object_delete
        delete_kwargs = {
            'id': object_id
        }

        # Add domain_name if context has it
        if hasattr(self.context, 'domain_name'):
            delete_kwargs['domain_name'] = self.context.domain_name

        # ✅ RBAC: Add api_key if set
        if self._api_key is not None:
            delete_kwargs['api_key'] = self._api_key

        try:
            self.context.api_lib._object_delete(obj_type, **delete_kwargs)
            return True
        except Exception:
            return False

    def delete_all(self) -> int:
        """
        Delete all objects matching the current filters.

        WARNING: This is a destructive operation. Use filters to limit scope.

        Returns:
            Number of objects deleted

        Example:
            >>> # Delete inactive projects
            >>> deleted = Project.query().filter(status="inactive").delete_all()

            # With RBAC override (v2.1)
            >>> deleted = Project.query().with_api_key(admin_key).filter(status="inactive").delete_all()

        ✅ NEW: Added in v2.1 for convenience
        """
        # Get all matching objects
        objects = self.all()

        if not objects:
            return 0

        obj_type = self.obj_class._OBJ_TYPE
        deleted_count = 0

        for obj in objects:
            obj_uuid = getattr(obj, 'uuid', None)
            if not obj_uuid:
                continue

            # Build kwargs for _object_delete
            delete_kwargs = {
                'id': obj_uuid
            }

            # Add domain_name if context has it
            if hasattr(self.context, 'domain_name'):
                delete_kwargs['domain_name'] = self.context.domain_name

            # ✅ RBAC: Add api_key if set
            if self._api_key is not None:
                delete_kwargs['api_key'] = self._api_key

            try:
                self.context.api_lib._object_delete(obj_type, **delete_kwargs)
                deleted_count += 1
            except Exception:
                pass

        return deleted_count

    def stats(
        self,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for current query filters.
        
        Combines current query filters with stats aggregation.
        
        Args:
            fields: Fields to get stats for (None = all numeric fields)
        
        Returns:
            Stats dict with count and field statistics
        
        Example:
            >>> # Basic stats
            >>> stats = (Project.query()
            ...     .filter(status="active")
            ...     .stats(fields=['budget', 'hours']))
            >>> print(f"Active projects: {stats['count']}")
            >>> print(f"Total budget: ${stats['fields']['budget']['sum']}")
            >>> 
            >>> # With RBAC
            >>> stats = (Project.query()
            ...     .with_api_key(user_key)
            ...     .filter(status="active")
            ...     .stats(fields=['budget']))
            >>> 
            >>> # Complex filters
            >>> stats = (Order.query()
            ...     .filter(status='completed')
            ...     .filter(created_at__gte='2025-01-01')
            ...     .stats(fields=['amount', 'quantity']))
        """
        # Build match filter from current filters
        match = {}
        for filter_key, filter_value in self._filters:
            # Only include simple equality filters in match
            # Skip Django-style lookups (contains, gt, etc.) as they're not MongoDB syntax
            if '__' not in filter_key:
                match[filter_key] = filter_value
        
        # Get aggregate manager from context
        agg_mgr = self.context.aggregate
        
        # Call with api_key if set
        return agg_mgr.stats(
            self.obj_class._OBJ_TYPE,
            fields=fields,
            match=match if match else None,
            api_key=self._api_key
        )

    def count_by(
        self,
        field: str,
        limit: int = 100,
        sort: str = '-count'
    ) -> List[Dict[str, Any]]:
        """
        Count results grouped by field with current query filters.
        
        Args:
            field: Field to group by
            limit: Max groups to return (1-1000, default 100)
            sort: Sort order ('count', '-count', 'value', '-value')
        
        Returns:
            List of {'value': field_value, 'count': count} dicts
        
        Example:
            >>> # Count by status for active projects
            >>> by_status = (Project.query()
            ...     .filter(active=True)
            ...     .count_by('status'))
            >>> for item in by_status:
            ...     print(f"{item['value']}: {item['count']}")
            >>> 
            >>> # Top 10 categories for completed orders
            >>> by_category = (Order.query()
            ...     .filter(status='completed')
            ...     .count_by('category', limit=10, sort='-count'))
            >>> 
            >>> # With RBAC
            >>> by_role = (User.query()
            ...     .with_api_key(admin_key)
            ...     .filter(enabled=True)
            ...     .count_by('role'))
        """
        # Build match filter from current filters
        match = {}
        for filter_key, filter_value in self._filters:
            if '__' not in filter_key:
                match[filter_key] = filter_value
        
        agg_mgr = self.context.aggregate
        
        return agg_mgr.count_by(
            self.obj_class._OBJ_TYPE,
            field=field,
            match=match if match else None,
            limit=limit,
            sort=sort,
            api_key=self._api_key
        )

    def distinct_values(
        self,
        field: str,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get distinct values for a field with current query filters.
        
        Args:
            field: Field to get distinct values for
            limit: Max values to return (1-10000, default 1000)
        
        Returns:
            List of distinct values
        
        Example:
            >>> # Get unique customer IDs for completed orders
            >>> customer_ids = (Order.query()
            ...     .filter(status='completed')
            ...     .distinct_values('customer_id', limit=100))
            >>> 
            >>> # Unique categories for active products
            >>> categories = (Product.query()
            ...     .filter(active=True)
            ...     .distinct_values('category'))
            >>> 
            >>> # With RBAC
            >>> statuses = (Order.query()
            ...     .with_api_key(user_key)
            ...     .distinct_values('status'))
        """
        # Build match filter from current filters
        match = {}
        for filter_key, filter_value in self._filters:
            if '__' not in filter_key:
                match[filter_key] = filter_value
        
        agg_mgr = self.context.aggregate
        
        return agg_mgr.distinct(
            self.obj_class._OBJ_TYPE,
            field=field,
            match=match if match else None,
            limit=limit,
            api_key=self._api_key
        )

    def aggregate(
        self,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline with current query filters.
        
        The current query filters are prepended as $match stage to the pipeline.
        
        Args:
            pipeline: MongoDB-style aggregation pipeline stages
        
        Returns:
            List of result documents
        
        Example:
            >>> # Group active projects by category
            >>> results = (Project.query()
            ...     .filter(status="active")
            ...     .aggregate([
            ...         {'$group': {
            ...             '_id': '$category',
            ...             'count': {'$sum': 1},
            ...             'total_budget': {'$sum': '$budget'}
            ...         }},
            ...         {'$sort': {'total_budget': -1}}
            ...     ]))
            >>> for item in results:
            ...     print(f"{item['_id']}: {item['count']} projects, ${item['total_budget']}")
            >>> 
            >>> # Top customers for completed orders
            >>> top_customers = (Order.query()
            ...     .filter(status='completed')
            ...     .aggregate([
            ...         {'$group': {
            ...             '_id': '$customer_id',
            ...             'total': {'$sum': '$amount'}
            ...         }},
            ...         {'$sort': {'total': -1}},
            ...         {'$limit': 10}
            ...     ]))
            >>> 
            >>> # With RBAC
            >>> results = (Project.query()
            ...     .with_api_key(user_key)
            ...     .filter(active=True)
            ...     .aggregate(pipeline))
        """
        # Build match filter from current filters
        match = {}
        for filter_key, filter_value in self._filters:
            if '__' not in filter_key:
                match[filter_key] = filter_value
        
        # Prepend match stage if we have filters
        if match:
            pipeline = [{'$match': match}] + pipeline
        
        agg_mgr = self.context.aggregate
        
        return agg_mgr.pipeline(
            self.obj_class._OBJ_TYPE,
            pipeline=pipeline,
            api_key=self._api_key
        )

    def _apply_filters(self, objects: List) -> List:
        """Apply all filter conditions."""
        for filter_key, filter_value in self._filters:
            objects = self._apply_single_filter(objects, filter_key, filter_value)
        return objects
    
    def _apply_single_filter(self, objects: List, key: str, value: Any) -> List:
        """Apply a single filter with lookup support."""
        # Parse lookup (e.g., "status__in", "priority__gte")
        if '__' in key:
            field, lookup = key.rsplit('__', 1)
        else:
            field, lookup = key, 'exact'
        
        filtered = []
        for obj in objects:
            if not hasattr(obj, field):
                continue
            
            obj_value = getattr(obj, field)
            
            if self._matches_lookup(obj_value, lookup, value):
                filtered.append(obj)
        
        return filtered
    
    def _matches_lookup(self, obj_value: Any, lookup: str, filter_value: Any) -> bool:
        """Check if object value matches filter with given lookup."""
        if lookup == 'exact':
            return obj_value == filter_value
        elif lookup == 'in':
            return obj_value in filter_value
        elif lookup == 'gt':
            return obj_value is not None and obj_value > filter_value
        elif lookup == 'gte':
            return obj_value is not None and obj_value >= filter_value
        elif lookup == 'lt':
            return obj_value is not None and obj_value < filter_value
        elif lookup == 'lte':
            return obj_value is not None and obj_value <= filter_value
        elif lookup == 'ne':
            return obj_value != filter_value
        elif lookup == 'isnull':
            return (obj_value is None) == filter_value
        elif lookup == 'contains':
            return obj_value is not None and filter_value in str(obj_value)
        elif lookup == 'icontains':
            return obj_value is not None and filter_value.lower() in str(obj_value).lower()
        elif lookup == 'startswith':
            return obj_value is not None and str(obj_value).startswith(filter_value)
        elif lookup == 'endswith':
            return obj_value is not None and str(obj_value).endswith(filter_value)
        elif lookup == 'regex':
            import re
            return obj_value is not None and bool(re.search(filter_value, str(obj_value)))
        elif lookup == 'iregex':
            import re
            return obj_value is not None and bool(re.search(filter_value, str(obj_value), re.IGNORECASE))
        else:
            # Unknown lookup - treat as exact
            return obj_value == filter_value
    
    def _apply_ordering(self, objects: List) -> List:
        """Apply ordering."""
        if not self._order_by_fields:
            return objects
        
        for field in reversed(self._order_by_fields):
            reverse = field.startswith('-')
            field_name = field.lstrip('-')
            
            # Handle None values in sorting
            def sort_key(obj):
                val = getattr(obj, field_name, None)
                # Put None values at the end
                if val is None:
                    return (1, '')
                return (0, val)
            
            objects.sort(key=sort_key, reverse=reverse)
        
        return objects
    
    def _apply_pagination(self, objects: List) -> List:
        """Apply limit and offset."""
        if self._offset_value:
            objects = objects[self._offset_value:]
        if self._limit_value:
            objects = objects[:self._limit_value]
        return objects

    def __repr__(self) -> str:
        """String representation of query builder state."""
        parts = [f"QueryBuilder({self.obj_class.__name__})"]
        if self._filters:
            parts.append(f".filter({self._filters})")
        if self._order_by_fields:
            parts.append(f".order_by({self._order_by_fields})")
        if self._limit_value:
            parts.append(f".limit({self._limit_value})")
        if self._offset_value:
            parts.append(f".offset({self._offset_value})")
        if self._api_key:
            parts.append(f".with_api_key(***)")
        return ''.join(parts)
