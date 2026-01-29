from cuipyd.popups.popup import BasePopup


class TextPopup(BasePopup):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._text = ""

    def set_text(self, text):
        self._text = text

    def confirm_pressed(self):
        pass

    def cancel_pressed(self):
        pass

    def render_frame(self, time_delta):
        super().render_frame(time_delta)

        rows, cols = self._get_size()

        for row in range(rows):
            for col in range(cols):
                self.add_char("a", row, col)
