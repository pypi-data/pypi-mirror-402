import fcntl
import os
import time
from kevin_toolbox.patches import for_os


class Mutex_Lock:
    """
        互斥锁
            基于非阻塞锁实现，可以避免死锁
    """

    def __init__(self, **kwargs):
        """
            参数：
                lock_name:              <str> string or file_path
                                            当为单纯的字符串时，将在当前文件夹下创建锁文件
                wait_interval:          <int/float> 处于阻塞状态时，获取锁的每次尝试之间的时间间隔，单位为 second。
                                            默认为 1e-1

        """
        # 默认参数
        paras = {
            # 必要参数
            "lock_name": ".233",
            "wait_interval": 1e-1,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        self.paras = paras

        if os.path.dirname(self.paras["lock_name"]):
            os.makedirs(os.path.dirname(self.paras["lock_name"]), exist_ok=True)
        self.fd = open(self.paras["lock_name"], 'a')
        self.state = dict(acquired=False)

    def acquire(self, b_block_if_fail=True, time_out=None):
        start_time = time.time()
        while True:
            try:
                # 尝试获取文件锁
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.state["acquired"] = True
                break
            except IOError:
                # 获取锁失败
                if not b_block_if_fail or (time_out is not None and time.time() - start_time > time_out):
                    # 超时或者设置了不阻塞
                    self.state["acquired"] = False
                    break
                else:
                    # 未超时，等待一段时间后重试
                    time.sleep(self.paras["wait_interval"])
        return self.state["acquired"]

    def release(self, b_cool_down=True):
        assert self.state["acquired"], \
            f'Please use acquire() to acquire the lock before calling release()'
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        if b_cool_down:
            time.sleep(self.paras["wait_interval"] * 2)  # 冷却当前锁，让其他排队中的锁有机会获取资源，避免当前锁对资源的长期占用

    @property
    def acquired(self):
        return self.state["acquired"]

    def __del__(self):
        try:
            self.fd.close()
        except:
            pass
