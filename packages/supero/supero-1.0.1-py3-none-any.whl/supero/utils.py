"""
Utility functions for Supero.
"""

import inflection
from typing import List, Dict, Any


def singularize(word: str) -> str:
    """
    Simple singularization.
    
    Args:
        word: Plural word
        
    Returns:
        Singular form
        
    Example:
        >>> singularize('projects')
        'project'
    """
    return inflection.singularize(word)


def snake_case(text: str) -> str:
    """
    Convert to snake_case.
    
    Args:
        text: Input text
        
    Returns:
        snake_case version
        
    Example:
        >>> snake_case('ProjectName')
        'project_name'
    """
    return inflection.underscore(text)


def camel_case(text: str) -> str:
    """
    Convert to CamelCase.
    
    Args:
        text: Input text
        
    Returns:
        CamelCase version
        
    Example:
        >>> camel_case('project_name')
        'ProjectName'
    """
    return inflection.camelize(text)


def extract_uuid(obj_or_uuid) -> str:
    """
    Extract UUID from object or string.
    
    Args:
        obj_or_uuid: Object with uuid attribute or UUID string
        
    Returns:
        UUID string
        
    Example:
        >>> extract_uuid(project)
        'abc-123-def'
        >>> extract_uuid('abc-123-def')
        'abc-123-def'
    """
    if isinstance(obj_or_uuid, str):
        return obj_or_uuid
    return getattr(obj_or_uuid, 'uuid', None)


def batch(items: List[Any], batch_size: int = 100) -> List[List[Any]]:
    """
    Split list into batches.
    
    Args:
        items: List of items
        batch_size: Size of each batch
        
    Returns:
        List of batches
        
    Example:
        >>> items = list(range(250))
        >>> batches = batch(items, batch_size=100)
        >>> len(batches)
        3
        >>> len(batches[0])
        100
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def deduplicate_by_uuid(objects: List[Any]) -> List[Any]:
    """
    Remove duplicate objects by UUID.
    
    Args:
        objects: List of objects
        
    Returns:
        Deduplicated list
        
    Example:
        >>> unique = deduplicate_by_uuid([obj1, obj2, obj1])
        >>> len(unique)
        2
    """
    seen_uuids = set()
    unique_objects = []
    
    for obj in objects:
        uuid = getattr(obj, 'uuid', None)
        if uuid and uuid not in seen_uuids:
            seen_uuids.add(uuid)
            unique_objects.append(obj)
        elif not uuid:
            # No UUID - include anyway
            unique_objects.append(obj)
    
    return unique_objects


def merge_link_data(existing: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge link data dictionaries.
    
    Args:
        existing: Existing link data
        updates: Updates to apply
        
    Returns:
        Merged dictionary
        
    Example:
        >>> existing = {'role': 'member', 'allocation': 0.5}
        >>> updates = {'role': 'lead'}
        >>> merged = merge_link_data(existing, updates)
        >>> merged
        {'role': 'lead', 'allocation': 0.5}
    """
    result = existing.copy()
    result.update(updates)
    return result
