from tqdm import tqdm
import optuna


def copy_study(src, dst, b_force=False):
    """
        复制 study
            （本函数改进自 optuna.copy_study，支持更多复制方式）

        参数：
            src:                <dict/optuna.study.Study> 
                                    有两种输入方式：
                                        1. 内存中的 study 实例对象。
                                        2. 从数据库 storage 中读取一个 study 对象。
                                            需要输入包含以下两个键值对的 dict：
                                                - "storage":            <str/optuna.storages.BaseStorage/None> 数据库
                                                                            默认为 None，表示从内存中读取
                                                - "study_name":         <str/None> study 在数据库中的标识符
                                                                            默认为 None
            dst:                <dict> 指定要复制到哪个目标数据库中哪个标识符下
                                    输入方式参考上面的方式 2。
            b_force:            <boolean> 当目标已存在时，是否进行覆盖。
                                    默认为 False，此时若目标已存在则报错。
    """
    # 校验参数
    if not isinstance(src, (optuna.study.Study, dict)):
        raise TypeError("src must be a dict or optuna.study.Study.")
    if not isinstance(dst, (dict,)):
        raise TypeError("dst must be a dict.")

    # 读取 src 对应的 study
    if isinstance(src, (dict,)):
        src_name = src.get("study_name", None)
        src = optuna.load_study(study_name=src_name, storage=src.get("storage", None))
    else:
        src_name = src.study_name

    # 构建 dst 的 study 实例
    dst_name = dst.get("study_name", src_name)
    if b_force:
        try:
            optuna.delete_study(study_name=dst_name, storage=dst.get("storage", None))
        except:
            pass
    dst = optuna.create_study(
        study_name=dst_name, storage=dst.get("storage", None),
        directions=src.directions, load_if_exists=False
    )

    # 复制
    for key, value in src._storage.get_study_system_attrs(src._study_id).items():
        dst._storage.set_study_system_attr(dst._study_id, key, value)
    for key, value in src.user_attrs.items():
        dst.set_user_attr(key, value)
    # trials
    for trial in tqdm(src.get_trials(deepcopy=False)):
        dst.add_trial(trial)  # 之所以不用 add_trials 而是用 add_trial 逐个添加，是为了在使用 sql 数据库时更加鲁棒

    return dst
