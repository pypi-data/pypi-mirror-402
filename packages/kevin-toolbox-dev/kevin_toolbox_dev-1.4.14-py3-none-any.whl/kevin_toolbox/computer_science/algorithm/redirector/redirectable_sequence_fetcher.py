from kevin_toolbox.computer_science.algorithm.redirector import Passive_Redirectable_Sequence_Fetcher

EMPTY = object()


class Redirectable_Sequence_Fetcher(Passive_Redirectable_Sequence_Fetcher):
    """
        用于从给定 seq 中获取元素，通过跳转来处理获取失败的情况

        功能描述：
            1. 对于给定的索引 idx，若能通过 seq(idx) 成功获取，则直接返回获取的结果。
            2. 若不能成功获取，则会根据给定的规则修改索引（如idx-1）重新尝试获取，递归调用直至获取成功或者递归调用次数达到上限。
                2.a 若开启了跳转记忆功能，则会为获取失败的 idx 记录其最终重定向到的新的 idx，以及其获取失败的次数。
                    当失败次数达到上限后，则不再进行尝试并直接返回重新向后的新的 idx 的结果。
                    若在此过程中原来失败的 idx 又能再次获取成功，则将失败次数减1，直至归零并删除该记录。
            3. 若递归次数达到上限，则进行报错或者返回给定的默认值。
                3.a 若开启了跳转记忆功能，在重试过程中，一旦某次调用成功，记录原始索引与最终有效索引之间的映射关系。

        使用建议：
            - 数据读取或模型训练过程中，当某些外部因素导致部分索引数据获取失败时，自动进行索引跳转和重试，从而保证整个流程的鲁棒性和连续性。
    """

    def __init__(self, **kwargs):
        """
            参数：
                seq:                <callable> 元素获取器。
                                        要求能通过 seq(idx) 或者 seq[idx] 返回元素。
                value_checker:      <callable> 元素检查器。
                                        形如 func(v) ==> boolean 的函数，当返回 True 时表示成功获取。
                                        默认为 None，不对元素进行检查。
                seq_len:          <int> 序列长度。
                                        默认不指定，将尝试通过 len(seq) 获取。
                idx_redirector:     <str/callable> 对 idx 进行重定向的方式。
                                        形如 func(idx, seq_len, attempts, rng) ==> new_idx 的函数，
                                            其中 attempts 是已进行重定向的次数，rng是随机生成器。
                                        当设定为 str 时，则使用默认的函数。目前支持以下选项：
                                            - "decrease":       new_idx=idx-1
                                            - "increase":       new_idx=idx+1
                                            - "randomly":       随机跳转（默认）
                redirect_max_attempts:  <int> 进行重定向的次数上限。
                                        默认为 3。
                default_value:      <any> 重定向失败时返回的值。
                                        默认不指定，此时重定向失败后将引发报错。
                                        所谓重定向失败，就是在进行 redirect_max_attempts 次重定向后仍然无法成功获取值。
                memory:             <int/Cache_Manager/dict> 跳转记忆器。
                                        当给定值为 int 时，将以该值为 upper_bound 构建 Cache_Manager，
                                            特别地，当设定为 -1 时，表示容量无上限。
                                        默认为 None，表示不使用记忆器。
                use_memory_after_failures:  <int> 在获取失败多少次后（failures计数+1大于该值后）将不再尝试获取而直接使用记忆。
                                        默认为 3。
                                        当设置为 None 时，表示从不使用记忆。
                memory_decay_rate:  <float> failures 计数衰减的速度。
                                        建议使用 0~1 之间的值。
                                        默认为 0.1，表示每直接使用一次记忆，则对 failures 计算减去 0.1
                logger:             <str/Logger> 用于记录每次发生的重定向行为。
                                        若为 dict，则需要包含 "target", "level", "formatter" 等键值对。
                                        若为 str，则会自动构建一个以该值为 target 的记录器。
                                            具体可以参见 for_logging.build_logger()
                                        默认为 None，表示不需要进行记录。
                seed:               <int>  随机种子
        """
        # 默认参数
        kwargs.setdefault("seq", None)
        kwargs.setdefault("value_checker", None)
        kwargs.setdefault("default_value", EMPTY)
        #
        self.seq = kwargs["seq"]
        if hasattr(kwargs["seq"], "__getitem__"):
            self.seq = lambda idx: kwargs["seq"][idx]
        assert callable(self.seq)
        self.value_checker = kwargs["value_checker"]
        assert self.value_checker is None or callable(self.value_checker)
        super().__init__(**kwargs)

    def fetch(self, idx):
        b_success = False
        error = None
        res = None
        try:
            res = self.seq(idx)
            b_success = True
        except Exception as e:
            error = e
        if self.value_checker is not None and b_success:
            b_success = self.value_checker(res)
            if not b_success:
                error = ValueError(f"value checker failed for idx={idx}")
        return res, b_success, error

    def redirectable_fetch(self, idx):
        new_idx = self.first_suggest(idx=idx)

        while True:
            res, b_success, error = self.fetch(new_idx)
            new_idx = self.notify_and_suggest(idx=new_idx, b_success=b_success, error=error)
            if new_idx is None or b_success:
                break

        if not b_success:
            if self.paras["default_value"] is EMPTY:
                raise error
            else:
                return self.paras["default_value"]

        return res

    def __call__(self, idx):
        return self.redirectable_fetch(idx)

    def __getitem__(self, idx):
        return self(idx)
