def get_rng_state(rng):
    """
        获取随机生成器的状态
    """
    return rng.bit_generator.state