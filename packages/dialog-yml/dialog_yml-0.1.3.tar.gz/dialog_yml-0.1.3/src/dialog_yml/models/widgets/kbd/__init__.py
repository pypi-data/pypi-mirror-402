from dialog_yml.models.widgets.kbd import keyboard

keyboard_classes = {
    "button": keyboard.ButtonModel,
    "url": keyboard.UrlButtonModel,
    "callback": keyboard.CallbackButtonModel,
    "switch_to": keyboard.SwitchToModel,
    "start": keyboard.StartModel,
    "next": keyboard.NextModel,
    "back": keyboard.BackModel,
    "cancel": keyboard.CancelModel,
    "group": keyboard.GroupKeyboardModel,
    "row": keyboard.RowKeyboardModel,
    "column": keyboard.ColumnKeyboardModel,
    "scrolling_group": keyboard.ScrollingGroupKeyboardModel,
}
