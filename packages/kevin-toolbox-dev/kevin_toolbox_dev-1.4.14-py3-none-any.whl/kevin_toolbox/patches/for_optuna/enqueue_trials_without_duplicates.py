from kevin_toolbox.patches.for_optuna import determine_whether_to_add_trial


def enqueue_trials_without_duplicates(study, hyper_paras_ls, **kwargs):
    """
        将 hyper_paras_ls 对应的一系列 trials 添加到 study 中

        参数：
            study
            hyper_paras:                <list of dict>
            skip_states:                <list/tuple of str/TrialState> 当 hyper_paras_ls 和 study 中已有 trial 重复时，若为这些状态则跳过不添加
                                            具体参见 determine_whether_to_add_trial() 中对应参数的介绍。
    """
    res_ls = []  # 成功添加了的 trial
    for i, hyper_paras in enumerate(hyper_paras_ls):
        # 判断使用了该超参数的trial是否已经存在，如果不存在则添加
        if determine_whether_to_add_trial(study=study, hyper_paras=hyper_paras, **kwargs):
            study.enqueue_trial(params=hyper_paras)
            res_ls.append(i)
    return res_ls
