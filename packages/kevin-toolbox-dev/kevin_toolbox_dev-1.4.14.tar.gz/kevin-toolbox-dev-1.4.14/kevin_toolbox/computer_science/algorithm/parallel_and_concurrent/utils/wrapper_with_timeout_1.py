import signal


# 定义超时异常
class TimeoutException(Exception):
    pass


# 定时器信号处理函数
def __alarm_handler(*args, **kwargs):
    raise TimeoutException("任务超时")


def wrapper_with_timeout_1(executor, timeout=None, idx=-1, _execution_orders=None, _completion_orders=None):
    """
        限制执行时间，使用 multiprocessing.Process 强制终止超时任务
            该函数仅适用于多进程以及 unix 操作系统

        参数:
            executor:               <Executor>执行器，需实现 run() 方法
            idx:                    <int> 任务索引（用于调试）
            timeout:                <int/float>最大等待时间（单位：秒，支持 float）
            _execution_orders, _completion_orders: 用于记录调试信息的 Manager.list
        返回:
            (result, b_success)     若超时或异常则 b_success 为 False
    """
    if _execution_orders is not None:
        _execution_orders.append(idx)

    # 定时器
    if timeout is not None:
        signal.signal(signal.SIGALRM, __alarm_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)

    # 执行
    res, b_success = None, True
    try:
        res = executor.run()
        if _completion_orders is not None:
            _completion_orders.append(idx)
    except TimeoutException:
        b_success = False
    finally:
        signal.alarm(0)  # 取消定时器
    return res, b_success


if __name__ == '__main__':
    import time


    def func_(i):
        if i in [2, 3, 7]:
            time.sleep(300)
        else:
            time.sleep(0.5)
        return i * 2


    from kevin_toolbox.computer_science.data_structure import Executor

    print(wrapper_with_timeout_1(Executor(func=func_, args=(2,)), timeout=1))
    print(wrapper_with_timeout_1(Executor(func=func_, args=(1,)), timeout=1))

    execution_orders = []
    completion_orders = []
    print(wrapper_with_timeout_1(Executor(func=func_, args=(2,)), timeout=1, _execution_orders=execution_orders,
                                 _completion_orders=completion_orders))
    print(execution_orders, completion_orders)
