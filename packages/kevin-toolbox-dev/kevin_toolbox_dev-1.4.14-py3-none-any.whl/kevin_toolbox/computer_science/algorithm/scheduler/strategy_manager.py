import random
import torch
import numpy as np
import copy
from kevin_toolbox.nested_dict_list import set_value, get_value, traverse


class Strategy_Manager:
    """
        策略管理器

        使用方法：
            # 1.a 初始化
                sm = Strategy_Manager()
            # 2. 添加策略（策略的具体编写方式参见 add() 函数介绍）
                sm.add(
                    strategy={
                        "__dict_form": "para_name:trigger_value",
                        "__trigger_name": "epoch",
                        ":lr": {
                            # 当 key 满足 trigger_value 时，将 ":lr" 指向的部分替换为 value
                            0: 0.1,
                            # 如果是以 <eval> 为开头的字符串，则视为函数并将 value 解释为函数执行后的结果
                            #       函数中 t, p 参数将被分别传入 trigger_value 和 para_value
                            "<eval>lambda t: t%100==0": "<eval>lambda p, t: p*0.1",
                        },
                    },
                    override=False,
                )
            # 3.调用策略计算，得到调整后的结果
                res = sm.cal(
                    trigger_state=dict(epoch=300, step=1, ),
                    ref=dict(lr=5)
                )
                # res: {'lr': 0.5}

            # 1.b 在初始化时添加策略
                sm = Strategy_Manager(
                    strategy=<dict> or <list of dict>,
                    override=False,
                    ...
                )
    """

    def __init__(self, **kwargs):
        """
            参数：
                strategy:           <dict / list of dict> 待添加的多个策略
                                        当其为 dict 时将调用 self.add() 进行添加，
                                        当其为 list 时，且其中元素为 dict 时，将迭代调用 self.add() 添加其中的策略。
                override:           <boolean> 当输入的策略与现有策略发生冲突时，是否强制覆盖旧策略。
                                        将作为 self.add() 中 override 的默认值。
                                        默认为 False
                b_deepcopy_p_value: <boolean> 在调用 self.cal() 使用策略计算出要修改的值后，是否先对该值进行一次深拷贝，再修改到 var 中
                                        默认为 True，此时能有效避免当值为list或dict时导致的意外关联。
        """
        # 默认参数
        paras = {
            "strategy": tuple(),
            "override": False,
            "b_deepcopy_p_value": True
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        if not isinstance(paras["strategy"], (list, tuple,)):
            paras["strategy"] = [paras["strategy"]]
        for v in paras["strategy"]:
            assert isinstance(v, (dict,))
        self.paras = paras

        self.database = dict()
        for strategy in self.paras["strategy"]:
            self.add(strategy=strategy)

    def add(self, strategy, **kwargs):
        """
            将输入的 strategy 策略解释并添加到内部的 database 中

            参数：
                strategy:       <dict of paras> 策略。
                                    支持以下两种组织方式：
                                        （在下面的例子中，我们以 epoch 为触发器，目标变量为 var={"lr":xx, "ratio_ls":[xx,xx]}，
                                        尝试通过策略让变量中的 lr 和 ratio_ls 随着 epoch 而更新。）

                                        1. 触发值作为键。
                                            strategy={
                                                "__dict_form": "trigger_value:para_name",  # 字典的组织方式。必要参数
                                                "__trigger_name": "epoch",  # 触发器的名字。必要参数
                                                0: {
                                                    ":lr": 0.1,
                                                    ":ratio_ls": [1e-3, 1e-2],
                                                },  # 在 epoch=0 时，将 lr 和 ratio_ls 设置为 0.1 和 [1e-3, 1e-2]
                                                300: {
                                                    ":ratio_ls@1": 1e-5,
                                                },  # 在 epoch=300 时，将 ratio_ls[1] 设置为 1e-5
                                                "<eval>lambda t: t%100==0": {
                                                    ":lr": "<eval>lambda p, t: p*0.1",
                                                },  # 当键为 string 且 开头带有 <eval> 标记时候，将使用 eval() 函数读取该字符串，
                                                    # 当键为 callable 的函数时，在匹配过程中向该函数输入触发值 t 和当前元素的值 p，
                                                    # 当函数返回True视为匹配成功。
                                                    # 比如上式表示的是：每经过 100 epoch，也就是当 epoch%100==0 时，lr 在原来的基础上乘上0.1。
                                                    # 函数匹配的的优先级低于直接的值匹配。
                                                ...
                                            }
                                            （不同的触发器可以有不同的触发值类型，不一定是 int 类型，也可以是 float、str 等等）

                                        2. 参数名作为键。
                                            strategy={
                                                "__dict_form": "para_name:trigger_value",
                                                "__trigger_name": "epoch",
                                                ":lr": {
                                                    0: 0.1,
                                                    "<eval>lambda t: t%100==0": "<eval>lambda p, t: p*0.1",
                                                },
                                                ":ratio_ls": {
                                                    0: [1e-3, 1e-2],
                                                },
                                                ":ratio_ls@1": {
                                                    300: 1e-5,
                                                },
                                                ...
                                            }
                                        以上两种形式等效。

                                        其中诸如 ":ratio_ls@1" 的参数名的含义参见 computer_science.algorithm.utils 下的
                                        set_value() 函数介绍

                override:       <boolean> 当输入的策略与现有策略发生冲突时，是否强制覆盖旧策略。
                                    默认为 False，在发生冲突时候将直接抛出错误。
        """
        # 校验参数
        assert strategy.get("__dict_form", None) in ["trigger_value:para_name", "para_name:trigger_value"]
        assert isinstance(strategy.get("__trigger_name", None), (str,))
        strategy = copy.deepcopy(strategy)
        override = kwargs.get("override", self.paras["override"])

        _dict_form, _trigger_name = strategy.pop("__dict_form"), strategy.pop("__trigger_name")

        # 将 2. 参数名作为键 的形式转换为 1. 触发值作为键 的形式
        if _dict_form == "para_name:trigger_value":
            temp = dict()
            for p_key in strategy.keys():
                assert isinstance(p_key, (str,))
                for t_key in strategy[p_key].keys():
                    if t_key not in temp:
                        temp[t_key] = dict()
                    temp[t_key][p_key] = strategy[p_key][t_key]
            strategy = temp

        def deal_eval_str(x):
            return eval(x[6:]) if isinstance(x, (str,)) and x.startswith("<eval>") else x

        # 使用 eval() 读取带 "<eval>" 标签的键or值
        def converter(_, value):
            if isinstance(value, (dict,)):
                res = {deal_eval_str(k): deal_eval_str(v) for k, v in value.items()}
            else:
                res = deal_eval_str(value)
            return res

        strategy = traverse(var=[strategy], match_cond=lambda _, __, value: isinstance(value, (dict, str,)),
                            action_mode="replace", converter=converter, traversal_mode="dfs_post_order",
                            b_use_name_as_idx=False, b_traverse_matched_element=True)[0]

        # 将策略添加到 database
        old_strategy = self.database.get(_trigger_name, dict())
        for t_key, item in strategy.items():
            if t_key not in old_strategy:
                old_strategy[t_key] = dict()
            #
            if not override:
                # 检查冲突
                temp = set(old_strategy[t_key].keys()).intersection(set(item.keys()))
                assert len(temp) == 0, \
                    f'conflicting strategies for trigger {_trigger_name} in value {t_key}: \n' \
                    f'\tpara_name: {temp}'
            #
            old_strategy[t_key].update(item)

        self.database[_trigger_name] = old_strategy

    def cal(self, var, trigger_state, **kwargs):
        """
            从 database 中读取 trigger_state 指定的触发器状态下的策略，并根据该策略修改目标变量 var 中的对应部分

            参数：
                var:                    <list/dict> 目标变量
                trigger_state:          <dict> 触发器状态

            返回:
                var, action_s_all
                    其中 action_s_all 是一个以 trigger_name 为键的 dict，下面各值为在该触发器状态下匹配上的策略
        """
        assert isinstance(trigger_state, (dict,)) and isinstance(var, (dict, list,))
        b_deepcopy_p_value = kwargs.get("b_deepcopy_p_value", self.paras["b_deepcopy_p_value"])

        # 查找策略
        action_s_all = dict()
        for t_name, t_value in trigger_state.items():
            if t_name not in self.database:
                continue
            strategy = self.database[t_name]
            #
            action_s = dict()  # {p_name: p_value, ...}
            # 使用匹配函数
            for key, p_s in strategy.items():
                if callable(key) and key(t_value):
                    action_s.update({i: j for i, j in p_s.items() if i not in action_s})
            # 直接匹配
            if t_value in strategy:
                action_s.update(strategy[t_value])
            # !! 这一步排序很关键，它保证了将先处理整体，然后再处理局部
            #   比如对于 ':ratio_ls' 和 ':ratio_ls@0'，将先处理前者
            action_s_all[t_name] = [(k, action_s[k]) for k in sorted(action_s.keys())]

        # 执行策略
        for t_name, action_s in sorted(action_s_all.items(), key=lambda x: x[0]):
            t_value = trigger_state[t_name]
            for name, p_value in action_s:
                if callable(p_value):
                    raw_value = get_value(var=var, name=name)
                    p_value = p_value(raw_value, t_value)
                if not isinstance(p_value, (int, float)) and b_deepcopy_p_value:
                    p_value = copy.deepcopy(p_value)
                var = set_value(var=var, name=name, value=p_value)

        return var, action_s_all

    def __str__(self):
        return str(self.database)


if __name__ == '__main__':
    sm = Strategy_Manager(strategy={
        "__dict_form": "para_name:trigger_value",
        "__trigger_name": "epoch",
        ":lr": {
            # 0: 0.1,
            "<eval>lambda t: t%100==0": "<eval>lambda p, t: p*0.1",
        },
    })
    sm.add(strategy={
        "__dict_form": "trigger_value:para_name",
        "__trigger_name": "epoch",
        0: {
            ":lr": 0.1,
            ":ratio_ls": [1e-3, 1e-2],
        },
        300: {
            ":ratio_ls@1": 1e-5,
        },
        # "<eval>lambda t: t%100==0": {
        #     ":lr": "<eval>lambda p, t: p*0.1",
        # },
    }, override=False)

    print(sm.database)

    var, action_s_all = sm.cal(trigger_state=dict(epoch=0, ), var=dict())
    print(var, action_s_all)

    var, action_s_all = sm.cal(trigger_state=dict(epoch=300, ), var=var)
    print(var, action_s_all)
