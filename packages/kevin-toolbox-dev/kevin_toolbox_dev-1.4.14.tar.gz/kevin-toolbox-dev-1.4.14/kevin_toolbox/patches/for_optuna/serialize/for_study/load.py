import optuna
import kevin_toolbox.nested_dict_list as ndl
from kevin_toolbox.patches.for_optuna.serialize import for_trial


def __converter(_, v):
    # trials
    if "trial_id" in v:
        try:
            return for_trial.load(var=v)
        except:
            pass
    # directions/direction
    if v.get("name", None) == "optuna.study.StudyDirection":
        v = eval(v["name"])(v["value"])
    return v


def load(var, study: optuna.study.Study = None):
    """
        加载已序列化的 study
            目前只支持加载以下项目：                额外给定 study 参数时：
                - study_name                    skip
                - directions/direction          check
                - user_attrs                    skip
                - trials                        load
        参数：
            var:                <ndl> 序列化过的 study
            study:              当给定时，将会首先检查该 study 的配置与待加载项目（除trials以外）是否一致，然后再加载 trials
    """
    assert isinstance(var, dict)

    # 反序列化
    var = ndl.traverse(var=var, match_cond=lambda _, __, v: isinstance(v, (dict,)),
                       action_mode="replace", converter=__converter, b_use_name_as_idx=False)

    # 保存到 study 中
    if study is None:
        study = optuna.create_study(
            study_name=var["__dict__"]["study_name"], directions=var["directions"])
        # user_attrs
        for key, value in var["user_attrs"].items():
            study.set_user_attr(key, value)
    else:
        # check directions/direction
        assert study.direction == var["direction"] or study.directions == var["directions"]

    # trials
    for trial in var["trials"]:
        study.add_trial(trial)

    return study
