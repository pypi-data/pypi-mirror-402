import os
from kevin_toolbox.computer_science.algorithm.registration import Registry

ignore_s = [
    {
        "func": lambda _, __, path: os.path.basename(path) in ["temp", "test", "__pycache__",
                                                               "_old_version"],
        "scope": ["root", "dirs"]
    },
]

# 包含缓存管理or更新策略
CACHE_STRATEGY_REGISTRY = Registry(uid="CACHE_STRATEGY_REGISTRY")

CACHE_STRATEGY_REGISTRY.collect_from_paths(
    path_ls=[os.path.join(os.path.dirname(__file__), "strategy"), ],
    ignore_s=ignore_s,
    b_execute_now=False
)

# 包含缓存构建器
CACHE_BUILDER_REGISTRY = Registry(uid="CACHE_BUILDER_REGISTRY")

CACHE_BUILDER_REGISTRY.collect_from_paths(
    path_ls=[os.path.join(os.path.dirname(__file__), "cache"), ],
    ignore_s=ignore_s,
    b_execute_now=False
)
