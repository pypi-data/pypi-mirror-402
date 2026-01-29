import pickle
import concurrent.futures
from multiprocessing import Manager
from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.computer_science.algorithm.parallel_and_concurrent.utils import wrapper_for_mp as wrapper
from kevin_toolbox.computer_science.algorithm.parallel_and_concurrent.utils import DEFAULT_PROCESS_NUMS


def multi_process_execute(executors, worker_nums=DEFAULT_PROCESS_NUMS, b_display_progress=True, timeout=None,
                          _hook_for_debug=None):
    """
        多进程执行

        参数：
            executors:                  <list/generator/iterator of Executor> 执行器序列
            worker_nums:                <int> 进程数
            b_display_progress:         <boolean> 是否显示进度条
            timeout:                    <int/float> 每个进程的最大等待时间，单位是s
                                            默认为 None，表示允许等待无限长的时间
            _hook_for_debug:            <dict/None> 当设置为非 None 值时，将保存中间的执行信息。
                                            包括：
                                                - "execution_orders":    执行顺序
                                                - "completion_orders":   完成顺序
                                            这些信息与最终结果无关，仅面向更底层的调试需求，任何人都不应依赖该特性
        返回：
            res_ls, failed_idx_ls
            执行结果列表，以及执行失败的执行器索引列表
    """
    executor_ls = []
    for i in executors:
        assert isinstance(i, (Executor,))
        try:
            pickle.dumps(i)
        except:
            raise AttributeError(
                f'非法任务。因为进程池中的任务必须要能被pickle化。\n对象 {i} 无法被 pickle，请检查其中是否使用了闭包内定义的函数')
        executor_ls.append(i)
    if b_display_progress:
        from tqdm import tqdm
        p_bar = tqdm(total=len(executor_ls))
    else:
        p_bar = None

    if isinstance(_hook_for_debug, dict):
        _execution_orders, _completion_orders = Manager().list(), Manager().list()
    else:
        _execution_orders, _completion_orders = None, None

    res_ls = [None] * len(executor_ls)
    failed_idx_ls = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=worker_nums) as process_pool:
        # 提交任务并添加进度回调
        futures = []
        for i, executor in enumerate(executor_ls):
            future = process_pool.submit(wrapper, executor, timeout, i, _execution_orders, _completion_orders)
            if b_display_progress:
                future.add_done_callback(lambda _: p_bar.update())
            futures.append(future)

        # 收集结果
        for i, future in enumerate(futures):
            try:
                res, b_success = future.result()
            except:
                b_success = False
            if b_success:
                res_ls[i] = res
            else:
                failed_idx_ls.append(i)

    if b_display_progress:
        p_bar.close()

    if isinstance(_hook_for_debug, (dict,)):
        _hook_for_debug.update({
            "execution_orders": list(_execution_orders),
            "completion_orders": list(_completion_orders)
        })

    return res_ls, failed_idx_ls


if __name__ == '__main__':
    import time


    def func_(i):
        # 模拟部分任务长时间运行，部分任务正常结束
        if i in [2, 3, 7]:
            time.sleep(100)
        else:
            time.sleep(0.01)
        print(f"任务 {i} 执行完成")
        return i * 2


    hook_for_debug = dict()
    a = time.time()
    results, failed = multi_process_execute(
        executors=[Executor(func=func_, args=(i,)) for i in range(10)],
        worker_nums=10,
        timeout=0.2,
        _hook_for_debug=hook_for_debug
    )
    gap = time.time() - a
    print("执行结果:", results)
    print("超时失败的任务索引:", failed)
    print("调试信息:", hook_for_debug)
    print("总耗时:", gap)
