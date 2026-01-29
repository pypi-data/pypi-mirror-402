import json, os
from pathlib import Path
from typing import Any, Dict

CLASS_REGISTRY = {}

def register_class(cls):
    CLASS_REGISTRY[cls.__name__] = cls
    return cls



@register_class
class Setting:
    '''
    title - Название настройки для показа
    name - СЛужебное название, которое будет использоваться в функциях
    '''
    _title: str
    _name: str
    _value: str = ""
    
    def __init__(self, title: str, name: str):
        self._title = title
        self._name = name
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = value
    
    def to_dict(self) -> dict:
        return {
            "__type__": self.__class__.__name__,
            "title": self._title,
            "name": self._name,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(
            title=data["title"],
            name=data["name"]
        )
        obj.value = data["value"]
        return obj


def requires(*keys: Setting):
    def wrapper(fn):
        fn.required_settings = set(keys)
        return fn
    return wrapper

def json_encoder(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    raise TypeError

def json_decoder(obj):
    type_name = obj.get("__type__")
    if not type_name:
        return obj

    cls = CLASS_REGISTRY.get(type_name)
    if not cls:
        raise ValueError(f"Unknown type: {type_name}")

    return cls.from_dict(obj)

class AppContext:
    def __init__(self, _base_path: Path):
        
        path = os.path.join(_base_path, "settings.json")
        if os.path.exists(path) == False:
            with open(path, "w") as f:
                json.dump({}, f, default=json_encoder)
            self.base_path = _base_path.__str__()
        else:
            with open(path, "r") as f:
                settings: Dict[str, Any] = json.load(f, object_hook=json_decoder)
                for key, value in settings.items():
                    setattr(self, key, value)

    def __setattr__(self, name: str, value:str):
        super().__setattr__(name, value)
        
        if name == "base_path":
            path = os.path.join(value, "settings.json")
        else:
            path = os.path.join(getattr(self, "base_path"),"settings.json")
        with open(path, "r") as f:
            d: Dict[str, Any] = json.load(f, object_hook=json_decoder)
            d[f"{name}"] = value
            removed = d.keys() - self.__dict__.keys()
            for key in removed:
                del d[f"{key}"]
        with open(path, "w") as f:
            json.dump(d, f, default=json_encoder)
            