from kevin_toolbox.patches.for_matplotlib.color import Color_Format


def get_format(var):
    if isinstance(var, str):
        if var.startswith("#"):
            res = Color_Format.HEX_STR
        else:
            res = Color_Format.NATURAL_NAME
    else:
        res = Color_Format.RGBA_ARRAY
    return res
