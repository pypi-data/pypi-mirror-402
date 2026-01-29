import pytest
import time
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.data_flow.core.cache import Cache_Manager_for_Iterator


def test_cache_manager_for_iterator():
    print("test Cache_Manager_for_Iterator")

    cache_manager = Cache_Manager_for_Iterator(
        iterator=range(10),
        b_del_cache_when_exit=True,
        paras_for_memo_cache=dict(upper_bound=3, refactor_size=3, strategy=":by_last_time:LRU")
    )

    check_consistency(
        cache_manager.file_dict,
        {i: f'{i}.pkl' for i in range(10)}
    )
    check_consistency(
        cache_manager.memo_cache_manager.metadata_s,
        dict()
    )
    key_to_counts = {0: 3, 3: 2, 6: 1, 9: 4}
    for key, counts in key_to_counts.items():
        for _ in range(counts):
            time.sleep(0.05)
            check_consistency(cache_manager.read(key), key)
    # counts
    for key, counts in key_to_counts.items():
        if key == 0:
            assert key not in cache_manager.memo_cache_manager.metadata_s
        else:
            check_consistency(cache_manager.memo_cache_manager.metadata_s[key]["counts"], counts - 1)
