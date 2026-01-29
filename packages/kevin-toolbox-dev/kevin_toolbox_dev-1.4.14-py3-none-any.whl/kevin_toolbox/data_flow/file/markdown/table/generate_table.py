from kevin_toolbox.data_flow.file.markdown.table import convert_format, Table_Format, padding_misaligned_values
from kevin_toolbox.data_flow.file.markdown.table.convert import complete_to_matrix


def generate_table(content_s, orientation="vertical", chunk_nums=None, chunk_size=None, b_allow_misaligned_values=False,
                   f_gen_order_of_values=None):
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
            b_allow_misaligned_values:  <boolean> 允许不对齐的 values
                                        默认为 False，此时当不同标题下的 values 的长度不相等时，将会直接报错。
                                        当设置为 True 时，对于短于最大长度的 values 将直接补充 ""。
            f_gen_order_of_values:  <callable> 生成values排序顺序的函数
                                        该函数需要接受一个形如 {<title>: <value>, ...} 的 <dict>，并返回一个用于排序的 int/float/tuple
    """
    # 检验参数
    assert chunk_nums is None or 1 <= chunk_nums
    assert chunk_size is None or 1 <= chunk_size
    assert orientation in ["vertical", "horizontal", "h", "v"]
    assert isinstance(content_s, (dict,))

    # 首先转换为完整模式
    content_s = convert_format(content_s=content_s, output_format=Table_Format.COMPLETE_DICT)
    # 对齐 values
    len_ls = [len(v["values"]) for v in content_s.values()]
    max_length = max(len_ls)
    if min(len_ls) != max_length:
        assert b_allow_misaligned_values, \
            f'The lengths of the values under each title are not aligned. ' \
            f'The maximum length is {max_length}, but each length is {len_ls}'
        content_s = padding_misaligned_values(content_s=content_s, padding_value="")
    # 对值进行排序
    if callable(f_gen_order_of_values):
        # 检查是否有重复的 title
        temp = [v["title"] for v in content_s.values()]
        assert len(set(temp)) == len(temp), \
            f'table has duplicate titles, thus cannot be sorted using f_gen_order_of_values'
        idx_ls = list(range(max_length))
        idx_ls.sort(key=lambda x: f_gen_order_of_values({v["title"]: v["values"][x] for v in content_s.values()}))
        for v in content_s.values():
            v["values"] = [v["values"][i] for i in idx_ls]

    # 转换为 matrix 格式
    content_s = complete_to_matrix(content_s=content_s, orientation=orientation, chunk_size=chunk_size,
                                   chunk_nums=chunk_nums)
    # 构建表格
    table = ""
    for idx, row in enumerate(content_s["matrix"]):
        row = [f'{i}' for i in row]
        table += "| " + " | ".join(row) + " |\n"
        if idx == 0:
            table += "| " + " | ".join(["---"] * len(row)) + " |\n"
    return table


if __name__ == '__main__':
    # content_s = {0: dict(title="a", values=[1, 2, 3]), 2: dict(title="b", values=[4, 5, 6])}
    # doc = generate_table(content_s=content_s, orientation="h")
    # print(doc)

    # from collections import OrderedDict
    #
    # content_s = OrderedDict({
    #     "y/n": [True] * 5 + [False] * 5,
    #     "a": list(range(10)),
    #     "b": [chr(i) for i in range(50, 60, 2)]
    # })
    # doc = generate_table(content_s=content_s, orientation="v", chunk_size=4, b_allow_misaligned_values=True,
    #                      f_gen_order_of_values=lambda x: (-int(x["y/n"] is False), -(x["a"] % 3)))
    # print(doc)
    # import os
    #
    # with open(os.path.join(
    #         "/home/SENSETIME/xukaiming/Desktop/my_repos/python_projects/kevin_toolbox/kevin_toolbox/data_flow/file/markdown/test/test_data/for_generate_table",
    #         f"data_5.md"), "w") as f:
    #     f.write(doc)

    doc = generate_table(
        content_s={'y/n': ['False', 'False', 'False', 'False', 'False', 'True', 'True', 'True', 'True', 'True'],
                   'a': ['5', '8', '7', '6', '9', '2', '1', '4', '0', '3'],
                   'b': ['', '', '', '', '', '6', '4', ':', '2', '8']},
        orientation="v", chunk_size=4, b_allow_misaligned_values=True,
        f_gen_order_of_values=lambda x: (-int(eval(x["y/n"]) is False), -(int(x["a"]) % 3))
    )
    print(doc)
