import torch
from .convert import convert_to_numpy
from kevin_toolbox.patches.for_torch.compatible import where as torch_where

# 计算设备（尽量使用gpu来加速计算）
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')


def merge_cfm_ls(cfm_ls, to_numpy=True, **kwargs):
    """
        将多个混淆矩阵进行合并

        参数：
            cfm_ls:                 list of confusion_matrices，每个 confusion matrices 都是一个包含
                                    thresholds、tp_ls、tn_ls、fp_ls、fn_ls 等字段的 dict
                                            其具体介绍参见函数 binary_classification.cal_cfm()
            to_numpy（可选）:           boolean，是否将结果从 tensor 转换为 numpy
                                            默认为True
        工作流程：
            我们以合并两个 confusion_matrices 为例，
                对于递增的 tp_ls 字段，
                    首先计算它的每两个相邻的 threshold 之间 tp 的差值：
                        diff_tp_ls = tp_ls.copy()
                        diff_tp_ls[1:] -= tp_ls[:-1]  # 其中 diff_tp_ls[m] 表示 threshold=thresholds[m] 时刚好取到的 tp 样本
                    然后根据 thresholds，对两个 diff_tp_ls 进行合并，比如：
                        thresholds_0：   [0.9, 0.8, 0,7]
                        diff_tp_ls_0：   [1, 4, 5]
                        thresholds_1：   [0.8, 0.6, 0,5]
                        diff_tp_ls_1：   [2, 3, 7]
                    那么合并后就是：
                        thresholds：     [0.9, 0.8, 0,7, 0.6, 0,5]
                        diff_tp_ls：     [1, 4+2, 5, 3, 7]
                    最后再根据 diff_tp_ls，使用 cumsum 累积出合并后的 tp_ls：
                        tp_ls:          [1, 7, 12, 15, 22]
                对于递增的 fp_ls 字段也有类似的操作，
                对于递减的 tn_ls 和 fn_ls 字段，则根据 tp_ls、fp_ls 得出。
    """
    assert isinstance(cfm_ls, (list,)) and len(cfm_ls) > 0

    # 合并
    res = dict()
    temp = dict()
    for key in {"thresholds", "tp_ls", "fp_ls"}:
        tensor_ls = []
        for prediction in cfm_ls:
            if isinstance(prediction[key], torch.Tensor):
                tensor_ls.append(prediction[key].to(device))
            else:
                tensor_ls.append(torch.tensor(prediction[key], device=device))
        res[key] = torch.cat(tensor_ls, dim=0)
        temp[key] = tensor_ls

    # 计算 diff
    for key in {"tp_ls", "fp_ls"}:
        beg = 0
        for tensor_ in temp[key]:
            end = beg + tensor_.shape[0]
            res[key][beg + 1:end] -= tensor_[: - 1]
            beg = end

    # 按照 thresholds 从大到小进行排序，然后进行累加
    res["thresholds"], sorted_indices = torch.sort(res["thresholds"], descending=True, dim=0)
    for key in {"tp_ls", "fp_ls"}:
        res[key] = torch.cumsum(res[key][sorted_indices.reshape(-1)], dim=0, dtype=torch.int64)

    # 去除相同 threshold 下的结果
    diff_thresholds = res["thresholds"].clone()
    diff_thresholds[:-1] -= res["thresholds"][1:]  # 取梯度
    diff_thresholds[-1] = -1  # 保证最后一个元素被下面的 torch.where 取出
    diff_indices = torch_where(diff_thresholds != 0)
    for key, value in res.items():
        res[key] = value[diff_indices]

    # 计算 tn_ls 和 fn_ls
    res["tn_ls"] = res["fp_ls"][-1] - res["fp_ls"]
    res["fn_ls"] = res["tp_ls"][-1] - res["tp_ls"]

    if to_numpy:
        res = convert_to_numpy(res)

    return res
