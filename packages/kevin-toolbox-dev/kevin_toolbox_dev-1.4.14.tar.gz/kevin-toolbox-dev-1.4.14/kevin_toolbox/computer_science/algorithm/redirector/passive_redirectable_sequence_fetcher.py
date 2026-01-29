import random
from kevin_toolbox.patches.for_logging import build_logger
from kevin_toolbox.patches.for_numpy.random import get_rng, set_rng_state, get_rng_state
from kevin_toolbox.computer_science.algorithm.cache_manager import Cache_Manager, Cache_Manager_wto_Strategy


def _randomly_idx_redirector(idx, seq_len, attempts, rng, *args):
    if idx == 0:
        return rng.randint(1, seq_len)
    elif idx == seq_len - 1:
        return rng.randint(0, seq_len - 1)
    else:
        return rng.choice([rng.randint(0, idx), rng.randint(idx + 1, seq_len)], size=1,
                          p=[idx / (seq_len - 1), (seq_len - idx - 1) / (seq_len - 1)])[0]


idx_redirector_s = {
    "decrease": lambda idx, *args: idx - 1,
    "increase": lambda idx, *args: idx + 1,
    "randomly": _randomly_idx_redirector,
}


def _round_idx(idx, st, ed):
    if idx < st or idx >= ed:
        idx = (idx - st) % (ed - st) + st
    assert st <= idx < ed
    return idx


class Passive_Redirectable_Sequence_Fetcher:
    """
        辅助用户通过跳转来处理获取失败的情况
            相较于 Redirectable_Sequence_Fetcher 主动去管理给定的 seq，并负责获取元素，判断获取是否成功，
            本类仅起到记忆和建议的功能，并不管理任何 seq，需要用户主动告知获取是否成功。

        功能描述：
            1. 用户首先通过 self.first_suggest() 获取第一个 idx 的建议，
                然后再通过 self.notify_and_suggest() 主动告知实例在建议下的 idx 是否获取成功，若获取成功，该函数返回 None，
                否则会返回下一个 idx 的建议。
            2. 在 self.notify_and_suggest() 中，对于获取失败的情况，会根据给定的规则修改索引（如idx-1）来向用户建议再次尝试获取的 idx，
               直至建议（跳转）次数达到上限。
                2.a 若开启了跳转记忆功能，则会为获取失败的 idx 记录其最终重定向到的新的 idx，以及其获取失败的次数。
                    当失败次数达到上限后，则不再进行尝试并直接返回重新向后的新的 idx 的结果。
                    若在此过程中原来失败的 idx 又能再次获取成功，则将失败次数减1，直至归零并删除该记录。
            3. 若跳转次数达到上限，self.notify_and_suggest() 将返回 None。
                3.a 若开启了跳转记忆功能，一旦某次调用成功，将记录原始索引与最终有效索引之间的映射关系。

        具体使用方式可以参考 Redirectable_Sequence_Fetcher 中 redirectable_fetch() 函数。
    """

    def __init__(self, **kwargs):
        """
            参数：
                seq_len:          <int> 序列长度。
                                        必须指定。
                idx_redirector:     <str/callable> 对 idx 进行重定向的方式。
                                        形如 func(idx, seq_len, attempts, rng) ==> new_idx 的函数，
                                            其中 attempts 是已进行重定向的次数，rng是随机生成器。
                                        当设定为 str 时，则使用默认的函数。目前支持以下选项：
                                            - "decrease":       new_idx=idx-1
                                            - "increase":       new_idx=idx+1
                                            - "randomly":       随机跳转（默认）
                redirect_max_attempts:  <int> 进行重定向的次数上限。
                                        默认为 3。
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
        paras = {
            "idx_redirector": "randomly",
            "memory": None,
            #
            "seq_len": None,
            "redirect_max_attempts": 3,
            "use_memory_after_failures": 3,
            "memory_decay_rate": 0.1,
            "logger": None,
            "seed": 114514
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        if paras["seq_len"] is None:
            assert hasattr(paras["seq"], "__len__"), "cannot infer the range of idx from seq"
            paras["seq_len"] = len(paras["seq"])
        assert paras["seq_len"] >= 0
        assert paras["redirect_max_attempts"] >= 0
        #
        self.idx_redirector = idx_redirector_s[paras[
            "idx_redirector"]] if paras["idx_redirector"] in idx_redirector_s else paras["idx_redirector"]
        assert callable(self.idx_redirector)
        #
        self.memory = paras["memory"]
        if paras["memory"] is not None:
            if isinstance(paras["memory"], dict):
                self.memory = Cache_Manager(**paras["memory"])
            elif isinstance(paras["memory"], int):
                self.memory = Cache_Manager(
                    upper_bound=paras["memory"]
                ) if paras["memory"] > 0 else Cache_Manager_wto_Strategy()
            assert isinstance(self.memory, (Cache_Manager_wto_Strategy,))
        #
        self.logger = paras["logger"]
        if paras["logger"] is not None:
            if isinstance(paras["logger"], str):
                paras["logger"] = dict(target=paras["logger"])
            if isinstance(paras["logger"], dict):
                paras["logger"].setdefault("level", "INFO")
                self.logger = build_logger(name=f':Redirectable_Sequence_Fetcher:{id(self)}',
                                           handler_ls=[paras["logger"]], )
        #
        self.rng = get_rng(seed=paras["seed"], rng=None)

        self.paras = paras

        # 记录当前获取状态
        self._state_s = dict(attempts=0, first_idx=None, last_suggested_idx=None, b_use_memory=False)

    def first_suggest(self, idx):
        """
            （首先调用）为给定的索引建议下一个尝试的索引
        """
        if idx >= len(self) or idx < -len(self):
            raise IndexError("Index out of range")
        idx = _round_idx(idx, st=0, ed=len(self))

        self._state_s = dict(attempts=0, first_idx=idx, last_suggested_idx=None, b_use_memory=False)

        new_idx = idx
        # 尝试从 memory 中获取 new_idx
        if self.memory is not None and self.memory.has(key=idx):
            v_s = self.memory.get(key=idx)
            if "failures" in v_s and v_s["failures"] + 1 > self.paras["use_memory_after_failures"]:
                v_s["failures"] -= self.paras["memory_decay_rate"]
                self._state_s["attempts"] = self.paras["redirect_max_attempts"]
                new_idx = v_s["final"]
                self._state_s["b_use_memory"] = True
                self._log_info(f"used memory for idx={idx}, jump to new_idx={new_idx}.")
        self._state_s["last_suggested_idx"] = new_idx
        return new_idx

    def notify_and_suggest(self, idx, b_success, error=None):
        """
            （后续调用）记录获取的成功与否并返回下一个尝试的索引

            参数：
                idx:            <int> 尝试获取的索引
                b_success:      <boolean> 是否获取成功
                error:          <Exception> 获取失败时的错误信息（可选）
        """
        assert self._state_s["last_suggested_idx"] is not None, \
            f'last_suggested_idx is None, please call first_suggest() first.'
        assert self._state_s["last_suggested_idx"] == idx, \
            f'idx: {idx} is not the last suggested idx: {self._state_s["last_suggested_idx"]}'

        if idx >= len(self) or idx < -len(self):
            raise IndexError("Index out of range")
        idx = _round_idx(idx, st=0, ed=len(self))

        if b_success:
            if self.memory is not None and self.memory.has(key=idx):
                v_s = self.memory.get(key=idx)
                v_s["failures"] -= 1
                if v_s["failures"] <= 1e-10:
                    self.memory.pop(key=idx)
            if self._state_s["first_idx"] != idx and self.memory is not None:  # 经过了重定向
                v_s = self.memory.get(key=self._state_s["first_idx"])
                v_s["final"] = idx
                if not self._state_s["b_use_memory"]:
                    v_s["failures"] = v_s.get("failures", 0) + 1
            self._state_s["last_suggested_idx"] = None
            return None

        if self._state_s["attempts"] < self.paras["redirect_max_attempts"]:
            new_idx = idx
            old_idx = idx
            if self.paras["seq_len"] > 1:
                new_idx = self.idx_redirector(idx, self.paras["seq_len"], self._state_s["attempts"], self.rng)
                new_idx = _round_idx(new_idx, st=0, ed=self.paras["seq_len"])
            #
            if self.memory is not None:
                v_s = self.memory.get(key=old_idx, b_add_if_not_found=True, default_factory=dict)
                v_s["next"] = new_idx
            #
            self._state_s["attempts"] += 1
            self._log_info(f'attempts {self._state_s["attempts"]}：')
            self._log_warn(f"failed to fetch {old_idx}, because of {error}.")
            self._log_info(f"redirected from {old_idx} to {new_idx}.")
            self._state_s["last_suggested_idx"] = new_idx
            return new_idx
        else:
            self._log_error(f'failed to fetch {self._state_s["first_idx"]} after {self._state_s["attempts"]} attempts,'
                            f' because of {error}.')
            self._state_s["last_suggested_idx"] = None
            return None

    def _log_info(self, value):
        if self.logger is not None:
            self.logger.info(value)

    def _log_warn(self, value):
        if self.logger is not None:
            self.logger.warn(value)

    def _log_error(self, value):
        if self.logger is not None:
            self.logger.error(value)

    def __len__(self):
        return self.paras["seq_len"]

    def clear(self):
        if self.memory is not None:
            self.memory.clear()
        self._log_info("invoked clear()")

    # ---------------------- 用于保存和加载状态 ---------------------- #
    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self._log_info("invoked load_state_dict()")
        if self.memory is not None:
            self.memory.load_state_dict(state_dict=state_dict["memory"])
        set_rng_state(state=state_dict["rng_state"], rng=self.rng)

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {
            "memory": self.memory.state_dict(b_deepcopy=False) if self.memory is not None else None,
            "rng_state": get_rng_state(rng=self.rng),
        }
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp
