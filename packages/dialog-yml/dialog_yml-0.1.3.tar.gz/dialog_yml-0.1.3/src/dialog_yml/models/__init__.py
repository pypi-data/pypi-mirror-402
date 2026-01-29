"""The `src.models` module provides the `YAMLModelFactory` class
for creating YAML models.

`YAMLModelFactory` class offers functionality for working with YAML data
and creating instances of custom model classes based on the YAML data.

Features:
-----------
- Allows the registration of custom model classes with unique tags.
- Provides a method to create instances of custom model classes from YAML data.
- Supports the retrieval of the registered model class based on the tag.

Classes:
-----------
- YAMLModelFactory: Static class for creating YAML models.
"""

import logging
import re
from logging import Logger
from typing import Type, Union, Dict, Any

from pydantic import ValidationError, BaseModel

from dialog_yml.exceptions import (
    ModelRegistrationError,
    InvalidTagName,
    DialogYamlException,
)
from dialog_yml.models.base import YAMLModel

logger: Logger = logging.getLogger(__name__)


class YAMLModelFactory:
    """The `YAMLModelFactory`
    class is a static class
    that provides functionality for working with YAML data
    and creating instances of custom model classes based on the YAML data.
    It allows the registration of custom model classes with unique tags
    and supports the retrieval of the registered model class based on the tag.

    - Allows the registration of custom model classes with unique tags.
    - Provides a method to create instances of custom
        model classes from YAML data.
    - Supports the retrieval of the registered model class based on the tag.

    :ivar _models_classes: A dictionary that maps tag to model class.
    :vartype _models_classes: Dict[str, Type[YAMLModel]]
    """

    _models_classes: Dict[str, Type[YAMLModel]] = {}

    @classmethod
    def is_valid_tag(cls, tag: str) -> bool:
        """Check if the given tag is a valid tag.

        :param tag: The tag to be checked.
        :type tag: str

        :return: True if the tag is valid, False otherwise.
        :rtype: bool

        :raises InvalidTagName: When the tag is invalid
        """
        if not tag or not isinstance(tag, str):
            raise InvalidTagName(tag, "{tag!r} must be non-empty string")

        if tag.isdigit():
            raise InvalidTagName(tag, "{tag!r} must contain a letters, not only numbers")

        if not re.fullmatch(r"[a-zA-Z0-9_-]+", tag):
            raise InvalidTagName(
                tag, "{tag!r} must contains only latin letters and numbers"
            )

        return True

    @classmethod
    def is_valid_model_class(
        cls, tag: str, model_class: Union[Type[YAMLModel], Type[BaseModel]]
    ) -> bool:
        """Check if the given model class is a valid
        model class for the specified tag.

        :param tag: The tag associated with the model class.
        :type tag: str
        :param model_class: The model class to be checked.
        :type model_class: Union[Type[YAMLModel], Type[BaseModel]]

        :return: True if the model class is valid, False otherwise.
        :rtype: bool

        :raises ModelRegistrationError: When a model is not
            a valid model class.
        """

        if not model_class or not issubclass(model_class, (YAMLModel, BaseModel)):
            raise ModelRegistrationError(
                tag,
                model_class,
                message="{model_class!r} mapped to {tag!r} "
                "must be type of YAMLModel or BaseModel",
            )

        return True

    @classmethod
    def _is_valid(
        cls, tag: str, model_class: Union[Type[YAMLModel], Type[BaseModel]]
    ) -> bool:
        """Check if the given tag is valid for the specified model class.

        :param tag: The tag associated with the model class.
        :type tag: str
        :param model_class: The model class to be checked.
        :type model_class: Type[YAMLModel]

        :return: True if the tag is valid, False otherwise.
        :rtype: bool
        """

        cls.is_valid_tag(tag)
        cls.is_valid_model_class(tag, model_class)
        return True

    @classmethod
    def add_model_class(
        cls,
        tag: str,
        model_class: Type[YAMLModel],
        replace_existing: bool = False,
    ):
        """Registers a custom model class with a unique tag.

        :param tag: A unique tag for the custom model class.
        :type tag: Str
        :param model_class: The custom model class to be registered.
        :type model_class: Type[YAMLModel]
        :param replace_existing: Whether to replace an existing
            model class with the same tag.
        :type replace_existing: bool

        :raises ModelRegistrationError: When a model with the same tag
            has already been registered.
        """

        if cls._is_valid(tag, model_class):
            registered_model_class = cls.get_model_class(tag)

            if registered_model_class and not replace_existing:
                raise ModelRegistrationError(
                    tag,
                    registered_model_class,
                    message="{tag!r} already registered with {model_class!r}",
                )

            cls._models_classes[tag] = model_class

    @classmethod
    def get_model_class(cls, tag: str) -> Union[Type[YAMLModel], None]:
        """Retrieves a registered custom model class based on its tag.

        :param tag: The tag of the custom model class to retrieve.
        :type tag: Str

        :return: The custom model class associated with
            the given tag or None if not found.
        :rtype: Type[YAMLModel] or None
        """

        logger.debug("Get class for tag %r", tag)
        return cls._models_classes.get(tag)

    @classmethod
    def set_classes(cls, models_classes: Dict[str, Type[YAMLModel]]) -> None:
        """Sets the registered custom model classes.

        :param models_classes: A dictionary of custom
            model classes with their tags.
        :type models_classes: Dict[str, Type[YAMLModel]]

        :raises DialogYamlException: When `models_classes` is not
            a valid dictionary of model classes.
        """

        if not isinstance(models_classes, dict):
            raise DialogYamlException(
                "models_classes must be a dictionary of strings to YAMLModel classes"
            )

        for key, value in models_classes.items():
            cls._is_valid(key, value)

        cls._models_classes = models_classes

    @classmethod
    def create_model(cls, yaml_data: Dict[str, Any]) -> YAMLModel:
        """Creates an instance of a custom model class based on YAML data.

        :param yaml_data: A dictionary representing the YAML data.
        :type yaml_data: Dict[str, Any]

        :return: An instance of the custom model class based
            on the existing class in the `YAMLModelFabric._models_classes`,
            founded by `tag` in `yaml_data`.
        :rtype: YAMLModel

        :raises DialogYamlException: When `yaml_data` is `None`
            or an empty dictionary.
        :raises InvalidTagName: When a tag key does not exist
            in the `YAMLModelFabric._models_classes`.
        """

        if not yaml_data or not isinstance(yaml_data, dict):
            raise DialogYamlException("yaml_data must be a non-empty dictionary")

        tag = next(iter(yaml_data))  # getting first key
        cls.is_valid_tag(tag)
        model_class = cls.get_model_class(tag)

        data = yaml_data[tag]
        logger.debug("Parse tag %r with data %s", tag, data)

        try:
            model = model_class.to_model(data)
        except ValidationError as e:
            raise DialogYamlException(f"Failed to parse tag {tag!r}: {e}") from e

        return model
