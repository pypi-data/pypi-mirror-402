"""The main functionality of the `src.states` module is to manage
and store states and state groups used in a dialog FSM system.

It provides the necessary functionality to dynamically
build and manage the states and state groups used
in a dialog FSM system.

Futures:
---------
- Loading states from data
- Build, store and manage `StatesGroup` and `States`

Classes:
---------
- YAMLStatesManager: A singleton class responsible
for managing and storing states and state groups.
"""

from collections import defaultdict
from typing import List, Dict, Union, Iterable, Set, Type

from aiogram.fsm.state import State, StatesGroup

from dialog_yml.decorators import singleton
from dialog_yml.exceptions import DialogYamlException, StatesGroupNotFoundError


@singleton
class YAMLStatesManager:
    """A singleton class responsible for managing and storing states
    and state groups used in a dialog FSM system.

    - Manages and stores states and state groups used in a dialog system
    - Loads states from data
    - Retrieves states by name
    - Adds states from a list

    :ivar DELIMITER: The delimiter used to separate state names
    :vartype DELIMITER: str
    :ivar _states_groups_map_: A Dictionary that maps state names
        to states and state groups.
    :vartype _states_groups_map_: Dict[str, Union[State, StatesGroup]]
    """

    DELIMITER = ":"
    _states_groups_map_: Dict[str, Union[State, StatesGroup]]

    def __init__(self):
        self._states_groups_map_ = {}

    def get_by_names(
        self, group_name: str, state_name: str
    ) -> Union[StatesGroup, State, None]:
        """Get the state object by its name.

        :param group_name: The name of the group
        :type group_name: str
        :param state_name: The name of the state
        :type state_name: str

        :return: The state object or None if state not found.
        :rtype: Union[State, None]
        """

        name = self.format_state_name(group_name, state_name)
        return self.get_by_name(name)

    def get_by_name(self, name: str) -> Union[StatesGroup, State, None]:
        """Get the state object by its name.

        :param name: The name of the state
        :type name: str

        :return: The StatesGroup or State object or None if not found.
        :rtype: Union[StatesGroup, State, None]
        """

        result = self._states_groups_map_.get(name)
        return result

    def build_states_from_yaml_data(self, input_data: Dict) -> None:
        """Builds the state object from YAML data
        and extends to `_states_groups_map_`.

        Example valid data:
            {'dialogs': {'group1': {'windows':
            {'state1': {}, 'state2': {}, ...}}, ...}}

        When:
            - "group1" is `StatesGroup` name
            - "state1" and "state2" are `State` names
            - ... are other `StatesGroup` and `State`

        Explained:
            This will build and extend group1 states group
            and his state1 and state2 states.
            Keys "dialogs" and "windows" are !required in input_data

        :param input_data: The data to load states from
        :type input_data: Dict

        :return: None
        :rtype: None

        :raises DialogYamlException: When the input data is invalid
        """

        try:
            for group_name, group_data in input_data["dialogs"].items():
                states = self._build_states(group_data["windows"].keys(), group_name)
                states_group = self._build_states_group(group_name, states)

                self.add_states_group_to_map(group_name, states_group)
                self.add_states_to_map(group_name, states)

        except (TypeError, KeyError, AttributeError) as e:
            raise DialogYamlException(
                'Invalid data. Use the "check_yaml_data_base_structure" '
                "function from class DialogYAMLBuilder "
                f"before using this method. Error: {e}"
            )

    @classmethod
    def _build_states(
        cls, values: Iterable[str], group_name: str | None = None
    ) -> Dict[str, State]:
        """Builds a Dictionary of State objects based on the given values.

        :param values: The tuple of state names.
        :type values: tuple

        :return: A Dictionary of state names and State objects.
        :rtype: Dict[str, State]
        """

        return {state_name: State(state_name, group_name) for state_name in values}

    @classmethod
    def _build_states_group(cls, group_name: str, states: Dict[str, State]) -> StatesGroup:
        """Builds a new StatesGroup subclass dynamically based
        on the given group name and states.

        :param group_name: The name of the new StatesGroup subclass.
        :type group_name: str
        :param states: The Dictionary of state names and State objects.
        :type states: Dict[str, State]

        :return: A new instance of the dynamically
            created StatesGroup subclass.
        :rtype: StatesGroup
        """

        group_class = type(group_name, (StatesGroup,), states)
        return group_class()

    @classmethod
    def extract_group_and_state_names(cls, raw_states_group: str) -> tuple[str, str]:
        """Extracts the group name and state name from
        the given raw states group string.

        :param raw_states_group: The raw states group.
        :type raw_states_group: str

        :return: The group name and state name.
        :rtype: tuple[str, str]

        :raises DialogYamlException: If the raw states group is invalid.
        """

        if not isinstance(raw_states_group, str):
            raise DialogYamlException(
                f"Invalid state name {raw_states_group!r}. "
                f"Expected str, got {type(raw_states_group)}"
            )

        if raw_states_group.startswith(cls.DELIMITER) or raw_states_group.endswith(
            cls.DELIMITER
        ):
            raise DialogYamlException(
                f"Invalid state name {raw_states_group!r}. "
                f"Wrong delimiter {cls.DELIMITER!r}"
            )

        delimiter_count = raw_states_group.count(cls.DELIMITER)
        if not (0 < delimiter_count < 2):
            raise DialogYamlException(
                f"Invalid state name {raw_states_group!r}. "
                f"Wrong number of delimiters {delimiter_count} "
                f"for {cls.DELIMITER!r} delimiter"
            )

        parts = raw_states_group.split(cls.DELIMITER)
        return parts[0], parts[1]

    def parse_raw_states_from_list(
        self, raw_states_list: Set[str]
    ) -> Dict[str, List[Union[StatesGroup, State]]]:
        """Parses the raw states from the given raw states list.

        :param raw_states_list: The raw states list.
        :type raw_states_list: List[str]

        :return: The parsed states.
        :rtype: Dict[str, List[Union[StatesGroup, State]]]
        """

        parsed_states = defaultdict(list)
        for raw_states in raw_states_list:
            group_name, state_name = self.extract_group_and_state_names(raw_states)
            parsed_states[group_name].append(state_name)

        result = {}
        for group_name, raw_states in parsed_states.items():
            states = self._build_states(raw_states, group_name)
            states_group = self._build_states_group(group_name, states)
            result[group_name] = states_group
            result.update(
                **{
                    self.format_state_name(group_name, state_name): state
                    for state_name, state in states.items()
                }
            )

        return result

    def _build_states_groups(self, data: Dict[str, List[str]]) -> None:
        """Adds states groups to the states groups map.

        :param data: The data
        :type data: Dict[str, List[str]]

        :return: None
        :rtype: None
        """

        for group_name, raw_states in data.items():
            states = self._build_states(tuple(raw_states))
            states_group = self._build_states_group(group_name, states)
            self.add_states_group_to_map(group_name, states_group)
            self.add_states_to_map(group_name, states)

    def add_state_to_map(self, group_name: str, state: State):
        """Adds a state to the states groups map.

        :param group_name: The group name
        :type group_name: str
        :param state: State instance
        :type state: State

        :return: None
        :rtype: None

        :raises StatesGroupNotFoundError: If the states group is not found.
        """

        state_name = state._state
        if state_name is None:
            raise DialogYamlException("State name cannot be None")
        full_state_name = self.format_state_name(group_name, state_name)
        states_group = self._states_groups_map_.get(group_name, None)

        if not states_group:
            raise StatesGroupNotFoundError(group_name)

        state.set_parent(states_group.__class__)
        self._states_groups_map_[full_state_name] = state

    def add_states_to_map(self, group_name: str, states: Dict[str, State]) -> None:
        """Adds states to the states groups map.

        :param group_name: The group name
        :type group_name: str
        :param states: The states
        :type states: Dict[str, State]

        :return: None
        :rtype: None
        """

        for state_name, state in states.items():
            self.add_state_to_map(group_name, state)

    def add_states_group_to_map(self, group_name: str, states_group: StatesGroup) -> None:
        """Adds a states group to the states groups map.

        :param group_name: The group name
        :type group_name: str
        :param states_group: The states group
        :type states_group: StatesGroup

        :return: None
        :rtype: None
        """

        self._states_groups_map_[group_name] = states_group

    @classmethod
    def format_state_name(cls, group_name: str, state_name: str) -> str:
        """Format the state name by concatenating
        the group name and the state name.

        :param group_name: The group name
        :type group_name: str
        :param state_name: The state name
        :type state_name: str

        :return: The formatted state name
        :rtype: str
        """

        return f"{group_name}{cls.DELIMITER}{state_name}"

    def get_group_names(self) -> List[str]:
        """Get all the group names from the states groups map.

        :return: A list of group names
        :rtype: List[str]
        """
        # Group names are the keys that don't contain the delimiter
        group_names = []
        for key in self._states_groups_map_.keys():
            if self.DELIMITER not in key:
                # Check if this key represents a StatesGroup (not a State)
                item = self._states_groups_map_[key]
                if isinstance(item, StatesGroup):
                    group_names.append(key)
        return group_names

    def include_states_group_by_class(self, custom_state_class: Type[StatesGroup]) -> None:
        """It creates an instance of the custom `StatesGroup` class,
        extracts the states from the instance, and adds them
        to the _states_groups_map_.

        :param custom_state_class: The custom `StatesGroup` class
        :type custom_state_class: Type[StatesGroup]

        :return: None
        :rtype: None

        :raises DialogYamlException: If the custom `StatesGroup` class is not
            a subclass of `StatesGroup`.
        """

        group_name = custom_state_class.__name__

        if not issubclass(custom_state_class, StatesGroup):
            raise DialogYamlException(f"{group_name!r} must be a subclass of StatesGroup")

        states_group = custom_state_class()
        self.add_states_group_to_map(group_name, states_group)

        # Access states via __dict__ or iterate through the group attributes
        states_attrs = {}
        for attr_name in dir(states_group):
            attr_value = getattr(states_group, attr_name)
            if isinstance(attr_value, State):
                states_attrs[attr_name] = attr_value

        if states_attrs:
            for state_name, state in states_attrs.items():
                self.add_state_to_map(group_name, state)
        else:
            raise DialogYamlException(f"{group_name!r} must have at least one state.")
