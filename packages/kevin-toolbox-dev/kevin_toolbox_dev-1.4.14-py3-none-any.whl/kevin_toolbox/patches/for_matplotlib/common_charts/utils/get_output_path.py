import os
from kevin_toolbox.patches.for_os.path import replace_illegal_chars


def get_output_path(output_path=None, output_dir=None, title=None, suffix=".png", **kwargs):
    if output_path is None:
        if output_dir is None:
            output_path = None
        else:
            assert title is not None
            assert suffix in [".png", ".jpg", ".bmp"]
            output_path = os.path.join(output_dir, f'{replace_illegal_chars(title)}{suffix}')
    else:
        output_path = os.path.join(os.path.dirname(output_path), replace_illegal_chars(os.path.basename(output_path)))
    return output_path
