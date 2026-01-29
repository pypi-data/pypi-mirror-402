import pytest
import time
import random
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.computer_science.algorithm.cache_manager import Cache_Manager


def test_cache_manager_with_lru_strategy():
    print("test Cache_Manager with LRU_Strategy")

    strategy = ":by_last_time:LRU"
    for cache in [":in_memory:Memo", ]:
        cache_manager = Cache_Manager(upper_bound=3, refactor_size=2, strategy=strategy, cache=cache)

        # 添加数据 a、b、c
        #   优先级依次为 c、b、a
        cache_manager.add(key="a", value=1)
        cache_manager.add(key="b", value=2)
        cache_manager.add(key="c", value=3)
        #
        for k, v in {"a": 1, "b": 2, "c": 3}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata

        # 重新添加 a，并访问 a
        #   优先级变为 a、c、b
        cache_manager.add(key="a", value=3)
        check_consistency(cache_manager.get(key="a"), 3)
        #
        for k, v in {"a": 3, "b": 2, "c": 3}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata
        for k in ["d", "e"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)

        # 添加数据 d
        #   优先级变为 d、a、c、b，超过upper_bound，触发重整到refactor_size大小，变为 d、a
        cache_manager.add(key="d", value=4)
        #
        for k, v in {"a": 3, "d": 4}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata
        for k in ["b", "c"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)

        # 继续添加 e、f、g
        #    重整后优先级依次为 g、f、e
        cache_manager.add(key="e", value=5)
        cache_manager.add(key="f", value=6)
        cache_manager.add(key="g", value=7)
        #
        for k, v in {"e": 5, "f": 6, "g": 7}.items():
            assert cache_manager.has(key=k)
        for k in ["a", "d"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)


def test_cache_manager_with_fifo_strategy():
    print("test Cache_Manager with FIFO_Strategy")

    strategy = ":by_initial_time:FIFO"
    for cache in [":in_memory:Memo", ]:
        cache_manager = Cache_Manager(upper_bound=3, refactor_size=2, strategy=strategy, cache=cache)

        # 添加数据 a、b、c
        #   优先级依次为 c、b、a
        cache_manager.add(key="a", value=1)
        cache_manager.add(key="b", value=2)
        cache_manager.add(key="c", value=3)
        #
        for k, v in {"a": 1, "b": 2, "c": 3}.items():
            check_consistency(cache_manager.get(key=k), v)

        # 无论后面怎么读取，优先级都不变
        for k, v in {"b": 2, "c": 3, "a": 1}.items():
            for _ in range(random.randint(3, 6)):
                cache_manager.get(key=k)
            cache_manager.add(key=k, value=v)

        # 添加数据 d
        #   优先级变为 d、c、b、a，超过upper_bound，触发重整到refactor_size大小，变为 d、c
        cache_manager.add(key="d", value=4)
        #
        for k, v in {"c": 3, "d": 4}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata
        for k in ["b", "a"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)

        # 继续添加 e、f、g
        #    重整后优先级依次为 g、f、e
        cache_manager.add(key="e", value=5)
        cache_manager.add(key="f", value=6)
        cache_manager.add(key="g", value=7)
        #
        for k, v in {"e": 5, "f": 6, "g": 7}.items():
            assert cache_manager.has(key=k)
        for k in ["a", "d"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)


def test_cache_manager_with_lfu_strategy():
    print("test Cache_Manager with LFU_Strategy")

    strategy = ":by_counts:LFU"
    for cache in [":in_memory:Memo", ]:
        cache_manager = Cache_Manager(upper_bound=3, refactor_size=2, strategy=strategy, cache=cache)

        # 添加数据 a、b、c，然后各访问 2、3、4
        #   优先级依次为 c、b、a
        cache_manager.add(key="a", value=1)
        cache_manager.add(key="b", value=2)
        cache_manager.add(key="c", value=3)
        #
        for k, v in {"a": 1, "b": 2, "c": 3}.items():
            for _ in range(v + 1):
                check_consistency(cache_manager.get(key=k), v)
        check_consistency(cache_manager.get(key="d", default_factory=lambda: "fuck"), "fuck")

        # 重新添加 c
        #   优先级变为 b、a、c
        cache_manager.add(key="c", value=4, b_allow_overwrite=True)
        check_consistency(cache_manager.get(key="c"), 4)
        #
        for k, v in {"a": 1, "b": 2, "c": 4}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata
        for k in ["d", "e"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)

        # 添加数据 d
        #   优先级变为 b、a、c、d，超过upper_bound，触发重整到refactor_size大小，变为 b、a
        cache_manager.get(key="d", default=4, b_add_if_not_found=True)
        #
        for k, v in {"a": 1, "b": 2}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata
        for k in ["c", "d"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)

        # 继续添加 e、f、g，访问一次 e
        #    重整后优先级依次为 b、a、g
        cache_manager.get(key="e", default=5, b_add_if_not_found=True)
        cache_manager.add(key="f", value=6)
        cache_manager.add(key="g", value=7)
        #
        for k, v in {"g": 7, "a": 1, "b": 2}.items():
            assert cache_manager.has(key=k)
        for k in ["f", "e"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)


def test_cache_manager_with_lst_strategy():
    print("test Cache_Manager with LST_Strategy")

    strategy = ":by_survival_time:LST"
    for cache in [":in_memory:Memo", ]:
        cache_manager = Cache_Manager(upper_bound=3, refactor_size=2, strategy=strategy, cache=cache)

        # 添加数据 a、b、c，然后读取2次 b，读取1次 c，读取3次 a
        #   优先级依次为 a、c、b
        cache_manager.add(key="a", value=1)
        cache_manager.add(key="b", value=2)
        cache_manager.add(key="c", value=3)
        #
        for k, v in {"b": 2, "c": 1, "a": 3}.items():
            for _ in range(v):
                time.sleep(0.1)
                cache_manager.get(key=k)

        # 添加数据 d
        #   优先级变为 a、c、b、d，超过upper_bound，触发重整到refactor_size大小，变为 a、c
        cache_manager.get(key="d", default=4, b_add_if_not_found=True)
        #
        for k, v in {"a": 1, "c": 3}.items():
            assert cache_manager.has(key=k)
            check_consistency(cache_manager.cache.read(key=k), v)  # 不影响 metadata
        for k in ["b", "d"]:
            assert not cache_manager.has(key=k)
            with pytest.raises(KeyError):
                cache_manager.get(key=k)
