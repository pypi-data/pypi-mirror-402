from cuipyd.colors.colors import get_color_pair_id_from_hex


class ColorScheme:

    def __init__(self):
        self._background_color = "#114B5F"
        self._alternate_background_color = "#58A4B0"
        self._default_text_color = "#FAFFFD"
        self._header_text_color = "#EA526F"
        self._important_text_color = "#eca72c"
        # self._alternate_important_color = "#ec7f2c"
        self._alternate_important_color = "#93e1d8"

    def _invert_args(self, args):
        return (args[1], args[0])

    def default_mod(self, invert=False):
        args = (self._default_text_color, self._background_color)
        if invert:
            args = self._invert_args(args)
        return get_color_pair_id_from_hex(*args)

    def alternate_mod(self, invert=False):
        args = (self._default_text_color, self._alternate_background_color)
        if invert:
            args = self._invert_args(args)
        return get_color_pair_id_from_hex(*args)

    def header_mod(self, invert=False):
        args = (self._header_text_color, self._background_color)
        if invert:
            args = self._invert_args(args)
        return get_color_pair_id_from_hex(*args)

    def alternate_important_mod(self, invert=False):
        args = (self._alternate_important_color, self._background_color)
        if invert:
            args = self._invert_args(args)
        return get_color_pair_id_from_hex(*args)

    def important_mod(self, invert=False):
        args = (self._important_text_color, self._background_color)
        if invert:
            args = self._invert_args(args)
        return get_color_pair_id_from_hex(*args)
