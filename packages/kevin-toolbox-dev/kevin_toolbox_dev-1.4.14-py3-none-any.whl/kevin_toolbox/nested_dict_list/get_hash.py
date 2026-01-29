import hashlib
import json
import warnings


def get_hash(item, length=None, mode="md5"):
    """
        将输入 item 序列化，再计算出 hash 值
            本函数对于无序的字典能够提供唯一的 hash 值

        参数:
            item:
            length:         <int> 返回 hash 字符串的前多少位
                                默认为 None，返回所有结果
            mode:           <str> 支持 hashlib 中提供的 hash 方法
                                当设置为 None 时候表示不使用 hash 处理而直接返回序列化后的字符串
    """
    assert mode is None or mode in hashlib.__all__

    try:
        hash_ = json.dumps(item, sort_keys=True).encode('utf-8')
    except:
        warnings.warn(
            f"the item {type(item)} unable to be serialized by json, reproducibility is no longer guaranteed!",
            UserWarning
        )
        hash_ = f"{item}".encode('utf-8')
    if mode is not None:
        worker = eval(f'hashlib.{mode}()')
        worker.update(hash_)
        hash_ = worker.hexdigest()
    hash_ = hash_ if length is None else hash_[:length]
    return hash_


if __name__ == '__main__':
    print(get_hash(item={2, 4}, mode="sha512"))
    print(get_hash(item=[2, 4], mode="sha512"))
