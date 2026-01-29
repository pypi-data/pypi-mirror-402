import pytest
import numpy as np
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.computer_science.algorithm.combinatorial_optimization import get_subset_with_largest_product
from kevin_toolbox.computer_science.algorithm.for_seq import get_subsets


def test_get_subset_with_largest_product():
    print("test combinatorial_optimization.get_subset_with_largest_product()")

    for _ in range(500):
        # 随机构建输入的 ls、upper_bound
        end = int(np.random.randint(1, 100))
        ls = np.random.random(np.random.randint(1, 10)) * end
        upper_bound = np.random.random() * end * 2.3
        if np.random.randint(0, 2):
            ls = ls.astype(int)
            upper_bound = int(upper_bound)
        if min(ls) <= 0:
            ls = ls - min(ls) + 1e-8
        if upper_bound <= 0:
            upper_bound = 1e-8

        # 使用 get_subset_with_largest_product() 求解
        # print(ls, upper_bound)
        product, subset = get_subset_with_largest_product(
            ls=ls.tolist(), upper_bound=upper_bound,
        )
        # print(product, subset)

        # 通过暴力搜索获取真实答案
        best_product, best_subset_ls = None, []
        for temp in get_subsets(inputs=ls):
            temp_pd = np.prod(temp)
            if temp_pd > upper_bound:
                continue
            if best_product is None or best_product < temp_pd:
                best_product, best_subset_ls = temp_pd, [temp]
            elif temp_pd == best_product:
                best_subset_ls.append(temp)
        if best_product is None:
            best_subset_ls = [None]
        # print(best_product, best_subset_ls)

        # 检验
        check_consistency(product, best_product)
        if subset is not None:
            subset.sort()
            best_subset_ls = [sorted(i) for i in best_subset_ls]
        assert subset in best_subset_ls
