import asyncio
from enum import Enum
from typing import (
    Dict,
    Union,
    Callable,
    Awaitable,
    Self,
    Annotated,
)

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from pydantic import (
    model_validator,
    BeforeValidator,
    ConfigDict,
    BaseModel,
    StringConstraints,
)

from dialog_yml.decorators import singleton
from dialog_yml.exceptions import (
    FunctionRegistrationError,
    InvalidFunctionType,
    CategoryNotFoundError,
    FunctionNotFoundError,
)
from dialog_yml.utils import clean_empty


class CategoryName(Enum):
    """The CategoryName class represents the names of categories for functions.

    :cvar func: The name of the 'func' category.
        This category is used for other functions, such as data
        getters, setters, filers, conditions, and others.
    :vartype func: CategoryName
    :cvar notify: The name of the 'notify' category.
        This category uses for notification functions
    :vartype notify: CategoryName
    """

    func = "func"
    notify = "notify"


class Category:
    """The Category class represents a category of functions
        and provides methods for registering and retrieving
    functions within the category.

    :param name: The name of the category, if not provided,
        the category will be named 'func'.
    :type name: CategoryName

    :ivar _name: The name of the category
    :vartype _name: CategoryName
    """

    _name: str
    _functions: Dict[str, Union[Callable, Awaitable]]

    def __init__(self, name: Union[str, CategoryName] = CategoryName.func):
        self._name = name.value if isinstance(name, CategoryName) else name
        self._functions = {}

    def __str__(self):
        return f"Category(name={self._name}, functions={self._functions})"

    def register(self, function: Union[Callable, Awaitable]):
        """Register a function within the category.

        :param function: The function to register
        :type function: Union[Callable, Awaitable]

        :raises FunctionRegistrationError: If the function is
            already registered within the category
        :raises InvalidFunctionType: If the function is not a Callable
            or an Awaitable object
        """

        if not isinstance(function, (Callable, Awaitable)):
            raise InvalidFunctionType(str(function))

        function_name = function.__name__
        if function_name in self._functions:
            raise FunctionRegistrationError(self._name, function_name)

        self._functions[function_name] = function

    def get(self, function_name: str) -> Union[Callable, Awaitable, None]:
        """Retrieve a function from the category.

        :param function_name: The name of the function to retrieve
        :type function_name: str

        :return: The retrieved function or None if the function
            is not registered within the category
        :rtype: Union[Callable, Awaitable, None]
        """

        return self._functions.get(function_name)


@singleton
class FuncsRegistry:
    """The FuncsRegistry class manages the registration
    and retrieval of functions.

    :ivar _categories_map_: A dictionary of categories
    :vartype _categories_: Dict[str, Category]
    """

    _categories_map_: Dict[str, Category]

    def __init__(self):
        self.clear_categories()

    def clear_categories(self):
        self._categories_map_ = {
            category_name.value: Category(category_name.value)
            for category_name in CategoryName
        }

    @property
    def func(self) -> Category:
        return self._categories_map_[CategoryName.func.value]

    @property
    def notify(self) -> Category:
        return self._categories_map_[CategoryName.notify.value]

    def register(
        self,
        function: Union[Callable, Awaitable],
        category_name: Union[str, CategoryName] = CategoryName.func,
    ) -> None:
        """Registers a function in the specified category.

        :param function: The function to be registered.
        :type function: Union[Callable, Awaitable]
        :param category_name: The name of the category.
            Defaults to `CategoryName.func`.
        :type category_name: Union[str, CategoryName], optional
        """

        if isinstance(category_name, CategoryName):
            category_name = category_name.value

        category = self.get_category(category_name)
        category.register(function)

    def get_category(self, name: str = CategoryName.func.value) -> Category:
        """Retrieves the category with the specified name.

        :param name: The name of the category. Defaults to `func`
        :type name: Union[str, CategoryName]

        :return: The category object.
        :rtype: Category
        """

        category = self._categories_map_.get(name)

        if category is not None:
            return category

        raise CategoryNotFoundError(name)

    def get_function(
        self, function_name: str, category_name: str = CategoryName.func.value
    ) -> Union[Callable, Awaitable]:
        """Retrieves the function with the specified name
        from the specified category.

        :param category_name: The name of the category. Defaults to `funcs`
        :type category_name: Union[str, CategoryName]
        :param function_name: The name of the function.
        :type function_name: str

        :return: The function object or `None` if not found.
        :rtype: Union[Callable, Awaitable, None]
        """

        category = self.get_category(category_name)
        function = category.get(function_name)
        return function


async def notify_func(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    data: Dict,
) -> None:
    if delay := data.get("delay"):
        await asyncio.sleep(delay=delay)
    await callback.answer(
        **data,
    )


function_registry = FuncsRegistry()
function_registry.notify.register(function=notify_func)


class FuncModel(BaseModel):
    def to_object(self) -> Union[Callable, Awaitable]:
        return self.func

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    category_name: str = CategoryName.func.value
    name: str

    @property
    def data(self) -> Dict:
        return clean_empty({"extra_data": self.model_extra})

    @property
    def func(self):
        f = function_registry.get_function(self.name, self.category_name)
        return f

    async def run_async(self, *args, **kwargs):
        asyncio.create_task(self.func(*args, **kwargs))

    @model_validator(mode="after")
    def check_func(self) -> Self:
        category_name = self.category_name
        func_name = self.name

        f = function_registry.get_function(func_name, category_name)

        if f is None:
            raise FunctionNotFoundError(category_name, func_name)

        return self

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            data = {"name": data}
        return cls(**data)


FuncField = Annotated[FuncModel, BeforeValidator(FuncModel.to_model)]


class NotifyModel(FuncModel):
    category_name: str = CategoryName.notify.value
    name: str = "notify_func"
    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    ]
    show_alert: bool = False
    delay: Union[int, None] = None

    @property
    def data(self) -> Dict:
        return clean_empty(
            {
                "text": self.text,
                "show_alert": self.show_alert,
                "delay": self.delay,
                "extra_data": self.model_extra,
            }
        )

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            if val := data.pop("val"):
                data["text"] = val
        if isinstance(data, str):
            data = {
                "text": data,
                "name": cls.model_fields["name"].default,
                "category_name": cls.model_fields["category_name"].default,
                "delay": cls.model_fields["delay"].default,
                "show_alert": cls.model_fields["show_alert"].default,
            }
        return cls(**data)


NotifyField = Annotated[NotifyModel, BeforeValidator(NotifyModel.to_model)]
