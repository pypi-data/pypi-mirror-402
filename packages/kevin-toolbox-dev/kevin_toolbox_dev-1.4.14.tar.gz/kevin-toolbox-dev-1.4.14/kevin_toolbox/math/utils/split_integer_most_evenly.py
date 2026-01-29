import numpy as np


def split_integer_most_evenly(x, group_nums):
    assert isinstance(x, (int, np.integer,)) and x >= 0 and group_nums > 0

    res = np.ones(group_nums, dtype=int) * (x // group_nums)
    res[:x % group_nums] += 1
    return res.tolist()


if __name__ == '__main__':
    print(split_integer_most_evenly(x=100, group_nums=7))
