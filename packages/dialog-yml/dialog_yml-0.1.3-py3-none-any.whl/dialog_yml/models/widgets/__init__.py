from .calendars import calendar_classes
from .counters import counter_classes
from .inputs import input_classes
from .kbd import keyboard_classes
from .medias import media_classes
from .scrolls import scroll_classes
from .selects import select_classes
from .texts import text_classes

widget_classes = {
    **calendar_classes,
    **counter_classes,
    **input_classes,
    **keyboard_classes,
    **media_classes,
    **scroll_classes,
    **select_classes,
    **text_classes,
}
