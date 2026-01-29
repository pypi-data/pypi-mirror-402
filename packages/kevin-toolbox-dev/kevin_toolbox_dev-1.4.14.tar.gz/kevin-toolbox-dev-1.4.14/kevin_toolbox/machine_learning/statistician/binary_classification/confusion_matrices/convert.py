import numpy as np


def convert_to_numpy(cfm, decimals=None):
    """
        将 confusion_matrices 从 tensor 转换为 numpy
    """
    for key, value in cfm.items():
        cfm[key] = value.cpu().numpy()
    # 由于 gpu 上的 tensor 通过 .cpu().numpy() 转换后会存在一定误差，因此需要进行进一步圆整
    if decimals is not None:
        cfm["thresholds"] = np.around(cfm["thresholds"], decimals)
    return cfm
