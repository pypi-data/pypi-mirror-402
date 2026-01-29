import curses
from enum import Enum


class MouseButton(Enum):
    NONE = 0
    LEFT_MOUSE = 1
    MIDDLE_MOUSE = 2
    RIGHT_MOUSE = 3
    MOUSE_BUTTON_4 = 4
    MOUSE_BUTTON_5 = 5

    WHEEL_UP = 4
    WHEEL_DOWN = 5


class MouseEventType(Enum):
    NONE = 0
    CLICKED = 1
    PRESSED = 2
    RELEASED = 3
    DOUBLE_CLICKED = 4
    TRIPLE_CLICKED = 5
    MOVED = 6


class MouseMod(Enum):
    NONE = 0
    SHIFT = 1
    CONTROL = 2
    ALT = 3


class MouseEvent:

    def __init__(
        self,
        row: int,
        col: int,
        button: MouseButton,
        event_type: MouseEventType,
        mod: MouseMod,
    ):
        self.row = row
        self.column = col
        self.button = button
        self.event_type = event_type
        self.mod = mod

    @staticmethod
    def get_null():
        return MouseEvent(-1, -1, MouseButton.NONE, MouseEventType.NONE, MouseMod.NONE)

    @property
    def is_null(self):
        return all(
            [
                self.row == -1,
                self.column == -1,
                self.button == MouseButton.NONE,
                self.event_type == MouseEventType.NONE,
                self.mod == MouseMod.NONE,
            ]
        )


def get_mouse_button_and_event(button):
    if button == curses.BUTTON1_CLICKED:
        return MouseButton.LEFT_MOUSE, MouseEventType.CLICKED
    elif button == curses.BUTTON2_CLICKED:
        return MouseButton.MIDDLE_MOUSE, MouseEventType.CLICKED
    elif button == curses.BUTTON3_CLICKED:
        return MouseButton.RIGHT_MOUSE, MouseEventType.CLICKED
    elif button == curses.BUTTON4_CLICKED:
        return MouseButton.MOUSE_BUTTON_4, MouseEventType.CLICKED
    elif hasattr(curses, "BUTTON5_CLICKED") and button == curses.BUTTON5_CLICKED:
        return MouseButton.MOUSE_BUTTON_5, MouseEventType.CLICKED

    elif button == curses.BUTTON1_DOUBLE_CLICKED:
        return MouseButton.LEFT_MOUSE, MouseEventType.DOUBLE_CLICKED
    elif button == curses.BUTTON2_DOUBLE_CLICKED:
        return MouseButton.MIDDLE_MOUSE, MouseEventType.DOUBLE_CLICKED
    elif button == curses.BUTTON3_DOUBLE_CLICKED:
        return MouseButton.RIGHT_MOUSE, MouseEventType.DOUBLE_CLICKED
    elif button == curses.BUTTON4_DOUBLE_CLICKED:
        return MouseButton.MOUSE_BUTTON_4, MouseEventType.DOUBLE_CLICKED
    elif (
        hasattr(curses, "BUTTON5_DOUBLE_CLICKED")
        and button == curses.BUTTON5_DOUBLE_CLICKED
    ):
        return MouseButton.MOUSE_BUTTON_5, MouseEventType.DOUBLE_CLICKED

    elif button == curses.BUTTON1_TRIPLE_CLICKED:
        return MouseButton.LEFT_MOUSE, MouseEventType.TRIPLE_CLICKED
    elif button == curses.BUTTON2_TRIPLE_CLICKED:
        return MouseButton.MIDDLE_MOUSE, MouseEventType.TRIPLE_CLICKED
    elif button == curses.BUTTON3_TRIPLE_CLICKED:
        return MouseButton.RIGHT_MOUSE, MouseEventType.TRIPLE_CLICKED
    elif button == curses.BUTTON4_TRIPLE_CLICKED:
        return MouseButton.MOUSE_BUTTON_4, MouseEventType.TRIPLE_CLICKED
    elif (
        hasattr(curses, "BUTTON5_TRIPLE_CLICKED")
        and button == curses.BUTTON5_TRIPLE_CLICKED
    ):
        return MouseButton.MOUSE_BUTTON_5, MouseEventType.TRIPLE_CLICKED

    elif button == curses.BUTTON1_PRESSED:
        return MouseButton.LEFT_MOUSE, MouseEventType.PRESSED
    elif button == curses.BUTTON2_PRESSED:
        return MouseButton.MIDDLE_MOUSE, MouseEventType.PRESSED
    elif button == curses.BUTTON3_PRESSED:
        return MouseButton.RIGHT_MOUSE, MouseEventType.PRESSED
    elif button == curses.BUTTON4_PRESSED:
        return MouseButton.MOUSE_BUTTON_4, MouseEventType.PRESSED
    elif hasattr(curses, "BUTTON5_PRESSED") and button == curses.BUTTON5_PRESSED:
        return MouseButton.MOUSE_BUTTON_5, MouseEventType.PRESSED

    elif button == curses.BUTTON1_RELEASED:
        return MouseButton.LEFT_MOUSE, MouseEventType.RELEASED
    elif button == curses.BUTTON2_RELEASED:
        return MouseButton.MIDDLE_MOUSE, MouseEventType.RELEASED
    elif button == curses.BUTTON3_RELEASED:
        return MouseButton.RIGHT_MOUSE, MouseEventType.RELEASED
    elif button == curses.BUTTON4_RELEASED:
        return MouseButton.MOUSE_BUTTON_4, MouseEventType.RELEASED
    elif hasattr(curses, "BUTTON5_RELEASED") and button == curses.BUTTON5_RELEASED:
        return MouseButton.MOUSE_BUTTON_5, MouseEventType.RELEASED

    return MouseButton.NONE, MouseEventType.MOVED


def get_mouse_info(button):
    mouse_button, mouse_event = get_mouse_button_and_event(button)
    modifier = MouseMod.NONE
    if button & curses.BUTTON_SHIFT > 0:
        modifier = MouseMod.SHIFT
    elif button & curses.BUTTON_ALT > 0:
        modifier = MouseMod.ALT
    elif button & curses.BUTTON_CTRL > 0:
        modifier = MouseMod.CONTROL
    return mouse_button, mouse_event, modifier


def get_mouse_event(row, col, button):
    btn, event_type, mod = get_mouse_info(button)
    return MouseEvent(row, col, btn, event_type, mod)
