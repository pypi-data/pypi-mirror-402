# kevin_toolbox

一个通用的工具代码包集合



环境要求

```shell
numpy>=1.19
pytorch>=1.2
```

安装方法：

```shell
pip install kevin-toolbox  --no-dependencies
```



[项目地址 Repo](https://github.com/cantbeblank96/kevin_toolbox)

[使用指南 User_Guide](./notes/User_Guide.md)

[免责声明 Disclaimer](./notes/Disclaimer.md)

[版本更新记录](./notes/Release_Record.md)：

- v 1.4.14 （2026-01-19）【bug fix】【new feature】【incompatible change】
  - env_info.variable_
    - 【new feature】add Vars_Parser，解释以ndl命名格式指定位置下的变量。
    - refactor Env_Vars_Parser with Vars_Parser，将 Env_Vars_Parser 改为依赖 Vars_Parser 实现的形式。
      - 出于兼容以往版本的考虑，我们在该版本中仍保留 Env_Vars_Parser，但我们强烈建议你改为使用 Vars_Parser 以获得更灵活高效的体验。
  - patches
    - for_matplotlib
      - common_charts
        - 【new feature】add plot_heatmap()， 绘制矩阵热力图（Heatmap）。
      - common_charts.utils
        - modify save_record() 修改以支持 label_formatter 参数为函数对象或`"<eval>..."`形式包裹的函数的情况。
    - for_optuna
      - 【new feature】add determine_whether_to_add_trial()，判断 hyper_paras 对应的 trial 是否应该添加到给定 study 中。
      - 【new feature】add enqueue_trials_without_duplicates()，将 hyper_paras_ls 对应的一系列 trials 添加到 study 中。
      - 添加了对应的测试用例。
    - for_test
      - modify check_consistency，新增参数 b_raise_error 用于控制检查到不一致时，是否引发报错。当设置为 False 时，将以 `(<boolean>, <msg>)` 的形式返回检查结果。
  - computer_science.algorithm
    - statistician
      - 【new feature】add Latest_Accumulator，用于保留最近一次add的值的累积器。
    - scheduler
      - 【bug fix】fix bug in Strategy_Manager
        - 将原来 line 218 中：先对 action_s 进行深拷贝再取出 p_value_func；改为先从 action_s 中取出 p_value_func 等待 p_value_func 进行可能的运算结束之后，再对 p_value_func 返回的结果深拷贝；前者在 p_value_func 为 callable 类实例且内部存在记忆变量时往往会因为对该实例本身进行深拷贝而产生意外结果，而后者对实例产生的结果再进行深拷贝就没有这个问题了。
        - 增加 b_deepcopy_p_value 参数用于控制是否对 p_value_func 产生的结果进行深拷贝。
    - cache_manager.cache
      - 【new feature】add Array_Cache，基于内存array的缓存结构。
        - 相较于基于dict的Memo_Cache，该类对于存储 Key 为非负整数（如索引 ID）的结构化数据更为友好。
    - redirector
      - 【new feature】add Passive_Redirectable_Sequence_Fetcher，辅助用户通过跳转来处理获取失败的情况。
        - 相较于 Redirectable_Sequence_Fetcher 主动去管理给定的 seq，并负责获取元素，判断获取是否成功，本类仅起到记忆和建议的功能，并不管理任何 seq，需要用户主动告知获取是否成功。这给与用户更大的灵活性。
      - refactor Redirectable_Sequence_Fetcher，改为依赖 Passive_Redirectable_Sequence_Fetcher 来实现功能。
    - sampler
      - 【new feature】add Moving_Reservoir_Sampler，滑动水库采样，对最近历史窗口内数据进行均匀采样。
      - 【incompatible change】modify Reservoir_Sampler，将原来 capacity 等参数更名为 target_nums 等。
      - 【new feature】add Vanilla_Sampler，一般的序列采样采样。
