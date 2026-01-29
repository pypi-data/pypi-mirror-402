import curses

# Global Vars
global _cuipyd_colors
_cuipyd_colors = {}

global _cuipyd_color_index
_cuipyd_color_index = 10

global _cuipyd_color_pairs
_cuipyd_color_pairs = {}

global _cuipyd_color_pair_index
_cuipyd_color_pair_index = 10


def clean_hex_val(hex_val: str):
    orig = hex_val
    hex_val = hex_val.lstrip("#")
    assert len(hex_val) == 6, f"Invalid Hex Value {orig}"
    return hex_val


def color_from_hex(hex_val: str):
    hex_val = clean_hex_val(hex_val)
    r = int(hex_val[0:2], 16)
    g = int(hex_val[2:4], 16)
    b = int(hex_val[4:6], 16)
    R = int((r / 256) * 1000)
    G = int((g / 256) * 1000)
    B = int((b / 256) * 1000)
    return (R, G, B)


def get_color_id_from_hex(hex_val: str):
    hex_val = clean_hex_val(hex_val)

    global _cuipyd_colors
    global _cuipyd_color_index

    if hex_val in _cuipyd_colors:
        return _cuipyd_colors[hex_val]
    else:
        r, g, b = color_from_hex(hex_val)
        curses.init_color(_cuipyd_color_index, r, g, b)
        _cuipyd_colors[hex_val] = _cuipyd_color_index
        _cuipyd_color_index += 1
        return _cuipyd_colors[hex_val]


def get_color_pair_id_from_hex(hex_foreground: str, hex_background: str):
    hex_fg = clean_hex_val(hex_foreground)
    hex_bg = clean_hex_val(hex_background)

    global _cuipyd_color_pairs
    global _cuipyd_color_pair_index

    if hex_bg in _cuipyd_color_pairs:
        if hex_fg in _cuipyd_color_pairs[hex_bg]:
            return curses.color_pair(_cuipyd_color_pairs[hex_bg][hex_fg])

    foreground_color_id = get_color_id_from_hex(hex_fg)
    background_color_id = get_color_id_from_hex(hex_bg)

    if hex_bg not in _cuipyd_color_pairs:
        _cuipyd_color_pairs[hex_bg] = {}

    curses.init_pair(_cuipyd_color_pair_index, foreground_color_id, background_color_id)

    _cuipyd_color_pairs[hex_bg][hex_fg] = _cuipyd_color_pair_index
    _cuipyd_color_pair_index += 1
    return curses.color_pair(_cuipyd_color_pairs[hex_bg][hex_fg])
