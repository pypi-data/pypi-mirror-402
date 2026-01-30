from enum import Enum
from typing import Callable, Type, TypeVar

from casefy import pascalcase
from dacite import Config, from_dict
from dacite.data import Data

T = TypeVar("T")


def transform_json(obj, key_transform: Callable[[str], str]):
    """
    Transforms a JSON object by recursively iterating over its key-value pairs and applying the
    `key_transform` function to the keys.

    Args:
        obj (dict or list): The JSON object to be transformed.
        key_transform (callable): A function that takes a key and returns a transformed key.

    Returns:
        The transformed JSON object.
    """
    if isinstance(obj, dict):
        return {
            key_transform(key): transform_json(value, key_transform)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [transform_json(item, key_transform) for item in obj]
    else:
        return obj


def remove_none_values(obj: Data | list) -> Data | list:
    """
    Recursively removes keys from a dictionary or list if the value is None.

    Args:
        obj (Union[dict, list]): The input dictionary or list to remove None values from.

    Returns:
        Union[dict, list]: The input object with all keys removed those have None value.
    """
    if isinstance(obj, dict):
        return {k: remove_none_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [remove_none_values(v) for v in obj]
    else:
        return obj


def from_data(data_class: Type[T], data: Data) -> T:
    """
    Convert JSON data into an instance of the specified data class.

    Args:
        data_class (Type[T]): The data class type to convert the data into.
        data (Data): The JSON data to be converted.

    Returns:
        T: An instance of the specified data class populated with the converted data.
    """
    converted_data = transform_json(data, pascalcase)
    converted_data = remove_none_values(converted_data)
    return from_dict(
        data_class=data_class, data=dict(converted_data), config=Config(cast=[Enum])
    )
