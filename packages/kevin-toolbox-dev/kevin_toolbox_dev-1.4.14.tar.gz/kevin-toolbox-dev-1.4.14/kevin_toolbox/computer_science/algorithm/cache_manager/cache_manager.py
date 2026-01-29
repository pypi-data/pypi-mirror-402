import time
from .strategy import Strategy_Base
from .cache import Cache_Base
from .variable import CACHE_STRATEGY_REGISTRY, CACHE_BUILDER_REGISTRY
from .cache_manager_wto_strategy import Cache_Manager_wto_Strategy


class Cache_Manager(Cache_Manager_wto_Strategy):
    """
        缓存管理器

        提供以下接口：
            - 添加条目 add(key, value, b_allow_overwrite)
            - 获取条目 get(key, b_add_if_not_found, default_factory, default)
            - 删除并返回条目 pop(key)
            - 判断是否有该条目 has()
            - 清空所有内容 clear()
            - 加载和保存状态 load_state_dict(), state_dict()

        并支持以下用法：
            通过 len(.) 获取缓存大小，通过 in 操作符判断是否有某个条目


        相关变量：
            self.cache：     缓存
            self.metadata_s：缓存的属性数据
                                包含以下字段，各字段将自动更新
                                例如：{
                                        <key>:  {
                                            "last_time": xxx,      # 最近读取时间
                                            "initial_time": xxx,   # 最初读取时间
                                            "survival_time": xxx,  # survival_time:=last_time-initial_time
                                            "counts": xxx,         # 读取次数
                                        },
                                       ...
                                    }
            self.strategy：  缓存更新策略
    """

    def __init__(self, **kwargs):
        """
            参数：
                upper_bound:            <int> 当缓存容量超过该值时，触发重整（抛弃部分条目以将容量降低到 refactor_size 指定的大小）
                refactor_size:          <int/float> 内存重整后的容量大小
                                            当设置为 int 时，表示具体容量的大小；
                                            当设置为 float 时表示占 upper_bound 的比例
                                            默认为 0.5
                strategy:               <str/dict/Strategy_Base> 管理策略
                                            支持以下策略：
                                                - ":by_initial_time:FIFO"     删除最后一次访问时间最久远的部分
                                                - ":by_counts:LFU"            删除访问频率最低的部分
                                                - ":by_last_time:LRU"          删除最后一次访问时间最久远的部分
                                                - ":by_survival_time:LST"      删除访问频率最低的部分
                                            默认使用 LRU 策略
                cache:                  <str/dict/Cache_Base> 缓存种类
                                            支持以下值：
                                                - ":in_memory:Array_Cache":     基于内存array的缓存结构
                                                                                    至少需要指定 value_names 和 value_types 两个参数
                                                - ":in_memory:Memo_Cache":      (默认)基于内存dict的缓存结构
        """
        # 默认参数
        paras = {
            "upper_bound": None,
            "refactor_size": 0.5,
            "strategy": ":by_last_time:LRU",
            "cache": ":in_memory:Memo_Cache"
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["upper_bound"], int) and paras["upper_bound"] > 0, \
            "upper_bound must be a positive integer"
        if isinstance(paras["refactor_size"], float):
            paras["refactor_size"] = int(paras["refactor_size"] * paras["upper_bound"])
        assert 0 <= paras["refactor_size"] <= paras["upper_bound"], \
            "refactor_size must be less than upper_bound and bigger than zero"
        # strategy
        assert isinstance(paras["strategy"], (str, dict, Strategy_Base)), \
            "strategy must be a string, dict of paras or a Strategy_Base object"
        if isinstance(paras["strategy"], str):
            strategy = CACHE_STRATEGY_REGISTRY.get(name=paras["strategy"])()
        elif isinstance(paras["strategy"], dict):
            strategy = CACHE_STRATEGY_REGISTRY.get(name=paras["strategy"]["name"])(
                **paras["strategy"].get("paras", dict()))
        else:
            strategy = paras["strategy"]
        # cache
        assert isinstance(paras["cache"], (str, dict, Cache_Base)), \
            "cache must be a string, dict of paras or a Cache_Base object"
        if isinstance(paras["cache"], str):
            cache = CACHE_BUILDER_REGISTRY.get(name=paras["cache"])()
        elif isinstance(paras["cache"], dict):
            cache = CACHE_BUILDER_REGISTRY.get(name=paras["cache"]["name"])(**paras["cache"].get("paras", dict()))
        else:
            cache = paras["cache"]

        self.paras = paras
        self.strategy = strategy  # type:Strategy_Base
        self.cache = cache  # type:Cache_Base
        self.metadata_s = dict()  # 保存条目的相关信息

    def _write_of_cache(self, key, value):
        """
            向缓存中新增不存在的条目
        """
        temp = time.time()
        metadata = {
            "initial_time": temp,  # 最初读取时间（加入缓存的时间）
            "last_time": temp,  # 最近读取时间
            "survival_time": 0.0,  # 最后一次读取与加入缓存时间之差，last_time - initial_time
            "counts": 0,  # 读取次数
        }
        #
        self.cache.write(key=key, value=value)
        self.metadata_s[key] = metadata
        # 通知策略管理器
        self.strategy.notified_by_write_of_cache(key=key, value=value, metadata=metadata)

        # 判断是否重构
        if len(self.cache) <= self.paras["upper_bound"]:
            return
        # 从策略管理器获取建议
        #   根据建议删除条目
        suggest_keys = self.strategy.suggest(refactor_size=self.paras["refactor_size"])
        assert len(suggest_keys) == len(self.cache) - self.paras["refactor_size"], \
            f'expect {len(self.cache) - self.paras["refactor_size"]} deletion suggestions, but got {len(suggest_keys)}'
        for key in suggest_keys:
            self._remove_of_cache(key=key)

    def _remove_of_cache(self, key):
        """
            从缓存中删除存在的条目
        """
        self.cache.remove(key=key)
        metadata = self.metadata_s.pop(key)
        # 通知策略管理器
        self.strategy.notified_by_remove_of_cache(key=key, metadata=metadata)

    def _read_of_cache(self, key):
        """
            读取缓存中 已经存在的 条目
        """
        value = self.cache.read(key=key)
        metadata = self.metadata_s[key]
        # 更新 metadata
        metadata["last_time"] = time.time()
        metadata["survival_time"] = metadata["last_time"] - metadata["initial_time"]
        metadata["counts"] += 1
        # 通知策略管理器
        self.strategy.notified_by_read_of_cache(key=key, value=value, metadata=metadata)

        return value

    def clear(self):
        self.cache.clear()
        self.metadata_s.clear()
        self.strategy.notified_by_clear_of_cache()

    # ---------------------- 用于保存和加载状态 ---------------------- #
    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.cache.load_state_dict(state_dict=state_dict["cache"])
        self.metadata_s.update(state_dict["metadata_s"])

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"cache": self.cache.state_dict(b_deepcopy=False), "metadata_s": self.metadata_s}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp
