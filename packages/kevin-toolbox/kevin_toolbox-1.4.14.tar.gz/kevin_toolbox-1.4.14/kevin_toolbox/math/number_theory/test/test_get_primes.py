import pytest
import numpy as np
import math
from kevin_toolbox.math.number_theory import get_primes
from kevin_toolbox.patches.for_test import check_consistency


def test_get_primes():
    print("test number_theory.get_primes()")

    for _ in range(100):
        # 随机构建输入
        n = max(1, int(np.random.rand() * 1000))
        # 查找
        p_ls = get_primes(n=n)
        # 标准答案
        p_ls_1 = []
        for p in range(1, n + 1):
            b_is_prime = True
            for i in range(2, min(math.ceil(p ** 0.5) + 1, p)):
                if p % i == 0:
                    b_is_prime = False
                    break
            if b_is_prime:
                p_ls_1.append(p)
        # 检查
        check_consistency(sorted(p_ls), sorted(p_ls_1))
