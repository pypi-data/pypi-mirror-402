import numpy as np


class DEFAULT_RNG:
    pass


for name in np.random.__all__:
    setattr(DEFAULT_RNG, name, getattr(np.random, name))

func_map_s = {
    'rand': lambda rng, *arg, **kwargs: rng.random(size=arg, **kwargs),
    'randint': 'integers',
    'randn': lambda rng, *arg, **kwargs: rng.normal(size=arg, **kwargs),
    'random_integers': 'integers',
    'random_sample': 'random',
    'ranf': 'random'
}


class My_RNG:
    def __init__(self, rng):
        self._rng = rng

        for name in np.random.__all__:
            setattr(DEFAULT_RNG, name, getattr(np.random, name))

    # self.key
    def __getattr__(self, key):
        if "_rng" not in self.__dict__:
            # _rng 未被设置，未完成初始化。
            return super().__getattr__(key)
        else:
            res = getattr(self._rng, key, None)
            if res is None and key in func_map_s:
                if callable(func_map_s[key]):
                    res = lambda *arg, **kwargs: func_map_s[key](self._rng, *arg, **kwargs)
                else:
                    res = getattr(self._rng, func_map_s[key], None)
            #
            if res is None:
                raise AttributeError(f"attribute '{key}' not found in {type(self)}")
            else:
                return res


def get_rng(seed=None, rng=None, **kwargs):
    if seed is not None:
        # 注意，随机生成器相较于 numpy.random 有部分属性缺失：
        #   ['get_state', 'rand', 'randint', 'randn', 'random_integers', 'random_sample', 'ranf', 'sample', 'seed',
        #   'set_state', 'Generator', 'RandomState', 'SeedSequence', 'MT19937', 'Philox', 'PCG64', 'PCG64DXSM',
        #   'SFC64', 'default_rng', 'BitGenerator']
        rng = My_RNG(rng=np.random.default_rng(seed=seed))
    if rng is not None:
        return rng
    else:
        return DEFAULT_RNG


if __name__ == '__main__':
    a = get_rng(seed=2)

    # 尝试访问随机生成器中缺失的部分方法
    print(a.randn(2, 3))
