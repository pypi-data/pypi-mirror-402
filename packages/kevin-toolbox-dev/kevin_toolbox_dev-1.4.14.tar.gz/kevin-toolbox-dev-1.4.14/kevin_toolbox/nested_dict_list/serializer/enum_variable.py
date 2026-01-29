from enum import Enum


class Strictness_Level(Enum):
    """
        对于正确性与完整性的要求的严格程度
    """
    COMPLETE = "high"  # 所有节点均有一个或者多个匹配上的 backend，且第一个匹配上的 backend 就成功写入。
    COMPATIBLE = "normal"  # 所有节点均有一个或者多个匹配上的 backend，但是首先匹配到的 backend 写入出错，使用其后再次匹配到的其他 backend 能够成功写入
    # （这种情况更多应归咎于 backend 的 writable() 方法无法拒绝所有错误输入或者 backend 本身没有按照预期工作。一般而言这对最终写入内容的正确不会有太大影响。）
    # 这个等级是默认等级
    IGNORE_FAILURE = "low"  # 匹配不完整，或者某些节点尝试过所有匹配到的 backend 之后仍然无法写入
