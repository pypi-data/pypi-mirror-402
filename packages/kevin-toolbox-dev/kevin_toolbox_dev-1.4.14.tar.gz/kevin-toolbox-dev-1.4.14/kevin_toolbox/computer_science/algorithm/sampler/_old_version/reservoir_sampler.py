from kevin_toolbox.patches.for_numpy.random import get_rng, get_rng_state, set_rng_state


class Reservoir_Sampler:
    """
        水库采样器
    """

    def __init__(self, **kwargs):
        """
            参数：
                capacity:                       <int> 水库的容量
                seed, rng:                      设定随机发生器
        """
        # 默认参数
        paras = {
            "capacity": 1,
            #
            "seed": None,
            "rng": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert paras["capacity"] >= 1

        #
        self.paras = paras
        self.reservoir = []
        self.state = self._init_state()
        self.rng = get_rng(seed=paras["seed"], rng=paras["rng"])

    @staticmethod
    def _init_state():
        """
            初始化状态
        """
        return dict(
            total_nums=0,
        )

    def add(self, item, **kwargs):
        """
            添加单个数据 item 到采样器中。
                对于前 k 个数据，直接存入水库；之后以 k/（当前数据数）概率选择替换水库中的一个随机位置。
        """
        self.state["total_nums"] += 1
        if self.state["total_nums"] <= self.paras["capacity"]:
            self.reservoir.append(item)
        else:
            # 生成一个 0 到 count-1 之间的随机整数
            j = self.rng.randint(0, self.state["total_nums"] - 1)
            if j < self.paras["capacity"]:
                self.reservoir[j] = item

    def add_sequence(self, item_ls, **kwargs):
        for item in item_ls:
            self.add(item, **kwargs)

    def get(self, **kwargs):
        """
            返回当前水库中的数据列表（浅拷贝）。
        """
        return self.reservoir.copy()

    def clear(self):
        """
            清空已有数据和状态，重置采样器。
        """
        self.reservoir.clear()
        self.state = self._init_state()
        self.rng = get_rng(seed=self.paras["seed"], rng=self.paras["rng"])

    def __len__(self):
        return self.state["total_nums"]

    # ---------------------- 用于保存和加载状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.state.update(state_dict["state"])
        self.reservoir.extend(state_dict["reservoir"])
        set_rng_state(state=state_dict["rng_state"], rng=self.rng)

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"state": self.state, "reservoir": self.reservoir, "rng_state": get_rng_state(rng=self.rng)}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp


# 测试示例
if __name__ == "__main__":
    sampler = Reservoir_Sampler(capacity=5, seed=12345)
    for i in range(1, 21):
        sampler.add(i)
    print("当前水库数据:", sampler.get())

    state = sampler.state_dict()
    print("状态字典:", state)

    # 清空后再恢复状态
    sampler.clear()
    print("清空后:", sampler.get())

    sampler.load_state_dict(state)
    print("恢复后水库数据:", sampler.get())
