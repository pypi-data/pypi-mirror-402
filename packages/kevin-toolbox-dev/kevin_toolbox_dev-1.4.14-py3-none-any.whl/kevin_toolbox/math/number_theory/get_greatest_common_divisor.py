import numpy as np


def get_greatest_common_divisor(n, m):
    """
        找出正整数 n 和 m 之间的最大公约数
    """
    for i in [n, m]:
        assert isinstance(i, (int, np.integer,)) and i >= 1

    # 辗转相除法求最大公约数
    while True:
        temp = m % n
        if temp == 0:  # n 为公约数
            break
        n, m = temp, n

    return n
