"""
CRUD Manager - REST-based CRUD operations without SDK download.

Provides org.crud.* API that mirrors the typed SDK functionality
but works immediately without install_sdk().

Usage:
    org = login(domain_name="my-app", email="...", password="...")
    
    # Basic CRUD
    task = org.crud.create("task", name="t1", title="Learn Supero")
    task = org.crud.get("task", uuid)
    tasks = org.crud.list("task")
    org.crud.update("task", uuid, done=True)
    org.crud.delete("task", uuid)
    
    # Query with filters
    tasks = org.crud.query("task").filter(done=False).order_by("-created").limit(10).all()
    
    # Aggregations
    total = org.crud.count("task")
    revenue = org.crud.sum("order", "amount")
    
    # References
    org.crud.set_ref("order", order_uuid, "customer", customer_uuid)
    
    # Parent-child objects
    order = org.crud.create("order", name="order-1", parent=customer, total=99.99)
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import copy
import logging

logger = logging.getLogger(__name__)


class CrudQueryBuilder:
    """
    Chainable query builder for REST-based queries.
    
    Mirrors QueryBuilder API but uses REST endpoints.
    
    Usage:
        org.crud.query("task") \\
            .filter(done=False, priority="high") \\
            .order_by("-created_at") \\
            .limit(10) \\
            .all()
    """
    
    def __init__(self, crud_manager: 'CrudManager', type_name: str):
        self._crud = crud_manager
        self._type_name = type_name
        self._filters: Dict[str, Any] = {}
        self._order_by: List[str] = []
        self._limit_val: Optional[int] = None
        self._offset_val: int = 0
        self._api_key: Optional[str] = None
    
    def with_api_key(self, api_key: str) -> 'CrudQueryBuilder':
        """Set API key for RBAC."""
        self._api_key = api_key
        return self
    
    def filter(self, **kwargs) -> 'CrudQueryBuilder':
        """Add filter conditions."""
        self._filters.update(kwargs)
        return self
    
    def order_by(self, *fields) -> 'CrudQueryBuilder':
        """Set ordering. Prefix with '-' for descending."""
        self._order_by = list(fields)
        return self
    
    def limit(self, count: int) -> 'CrudQueryBuilder':
        """Limit number of results."""
        self._limit_val = count
        return self
    
    def offset(self, count: int) -> 'CrudQueryBuilder':
        """Skip first N results."""
        self._offset_val = count
        return self
    
    def paginate(self, page: int, per_page: int = 20) -> 'CrudQueryBuilder':
        """Paginate results (1-indexed pages)."""
        self._limit_val = per_page
        self._offset_val = (page - 1) * per_page
        return self
    
    def _build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for REST call."""
        params = {}
        if self._filters:
            params["filters"] = self._filters
        if self._order_by:
            params["order_by"] = self._order_by
        if self._limit_val is not None:
            params["limit"] = self._limit_val
        if self._offset_val:
            params["offset"] = self._offset_val
        return params
    
    def all(self) -> List[Dict[str, Any]]:
        """Execute query and return all results."""
        params = self._build_query_params()
        return self._crud._query(self._type_name, api_key=self._api_key, **params)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Execute query and return first result."""
        self._limit_val = 1
        results = self.all()
        return results[0] if results else None
    
    def count(self) -> int:
        """Return count of matching objects."""
        return self._crud._count(self._type_name, filters=self._filters, api_key=self._api_key)
    
    def exists(self) -> bool:
        """Check if any matching objects exist."""
        return self.count() > 0
    
    def get(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Get object by UUID."""
        return self._crud.get(self._type_name, uuid, api_key=self._api_key)
    
    def get_by_fq_name(self, fq_name: List[str]) -> Optional[Dict[str, Any]]:
        """Get object by fully qualified name."""
        return self._crud.get_by_fq_name(self._type_name, fq_name, api_key=self._api_key)
    
    def delete(self, uuid: str) -> bool:
        """Delete object by UUID."""
        return self._crud.delete(self._type_name, uuid, api_key=self._api_key)
    
    def delete_all(self) -> int:
        """Delete all matching objects. Returns count deleted."""
        return self._crud._delete_all(self._type_name, filters=self._filters, api_key=self._api_key)
    
    def __repr__(self) -> str:
        return f"CrudQueryBuilder({self._type_name}, filters={self._filters})"


class CrudManager:
    """
    REST-based CRUD manager providing org.crud.* API.
    
    Works without SDK download - uses REST endpoints directly.
    """
    
    def __init__(self, supero):
        """
        Initialize CrudManager.
        
        Args:
            supero: Supero instance with domain_name and HTTP methods
        """
        self._org = supero
    
    @property
    def _domain(self) -> str:
        return self._org.domain_name
    
    def _endpoint(self, type_name: str, *parts) -> str:
        """Build endpoint URL."""
        base = f"/crud/{self._domain}/{type_name}"
        if parts:
            base += "/" + "/".join(str(p) for p in parts)
        return base
    
    def _request_kwargs(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Build request kwargs with optional API key."""
        kwargs = {}
        if api_key:
            kwargs["headers"] = {"X-API-Key": api_key}
        return kwargs
    
    # =========================================
    # Basic CRUD
    # =========================================
    
    def create(self, type_name: str, parent: Optional[Dict] = None, 
               api_key: Optional[str] = None, **data) -> Dict[str, Any]:
        """
        Create a new object.
        
        Args:
            type_name: Schema type (e.g., "task", "customer")
            parent: Optional parent object dict (must have 'uuid' and object type)
            api_key: Optional API key for RBAC
            **data: Object fields (must include 'name')
        
        Returns:
            Created object with uuid
        
        Example:
            # Top-level object (parent is domain)
            task = org.crud.create("task", name="t1", title="My Task")
            
            # Child object (parent is another object)
            order = org.crud.create("order", parent=customer, name="o1", total=99.99)
        """
        if "name" not in data:
            raise ValueError("'name' field is required")
        
        # Handle parent relationship
        if parent:
            # Parent is another object
            parent_uuid = parent.get("uuid")
            parent_type = parent.get("object_type", parent.get("type"))
            if not parent_uuid or not parent_type:
                raise ValueError("Parent must have 'uuid' and 'object_type' fields")
            data.setdefault("fq_name", [self._domain, parent["name"], data["name"]])
            data.setdefault("parent_type", parent_type)
            data.setdefault("parent_uuid", parent_uuid)
        else:
            # Parent is domain
            data.setdefault("fq_name", [self._domain, data["name"]])
            data.setdefault("parent_type", "domain")
        
        return self._org.post(self._endpoint(type_name), json=data, **self._request_kwargs(api_key))
    
    def get(self, type_name: str, uuid: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get object by UUID.
        
        Args:
            type_name: Schema type
            uuid: Object UUID
            api_key: Optional API key for RBAC
        
        Returns:
            Object dict or None if not found
        
        Example:
            task = org.crud.get("task", "550e8400-e29b-41d4-a716-446655440000")
        """
        try:
            return self._org.get(self._endpoint(type_name, uuid), **self._request_kwargs(api_key))
        except Exception as e:
            logger.debug(f"Get {type_name}/{uuid} failed: {e}")
            return None
    
    def get_by_fq_name(self, type_name: str, fq_name: List[str], 
                       api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get object by fully qualified name.
        
        Args:
            type_name: Schema type
            fq_name: Fully qualified name list
            api_key: Optional API key for RBAC
        
        Returns:
            Object dict or None if not found
        
        Example:
            task = org.crud.get_by_fq_name("task", ["my-domain", "task-001"])
        """
        try:
            return self._org.post(
                self._endpoint(type_name, "by-fq-name"),
                json={"fq_name": fq_name},
                **self._request_kwargs(api_key)
            )
        except Exception as e:
            logger.debug(f"Get by fq_name {type_name}/{fq_name} failed: {e}")
            return None
    
    def list(self, type_name: str, limit: int = 100, offset: int = 0,
             api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all objects of a type.
        
        Args:
            type_name: Schema type
            limit: Max results (default 100)
            offset: Skip first N results
            api_key: Optional API key for RBAC
        
        Returns:
            List of objects
        
        Example:
            tasks = org.crud.list("task")
        """
        result = self._org.get(
            self._endpoint(type_name),
            params={"limit": limit, "offset": offset},
            **self._request_kwargs(api_key)
        )
        # Handle both list and paginated response formats
        if isinstance(result, list):
            return result
        return result.get("results", result.get("items", []))
    
    def update(self, type_name: str, uuid: str, api_key: Optional[str] = None,
               **data) -> Dict[str, Any]:
        """
        Update an object.
        
        Args:
            type_name: Schema type
            uuid: Object UUID
            api_key: Optional API key for RBAC
            **data: Fields to update
        
        Returns:
            Updated object
        
        Example:
            org.crud.update("task", uuid, done=True, priority="low")
        """
        return self._org.put(
            self._endpoint(type_name, uuid), 
            json=data, 
            **self._request_kwargs(api_key)
        )
    
    def delete(self, type_name: str, uuid: str, api_key: Optional[str] = None) -> bool:
        """
        Delete an object.
        
        Args:
            type_name: Schema type
            uuid: Object UUID
            api_key: Optional API key for RBAC
        
        Returns:
            True if deleted
        
        Example:
            org.crud.delete("task", uuid)
        """
        try:
            self._org.delete(self._endpoint(type_name, uuid), **self._request_kwargs(api_key))
            return True
        except Exception as e:
            logger.debug(f"Delete {type_name}/{uuid} failed: {e}")
            return False
    
    # =========================================
    # Query
    # =========================================
    
    def query(self, type_name: str) -> CrudQueryBuilder:
        """
        Start a query builder chain.
        
        Args:
            type_name: Schema type
        
        Returns:
            CrudQueryBuilder for chaining
        
        Example:
            tasks = org.crud.query("task") \\
                .filter(done=False) \\
                .order_by("-priority") \\
                .limit(10) \\
                .all()
        """
        return CrudQueryBuilder(self, type_name)
    
    def _query(self, type_name: str, filters: Dict = None, order_by: List[str] = None,
               limit: int = None, offset: int = 0, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Internal: Execute query with parameters."""
        payload = {}
        if filters:
            payload["filters"] = filters
        if order_by:
            payload["order_by"] = order_by
        if limit is not None:
            payload["limit"] = limit
        if offset:
            payload["offset"] = offset
        
        result = self._org.post(
            self._endpoint(type_name, "query"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        if isinstance(result, list):
            return result
        return result.get("results", result.get("items", []))
    
    def find(self, type_name: str, api_key: Optional[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Find objects matching filters.
        
        Shortcut for query().filter(**filters).all()
        
        Example:
            high_priority = org.crud.find("task", priority="high", done=False)
        """
        return self.query(type_name).with_api_key(api_key).filter(**filters).all() if api_key else \
               self.query(type_name).filter(**filters).all()
    
    # =========================================
    # Aggregations
    # =========================================
    
    def _count(self, type_name: str, filters: Dict = None, api_key: Optional[str] = None) -> int:
        """Internal: Count with optional filters."""
        payload = {"op": "count"}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("count", result.get("result", 0))
    
    def count(self, type_name: str, api_key: Optional[str] = None, **filters) -> int:
        """
        Count objects.
        
        Example:
            total = org.crud.count("task")
            active = org.crud.count("task", done=False)
        """
        return self._count(type_name, filters if filters else None, api_key)
    
    def sum(self, type_name: str, field: str, api_key: Optional[str] = None, 
            **filters) -> Union[int, float]:
        """
        Sum a numeric field.
        
        Example:
            revenue = org.crud.sum("order", "amount", status="completed")
        """
        payload = {"op": "sum", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("sum", result.get("result", 0))
    
    def avg(self, type_name: str, field: str, api_key: Optional[str] = None,
            **filters) -> float:
        """
        Average of a numeric field.
        
        Example:
            avg_price = org.crud.avg("product", "price")
        """
        payload = {"op": "avg", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("avg", result.get("result", 0.0))
    
    def min(self, type_name: str, field: str, api_key: Optional[str] = None,
            **filters) -> Any:
        """
        Minimum value of a field.
        
        Example:
            cheapest = org.crud.min("product", "price")
        """
        payload = {"op": "min", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("min", result.get("result"))
    
    def max(self, type_name: str, field: str, api_key: Optional[str] = None,
            **filters) -> Any:
        """
        Maximum value of a field.
        
        Example:
            highest = org.crud.max("product", "price")
        """
        payload = {"op": "max", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("max", result.get("result"))
    
    def distinct(self, type_name: str, field: str, api_key: Optional[str] = None,
                 **filters) -> List[Any]:
        """
        Get distinct values of a field.
        
        Example:
            statuses = org.crud.distinct("task", "status")
            # ['pending', 'active', 'done']
        """
        payload = {"op": "distinct", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("distinct", result.get("values", result.get("result", [])))
    
    def count_by(self, type_name: str, field: str, api_key: Optional[str] = None,
                 **filters) -> Dict[str, int]:
        """
        Count grouped by field value.
        
        Example:
            by_status = org.crud.count_by("task", "status")
            # {'pending': 5, 'active': 10, 'done': 25}
        """
        payload = {"op": "count_by", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("count_by", result.get("groups", result.get("result", {})))
    
    def stats(self, type_name: str, field: str, api_key: Optional[str] = None,
              **filters) -> Dict[str, Any]:
        """
        Get statistics for a numeric field.
        
        Returns: {count, sum, avg, min, max}
        
        Example:
            price_stats = org.crud.stats("product", "price")
            # {'count': 100, 'sum': 5000, 'avg': 50.0, 'min': 10, 'max': 200}
        """
        payload = {"op": "stats", "field": field}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("stats", result.get("result", {}))
    
    def aggregate(self, type_name: str, op: str, field: str = None, 
                  api_key: Optional[str] = None, **filters) -> Any:
        """
        Generic aggregation method.
        
        Args:
            type_name: Schema type
            op: Operation (count, sum, avg, min, max, distinct, count_by, stats)
            field: Field to aggregate (not required for count)
            api_key: Optional API key for RBAC
            **filters: Optional filters
        
        Example:
            result = org.crud.aggregate("order", "sum", "amount", status="completed")
        """
        payload = {"op": op}
        if field:
            payload["field"] = field
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "aggregate"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get(op, result.get("result"))
    
    # =========================================
    # References
    # =========================================
    
    def set_ref(self, type_name: str, uuid: str, ref_field: str, 
                ref_uuid: str, api_key: Optional[str] = None, **link_data) -> Dict[str, Any]:
        """
        Set a reference to another object.
        
        Args:
            type_name: Schema type of the source object
            uuid: UUID of the source object
            ref_field: Reference field name
            ref_uuid: UUID of the target object
            api_key: Optional API key for RBAC
            **link_data: Additional link metadata
        
        Returns:
            Updated object
        
        Example:
            org.crud.set_ref("order", order_uuid, "customer", customer_uuid)
            org.crud.set_ref("order", order_uuid, "customer", customer_uuid, role="primary")
        """
        payload = {
            "ref_field": ref_field,
            "ref_uuid": ref_uuid,
        }
        if link_data:
            payload["link_data"] = link_data
        
        return self._org.post(
            self._endpoint(type_name, uuid, "ref"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
    
    def get_ref(self, type_name: str, uuid: str, ref_field: str,
                api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get reference details including link data.
        
        Args:
            type_name: Schema type of the source object
            uuid: UUID of the source object
            ref_field: Reference field name
            api_key: Optional API key for RBAC
        
        Returns:
            Reference dict with target object and link_data, or None
        
        Example:
            ref = org.crud.get_ref("order", order_uuid, "customer")
            # {'target': {...customer object...}, 'link_data': {'role': 'primary'}}
        """
        try:
            return self._org.get(
                self._endpoint(type_name, uuid, "ref", ref_field),
                **self._request_kwargs(api_key)
            )
        except Exception as e:
            logger.debug(f"Get ref {type_name}/{uuid}/{ref_field} failed: {e}")
            return None
    
    def update_ref(self, type_name: str, uuid: str, ref_field: str,
                   api_key: Optional[str] = None, **link_data) -> Dict[str, Any]:
        """
        Update link data on an existing reference.
        
        Example:
            org.crud.update_ref("order", order_uuid, "customer", role="secondary", notes="VIP")
        """
        payload = {
            "ref_field": ref_field,
            "link_data": link_data
        }
        return self._org.put(
            self._endpoint(type_name, uuid, "ref"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
    
    def remove_ref(self, type_name: str, uuid: str, ref_field: str,
                   api_key: Optional[str] = None) -> bool:
        """
        Remove a reference.
        
        Example:
            org.crud.remove_ref("order", order_uuid, "customer")
        """
        try:
            self._org.delete(
                self._endpoint(type_name, uuid, "ref", ref_field),
                **self._request_kwargs(api_key)
            )
            return True
        except Exception as e:
            logger.debug(f"Remove ref {type_name}/{uuid}/{ref_field} failed: {e}")
            return False
    
    # =========================================
    # Bulk Operations
    # =========================================
    
    def bulk_get(self, type_name: str, uuids: List[str],
                 api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get multiple objects by UUIDs.
        
        Example:
            tasks = org.crud.bulk_get("task", ["uuid1", "uuid2", "uuid3"])
        """
        result = self._org.post(
            self._endpoint(type_name, "bulk-get"),
            json={"uuids": uuids},
            **self._request_kwargs(api_key)
        )
        if isinstance(result, list):
            return result
        return result.get("results", result.get("items", []))
    
    def bulk_create(self, type_name: str, items: List[Dict[str, Any]],
                    api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Create multiple objects.
        
        Example:
            tasks = org.crud.bulk_create("task", [
                {"name": "t1", "title": "Task 1"},
                {"name": "t2", "title": "Task 2"},
            ])
        """
        # Deep copy to avoid mutating input
        items_copy = copy.deepcopy(items)
        
        # Auto-populate required fields for each item
        for item in items_copy:
            if "name" not in item:
                raise ValueError("Each item must have a 'name' field")
            item.setdefault("fq_name", [self._domain, item["name"]])
            item.setdefault("parent_type", "domain")
        
        result = self._org.post(
            self._endpoint(type_name, "bulk-create"),
            json={"items": items_copy},
            **self._request_kwargs(api_key)
        )
        if isinstance(result, list):
            return result
        return result.get("results", result.get("created", []))
    
    def bulk_update(self, type_name: str, updates: List[Dict[str, Any]],
                    api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Update multiple objects.
        
        Each update dict must contain 'uuid' and fields to update.
        
        Example:
            org.crud.bulk_update("task", [
                {"uuid": "uuid1", "done": True},
                {"uuid": "uuid2", "done": True},
            ])
        """
        for update in updates:
            if "uuid" not in update:
                raise ValueError("Each update must have a 'uuid' field")
        
        result = self._org.post(
            self._endpoint(type_name, "bulk-update"),
            json={"updates": updates},
            **self._request_kwargs(api_key)
        )
        if isinstance(result, list):
            return result
        return result.get("results", result.get("updated", []))
    
    def bulk_delete(self, type_name: str, uuids: List[str],
                    api_key: Optional[str] = None) -> int:
        """
        Delete multiple objects.
        
        Returns:
            Number of objects deleted
        
        Example:
            deleted = org.crud.bulk_delete("task", ["uuid1", "uuid2", "uuid3"])
        """
        result = self._org.post(
            self._endpoint(type_name, "bulk-delete"),
            json={"uuids": uuids},
            **self._request_kwargs(api_key)
        )
        return result.get("deleted", result.get("count", len(uuids)))
    
    def _delete_all(self, type_name: str, filters: Dict = None,
                    api_key: Optional[str] = None) -> int:
        """Internal: Delete all matching objects."""
        payload = {}
        if filters:
            payload["filters"] = filters
        result = self._org.post(
            self._endpoint(type_name, "delete-all"), 
            json=payload,
            **self._request_kwargs(api_key)
        )
        return result.get("deleted", result.get("count", 0))
    
    # =========================================
    # Convenience Methods
    # =========================================
    
    def exists(self, type_name: str, api_key: Optional[str] = None, **filters) -> bool:
        """
        Check if any objects match filters.
        
        Example:
            if org.crud.exists("user", email="test@example.com"):
                print("User exists!")
        """
        return self.count(type_name, api_key=api_key, **filters) > 0
    
    def get_by_name(self, type_name: str, name: str,
                    api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get object by name.
        
        Example:
            task = org.crud.get_by_name("task", "task-001")
        """
        results = self.find(type_name, api_key=api_key, name=name)
        return results[0] if results else None
    
    def get_or_create(self, type_name: str, name: str, api_key: Optional[str] = None,
                      **defaults) -> Tuple[Dict[str, Any], bool]:
        """
        Get existing object or create new one.
        
        Returns:
            (object, created) tuple
        
        Example:
            task, created = org.crud.get_or_create("task", "task-001", title="Default Title")
        """
        existing = self.get_by_name(type_name, name, api_key=api_key)
        if existing:
            return existing, False
        
        created_obj = self.create(type_name, name=name, api_key=api_key, **defaults)
        return created_obj, True
    
    def update_or_create(self, type_name: str, name: str, api_key: Optional[str] = None,
                         **data) -> Tuple[Dict[str, Any], bool]:
        """
        Update existing object or create new one.
        
        Returns:
            (object, created) tuple
        
        Example:
            task, created = org.crud.update_or_create("task", "task-001", title="Updated", done=True)
        """
        existing = self.get_by_name(type_name, name, api_key=api_key)
        if existing:
            updated = self.update(type_name, existing["uuid"], api_key=api_key, **data)
            return updated, False
        
        created_obj = self.create(type_name, name=name, api_key=api_key, **data)
        return created_obj, True
