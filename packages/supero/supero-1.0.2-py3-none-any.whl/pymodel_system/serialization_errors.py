# File: serialization_errors.py
"""
Enhanced serialization and deserialization error handling with detailed reporting.
"""

import json
import traceback
from typing import Any, Dict, List, Optional, Type

class InvalidParentError(ValueError):
    """Raised when attempting to set an invalid parent."""
    pass

class SerializationError(Exception):
    """Base exception for serialization/deserialization errors."""
    
    def __init__(self, message: str, obj_type: str = None, attribute: str = None, 
                 value: Any = None, original_error: Exception = None):
        self.obj_type = obj_type
        self.attribute = attribute  
        self.value = value
        self.original_error = original_error
        
        # Build detailed error message
        detailed_msg = message
        if obj_type:
            detailed_msg = f"[{obj_type}] {detailed_msg}"
        if attribute:
            detailed_msg = f"{detailed_msg} - Attribute: '{attribute}'"
        if value is not None:
            # Safely represent the value
            try:
                value_repr = repr(value)
                if len(value_repr) > 200:
                    value_repr = value_repr[:200] + "..."
            except:
                value_repr = f"<{type(value).__name__} object>"
            detailed_msg = f"{detailed_msg} - Value: {value_repr}"
        if original_error:
            detailed_msg = f"{detailed_msg} - Original error: {str(original_error)}"
            
        super().__init__(detailed_msg)


class ObjectSerializationError(SerializationError):
    """Raised when object-to-dict/JSON conversion fails."""
    pass


class ObjectDeserializationError(SerializationError):
    """Raised when dict/JSON-to-object conversion fails."""
    pass


class JSONSerializationError(SerializationError):
    """Raised when dict-to-JSON conversion fails.""" 
    pass


class JSONDeserializationError(SerializationError):
    """Raised when JSON-to-dict conversion fails."""
    pass


def safe_serialize_to_dict(obj: Any, obj_type: str = None) -> Dict[str, Any]:
    """
    Safely serialize object to dictionary with detailed error reporting.
    
    Args:
        obj: Object to serialize
        obj_type: Type name for error reporting
        
    Returns:
        Dictionary representation
        
    Raises:
        ObjectSerializationError: With detailed info about what failed
    """
    if obj is None:
        raise ObjectSerializationError("Cannot serialize None object", obj_type=obj_type)
    
    if not obj_type:
        obj_type = getattr(obj, 'obj_type', None) or getattr(obj, '__class__', type(obj)).__name__
    
    try:
        # First, check if object has to_dict method
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            try:
                result = obj.to_dict()
                if not isinstance(result, dict):
                    raise ObjectSerializationError(
                        f"to_dict() returned {type(result).__name__} instead of dict",
                        obj_type=obj_type
                    )
                
                # Validate the resulting dictionary
                _validate_serializable_dict(result, obj_type)
                return result
                
            except ObjectSerializationError:
                raise  # Re-raise our custom errors
            except Exception as e:
                # Analyze what went wrong in to_dict()
                error_details = _analyze_to_dict_error(obj, e, obj_type)
                raise ObjectSerializationError(
                    f"to_dict() method failed: {error_details}",
                    obj_type=obj_type,
                    original_error=e
                )
        
        # Fallback to __dict__ inspection
        elif hasattr(obj, '__dict__'):
            try:
                result = {}
                obj_dict = obj.__dict__
                
                for attr_name, attr_value in obj_dict.items():
                    try:
                        # Test serializability of each attribute
                        json.dumps(attr_value, default=str)  # Quick serializability test
                        result[attr_name] = attr_value
                    except (TypeError, ValueError) as e:
                        raise ObjectSerializationError(
                            f"Attribute contains non-serializable value",
                            obj_type=obj_type,
                            attribute=attr_name,
                            value=attr_value,
                            original_error=e
                        )
                
                return result
                
            except ObjectSerializationError:
                raise
            except Exception as e:
                raise ObjectSerializationError(
                    f"Failed to serialize object attributes: {str(e)}",
                    obj_type=obj_type,
                    original_error=e
                )
        
        else:
            raise ObjectSerializationError(
                "Object has no to_dict() method or __dict__ attribute",
                obj_type=obj_type
            )
            
    except ObjectSerializationError:
        raise
    except Exception as e:
        raise ObjectSerializationError(
            f"Unexpected serialization error: {str(e)}",
            obj_type=obj_type,
            original_error=e
        )


def safe_serialize_to_json(obj_or_dict: Any, obj_type: str = None) -> str:
    """
    Safely serialize object/dict to JSON with detailed error reporting.
    
    Args:
        obj_or_dict: Object or dictionary to serialize
        obj_type: Type name for error reporting
        
    Returns:
        JSON string
        
    Raises:
        JSONSerializationError: With detailed info about what failed
    """
    if not obj_type:
        obj_type = getattr(obj_or_dict, 'obj_type', None) or type(obj_or_dict).__name__
    
    try:
        # Convert to dict first if it's an object
        if isinstance(obj_or_dict, dict):
            data_dict = obj_or_dict
        else:
            data_dict = safe_serialize_to_dict(obj_or_dict, obj_type)
        
        # Attempt JSON serialization
        try:
            return json.dumps(data_dict, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Analyze which part of the dict failed to serialize
            problem_path = _find_json_serialization_problem(data_dict)
            
            raise JSONSerializationError(
                f"JSON serialization failed at path: {problem_path}",
                obj_type=obj_type,
                attribute=problem_path,
                original_error=e
            )
            
    except (ObjectSerializationError, JSONSerializationError):
        raise
    except Exception as e:
        raise JSONSerializationError(
            f"Unexpected JSON serialization error: {str(e)}",
            obj_type=obj_type,
            original_error=e
        )


def safe_deserialize_from_dict(data: Dict[str, Any], obj_class: Type, obj_type: str = None) -> Any:
    """
    Safely deserialize dictionary to object with detailed error reporting.
    
    Args:
        data: Dictionary data to deserialize
        obj_class: Target object class
        obj_type: Type name for error reporting
        
    Returns:
        Object instance
        
    Raises:
        ObjectDeserializationError: With detailed info about what failed
    """
    if not obj_type:
        obj_type = getattr(obj_class, '__name__', str(obj_class))
    
    if not isinstance(data, dict):
        raise ObjectDeserializationError(
            f"Expected dict, got {type(data).__name__}",
            obj_type=obj_type,
            value=data
        )
    
    if not data:
        raise ObjectDeserializationError(
            "Cannot deserialize empty dictionary",
            obj_type=obj_type,
            value=data
        )
    
    try:
        # Check if class has from_dict method
        if hasattr(obj_class, 'from_dict') and callable(getattr(obj_class, 'from_dict')):
            try:
                return obj_class.from_dict(data)
            except Exception as e:
                # Analyze what went wrong in from_dict
                error_details = _analyze_from_dict_error(data, obj_class, e, obj_type)
                raise ObjectDeserializationError(
                    f"from_dict() method failed: {error_details}",
                    obj_type=obj_type,
                    original_error=e
                )
        
        # Fallback to direct instantiation
        else:
            try:
                obj = obj_class()
                for attr_name, attr_value in data.items():
                    try:
                        setattr(obj, attr_name, attr_value)
                    except Exception as e:
                        raise ObjectDeserializationError(
                            f"Failed to set attribute during deserialization",
                            obj_type=obj_type,
                            attribute=attr_name,
                            value=attr_value,
                            original_error=e
                        )
                return obj
                
            except ObjectDeserializationError:
                raise
            except Exception as e:
                raise ObjectDeserializationError(
                    f"Failed to instantiate {obj_type}: {str(e)}",
                    obj_type=obj_type,
                    original_error=e
                )
            
    except ObjectDeserializationError:
        raise
    except Exception as e:
        raise ObjectDeserializationError(
            f"Unexpected deserialization error: {str(e)}",
            obj_type=obj_type,
            original_error=e
        )


def safe_deserialize_from_json(json_str: str, obj_class: Type, obj_type: str = None) -> Any:
    """
    Safely deserialize JSON to object with detailed error reporting.
    
    Args:
        json_str: JSON string to deserialize
        obj_class: Target object class  
        obj_type: Type name for error reporting
        
    Returns:
        Object instance
        
    Raises:
        JSONDeserializationError, ObjectDeserializationError: With detailed info
    """
    if not obj_type:
        obj_type = getattr(obj_class, '__name__', str(obj_class))
    
    if not isinstance(json_str, str):
        raise JSONDeserializationError(
            f"Expected string, got {type(json_str).__name__}",
            obj_type=obj_type,
            value=json_str
        )
    
    if not json_str.strip():
        raise JSONDeserializationError(
            "Cannot deserialize empty or whitespace-only JSON string",
            obj_type=obj_type,
            value=json_str
        )
    
    try:
        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise JSONDeserializationError(
                f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}",
                obj_type=obj_type,
                value=json_str[:200] + "..." if len(json_str) > 200 else json_str,
                original_error=e
            )
        
        # Deserialize to object
        return safe_deserialize_from_dict(data, obj_class, obj_type)
        
    except (JSONDeserializationError, ObjectDeserializationError):
        raise
    except Exception as e:
        raise JSONDeserializationError(
            f"Unexpected JSON deserialization error: {str(e)}",
            obj_type=obj_type,
            original_error=e
        )


def _validate_serializable_dict(data: Dict[str, Any], obj_type: str) -> None:
    """Validate that dictionary is JSON serializable."""
    try:
        json.dumps(data)
    except (TypeError, ValueError) as e:
        problem_path = _find_json_serialization_problem(data)
        raise ObjectSerializationError(
            f"Dictionary contains non-serializable data at path: {problem_path}",
            obj_type=obj_type,
            attribute=problem_path,
            original_error=e
        )


def _find_json_serialization_problem(data: Any, path: str = "") -> str:
    """Find the exact path where JSON serialization fails."""
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                try:
                    json.dumps(value)
                except (TypeError, ValueError):
                    return _find_json_serialization_problem(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                try:
                    json.dumps(item) 
                except (TypeError, ValueError):
                    return _find_json_serialization_problem(item, current_path)
        else:
            # This is the problematic value
            return f"{path} (type: {type(data).__name__}, value: {repr(data)[:100]})"
    except Exception:
        pass
    
    return path or "unknown"


def _analyze_to_dict_error(obj: Any, error: Exception, obj_type: str) -> str:
    """Analyze what went wrong in an object's to_dict() method."""
    try:
        # Check for common issues
        if hasattr(obj, '_pending_field_updates'):
            pending = getattr(obj, '_pending_field_updates', set())
            if pending and not isinstance(pending, set):
                return f"_pending_field_updates is {type(pending).__name__}, expected set"
        
        # Check for non-serializable attributes
        if hasattr(obj, '__dict__'):
            for attr_name, attr_value in obj.__dict__.items():
                try:
                    json.dumps(attr_value, default=str)
                except Exception:
                    return f"Attribute '{attr_name}' contains non-serializable value of type {type(attr_value).__name__}"
        
        return f"Unknown error in to_dict(): {str(error)}"
        
    except Exception:
        return f"Could not analyze to_dict() error: {str(error)}"


def _analyze_from_dict_error(data: Dict[str, Any], obj_class: Type, error: Exception, obj_type: str) -> str:
    """Analyze what went wrong in a class's from_dict() method."""
    try:
        # Check for missing required fields
        if hasattr(obj_class, '_type_metadata'):
            metadata = getattr(obj_class, '_type_metadata', {})
            for field_name, field_info in metadata.items():
                if field_info.get('mandatory', False) and field_name not in data:
                    return f"Missing required field '{field_name}'"
        
        # Check for invalid field types
        for field_name, field_value in data.items():
            if field_value is not None:
                # Check for obviously invalid types
                if isinstance(field_value, (type, classmethod, staticmethod, property)):
                    return f"Field '{field_name}' has invalid type {type(field_value).__name__}"
        
        return f"Unknown error in from_dict(): {str(error)}"
        
    except Exception:
        return f"Could not analyze from_dict() error: {str(error)}"
