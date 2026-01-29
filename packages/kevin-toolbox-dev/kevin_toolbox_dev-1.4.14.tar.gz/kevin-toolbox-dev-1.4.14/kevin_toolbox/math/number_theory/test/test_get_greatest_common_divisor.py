import pytest
import numpy as np
import math
from kevin_toolbox.math.number_theory import get_greatest_common_divisor
from kevin_toolbox.patches.for_test import check_consistency


def test_get_greatest_common_divisor():
    print("test number_theory.get_greatest_common_divisor()")

    for _ in range(100):
        # 随机构建输入
        n = max(1, int(np.random.rand() * 1000))
        m = max(1, int(np.random.rand() * 1000))
        # 查找
        gcd = get_greatest_common_divisor(n=n, m=m)
        # 标准答案
        gcd_1 = 1
        for i in reversed(range(1, min(n + 1, m + 1))):
            if m % i == 0 and n % i == 0:
                gcd_1 = i
                break
        # 检查
        check_consistency(gcd, gcd_1)
