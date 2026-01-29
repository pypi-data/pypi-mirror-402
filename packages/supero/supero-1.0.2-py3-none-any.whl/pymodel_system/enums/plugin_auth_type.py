# File: pymodel_system/enums/plugin_auth_type.py
# This file was generated from the PluginAuthType.json schema
from typing import List, Dict, Any, Optional
import importlib
import uuid
import inflection

class DeserializationError(Exception):
    """Raised when object deserialization fails."""
    pass

class PluginAuthType:
    """
    Enum class for PluginAuthType with support for multiple base types.
    Base type: str
    """
    NONE = 'none'
    HEADER = 'header'

    
    def __init__(self, value):
        """
        Create an enum instance from a value of the appropriate base type.
        
        Args:
            value: The value (can be string, int, float, bool based on enum base type)
            
        Raises:
            DeserializationError: If the value is not valid
        """
        # Convert input to the expected base type for comparison
        converted_value = self._convert_to_base_type(value)
        
        if not self.__class__.is_valid(converted_value):
            available_values = self.__class__.get_all_values()
            raise DeserializationError(
                f"Invalid enum value '{value}' for {self.__class__.__name__}. "
                f"Available values: {available_values}"
            )
        self.value = converted_value
    
    def _convert_to_base_type(self, value):
        """Convert input value to the enum's base type."""
        if value is None:
            return None
            
        try:
            # Get the base type from the template variable
            base_type = "str"
            
            if base_type == "int":
                if isinstance(value, str):
                    return int(value)
                return int(value)
            elif base_type == "float":
                if isinstance(value, str):
                    return float(value)
                return float(value)
            elif base_type == "bool":
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            else:  # string type
                return str(value)
                
        except (ValueError, TypeError):
            # If conversion fails, return original value for error handling
            return value
    
    def __str__(self):
        """String representation of the enum."""
        return str(self.value)
    
    def __repr__(self):
        """Developer representation of the enum."""
        return f"{self.__class__.__name__}({repr(self.value)})"
    
    def __eq__(self, other):
        """Check equality with another enum instance or base type value."""
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            # Try to convert other to base type for comparison
            converted_other = self._convert_to_base_type(other)
            return self.value == converted_other
    
    def __hash__(self):
        """Make enum instances hashable."""
        return hash((self.__class__.__name__, self.value))
    
    @classmethod
    def get_all_values(cls):
        """Return list of all enum values in their base types."""
        return ['none', 'header']
    
    @classmethod
    def get_base_type(cls):
        """Return the base type of this enum."""
        return "str"
    
    @classmethod
    def from_dict(cls, data):
        """
        Create enum instance(s) from dictionary data.
        Supports both single values and lists.
        
        Args:
            data: Can be:
                - Any type: Single enum value -> returns single enum instance
                - List: List of enum values -> returns List[enum instances]
                - Dict with enum field -> extracts and processes the enum field
        
        Returns:
            Single enum instance, list of enum instances, or the input dict with enum fields converted
            
        Raises:
            DeserializationError: If any value is invalid
        """
        # Handle direct value
        if not isinstance(data, (list, dict)):
            return cls(data)
        
        # Handle list of values
        elif isinstance(data, list):
            enum_instances = []
            for i, item in enumerate(data):
                try:
                    enum_instances.append(cls(item))
                except DeserializationError as e:
                    raise DeserializationError(
                        f"Error at index {i} in enum list: {str(e)}"
                    )
            return enum_instances
        
        # Handle dictionary with enum fields
        elif isinstance(data, dict):
            # Create a copy to avoid modifying the original
            result = data.copy()
            
            # Find and convert any enum fields in the dictionary
            for key, value in data.items():
                if cls.is_valid(value):
                    result[key] = cls(value)
                elif isinstance(value, list) and all(cls.is_valid(item) for item in value):
                    result[key] = [cls(item) for item in value]
            
            return result
        
        else:
            raise DeserializationError(
                f"Cannot deserialize {cls.__name__} from {type(data).__name__}: {repr(data)}"
            )
    
    @classmethod
    def from_string(cls, value_str: str):
        """
        Create enum instance from string value.
        
        Args:
            value_str: The string representation of the value
            
        Returns:
            Enum instance
            
        Raises:
            DeserializationError: If the value is not valid
        """
        return cls(value_str)
    
    @classmethod
    def from_string_list(cls, value_list: List[str]):
        """
        Create list of enum instances from list of string values.
        
        Args:
            value_list: List of string representations
            
        Returns:
            List of enum instances
            
        Raises:
            DeserializationError: If any value is invalid
        """
        return cls.from_dict(value_list)
    
    @classmethod
    def get_attribute_name(cls, value) -> str:
        """
        Get the Python attribute name for an enum value.
        
        Args:
            value: The enum value (any base type)
            
        Returns:
            The corresponding attribute name (e.g., 'APPAREL_ACCESSORIES')
            
        Raises:
            DeserializationError: If the value is not valid
        """
        # Convert to base type first
        temp_instance = cls.__new__(cls)
        converted_value = temp_instance._convert_to_base_type(value)
        
        # Look through all class attributes to find matching value
        for attr_name in dir(cls):
            if not attr_name.startswith('__') and not callable(getattr(cls, attr_name, None)):
                attr_value = getattr(cls, attr_name, None)
                if attr_value == converted_value:
                    return attr_name
        
        # If no match found, provide helpful error
        available_values = cls.get_all_values()
        raise DeserializationError(
            f"Invalid enum value '{value}' for {cls.__name__}. "
            f"Available values: {available_values}"
        )
    
    @classmethod
    def to_string(cls, attr_name: str):
        """
        Convert enum attribute name to string representation of the value.
        
        Args:
            attr_name: The attribute name (e.g., 'APPAREL_ACCESSORIES')
            
        Returns:
            String representation of the corresponding value
            
        Raises:
            DeserializationError: If the attribute doesn't exist
        """
        if not hasattr(cls, attr_name):
            available_attrs = [name for name in dir(cls) 
                             if not name.startswith('__') and not callable(getattr(cls, name, None))]
            raise DeserializationError(
                f"Unknown enum attribute '{attr_name}' for {cls.__name__}. "
                f"Available attributes: {available_attrs}"
            )
        
        return str(getattr(cls, attr_name))
    
    @classmethod 
    def is_valid(cls, value) -> bool:
        """Check if a value is a valid enum value."""
        if value is None:
            return False
            
        # Create temporary instance to access conversion method
        temp_instance = cls.__new__(cls)
        try:
            converted_value = temp_instance._convert_to_base_type(value)
            return converted_value in cls.get_all_values()
        except:
            return False
    
    def to_dict(self):
        """
        Convert enum instance back to its base type value for serialization.
        """
        return self.value

PluginAuthType=PluginAuthType
plugin_auth_type=PluginAuthType
