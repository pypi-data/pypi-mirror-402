import numpy as np


def normalize(v, ord, axis=-1):
    """
        对变量沿着轴 axis 进行归一化

        参数：
            v：
            ord：            表示范数的类型。可以设置为1、2、无穷大范数（np.inf）或其他正整数值。
            axis：           表示沿着哪个轴计算范数并进行归一化。
                                默认为-1。
    """
    n = np.linalg.norm(v, ord=ord, axis=axis, keepdims=True)
    n = np.where(n > 0, n, 1e-10)  # 防溢出
    return v / n


if __name__ == '__main__':
    print(normalize(np.array([[1, 2, 3, 4, 5]]), ord=2))
