from abc import ABC, abstractmethod
from typing import Any, Self

from aiogram_dialog.api.internal import Widget
from pydantic import ConfigDict, BaseModel

from dialog_yml.models.funcs.func import FuncField


class YAMLModel(BaseModel, ABC):
    """Base class for all YAML models.

    It provides a base implementation for converting data to a model
    and vice versa, specifically for YAML serialization and deserialization.

    :ivar model_config: The configuration of the YAML models.
    :vartype model_config: ConfigDict
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @classmethod
    @abstractmethod
    def to_model(cls, data: Any) -> Self:
        pass

    @abstractmethod
    def to_object(self) -> Widget:
        pass


class WidgetModel(YAMLModel):
    """Base class for all widget models.

    :ivar when: The function to be called when the widget is selected.
        FuncField the pydantic annotation to FuncModel
    :vartype when: FuncField
    """

    def to_object(self):
        raise NotImplementedError()

    when: FuncField = None

    @classmethod
    def to_model(cls, data: Any):
        raise NotImplementedError(data)
