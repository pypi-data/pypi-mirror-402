import os
from kevin_toolbox.computer_science.algorithm.registration import Registry

COMMON_CHARTS = Registry(uid="COMMON_CHARTS")

# 导入时的默认过滤规则
ignore_s = [
    {
        "func": lambda _, __, path: os.path.basename(path) in ["temp", "test", "__pycache__",
                                                               "_old_version"],
        "scope": ["root", "dirs"]
    },
]

# 从 kevin_toolbox/patches/for_matplotlib/common_charts 下收集被注册的方法
COMMON_CHARTS.collect_from_paths(
    path_ls=[os.path.join(os.path.dirname(__file__), "common_charts"), ],
    ignore_s=ignore_s,
    b_execute_now=False
)
