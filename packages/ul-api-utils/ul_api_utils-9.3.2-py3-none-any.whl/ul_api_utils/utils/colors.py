from typing import Dict

C_NC = "[0m"
C_FG_RED = "[38;5;1m"
C_FG_GREEN = "[38;5;2m"
C_FG_YELLOW = "[38;5;3m"
C_FG_GRAY = "[38;5;8m"
C_FG_BLUE = "[38;5;4m"

COLORS_MAP__TERMINAL: Dict[str, str] = {
    C_NC: C_NC,
    C_FG_RED: C_FG_RED,
    C_FG_GREEN: C_FG_GREEN,
    C_FG_YELLOW: C_FG_YELLOW,
    C_FG_GRAY: C_FG_GRAY,
    C_FG_BLUE: C_FG_BLUE,
    "": "",
}


COLORS_MAP__HTML = {
    C_NC: '</span>',
    C_FG_GRAY: '<span style="color: gray;">',
    C_FG_RED: '<span style="color: red;">',
    C_FG_YELLOW: '<span style="color: yellow;">',
    C_FG_GREEN: '<span style="color: green;">',
    C_FG_BLUE: '<span style="color: blue;">',
    "": "",
}

assert set(COLORS_MAP__TERMINAL.keys()) == set(COLORS_MAP__HTML.keys())
