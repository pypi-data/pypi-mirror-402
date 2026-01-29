import numpy as np
import torch
import warnings
import kevin_toolbox.nested_dict_list as ndl


def check_consistency(*args, tolerance=1e-7, require_same_shape=True, b_raise_error=True):
    """
        检查 args 中多个变量之间是否一致
            变量支持 python 的所有内置类型，以及复杂的 nested_dict_list 结构， array 等
            对于 array，不区分 numpy 的 array，torch 的 tensor，还是 tuple of number，只要其中的值相等，即视为相同。

        参数：
            tolerance:          <float> 判断 <np.number/np.bool_> 之间是否一致时，的容许误差。
                                    默认为 1e-7。
            require_same_shape: <boolean> 是否强制要求 array 变量的形状一致。
                                    默认为 True，
                                    当设置为 False 时，不同形状的变量可能因为 numpy 的 broadcast 机制而在比较前自动 reshape 为相同维度，进而可能通过比较。
            b_raise_error:      <boolean> 当检查到不一致时，是否引发报错
                                    默认为 True
                                    当设置为 False 时，将以 (<boolean>, <msg>) 的形式返回检查结果
    """
    assert len(args) >= 2

    if b_raise_error:
        _check_consistency(*args, tolerance=tolerance, require_same_shape=require_same_shape)
    else:
        try:
            _check_consistency(*args, tolerance=tolerance, require_same_shape=require_same_shape)
            return True, None
        except Exception as e:
            return False, e


def _check_consistency(*args, tolerance, require_same_shape):
    # 复杂结构 ndl
    if isinstance(args[0], (list, dict,)):
        nodes_ls = [sorted(ndl.get_nodes(var=arg, level=-1), key=lambda x: x[0]) for arg in args]
        names_ls, values_ls = [], []
        for nodes in nodes_ls:
            names_ls.append([i[0] for i in nodes])
            values_ls.append([i[1] for i in nodes])
        try:
            _check_item(*names_ls, tolerance=tolerance, require_same_shape=True)
        except AssertionError as e:
            raise AssertionError(f'inputs <nested_dict_list> has different structure\nthe nodes that differ are:\n{e}')
        for its in zip(names_ls[0], *values_ls):
            try:
                _check_item(*its[1:], tolerance=tolerance, require_same_shape=require_same_shape)
            except AssertionError as e:
                raise AssertionError(
                    f'value of nodes {its[0]} in inputs <nested_dict_list> are inconsistent\nthe difference is:\n{e}')
    # 简单结构
    else:
        _check_item(*args, tolerance=tolerance, require_same_shape=require_same_shape)


def _check_item(*args, tolerance, require_same_shape):
    """
        检查 args 中多个 array 之间是否一致

        工作流程：
            1. 对于 args 都是 tuple/list 且每个 tuple/list 的长度都一致的情况，将会拆分为对应各个元素递归进行比较。
            2. 将 args 中的 tuple 和 tensor 分别转换为 list 和 numpy。
            3. 检查 args 中是否有 np.array 或者 tensor，若有则根据 require_same_shape 判断其形状是否一致。
            4. 先将输入的 args 中的所有变量转换为 np.array;
                然后使用 issubclass() 判断转换后得到的变量属于以下哪几种基本类型：
                    - 当所有变量都属于 np.number 数值（包含int、float等）或者 np.bool_ 布尔值时，
                        将对变量两两求差，当差值小于给定的容许误差 tolerance 时，视为一致。
                        注意：在比较过程中，若变量中存在 np.nan 值，将会首先比较有 np.nan 值的位置是否相等，然后再比较非 np.nan 值部分。
                            亦即在相同位置上都具有 np.nan 视为相同。
                            比如 [np.nan, np.nan, 3] 和 [np.nan, np.nan, 3] 会视为相等，
                            [np.nan, np.nan] 和 np.nan 在 require_same_shape=False 时会被视为相等。
                    - 当所有变量都属于 np.flexible 可变长度类型（包含string等）或者 np.object 时，
                        将使用==进行比较，当返回值都为 True 时，视为一致。
                    - 当变量的基本类型不一致（比如同时有np.number和np.flexible）时，
                        直接判断为不一致。
                numpy 中基本类型之间的继承关系参见： https://numpy.org.cn/reference/arrays/scalars.html

        参数：
            tolerance:          <float> 判断 <np.number/np.bool_> 之间是否一致时，的容许误差。
            require_same_shape: <boolean> 是否强制要求变量的形状一致。
                                    注意：仅在原始 args 中含有 np.array 或者 tensor 的情况会采取 broadcast，亦即此时该参数才会起效。
                                    当设置为 False 时，不同形状的变量可能因为 broadcast 机制而在比较前自动 reshape 为相同维度，进而通过比较。
    """
    warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    assert len(args) >= 2
    assert isinstance(tolerance, (int, float,)) and tolerance >= 0
    raw_args = args

    # 当 args 都是 tuple/list 且每个 tuple 的长度都一致时，将会拆分为对应各个元素进行比较
    if all([isinstance(i, (tuple, list)) for i in args]) and all([len(i) == len(args[0]) for i in args[1:]]):
        for i, it_ls in enumerate(zip(*args)):
            try:
                _check_item(*it_ls, tolerance=tolerance, require_same_shape=require_same_shape)
            except AssertionError as e:
                raise AssertionError(f'elements {i} are inconsistent\nthe difference is:\n{e}')
        return

    #
    args = ndl.traverse(var=list(args), match_cond=lambda _, __, v: isinstance(v, (tuple,)), action_mode="replace",
                        converter=lambda _, v: list(v), b_traverse_matched_element=True)
    args = ndl.traverse(var=list(args), match_cond=lambda _, __, v: torch.is_tensor(v), action_mode="replace",
                        converter=lambda _, v: v.detach().cpu().numpy(), b_traverse_matched_element=False)
    b_has_raw_array = any([isinstance(i, np.ndarray) for i in args])

    try:
        args = [np.asarray(v) for v in args]  # if b_has_raw_array else [np.array(v, dtype=object) for v in args]
    except Exception as e:
        raise RuntimeError(f'{raw_args} cannot be converted to np.array, \n'
                           f'because {e}')

    # 比较形状
    if b_has_raw_array:
        if require_same_shape:
            # 要求形状一致
            for v in args[1:]:
                assert args[0].shape == v.shape, \
                    f"{args[0]}, {v}, different shape: {args[0].shape}, {v.shape}"
        else:
            # 否则要求至少能够进行 broadcast
            for v in args[1:]:
                try:
                    np.broadcast_arrays(args[0], v)
                except:
                    raise AssertionError(f'{args[0]}, {v}, failed to broadcast')
            # 如果都是空的 array，直接视为相等
            if all([i.size == 0 for i in args]):
                return
    b_allow_broadcast = b_has_raw_array and not require_same_shape

    # 比较值
    if issubclass(args[0].dtype.type, (np.number, np.bool_,)):
        # 数字类型
        for v in args[1:]:
            assert issubclass(v.dtype.type, (np.number, np.bool_,))
            v_0, v_1 = args[0].astype(dtype=float), v.astype(dtype=float)
            v_0, v_1 = np.broadcast_arrays(v_0, v_1) if b_allow_broadcast else (v_0, v_1)
            assert v_0.shape == v_1.shape, \
                f'{v_0}, {v_1}, different shape: {v_0.shape}, {v_1.shape}'
            #
            if v_0.size > 0:
                try:
                    if np.any(np.isnan(v)):
                        assert np.all(np.isnan(v_0) == np.isnan(v_1))
                        v_0 = np.nan_to_num(v_0, nan=1e10)
                        v_1 = np.nan_to_num(v_1, nan=1e10)
                    assert np.max(np.abs(v_0 - v_1)) < tolerance
                except AssertionError:
                    raise AssertionError(f"{args[0]}, {v}, deviation: {np.max(np.abs(args[0] - v))}")
    elif issubclass(args[0].dtype.type, (np.flexible, object,)):
        # 可变长度类型
        for v in args[1:]:
            assert issubclass(v.dtype.type, (np.flexible, object,))
            v_0, v_1 = np.broadcast_arrays(args[0], v) if b_allow_broadcast else (args[0], v)
            assert v_0.shape == v_1.shape, \
                f'{v_0}, {v_1}, different shape: {v_0.shape}, {v_1.shape}\n' + (
                    '' if require_same_shape else
                    f'\tMore details: \n'
                    f'\t\tAlthough require_same_shape=False has been setted, broadcast failed because the variable at \n'
                    f'\t\tthis position does not contain elements of type np.array and tensor.')
            #
            for i, j in zip(v_0.reshape(-1), v_1.reshape(-1)):
                if i is j:
                    continue
                temp = i == j
                if isinstance(temp, (bool,)):
                    assert temp, \
                        f"{args[0]}, {v}, diff: {temp}"
                else:
                    assert temp.all(), \
                        f"{args[0]}, {v}, diff: {temp}"
    else:
        raise ValueError


if __name__ == '__main__':
    a = np.array([[1, 2, 3]])
    b = np.array([[1, 2, 3]])
    c = {'d': 3, 'c': 4}

    # var = ((1, 2), (4))
    #
    # var = ndl.traverse(var=[var], match_cond=lambda _, __, v: isinstance(v, (tuple,)), action_mode="replace",
    #                    converter=lambda _, v: list(v), b_traverse_matched_element=True)[0]
    # print(var)
