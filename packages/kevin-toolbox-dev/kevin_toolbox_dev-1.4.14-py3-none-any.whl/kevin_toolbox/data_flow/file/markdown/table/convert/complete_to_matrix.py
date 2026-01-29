from kevin_toolbox.math.utils import split_integer_most_evenly
from kevin_toolbox.data_flow.file.markdown.table import Table_Format, get_format, padding_misaligned_values


def complete_to_matrix(content_s, orientation="vertical", chunk_nums=None, chunk_size=None):
    """
        生成表格

        参数：
            content_s:              <dict> 内容
                                        目前支持 Table_Format 中的两种输入模式：
                                            1.简易模式：
                                                content_s = {<title>: <list of value>, ...}
                                                此时键作为标题，值作为标题下的一系列值。
                                                由于字典的无序性，此时标题的顺序是不能保证的，若要额外指定顺序，请使用下面的 完整模式。
                                            2. 完整模式:
                                                content_s = {<index>: {"title": <title>,"values":<list of value>}, ...}
                                                此时将取第 <index> 个 "title" 的值来作为第 <index> 个标题的值。values 同理。
                                                该模式允许缺省某些 <index>，此时这些 <index> 对应的行/列将全部置空。
            orientation:            <str> 表格的方向
                                        支持以下值：
                                            "vertical" / "v":       纵向排列，亦即标题在第一行
                                            "horizontal" / "h":     横向排列，亦即标题在第一列
            chunk_nums:             <int> 将表格平均分割为多少份进行并列显示。
            chunk_size:             <int> 将表格按照最大长度进行分割，然后并列显示。
                注意：以上两个参数只能设置一个，同时设置时将报错
    """
    # 检验参数
    assert chunk_nums is None or 1 <= chunk_nums
    assert chunk_size is None or 1 <= chunk_size
    assert orientation in ["vertical", "horizontal", "h", "v"]
    assert get_format(content_s) is Table_Format.COMPLETE_DICT

    # 当不同标题下的 values 的长度不相等时，先使用 padding_misaligned_values() 来进行对齐
    content_s = padding_misaligned_values(content_s=content_s, padding_value="")
    max_length = len(list(content_s.values())[0]["values"])

    # 补充缺省的 title
    for i in range(max(content_s.keys()) + 1):
        if i not in content_s:
            content_s[i] = {"title": "", "values": [""] * max_length}
    # 按照 chunk_nums 或者 chunk_size 对表格进行分割
    if chunk_nums is not None or chunk_size is not None:
        if chunk_nums is not None:
            split_len_ls = split_integer_most_evenly(x=max_length, group_nums=chunk_nums)
        else:
            split_len_ls = [chunk_size] * (max_length // chunk_size)
            if max_length % chunk_size != 0:
                split_len_ls += [max_length % chunk_size]
        max_length = max(split_len_ls)
        temp = dict()
        beg = 0
        for i, new_length in enumerate(split_len_ls):
            end = beg + new_length
            temp.update({k + i * len(content_s): {"title": v["title"],
                                                  "values": v["values"][beg:end] + [""] * (max_length - new_length)} for
                         k, v in content_s.items()})
            beg = end
        content_s = temp

    # 转换
    row_ls = []
    if orientation in ["vertical", "v"]:
        row_ls.append([content_s[i]["title"] for i in range(len(content_s))])
        for row in zip(*[content_s[i]["values"] for i in range(len(content_s))]):
            row_ls.append(row)
    else:
        for i in range(len(content_s)):
            row_ls.append([content_s[i]["title"]] + content_s[i]["values"])

    return dict(matrix=row_ls, orientation=orientation, chunk_size=chunk_size, chunk_nums=chunk_nums,
                b_remove_empty_lines=chunk_size is not None or chunk_nums is not None)


if __name__ == '__main__':
    from kevin_toolbox.data_flow.file.markdown.table import convert_format

    content_s = complete_to_matrix(
        content_s=convert_format(
            content_s={'y/n': ['False', 'False', 'False', 'False', 'False', 'True', 'True', 'True', 'True', 'True'],
                       'a': ['5', '8', '7', '6', '9', '2', '1', '4', '0', '3'],
                       'b': ['', '', '', '', '', '6', '4', ':', '2', '8']},
            output_format=Table_Format.COMPLETE_DICT
        ),
        orientation="v", chunk_size=4
    )


    def _show_table(row_ls):
        """
            生成表格文本

            参数：
                row_ls:                 <list of row>
        """
        table = ""
        for idx, row in enumerate(row_ls):
            row = [f'{i}' for i in row]
            table += "| " + " | ".join(row) + " |\n"
            if idx == 0:
                table += "| " + " | ".join(["---"] * len(row)) + " |\n"
        return table


    doc = _show_table(content_s["matrix"])
    print(doc)
