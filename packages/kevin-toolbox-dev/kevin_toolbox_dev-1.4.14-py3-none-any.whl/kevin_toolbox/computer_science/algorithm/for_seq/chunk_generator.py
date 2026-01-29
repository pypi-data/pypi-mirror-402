import math


def chunk_generator(inputs, chunk_size, b_drop_last=False, b_display_progress=False, hook_for_progress_rate=None):
    """
        构建返回指定批大小的生成器

        参数：
            inputs:                     <Sequence/iterator/generator>
            chunk_size:                 <int> 批大小
            b_drop_last:                <boolean> 若最后一个 chunk 的大小不满足指定的 chunk_size，则抛弃
                                            默认为 False，不开启
            b_display_progress:         <boolean> 显示进度条
            hook_for_progress_rate:     <dict/None> 用于获取进度的“钩子”
                                            当其不为 None 时，将在每次迭代返回 batch 时，同步修改钩子中 "progress_rate" 对应的值为当前进度，
                                                当 inputs 的大小已知，进度是一个 0~1 的 float 值，
                                                当大小未知，进度是一个大于 0 的整数，表示当前是第几个 batch。
    """
    assert chunk_size > 0
    if b_display_progress:
        from tqdm import tqdm
        inputs = tqdm(inputs)

    if isinstance(hook_for_progress_rate, (dict,)):
        count = 0
        if hasattr(inputs, "__len__"):
            total = len(inputs) / chunk_size
            total = math.floor(total) if b_drop_last else math.ceil(total)

            def update_progress_rate():
                nonlocal total, count, hook_for_progress_rate
                count += 1
                hook_for_progress_rate["progress_rate"] = count / total
        else:
            def update_progress_rate():
                nonlocal count, hook_for_progress_rate
                count += 1
                hook_for_progress_rate["progress_rate"] = count
    else:
        def update_progress_rate():
            pass

    #
    chunk = []
    for it in inputs:
        chunk.append(it)
        if len(chunk) == chunk_size + 1:
            update_progress_rate()
            yield chunk[:chunk_size]
            chunk = chunk[-1:]

    if b_drop_last and len(chunk) < chunk_size:
        return
    else:
        update_progress_rate()
        yield chunk


if __name__ == '__main__':
    hook_for_progress_rate_ = dict()
    for i in chunk_generator(inputs=range(2), chunk_size=3, hook_for_progress_rate=hook_for_progress_rate,
                             b_display_progress=True, b_drop_last=False):
        print(hook_for_progress_rate_, i)
