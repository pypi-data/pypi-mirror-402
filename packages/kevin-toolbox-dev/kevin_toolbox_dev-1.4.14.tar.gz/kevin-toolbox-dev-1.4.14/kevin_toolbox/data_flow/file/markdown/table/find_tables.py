import re


def find_tables(text, b_compact_format=True):
    """
        查找文本中的表格

        参数:
            text:               <str> 文本
            b_compact_format:   <bool> 是否只返回 table 部分
                                    默认为 True，此时返回 table_ls，其中每个元素是一个 MATRIX 格式的表格
                                    当设置为 False，此时返回 (table_ls, part_slices_ls, table_idx_ls)，
                                        其中 part_slices_ls 是表格和表格前后文本在 text 中对应的 slice，
                                        而 table_idx_ls 指出了 part_slices_ls 中第几个元素对应的是表格，
                                        table_idx_ls 与 table_ls 依次对应。
    """
    text = "\n\n" + text + "\n\n"  # 前后使用哨兵包围
    matches = re.finditer(r'\n{2,}', text, re.DOTALL)

    table_ls = []
    part_slices_ls = []
    table_idx_ls = []
    #
    match = next(matches)
    start, sub_start = match.start(), match.end()
    assert sub_start - start >= 2
    if sub_start - start > 2:
        part_slices_ls.append([start + 2, sub_start])
    start = sub_start
    #
    for match in matches:
        sub_text = text[sub_start:match.start()]
        ret = _find_table(text=sub_text)
        if ret is not None:
            if start != sub_start:
                part_slices_ls.append([start, sub_start])
            table_idx_ls.append(len(part_slices_ls))
            table_ls.append(ret)
            part_slices_ls.append([sub_start, match.start()])
            start = match.start()
        sub_start = match.end()
    #
    assert sub_start - start >= 2
    if sub_start - start > 2:
        part_slices_ls.append([start, sub_start - 2])
    # 移除前面哨兵
    part_slices_ls = [[i - 2, j - 2] for i, j in part_slices_ls]

    if b_compact_format:
        return table_ls
    else:
        return table_ls, part_slices_ls, table_idx_ls


# def _find_table(text):
#     # 正则表达式匹配Markdown表格
#     table_pattern = re.compile(r'\|([^\n]+)\|', re.DOTALL)
#     table_matches = table_pattern.findall(text)
#     if len(table_matches) < 2:
#         # 因为一个合法的 markdown 表格需要含有表头的分隔线，所以行数至少应该为 2
#         return None
#
#     # 去除表头的分隔线
#     table_matches.pop(1)
#     #
#     tables = []  # 每个元素为一行
#     for match in table_matches:
#         # 分割每一行
#         tables.append([i.strip() for i in match.split('|', -1)])
#
#     return {"matrix": tables, "orientation": None}

def _find_table(text):
    # 按行分割文本
    lines = text.splitlines()
    table_rows = []
    for line in lines:
        # 移除行首尾空白
        stripped_line = line.strip()
        if not stripped_line:
            continue  # 跳过空行
        # 移除行首尾的可选竖线（如果存在）
        if stripped_line.startswith('|'):
            stripped_line = stripped_line[1:]
        if stripped_line.endswith('|'):
            stripped_line = stripped_line[:-1]
        # 分割单元格并去除每个单元格的空白
        row_cells = [cell.strip() for cell in stripped_line.split('|')]
        table_rows.append(row_cells)

    if len(table_rows) < 2:
        # 因为一个合法的 markdown 表格需要含有表头的分隔线，所以行数至少应该为 2
        return None
    # 去除表头的分隔线
    table_rows.pop(1)

    return {"matrix": table_rows, "orientation": None}


if __name__ == '__main__':
    # # 示例Markdown表格文本
    # file_path = ""
    # with open(file_path, 'r') as f:
    #     markdown_text = f.read()

    markdown_text = """
| Name | Age | Occupation |
|------|-----|------------|
| Alice | 28  | Engineer   |
| Bob   | 23  | Teacher    |
| Name | Age | Occupation |
| Carol | 32  | Hacker   |
| David | 18  | Student   |

2333

|  | a | b |  | a | b |  | a | b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | 0 | 2 |  | 4 | 6 |  | 7 | 9 |
|  | 1 | 3 |  | 5 | 7 |  | 8 | : |
|  | 2 | 4 |  | 6 | 8 |  | 9 | ; |
|  | 3 | 5 |  |  |  |  |  |  |
"""

    # 调用函数并打印结果
    tables = find_tables(text=markdown_text)
    print(tables[0])
    print(tables[1])

    #
    table_ls_, part_slices_ls_, table_idx_ls_ = find_tables(text=markdown_text, b_compact_format=False)
    print(table_idx_ls_)

    for part_slices in  part_slices_ls_:
        print(part_slices)
        print(markdown_text[part_slices[0]:part_slices[1]])

