import numpy as np
from kevin_toolbox.patches.for_numpy import linalg


def cos_similar(v0, v1, axis=-1, keepdims=False, need_normalize=True):
    if need_normalize:
        v0, v1 = linalg.normalize(v0, axis=axis, ord=2), linalg.normalize(v1, axis=axis, ord=2)
    return np.sum(v0 * v1, axis=axis, keepdims=keepdims)


if __name__ == '__main__':
    print(cos_similar(v0=np.asarray([0, 0.1]), v1=np.asarray([0.3, 0.1])))
    print(cos_similar(v0=np.asarray([[0, 0.1]]), v1=np.asarray([[0.3, 0.1],
                                                                [0, 0.1]]), axis=1))
