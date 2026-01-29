from kevin_toolbox.patches.for_numpy.random import get_rng


def set_rng_state(state, rng=None):
    """
        加载状态到随机生成器中

        参数：
            state:
            rng:            当设置为 None 时，将通过 get_rng() 新建一个 rng，然后加载状态并返回
    """
    rng = rng or get_rng(seed=114514)
    rng.bit_generator.state = state
    return rng
