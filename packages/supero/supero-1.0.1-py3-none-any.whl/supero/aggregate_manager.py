"""
Aggregate Manager - Analytics and aggregation operations
Location: ~/supero/platform/infra/libs/py/src/supero/aggregate_manager.py

REFACTORED v1.0 (Context-Aware Architecture):
- ✅ Context-aware: Gets domain from PlatformClient
- ✅ Single source of truth: No redundant domain parameters
- ✅ RBAC support: api_key parameter in all methods
- ✅ Full aggregate API coverage: stats, distinct, count_by, pipeline

Provides analytics and aggregation capabilities for domain data through
Platform Core's aggregate API.
"""

from typing import Dict, List, Any, Optional
import logging
import json


class AggregateManager:
    """
    Manages aggregate operations for analytics and reporting.
    
    Handles:
    - Full aggregation pipelines (MongoDB-style)
    - Quick statistics (count, sum, avg, min, max)
    - Distinct value extraction
    - Grouped counts
    
    Version 1.0 Context-Aware Architecture:
    - Gets domain from PlatformClient JWT
    - Single source of truth: PlatformClient owns all context
    - RBAC support: api_key parameter for per-call authorization
    - Consistent with refactored UserManager, SchemaManager, SDKManager
    """
    
    def __init__(
        self,
        platform_client,
        logger: logging.Logger = None
    ):
        """
        Initialize AggregateManager with context-aware client.
        
        Args:
            platform_client: PlatformClient instance (contains domain context)
            logger: Logger instance (creates new if None)
        
        Example:
            >>> agg_mgr = AggregateManager(platform_client=client, logger=logger)
            >>> print(agg_mgr.domain_name)  # From client.domain_name
            >>> 
            >>> # Operations use context automatically
            >>> stats = agg_mgr.stats('order', fields=['amount'])
            >>> # domain automatically included from client!
        """
        self.client = platform_client
        self.logger = logger or logging.getLogger(__name__)
        
        # ✅ REFACTORED: Extract from client
        self.domain_name = platform_client.domain_name
        self.domain_uuid = platform_client.domain_uuid
        
        self.logger.debug(f"AggregateManager initialized for domain: {self.domain_name}")
    
    # ========================================================================
    # AGGREGATION PIPELINE
    # ========================================================================
    
    def aggregate(
        self,
        obj_type: str,
        pipeline: List[Dict[str, Any]],
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        Execute MongoDB-style aggregation pipeline.
        
        Args:
            obj_type: Object type to aggregate (e.g., 'order', 'project')
            pipeline: Aggregation pipeline stages
            api_key: Optional API key for RBAC (overrides instance default)
        
        Returns:
            Dict with 'results', 'count', 'pipeline_stages', 'execution_time_ms'
        
        Raises:
            ValueError: If aggregation fails
        
        Example:
            >>> # Sales by category
            >>> result = agg_mgr.aggregate('order', [
            ...     {'$match': {'status': 'completed'}},
            ...     {'$group': {
            ...         '_id': '$category',
            ...         'total_sales': {'$sum': '$amount'},
            ...         'count': {'$sum': 1}
            ...     }},
            ...     {'$sort': {'total_sales': -1}}
            ... ])
            >>> for item in result['results']:
            ...     print(f"{item['_id']}: ${item['total_sales']}")
            
            >>> # With RBAC override
            >>> result = agg_mgr.aggregate('order', pipeline, api_key=user_key)
        """
        if not pipeline or not isinstance(pipeline, list):
            raise ValueError("pipeline must be a non-empty list")
        
        response = self.client.post(
            f'/api/v1/aggregate/{self.domain_name}/{obj_type}/aggregate',
            json={'pipeline': pipeline},
            api_key=api_key
        )
        
        if response.get('success'):
            return response['data']
        else:
            error = response.get('message', response.get('error', 'Unknown error'))
            raise ValueError(f"Aggregate failed: {error}")
    
    def pipeline(
        self,
        obj_type: str,
        pipeline: List[Dict[str, Any]],
        api_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline and return just the results.
        
        Convenience wrapper around aggregate() that returns only the results array.
        
        Args:
            obj_type: Object type to aggregate
            pipeline: Aggregation pipeline stages
            api_key: Optional API key for RBAC
        
        Returns:
            List of result documents
        
        Example:
            >>> # Get top 10 customers by spending
            >>> top_customers = agg_mgr.pipeline('order', [
            ...     {'$group': {
            ...         '_id': '$customer_id',
            ...         'total': {'$sum': '$amount'}
            ...     }},
            ...     {'$sort': {'total': -1}},
            ...     {'$limit': 10}
            ... ])
            >>> for customer in top_customers:
            ...     print(f"Customer {customer['_id']}: ${customer['total']}")
        """
        result = self.aggregate(obj_type, pipeline, api_key=api_key)
        return result.get('results', [])
    
    # ========================================================================
    # QUICK STATISTICS
    # ========================================================================
    
    def stats(
        self,
        obj_type: str,
        fields: Optional[List[str]] = None,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        Get quick statistics (count, sum, avg, min, max) for numeric fields.
        
        Args:
            obj_type: Object type to analyze
            fields: Field names to get stats for (None = all numeric fields)
            match: Filter conditions (MongoDB query format)
            api_key: Optional API key for RBAC
        
        Returns:
            Dict with 'count' (total docs) and 'fields' (stats per field):
            {
                'count': 1250,
                'fields': {
                    'amount': {
                        'sum': 125000.50,
                        'avg': 100.00,
                        'min': 10.00,
                        'max': 5000.00,
                        'count': 1250
                    }
                }
            }
        
        Raises:
            ValueError: If stats operation fails
        
        Example:
            >>> # All numeric field stats
            >>> stats = agg_mgr.stats('order')
            >>> print(f"Total orders: {stats['count']}")
            >>> print(f"Avg amount: ${stats['fields']['amount']['avg']}")
            
            >>> # Specific fields only
            >>> stats = agg_mgr.stats('order', fields=['amount', 'quantity'])
            >>> 
            >>> # With filter
            >>> stats = agg_mgr.stats('order', 
            ...     fields=['amount'],
            ...     match={'status': 'completed'}
            ... )
            >>> print(f"Completed orders: ${stats['fields']['amount']['sum']}")
            
            >>> # With RBAC
            >>> stats = agg_mgr.stats('order', fields=['amount'], api_key=user_key)
        """
        params = {}
        if fields:
            if isinstance(fields, list):
                params['fields'] = ','.join(fields)
            else:
                params['fields'] = str(fields)
        if match:
            params['match'] = json.dumps(match)
        
        response = self.client.get(
            f'/api/v1/aggregate/{self.domain_name}/{obj_type}/stats',
            params=params if params else None,
            api_key=api_key
        )
        
        if response.get('success'):
            return response['data']
        else:
            error = response.get('message', response.get('error', 'Unknown error'))
            raise ValueError(f"Stats failed: {error}")
    
    # ========================================================================
    # DISTINCT VALUES
    # ========================================================================
    
    def distinct(
        self,
        obj_type: str,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        api_key: str = None
    ) -> List[Any]:
        """
        Get distinct (unique) values for a field.
        
        Args:
            obj_type: Object type to query
            field: Field name to get distinct values for
            match: Filter conditions
            limit: Max values to return (1-10000, default 1000)
            api_key: Optional API key for RBAC
        
        Returns:
            List of distinct values
        
        Raises:
            ValueError: If distinct operation fails or field is empty
        
        Example:
            >>> # Get all unique statuses
            >>> statuses = agg_mgr.distinct('order', 'status')
            >>> print(statuses)  # ['pending', 'completed', 'cancelled']
            
            >>> # Get unique customer IDs for completed orders
            >>> customers = agg_mgr.distinct('order', 'customer_id',
            ...     match={'status': 'completed'},
            ...     limit=100
            ... )
            
            >>> # With RBAC
            >>> statuses = agg_mgr.distinct('order', 'status', api_key=user_key)
        """
        if not field or not field.strip():
            raise ValueError("field parameter is required and cannot be empty")
        
        # Validate limit range
        limit = max(1, min(limit, 10000))
        
        params = {'limit': limit}
        if match:
            params['match'] = json.dumps(match)
        
        response = self.client.get(
            f'/api/v1/aggregate/{self.domain_name}/{obj_type}/distinct/{field}',
            params=params,
            api_key=api_key
        )
        
        if response.get('success'):
            data = response['data']
            return data.get('values', [])
        else:
            error = response.get('message', response.get('error', 'Unknown error'))
            raise ValueError(f"Distinct failed: {error}")
    
    # ========================================================================
    # GROUPED COUNTS
    # ========================================================================
    
    def count_by(
        self,
        obj_type: str,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        sort: str = '-count',
        api_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get counts grouped by field values (like SQL GROUP BY with COUNT).
        
        Args:
            obj_type: Object type to query
            field: Field to group by
            match: Filter conditions
            limit: Max groups to return (1-1000, default 100)
            sort: Sort order ('count', '-count', 'value', '-value')
            api_key: Optional API key for RBAC
        
        Returns:
            List of {'value': field_value, 'count': count} dicts
        
        Raises:
            ValueError: If count-by operation fails or parameters invalid
        
        Example:
            >>> # Orders by status (most common first)
            >>> by_status = agg_mgr.count_by('order', 'status')
            >>> for item in by_status:
            ...     print(f"{item['value']}: {item['count']} orders")
            
            >>> # Products by category (alphabetical)
            >>> by_category = agg_mgr.count_by('product', 'category', 
            ...     sort='value',
            ...     limit=50
            ... )
            
            >>> # Active users by role
            >>> by_role = agg_mgr.count_by('user_account', 'role',
            ...     match={'enabled': True}
            ... )
            
            >>> # With RBAC
            >>> by_status = agg_mgr.count_by('order', 'status', api_key=user_key)
        """
        if not field or not field.strip():
            raise ValueError("field parameter is required and cannot be empty")
        
        # Validate sort parameter
        valid_sorts = ('count', '-count', 'value', '-value')
        if sort not in valid_sorts:
            raise ValueError(f"sort must be one of: {', '.join(valid_sorts)}")
        
        # Validate limit range
        limit = max(1, min(limit, 1000))
        
        params = {'limit': limit, 'sort': sort}
        if match:
            params['match'] = json.dumps(match)
        
        response = self.client.get(
            f'/api/v1/aggregate/{self.domain_name}/{obj_type}/count-by/{field}',
            params=params,
            api_key=api_key
        )
        
        if response.get('success'):
            data = response['data']
            return data.get('groups', [])
        else:
            error = response.get('message', response.get('error', 'Unknown error'))
            raise ValueError(f"Count-by failed: {error}")
    
    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================
    
    def count(
        self,
        obj_type: str,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> int:
        """
        Get total count of documents.
        
        Args:
            obj_type: Object type to count
            match: Filter conditions
            api_key: Optional API key for RBAC
        
        Returns:
            Total count as integer
        
        Example:
            >>> # Total orders
            >>> total = agg_mgr.count('order')
            >>> print(f"Total orders: {total}")
            
            >>> # Completed orders
            >>> completed = agg_mgr.count('order', match={'status': 'completed'})
            >>> print(f"Completed: {completed}")
        """
        stats = self.stats(obj_type, fields=[], match=match, api_key=api_key)
        return stats.get('count', 0)
    
    def sum(
        self,
        obj_type: str,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> float:
        """
        Get sum of a numeric field.
        
        Args:
            obj_type: Object type
            field: Numeric field to sum
            match: Filter conditions
            api_key: Optional API key for RBAC
        
        Returns:
            Sum value as float
        
        Example:
            >>> # Total revenue
            >>> revenue = agg_mgr.sum('order', 'amount')
            >>> print(f"Total revenue: ${revenue:,.2f}")
            
            >>> # Revenue from completed orders
            >>> completed_revenue = agg_mgr.sum('order', 'amount',
            ...     match={'status': 'completed'}
            ... )
        """
        stats = self.stats(obj_type, fields=[field], match=match, api_key=api_key)
        field_stats = stats.get('fields', {}).get(field, {})
        return field_stats.get('sum', 0.0)
    
    def avg(
        self,
        obj_type: str,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> float:
        """
        Get average of a numeric field.
        
        Args:
            obj_type: Object type
            field: Numeric field to average
            match: Filter conditions
            api_key: Optional API key for RBAC
        
        Returns:
            Average value as float
        
        Example:
            >>> avg_order_value = agg_mgr.avg('order', 'amount')
            >>> print(f"Average order: ${avg_order_value:.2f}")
        """
        stats = self.stats(obj_type, fields=[field], match=match, api_key=api_key)
        field_stats = stats.get('fields', {}).get(field, {})
        return field_stats.get('avg', 0.0)
    
    def min(
        self,
        obj_type: str,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> Any:
        """
        Get minimum value of a field.
        
        Args:
            obj_type: Object type
            field: Field to get minimum for
            match: Filter conditions
            api_key: Optional API key for RBAC
        
        Returns:
            Minimum value (type depends on field)
        
        Example:
            >>> min_price = agg_mgr.min('product', 'price')
            >>> print(f"Lowest price: ${min_price}")
        """
        stats = self.stats(obj_type, fields=[field], match=match, api_key=api_key)
        field_stats = stats.get('fields', {}).get(field, {})
        return field_stats.get('min')
    
    def max(
        self,
        obj_type: str,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> Any:
        """
        Get maximum value of a field.
        
        Args:
            obj_type: Object type
            field: Field to get maximum for
            match: Filter conditions
            api_key: Optional API key for RBAC
        
        Returns:
            Maximum value (type depends on field)
        
        Example:
            >>> max_price = agg_mgr.max('product', 'price')
            >>> print(f"Highest price: ${max_price}")
        """
        stats = self.stats(obj_type, fields=[field], match=match, api_key=api_key)
        field_stats = stats.get('fields', {}).get(field, {})
        return field_stats.get('max')
