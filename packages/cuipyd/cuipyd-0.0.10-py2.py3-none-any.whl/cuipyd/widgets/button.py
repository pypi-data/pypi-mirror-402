class Button:

    def __init__(self, text="Click Me!", function=None):
        self._text = text
        self._function = function

    def _click(self):
        if self._function:
            self._function()
