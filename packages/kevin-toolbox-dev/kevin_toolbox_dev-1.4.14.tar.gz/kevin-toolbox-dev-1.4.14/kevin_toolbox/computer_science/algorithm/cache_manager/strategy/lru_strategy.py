from collections import OrderedDict
from kevin_toolbox.computer_science.algorithm.cache_manager.strategy import Strategy_Base
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_STRATEGY_REGISTRY


@CACHE_STRATEGY_REGISTRY.register()
class LRU_Strategy(Strategy_Base):
    """
        删除最后一次访问时间最久远的部分
        drop items with smaller last_time
    """

    name = ":by_last_time:LRU_Strategy"

    def __init__(self):
        self.record_s = OrderedDict()

    def notified_by_write_of_cache(self, key, value, metadata):
        self.record_s[key] = None

    def notified_by_read_of_cache(self, key, value, metadata):
        self.record_s.pop(key)
        self.record_s[key] = None

    def notified_by_remove_of_cache(self, key, metadata):
        self.record_s.pop(key)

    def notified_by_clear_of_cache(self):
        self.record_s.clear()

    def suggest(self, refactor_size):
        if refactor_size == 0:
            return list(self.record_s.keys())
        else:
            return list(self.record_s.keys())[:-refactor_size]

    def clear(self):
        self.record_s.clear()


# 添加其他别名
for name in [":by_last_time:LRU", ":by_last_time:Least_Recently_Used", ":by_last_time:drop_smaller"]:
    CACHE_STRATEGY_REGISTRY.add(obj=LRU_Strategy, name=name, b_force=False, b_execute_now=False)
