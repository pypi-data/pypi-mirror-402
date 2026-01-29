def deep_update(stem, patch):
    """
        使用 patch 递归地更新 stem 中对应结构下的值
            比如对于 stem = {"a": {"b": [233], "g": 3}}
            如果使用 patch = {"a": {"b": 444}} 进行更新，可以得到：
                {'a': {'b': 444, 'g': 3}}
    """
    assert isinstance(stem, (dict,)) and isinstance(patch, (dict,))

    return _recursion(stem=stem, patch=patch)


def _recursion(stem, patch):
    for k, v in patch.items():
        if k in stem and isinstance(v, (dict,)) and isinstance(stem[k], (dict,)):
            stem[k] = _recursion(stem=stem[k], patch=v)
        else:
            stem[k] = v
    return stem
