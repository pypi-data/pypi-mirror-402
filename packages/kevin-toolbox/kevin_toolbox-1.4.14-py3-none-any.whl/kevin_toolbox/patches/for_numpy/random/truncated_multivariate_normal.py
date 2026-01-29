import numpy as np
from scipy.stats import chi2
from kevin_toolbox.patches.for_numpy.linalg import normalize
from kevin_toolbox.patches.for_numpy.random import get_rng
from kevin_toolbox.patches.for_numpy.random.variable import DEFAULT_SETTINGS
from kevin_toolbox.computer_science.algorithm.cache_manager import Cache_Manager

cache_for_cov = Cache_Manager(upper_bound=20, refactor_size=0.5)


def truncated_multivariate_normal(
        mean, cov=None, low_radius=None, high_radius=None, size=None, b_check_cov=False,
        hit_ratio_threshold=DEFAULT_SETTINGS["truncated_multivariate_normal"]["hit_ratio_threshold"],
        expand_ratio=DEFAULT_SETTINGS["truncated_multivariate_normal"]["expand_ratio"],
        **kwargs):
    """
        从截断的多维高斯分布中进行随机采样

        参数：
            mean:                   <list of float> 均值
            cov:                    <matrix> 协方差矩阵
            low_radius,high_radius: <float> 截断边界
                                        注意：
                                            - 是截断多少倍 sigma 以内的部分。
                                            - low_radius 是指排除该半径距离内的点
                                            - high_radius 是指包含该半径距离内的点
                                            - 区间为左闭右开，亦即 [low_radius, high_radius)
            size:                   <tuple/list/int/None> 输出的形状
            b_check_cov:            <boolean> 是否检查 cov 是正半定矩阵。
                                        默认为 False 此时不检查
                                        当设置为 True 时，若不通过检查将报错。

        用于调节采样效率的超参数（与设备情况有关）：
            hit_ratio_threshold:    <float> 决定采样方式的阈值
                                        当 hit_ratio 小于该阈值时，使用方式 2 （重要性采样）来生成，
                                        当大于阈值时，使用方式 1 采样 expand_ratio * size 个样本再挑选符合落在截断区间内的样本
            expand_ratio:           <float> 方式1的系数
                                        要求大于 1

        其他参数：
            seed:                   <int> 随机种子
            rng:                    <Random Generator> 给定的随机采样器
                            以上参数二选一

        返回:
            res:                    当 shape 为 None 时，返回的是与mean大小相同的 n 维向量
                                    否则返回的是 shape+[len(mean)] 维度的张量
    """
    # 检查参数
    assert len(mean) > 1
    assert high_radius is None or 0 < high_radius
    assert low_radius is None or 0 <= low_radius
    if high_radius is not None and low_radius is not None:
        assert low_radius < high_radius
    if b_check_cov and cov is not None:
        cov = np.asarray(cov)
        assert np.allclose(cov, cov.T) and np.all(np.linalg.eig(cov)[0] > 0)
    #
    rng = get_rng(**kwargs)
    low = None if low_radius is None else low_radius ** 2
    high = None if high_radius is None else high_radius ** 2

    # quick return
    if (low is None or low == 0) and high is None:
        return rng.multivariate_normal(mean, cov, size=size, check_valid="warn" if b_check_valid else "ignore")

    # 因为标准高维高斯分布的采样点的方向服从均匀分布，而距离服从自由度为k的卡方分布
    #   因此可以把方向和距离分开来进行采样
    raw_size = 1 if size is None else np.prod([size])

    # 对方向进行采样
    theta = rng.normal(0, 1, size=[raw_size, len(mean)])
    theta = normalize(v=theta, ord=2, axis=-1)

    # 对距离进行采样
    # 计算命中概率
    cdf_high = chi2.cdf(high, df=len(mean)) if high is not None else 1
    cdf_low = chi2.cdf(low, df=len(mean)) if low is not None else 0
    hit_prob = cdf_high - cdf_low
    if hit_prob >= hit_ratio_threshold:
        # 采样方式1
        delta = np.empty(raw_size)
        count = 0
        while count < raw_size:
            temp = rng.chisquare(len(mean), int((raw_size - count) / hit_prob * expand_ratio) + 1)
            if low is not None:
                temp = temp[temp >= low]
            if high is not None:
                temp = temp[temp < high]
            delta[count:count + len(temp)] = temp[:raw_size - count]
            count += len(temp)
    else:
        # 采样方式2（重要性采样）
        # 从均匀分布中采样
        delta = rng.uniform(cdf_low, cdf_high, raw_size)
        # 对均匀分布的样本进行逆变换得到截断正态分布的样本
        delta = chi2.ppf(delta, df=len(mean))

    # 整合方向和距离
    res = theta * delta[:, None] ** 0.5

    # 根据协方差矩阵进行缩放
    if cov is not None:
        A = cache_for_cov.get(cov.tobytes(), default_factory=lambda: np.linalg.cholesky(cov), b_add_if_not_found=True)
        res = (A @ res.T).T
    res += mean

    if size is None:
        res = res[0]
    else:
        size = [size] if isinstance(size, int) else list(size)
        res = res.reshape(size + [len(mean)])

    return res


if __name__ == '__main__':
    print(truncated_multivariate_normal(mean=[0, 0], cov=np.array([[1, 0.5], [0.5, 1]]),
                                        high_radius=2, seed=114, size=[2, 5]))

    # 可视化
    import matplotlib.pyplot as plt

    res_ = truncated_multivariate_normal(mean=[0, 0], cov=np.array([[1, 0.5], [0.5, 1]]), low_radius=0.5,
                                         high_radius=1.5, seed=114, b_check_cov=True,
                                         size=10000)
    plt.scatter(res_[:, 0], res_[:, 1], c='r', s=1)

    plt.show()
