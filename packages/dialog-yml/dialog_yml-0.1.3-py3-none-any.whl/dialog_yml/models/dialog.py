from typing import Union, Self

from aiogram_dialog import LaunchMode, Dialog
from pydantic import field_validator

from dialog_yml.models.base import YAMLModel
from dialog_yml.models.funcs.func import FuncField
from dialog_yml.utils import clean_empty


class DialogModel(YAMLModel):
    windows: list[YAMLModel]
    on_start: FuncField = None
    on_close: FuncField = None
    on_process_result: FuncField = None
    launch_mode: LaunchMode = LaunchMode.STANDARD
    getter: FuncField = None
    preview_data: FuncField = None

    def to_object(self) -> Dialog:
        kwargs = clean_empty(
            {
                "on_start": self.on_start.func if self.on_start else None,
                "on_close": self.on_close.func if self.on_close else None,
                "on_process_result": self.on_process_result.func
                if self.on_process_result
                else None,
                "launch_mode": self.launch_mode,
                "getter": self.getter.func if self.getter else None,
                "preview_data": self.preview_data.func if self.getter else None,
            }
        )
        return Dialog(*[window.to_object() for window in self.windows], **kwargs)

    @field_validator("launch_mode", mode="before")
    def validate_launch_mode(cls, value) -> Union[LaunchMode, None]:
        if isinstance(value, LaunchMode):
            return value
        if isinstance(value, str):
            return LaunchMode[value.upper()]
        return None

    @classmethod
    def to_model(cls, data: Union[dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        return cls(**data)
