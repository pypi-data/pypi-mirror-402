import functools
from typing import Union, Self, Any, Annotated, Callable

from aiogram.fsm.state import State
from aiogram_dialog import StartMode
from aiogram_dialog.widgets.kbd import (
    Url,
    Button,
    SwitchTo,
    Start,
    Next,
    Back,
    Cancel,
    Group,
    ScrollingGroup,
)
from pydantic import field_validator, BeforeValidator

from dialog_yml.exceptions import StateNotFoundError
from dialog_yml.models import YAMLModelFactory
from dialog_yml.models.base import WidgetModel
from dialog_yml.models.funcs.func import (
    FuncField,
    NotifyField,
    FuncModel,
    function_registry,
)
from dialog_yml.models.widgets.texts.text import TextField
from dialog_yml.states import YAMLStatesManager
from dialog_yml.utils import clean_empty


class ButtonModel(WidgetModel):
    id: str = None
    text: TextField

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if not data:
            return cls()
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            data = {"text": data}
        return cls(**data)


class UrlButtonModel(ButtonModel):
    uri: TextField

    def to_object(self) -> Url:
        kwargs = clean_empty(
            {
                "text": self.text.to_object() if self.text else None,
                "url": self.uri.to_object() if self.uri else None,
                "when": self.when.func if self.when else None,
            }
        )
        return Url(**kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            data = {"uri": data}
        return cls(**data)


class CallbackButtonModel(ButtonModel):
    on_click: FuncField = None
    notify: NotifyField = None

    def _get_partial_on_click(self) -> Callable:
        """Returns a partial function that can be used
        as a callback for a button click event.

        The returned partial function captures the values
        of `on_click` and `notify` from the `self` object.

        :return: partial function that can be used as a callback
        :rtype: Callable
        """

        partial_on_click = None
        partial_data = clean_empty({"on_click": self.on_click, "notify": self.notify})

        async def wrap_functions(*args, **kwargs) -> None:
            """Function that wraps the `on_click` and `notify` functions.

            :param args: args to pass to `on_click`
            :param kwargs: kwargs to pass to `on_click`

            :return: None
            :rtype: None
            """
            callback = None

            if notify := self.notify:
                callback = (
                    notify.func,
                    {"data": {**notify.data, **self.model_extra}},
                )

            if on_click := self.on_click:
                if callback:
                    await notify.run_async(*args, **callback[1])
                callback = (
                    on_click.func,
                    {"data": {**on_click.data, **self.model_extra}},
                )

            if callback is not None:
                await callback[0](*args, **callback[1])

        if partial_data:
            partial_on_click = functools.partial(wrap_functions, **partial_data)

        return partial_on_click

    def to_object(self) -> Button:
        kwargs = clean_empty(
            {
                "text": self.text.to_object() if self.text else None,
                "id": self.id,
                "on_click": self._get_partial_on_click(),
                "when": self.when.func if self.when else None,
            }
        )
        return Button(**kwargs)


class SwitchToModel(CallbackButtonModel):
    id: str
    state: State

    def to_object(self) -> SwitchTo:
        kwargs = clean_empty(
            {
                "id": self.id,
                "text": self.text.to_object() if self.text else None,
                "on_click": self._get_partial_on_click(),
                "when": self.when.func if self.when else None,
                "state": self.state,
            }
        )
        return SwitchTo(**kwargs)

    @classmethod
    def to_model(cls, data: Union[dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        return cls(**data)

    @field_validator("state", mode="before")
    def validate_state(cls, value) -> State:
        state = YAMLStatesManager().get_by_name(value)
        if not state:
            raise StateNotFoundError(value)
        return state


class StartModel(CallbackButtonModel):
    id: str
    data: Union[str, int, float, dict[str, Any], list[Any]] = None
    mode: StartMode = StartMode.NORMAL
    state: State

    def to_object(self) -> Start:
        kwargs = clean_empty(
            {
                "id": self.id,
                "text": self.text.to_object() if self.text else None,
                "on_click": self._get_partial_on_click(),
                "when": self.when.func if self.when else None,
                "state": self.state,
                "data": self.data,
                "mode": self.mode,
            }
        )
        return Start(**kwargs)

    @field_validator("state", mode="before")
    def validate_state(cls, value) -> State:
        state = YAMLStatesManager().get_by_name(value)
        if not state:
            raise ValueError(f'State "{value}" is declared but not provided.')
        return state

    @field_validator("mode", mode="before")
    def validate_mode(cls, value):
        if isinstance(value, StartMode):
            return value
        elif isinstance(value, str):
            return StartMode[value.upper()]
        else:
            return None


class NextModel(CallbackButtonModel):
    text: TextField = None

    def to_object(self) -> Next:
        kwargs = clean_empty(
            {
                "id": self.id,
                "text": self.text.to_object() if self.text else None,
                "on_click": self._get_partial_on_click(),
                "when": self.when.func if self.when else None,
            }
        )
        return Next(**kwargs)


class BackModel(CallbackButtonModel):
    text: TextField = None

    def to_object(self) -> Back:
        kwargs = clean_empty(
            {
                "id": self.id,
                "text": self.text.to_object() if self.text else None,
                "on_click": self._get_partial_on_click(),
                "when": self.when.func if self.when else None,
            }
        )
        return Back(**kwargs)


class CancelModel(CallbackButtonModel):
    text: TextField = None
    result: Union[FuncField, Any] = None

    def to_object(self) -> Cancel:
        result = self.result
        if isinstance(result, FuncModel):
            result = result.func
        kwargs = clean_empty(
            {
                "id": self.id,
                "text": self.text.to_object() if self.text else None,
                "on_click": self._get_partial_on_click(),
                "when": self.when.func if self.when else None,
                "result": result,
            }
        )
        return Cancel(**kwargs)


class GroupKeyboardModel(WidgetModel):
    id: str = None
    width: int = None
    buttons: list[WidgetModel]

    def to_object(self) -> Group:
        kwargs = clean_empty(
            {
                "id": self.id,
                "width": self.width,
                "when": self.when.func if self.when else None,
            }
        )
        return Group(*[button.to_object() for button in self.buttons], **kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            if buttons := data.get("buttons"):
                if isinstance(buttons, str):
                    buttons_getter_func = function_registry.func.get(buttons)
                    buttons = buttons_getter_func()
                if isinstance(buttons, list):
                    data["buttons"] = [
                        YAMLModelFactory.create_model(button_data)
                        for button_data in buttons
                    ]
        return cls(**data)


GroupKeyboardField = Annotated[
    GroupKeyboardModel, BeforeValidator(GroupKeyboardModel.to_model)
]


class ColumnKeyboardModel(GroupKeyboardModel):
    width: int = 1


class RowKeyboardModel(GroupKeyboardModel):
    width: int = 9999


class ScrollingGroupKeyboardModel(GroupKeyboardModel):
    id: str
    height: int = 1
    on_page_changed: FuncField = None
    hide_on_single_page: bool = False
    hide_pager: bool = False

    def to_object(self) -> ScrollingGroup:
        kwargs = clean_empty(
            {
                "id": self.id,
                "height": self.height,
                "width": self.width,
                "on_page_changed": self.on_page_changed.func
                if self.on_page_changed
                else None,
                "hide_on_single_page": self.hide_on_single_page,
                "hide_pager": self.hide_pager,
            }
        )
        return ScrollingGroup(*[button.to_object() for button in self.buttons], **kwargs)
