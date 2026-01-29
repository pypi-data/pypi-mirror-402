from kevin_toolbox.patches.for_test import check_consistency


def determine_whether_to_add_trial(study, hyper_paras, skip_states=("COMPLETE", "RUNNING", "WAITING")):
    """
        判断 hyper_paras 对应的 trial 是否应该添加到给定 study 中

        参数：
            study
            hyper_paras:                <dict>
            skip_states:                <list/tuple of str/TrialState> 当 hyper_paras 对应的 trial 已经在 study 中存在，且状态为这些值时，则认为不应该添加
                                            支持以下取值：
                                                - RUNNING
                                                - COMPLETE
                                                - PRUNED
                                                - FAIL
                                                - WAITING
                                            默认为 "COMPLETE", "RUNNING", "WAITING"
    """
    from optuna.trial import TrialState
    skip_states = [getattr(TrialState, i) for i in skip_states]

    for trial in study.trials:
        if check_consistency(trial.params, hyper_paras, b_raise_error=False)[0] or check_consistency(
                trial.system_attrs["fixed_params"], hyper_paras, b_raise_error=False)[0]:
            if trial.state in skip_states:
                return False
            else:
                return True
    return True
