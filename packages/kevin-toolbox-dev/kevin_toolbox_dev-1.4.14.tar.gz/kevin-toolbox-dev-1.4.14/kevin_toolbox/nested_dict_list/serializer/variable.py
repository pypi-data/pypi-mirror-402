import os
from kevin_toolbox.computer_science.algorithm.registration import Registry

SERIALIZER_BACKEND = Registry(uid="SERIALIZER_BACKEND")

# 导入时的默认过滤规则
ignore_s = [
    {
        "func": lambda _, __, path: os.path.basename(path) in ["temp", "test", "__pycache__",
                                                               "_old_version"],
        "scope": ["root", "dirs"]
    },
]

# 从 kevin_toolbox/nested_dict_list/serializer/backends 下收集被注册的 backend
SERIALIZER_BACKEND.collect_from_paths(
    path_ls=[os.path.join(os.path.dirname(__file__), "backends"), ],
    ignore_s=ignore_s,
    b_execute_now=False
)
