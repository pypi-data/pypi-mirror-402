from enum import Enum


class Table_Format(Enum):
    """
        表格的几种模式
            1.simple_dict 简易字典模式：
                content_s = {<title>: <list of value>, ...}
                此时键作为标题，值作为标题下的一系列值。
                由于字典的无序性，此时标题的顺序是不能保证的，若要额外指定顺序，请使用下面的 完整模式。
            2. complete_dict 完整字典模式:
                content_s = {<index>: {"title": <title>, "values": <list of value>}, ...}
                此时将取第 <index> 个 "title" 的值来作为第 <index> 个标题的值。values 同理。
                该模式允许缺省某些 <index>，此时这些 <index> 对应的行/列将全部置空。
            3. matrix 矩阵形式：
                content_s = {"matrix": [[...], [...], ...], "orientation":...(, "chunk_nums":..., "chunk_size":...)}
                其中，必要的键值对有：
                    "matrix":           以 list of row 形式保存表格的内容
                    "orientation":      指定表格的解释方向
                                            当为 "vertical" 或 "v" 时，表格为竖直方向，此时第一行为标题，
                                            为 "horizontal" 或 "h" 时，表格为水平方向，此时第一列为标题
                可选键值对有：
                    "chunk_nums":       表格是平均分割为多少份进行并列显示。
                    "chunk_size":       表格是按照最大长度进行分割，然后并列显示。
                    "b_remove_empty_lines": 是否需要将空行去除掉。
    """
    SIMPLE_DICT = "simple_dict"
    COMPLETE_DICT = "complete_dict"
    MATRIX = "matrix"
