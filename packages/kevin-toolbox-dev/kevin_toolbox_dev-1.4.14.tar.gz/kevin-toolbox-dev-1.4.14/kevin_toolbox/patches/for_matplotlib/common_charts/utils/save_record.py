import inspect
import kevin_toolbox.nested_dict_list as ndl
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS


def save_record(_name, _output_path, _func=None, **kwargs):
    if _output_path is None:
        return None

    # 获取函数的参数列表
    frame = inspect.currentframe().f_back
    if _func is None:
        func_name = inspect.getframeinfo(frame).function
        _func = globals()[func_name]
    sig = inspect.signature(_func)
    #   获取参数值
    args_info = inspect.getargvalues(frame)
    arg_names = args_info.args
    arg_values = args_info.locals
    #   将参数值映射到函数签名中
    kwargs_raw = {name: arg_values[name] for name in arg_names}
    for param_name, param in sig.parameters.items():
        if param.kind == param.VAR_KEYWORD:
            kwargs_raw.update(arg_values[param_name])
        elif param.kind == param.VAR_POSITIONAL:
            kwargs_raw[param_name] = arg_values[param_name]

    kwargs_raw.update(kwargs)
    kwargs_raw = ndl.traverse(var=ndl.copy_(var=kwargs_raw, b_deepcopy=True),
                              match_cond=lambda _, __, v: callable(v),
                              action_mode="replace", converter=lambda _, v: "<lambda func, skip>")

    from kevin_toolbox.computer_science.algorithm.registration import Serializer_for_Registry_Execution
    serializer = Serializer_for_Registry_Execution()
    file_path = serializer.record_name(
        _name=_name, _registry=COMMON_CHARTS
    ).record_paras(**kwargs_raw).save(_output_path + ".record", b_pack_into_tar=True, b_allow_overwrite=True)
    return file_path
