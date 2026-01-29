import json
from typing import get_type_hints, Optional, get_origin, get_args, Union, List, Dict, Any

class BaseModel:
    """Simple typed container with JSON-friendly helpers.

    Attributes are declared via type hints on subclasses. Incoming keyword
    arguments are coerced to the annotated types, including nested
    ``BaseModel`` subclasses as well as container types like ``list`` and
    ``dict``. Instances can be created from plain dictionaries with
    ``from_dict`` and serialized back with ``to_dict`` or ``to_json`` for
    easy interchange with JSON payloads.
    """
    def __init__(self, **kwargs):
        """Coerce provided keyword arguments into annotated attributes."""
        hints = get_type_hints(self.__class__)
        for field, field_type in hints.items():
            if field in kwargs:
                value = kwargs[field]
            else:
                value = getattr(self, field, None)

            value = self._parse_value(value, field_type, field)
            setattr(self, field, value)

    @classmethod
    def from_dict(cls, data: dict):
        """Instantiate the model from a plain dictionary payload."""
        return cls(**data)

    def to_dict(self):
        """Return a nested dictionary representation of the model."""
        result = {}
        for field, field_type in get_type_hints(self.__class__).items():
            value = getattr(self, field, None)
            if value is None:
                result[field] = None
            elif isinstance(value, BaseModel):
                result[field] = value.to_dict()
            elif isinstance(value, list):
                result[field] = [item.to_dict() if isinstance(item, BaseModel) else item for item in value]
            else:
                result[field] = value
        return result

    def to_json(self):
        """Serialize the model to a JSON string."""
        return json.dumps(self.to_dict())

    def _parse_value(self, value, field_type, field_name):
        """Normalize a value according to the field type declaration."""
        # Handle None values for any type
        if value is None:
            return None
            
        origin = get_origin(field_type)
        args = get_args(field_type)
        
        # Handle Optional (Union with NoneType)
        if origin is Union:
            if type(None) in args:
                for arg in args:
                    if arg is not type(None):
                        # Found the non-None type in the Union
                        # If value is None, we already returned above
                        return self._parse_value(value, arg, field_name)
        
        # Handle List
        if origin is list:
            if not isinstance(value, list):
                raise ValueError(f"Field '{field_name}' must be a list, got {type(value)}")
            
            # If list is empty or no type args, return as is
            if not args or not value:
                return value
                
            # Get the type of the list items
            item_type = args[0]
            
            # Convert items in the list if needed
            return [self._parse_value(item, item_type, f"{field_name}[{i}]") 
                   for i, item in enumerate(value)]
        
        # Handle Dict
        if origin is dict:
            if not isinstance(value, dict):
                raise ValueError(f"Field '{field_name}' must be a dict, got {type(value)}")
            
            # If dict is empty or no type args, return as is
            if not args or len(args) < 2 or not value:
                return value
                
            # Get the types of dict keys and values
            key_type, val_type = args
            
            # Convert keys and values if needed
            return {
                self._parse_value(k, key_type, f"{field_name}_key"): 
                self._parse_value(v, val_type, f"{field_name}[{k}]")
                for k, v in value.items()
            }
        
        # Handle nested models - check if field_type is a class (not an instance) and subclass of BaseModel
        if isinstance(value, dict) and isinstance(field_type, type) and issubclass(field_type, BaseModel):
            return field_type.from_dict(value)
        
        # Basic type validation
        if origin is None:  # It's a non-generic type
            if not isinstance(value, field_type):
                try:
                    return field_type(value)
                except Exception as e:
                    raise ValueError(f"Field '{field_name}' must be of type {field_type}, got {type(value)}")
        
        return value
