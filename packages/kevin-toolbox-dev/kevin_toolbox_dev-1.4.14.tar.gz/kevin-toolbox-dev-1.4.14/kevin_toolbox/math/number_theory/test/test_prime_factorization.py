import pytest
import numpy as np
import math
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.math.number_theory import prime_factorization, get_primes


def test_prime_factorization():
    print("test number_theory.prime_factorization()")

    for _ in range(100):
        # 随机构建输入
        n = max(1, int(np.random.rand() * 1000))
        # 查找
        p_ls = prime_factorization(n=n)
        # 检查
        assert set(get_primes(n=n)).issuperset(set(p_ls))
        check_consistency(n, np.prod(p_ls))
