"""Dialog YML library for building aiogram-dialog applications using YAML configuration files."""

import sys

from .core import DialogYAMLBuilder
from .models.funcs.func import FuncsRegistry
from .exceptions import (
    DialogYamlException,
    ModelRegistrationError,
    FunctionRegistrationError,
    FunctionNotFoundError,
    StatesGroupNotFoundError,
    StateNotFoundError,
    InvalidFunctionType,
    MissingFunctionName,
    CategoryNotFoundError,
    InvalidTagName,
    InvalidTagDataType,
)
from .middleware import DialogYAMLMiddleware
from .reader import YAMLReader
from .states import YAMLStatesManager
from .utils import clean_empty

__all__ = [
    "DialogYAMLBuilder",
    "DialogYamlException",
    "DialogYAMLMiddleware",
    "ModelRegistrationError",
    "FuncsRegistry",
    "FunctionRegistrationError",
    "FunctionNotFoundError",
    "StatesGroupNotFoundError",
    "StateNotFoundError",
    "InvalidFunctionType",
    "MissingFunctionName",
    "CategoryNotFoundError",
    "InvalidTagName",
    "InvalidTagDataType",
    "YAMLReader",
    "YAMLStatesManager",
    "clean_empty",
]

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

try:
    __version__ = metadata.version("dialog_yml")
except Exception:
    __version__ = "unknown"
