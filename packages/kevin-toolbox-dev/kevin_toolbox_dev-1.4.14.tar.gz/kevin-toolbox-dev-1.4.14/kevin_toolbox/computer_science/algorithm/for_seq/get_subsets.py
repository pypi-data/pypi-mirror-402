def get_subsets(inputs):
    """
        获取所有的子集
    """
    sub_sets = [[]]
    for x in inputs:
        temp = []
        for item in sub_sets:
            temp.append(item + [x])
        sub_sets.extend(temp)
    return sub_sets


if __name__ == '__main__':
    print(get_subsets(range(20)))
