import numpy as np
from kevin_toolbox.math.number_theory import cache
from kevin_toolbox.computer_science.algorithm.search import binary_search


def get_primes(n):
    """
        获取 小于等于 正整数n的所有素数
    """
    assert isinstance(n, (int, np.integer)) and n >= 1
    n += 1

    # 利用已有素数
    if n <= cache.primes[-1]:
        index = binary_search(cache.primes, n)
        return cache.primes[:index]

    # 求取素数
    for i in range(cache.primes[-1] + 1, n):
        b_prime = True
        for p, p_2 in zip(cache.primes[1:], cache.primes_square[1:]):
            if i % p == 0:
                b_prime = False
                break
            if p_2 > i:
                break
        if b_prime:
            cache.primes.append(i)
            cache.primes_square.append(i ** 2)
    return cache.primes[:]


if __name__ == '__main__':
    print(get_primes(n=271)[-1])
    print(get_primes(n=277)[-1])
