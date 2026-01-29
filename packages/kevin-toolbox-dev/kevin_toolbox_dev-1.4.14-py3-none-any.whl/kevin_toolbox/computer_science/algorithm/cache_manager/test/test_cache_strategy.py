import pytest
import random
import time
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.computer_science.algorithm.cache_manager.strategy import Strategy_Base
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_STRATEGY_REGISTRY


def test_lru_strategy():
    print("test LRU_Strategy")

    strategy = CACHE_STRATEGY_REGISTRY.get(name=":by_last_time:LRU")()  # type: Strategy_Base

    # 写入 1、2、3、4
    #   按照 last_time 排序，优先级为 4、3、2、1
    for i in range(1, 5):
        strategy.notified_by_write_of_cache(key=i, value=i, metadata=None)
    #
    expected_orders = [4, 3, 2, 1]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))
    # 移除并重写 3
    #   优先级变为 3、4、2、1
    strategy.notified_by_remove_of_cache(key=3, metadata=None)
    strategy.notified_by_write_of_cache(key=3, value=3, metadata=None)
    #
    expected_orders = [3, 4, 2, 1]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))
    # 读取 1
    #   优先级变为 1、3、4、2
    strategy.notified_by_read_of_cache(key=1, value=1, metadata=None)
    #
    expected_orders = [1, 3, 4, 2]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))


def test_fifo_strategy():
    print("test FIFO_Strategy")

    strategy = CACHE_STRATEGY_REGISTRY.get(name=":by_initial_time:FIFO")()  # type: Strategy_Base

    # 写入 1、2、3、4
    #   按照 initial_time 排序，优先级为 4、3、2、1
    for i in range(1, 5):
        strategy.notified_by_write_of_cache(key=i, value=i, metadata=None)
    #
    expected_orders = [4, 3, 2, 1]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))

    # 无论后面怎么读取，优先级都不变
    for i in range(1, 5):
        for _ in range(random.randint(3, 6)):
            strategy.notified_by_read_of_cache(key=i, value=i, metadata=None)
    #
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))

    # 重写 1，删除 4
    #   优先级变为 1、3、2
    strategy.notified_by_remove_of_cache(key=1, metadata=None)
    strategy.notified_by_write_of_cache(key=1, value=3, metadata=None)
    strategy.notified_by_remove_of_cache(key=4, metadata=None)
    #
    expected_orders = [1, 3, 2]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))


def test_lfu_strategy():
    print("test LFU_Strategy")

    strategy = CACHE_STRATEGY_REGISTRY.get(name=":by_counts:LFU")()  # type: Strategy_Base

    # 写入 1、2、3、4
    #   按照 counts 排序，优先级为 4==3==2==1
    for i in range(1, 5):
        strategy.notified_by_write_of_cache(key=i, value=i, metadata=None)
    # 读取2次 1，读取1次 3，读取3次 2
    #   counts变为 4:0 3:1 2:3 1:2
    #   优先级变为 2、1、3、4
    for key, counts in {1: 2, 3: 1, 2: 3}.items():
        for i in range(counts):
            strategy.notified_by_read_of_cache(key=key, value=key, metadata=None)
    #
    expected_orders = [2, 1, 3, 4]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))
    # 移除并重写 3，读取一次 4
    #   优先级变为 2、1、4、3
    strategy.notified_by_remove_of_cache(key=3, metadata=None)
    strategy.notified_by_write_of_cache(key=3, value=3, metadata=None)
    strategy.notified_by_read_of_cache(key=4, value=4, metadata=None)
    #
    expected_orders = [2, 1, 4, 3]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))


def test_lst_strategy():
    print("test LST_Strategy")

    strategy = CACHE_STRATEGY_REGISTRY.get(name=":by_survival_time:LST")()  # type: Strategy_Base

    # 写入 1、2、3、4
    #   按照 survival_time 排序，优先级为 4==3==2==1
    for i in range(1, 5):
        strategy.notified_by_write_of_cache(key=i, value=i, metadata={"survival_time": 0})
    init_time = time.time()
    # 依次 读取2次 1，读取1次 3，读取3次 2
    #   优先级变为 2、3、1、4
    for key, counts in {1: 2, 3: 1, 2: 3}.items():
        for i in range(counts):
            strategy.notified_by_read_of_cache(key=key, value=key, metadata={"survival_time": time.time() - init_time})
    #
    expected_orders = [2, 3, 1, 4]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))
    # 移除并重写 3，读取一次 4
    #   优先级变为 4、2、1、3
    strategy.notified_by_remove_of_cache(key=3, metadata=None)
    strategy.notified_by_write_of_cache(key=3, value=3, metadata={"survival_time": 0})
    strategy.notified_by_read_of_cache(key=4, value=4, metadata={"survival_time": time.time() - init_time})
    #
    expected_orders = [4, 2, 1, 3]
    for i in range(0, 5):
        check_consistency(strategy.suggest(refactor_size=i), list(reversed(expected_orders[i:])))
