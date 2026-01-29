def matrix_to_complete(matrix, orientation, chunk_size=None, chunk_nums=None, b_remove_empty_lines=False):
    """
        将二维数组形式的 MATRIX 格式（比如find_tables()的返回列表的元素），转换成 COMPLETE_DICT 格式

        参数：
            matrix:                     <list of row> 二维数组形式的表格
            orientation:                <str> 解释表格时取哪个方向
                                            支持以下值：
                                            "vertical" / "v":       将第一行作为标题
                                            "horizontal" / "h":     将第一列作为标题
            chunk_nums:                 <int> 表格被平均分割为多少份进行并列显示。
            chunk_size:                 <int> 表格被按照最大长度进行分割，然后并列显示。
                以上两个参数是用于解释 generate_table() 中使用对应参数生成的表格，其中 chunk_size 仅作检验行数是否符合要求，
                对解释表格无作用。但是当指定该参数时，将视为表格有可能是多个表格并列的情况，因此将尝试根据标题的重复规律，
                推断出对应的 chunk_nums，并最终将其拆分成多个表格。
            b_remove_empty_lines:       <boolean> 移除空的行、列
    """
    # 检验参数
    assert chunk_nums is None or 1 <= chunk_nums
    assert chunk_size is None or 1 <= chunk_size
    assert isinstance(matrix, (list, tuple,))
    assert orientation in ["vertical", "horizontal", "h", "v"]

    # 转换为字典形式
    if orientation not in ["vertical", "v"]:
        # 需要转为垂直方向
        matrix = list(zip(*matrix))
    r_nums, c_nums = len(matrix), len(matrix[0])
    if chunk_size is not None:
        assert chunk_size == r_nums - 1, \
            (f'The number of values {r_nums - 1} actually contained in the table '
             f'does not match the specified chunk_size {chunk_size}')
        chunk_nums = c_nums // _find_shortest_repeating_pattern_size(arr=matrix[0])
    chunk_nums = 1 if chunk_nums is None else chunk_nums
    assert c_nums % chunk_nums == 0, \
        f'The number of headers actually contained in the table does not match the specified chunk_nums, ' \
        f'Expected n*{chunk_nums}, but got {c_nums}'
    # 解释出标题
    keys = matrix[0][0:c_nums // chunk_nums]
    # 解释出值
    if chunk_nums == 1:
        values = matrix[1:]
    else:
        values = []
        for i in range(chunk_nums):
            for j in range(1, r_nums):
                values.append(matrix[j][i * len(keys):(i + 1) * len(keys)])
    # 去除空行
    if b_remove_empty_lines:
        values = [line for line in values if any(i != '' for i in line)]
    table_s = {i: {"title": k, "values": list(v)} for i, (k, v) in enumerate(zip(keys, list(zip(*values))))}
    # 去除空列
    if b_remove_empty_lines:
        table_s = {k: v_s for k, v_s in table_s.items() if v_s["title"] != '' and any(i != '' for i in v_s["values"])}

    return table_s


def _find_shortest_repeating_pattern_size(arr):
    n = len(arr)

    # 部分匹配表
    pi = [0] * n
    k = 0
    for i in range(1, n):
        if k > 0 and arr[k] != arr[i]:
            k = 0
        if arr[k] == arr[i]:
            k += 1
        pi[i] = k

    # 最短重复模式的长度
    pattern_length = n - pi[n - 1]
    # 是否是完整的重复模式
    if n % pattern_length != 0:
        pattern_length = n
    return pattern_length


if __name__ == '__main__':
    from kevin_toolbox.data_flow.file.markdown import find_tables

    # # 示例Markdown表格文本
    # file_path = ""
    # with open(file_path, 'r') as f:
    #     markdown_text = f.read()

    # markdown_text = """
    # | Name | Age | Occupation |
    # |------|-----|------------|
    # | Alice | 28  | Engineer   |
    # | Bob   | 23  | Teacher    |
    # | Name | Age | Occupation |
    # | Carol | 32  | Hacker   |
    # | David | 18  | Student   |
    # """

    markdown_text = """
|  | a | b |  | a | b |  | a | b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | 0 | 2 |  | 4 | 6 |  | 7 | 9 |
|  | 1 | 3 |  | 5 | 7 |  | 8 | : |
|  | 2 | 4 |  | 6 | 8 |  | 9 | ; |
|  | 3 | 5 |  |  |  |  |  |  |
"""
    table_ls = find_tables(text=markdown_text)

    # 调用函数并打印结果
    tables = matrix_to_complete(matrix=table_ls[0], orientation="v", chunk_nums=3, b_remove_empty_lines=True)
    print(tables)
