import numpy as np
from .generate_shuffled_index_ls import generate_shuffled_index_ls
from .generate_z_pattern_indices_ls import generate_z_pattern_indices_ls
from ... import coordinates

SUPPORTED_PATTERNS = {"z_pattern", "shuffle_inside_block", "normal"}
SUPPORTED_FORMATS = {"index_ls", "indices_ls", "zip_indices"}


def generate_integrated_api(**kwargs):
    """
        整合了已有生成方法的集成接口
            按照不同模式 pattern 对 shape 进行遍历，并生成指定格式的 坐标列表

        参数：
            shape:              <list/tuple of integers> 坐标所属的多维变量的形状。
            pattern:            <str> 生成/遍历坐标的模式
                                    目前支持：
                                        "normal":
                                            生成 从原点出发按照行/列（在kwargs中通过order可以指定）优先遍历的下标列表
                                            核心调用的是 normal_indices_generator()
                                        "z_pattern" :
                                            生成 从原点出发进行之字形（Z形）遍历 的下标列表。
                                            核心调用的是 generate_z_pattern_indices_ls()
                                        "shuffle_inside_block" :
                                            对 shape 内的各个 block 中的坐标进行打乱，生成随机打乱的下标列表。
                                            核心调用的是 generate_shuffled_index_ls()
            kwargs:             <dict> 其他补充参数。
            output_format:      <str> 输出的目标格式。
                                    目前支持的坐标格式：
                                        "index_ls" , "indices_ls" , "zip_indices"
                                        各种格式的具体定义参见 coordinates.convert()
    """

    # 默认参数
    paras = {
        # 必要参数
        "shape": None,
        "pattern": None,
        "output_format": None,
        #
        "kwargs": dict(),
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert isinstance(paras["shape"], (list, tuple,)) and len(paras["shape"]) > 0
    #
    assert paras["pattern"] in SUPPORTED_PATTERNS, \
        f'Unknown pattern!\ncurrently supported patterns: {SUPPORTED_PATTERNS}'
    #
    assert paras["output_format"] in SUPPORTED_FORMATS, \
        f'Unknown format!\ncurrently supported formats: {SUPPORTED_FORMATS}'
    #
    assert isinstance(paras["kwargs"], (dict,))

    # 生成坐标
    if paras["pattern"] == "z_pattern":
        var = generate_z_pattern_indices_ls(shape=paras["shape"], **paras["kwargs"])
        input_format = "indices_ls"
    elif paras["pattern"] == "shuffle_inside_block":
        var = generate_shuffled_index_ls(shape=paras["shape"], **paras["kwargs"])
        input_format = "index_ls"
    else:  # "normal"
        var = np.asarray(list(coordinates.normal_indices_generator(shape=paras["shape"], **paras["kwargs"])))
        input_format = "indices_ls"

    # 转换格式
    res = coordinates.convert(var=var,
                              input_format=input_format, output_format=paras["output_format"],
                              shape=paras["shape"])

    return res
