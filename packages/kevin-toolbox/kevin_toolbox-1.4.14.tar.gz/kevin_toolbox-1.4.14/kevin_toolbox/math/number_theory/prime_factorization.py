import numpy as np
from kevin_toolbox.math.number_theory import get_primes


def prime_factorization(n):
    """
        对正整数n进行质因数分解
            返回它的所有素数因子，包括1
    """
    assert isinstance(n, (int, np.integer,)) and n >= 1

    primes = get_primes(n=n + 1)
    factors = [1]
    for p in primes[1:]:
        while n % p == 0:
            factors.append(p)
            n /= p
        if p > n:
            break
    assert n == 1

    return factors
