class Cache:
    def __init__(self):
        self.primes = None
        self.primes_square = None
        self.reset()

    def reset(self):
        self.primes = [1]
        self.primes_square = [i ** 2 for i in self.primes]


cache = Cache()
