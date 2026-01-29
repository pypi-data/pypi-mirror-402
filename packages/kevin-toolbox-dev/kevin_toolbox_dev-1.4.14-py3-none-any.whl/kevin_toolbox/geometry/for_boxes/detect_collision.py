from .detect_collision_inside_boxes import detect_collision_inside_boxes
from .detect_collision_among_boxes_ls import detect_collision_among_boxes_ls


def detect_collision(**kwargs):
    """
        碰撞检测
            Adapt the entry of different detection functions
            当输入参数中有 boxes 时，调用 detect_collision_inside_boxes() 进行碰撞检测，此时将 boxes 中的每个 box 视为一个 item
            当输入参数中有 boxes_ls 时，调用 detect_collision_among_boxes_ls()，此时将 boxes_ls 中的每个 boxes 视为一个 item
    """
    if "boxes" in kwargs:
        return detect_collision_inside_boxes(**kwargs)
    elif "boxes_ls" in kwargs:
        return detect_collision_among_boxes_ls(**kwargs)
    else:
        raise ValueError(f"parameter boxes or boxes_ls is required!")
