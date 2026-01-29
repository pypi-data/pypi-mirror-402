from enum import Enum


class Color_Format(Enum):
    HEX_STR = "hex_str"  # 例如 '#FF573380'
    RGBA_ARRAY = "rgba_array"  # 例如 (255, 87, 51, 0.5)
    NATURAL_NAME = "natural_name"  # 例如 'red'
