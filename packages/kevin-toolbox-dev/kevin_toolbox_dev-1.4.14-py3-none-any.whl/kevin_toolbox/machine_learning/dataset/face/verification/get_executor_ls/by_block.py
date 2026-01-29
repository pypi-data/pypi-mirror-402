from kevin_toolbox.machine_learning.dataset.face.verification import Factory
from . import __by_block


def get_executor_ls_by_block(**kwargs):
    """
        通过调用 verification.Factory 中的 generate_by_block() 函数，
            生成一系列的执行器 executor_ls，
            每个执行器在被 executor() 调用后都将返回一个数据集

        参数：
            mode:                   构造哪种迭代器，现在支持以下模式：
                                        "all":  对整个特征矩阵进行构造
                                        "triangle": 对特征矩阵的上三角进行构造
            factory:                verification.Factory 实例

        设定数据集大小：
            chunk_step:             每个分块的大小（根据实际内存容量来选择）
                                        限制了每次返回的数据集大小。
            upper_bound_of_dataset_size:        每次返回的数据集的大小的上界（根据实际内存容量来选择）
                                        当给定有 upper_bound_of_dataset_size 时，
                                        程序将可以通过 cal_chunk_step() 来计算得到 chunk_step。
                                        该参数是间接设置 chunk_step 的方式，但相较而言更加直观。
            （建议使用 upper_bound_of_dataset_size 而不使用 chunk_step。两者同时设置时，将以两者中最小的为限制）

        输入到 Factory.generate_by_block 中：
            need_to_generate:       需要生成的字段
                                        （参见 Factory.generate_by_block() 中的介绍）
            include_diagonal:       是否包含对角线
    """
    # 默认参数
    paras = {
        "mode": "triangle",
        "factory": None,
        "chunk_step": None,
        "upper_bound_of_dataset_size": None,
        "need_to_generate": None,
        "include_diagonal": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert paras["mode"] in ["all", "triangle"]
    assert isinstance(paras["factory"], (Factory,)), \
        Exception(f"Error: The type of input factory should be {Factory}, but get a {type(paras['factory'])}!")

    temp_ls = []
    if paras["upper_bound_of_dataset_size"] is not None:
        temp_ls.append(cal_chunk_step(paras["upper_bound_of_dataset_size"]))
    if paras["chunk_step"] is not None:
        temp_ls.append(paras["chunk_step"])
    assert len(temp_ls) > 0
    paras["chunk_step"] = min(temp_ls)

    #
    if paras["mode"] == "all":
        executor_ls, size_ls = __by_block.of_all(**paras)
    else:
        executor_ls, size_ls = __by_block.of_triangle(**paras)
    return executor_ls, size_ls


def cal_chunk_step(upper_bound):
    """
        根据数据集大小的限制，计算每个数据块的边长上界。
        返回值满足:
            chunk_step = argmax( chunk_step * (chunk_step + 1) <= upper_bound )
    """
    # block的宽
    return int(((1 + 4 * upper_bound) ** 0.5 - 1) / 2)
