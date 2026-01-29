import threading
from collections import Iterable

'''
https://mp.weixin.qq.com/s?src=11&timestamp=1650039124&ver=3740&signature=Sm*QyFsWmuR2JoIrPqqsaOl6*r2pt2e53sHM2bVOjrm8ELxOfdvo9fRXHYAUZA-xwgHL4tDa*FjaQ9IGbEtPBKhPn4z553V0QdVuZ8ISXAfSMh-FBtCVwyhoKhdxlm6Z&new=1
https://www.cda.cn/view/123373.html
https://zhuanlan.zhihu.com/p/29379247
'''


class Producer:
    def __init__(self, **kwargs):
        # 默认参数
        paras = {
            # 必要参数
            "creator": None,
            # 仓库大小
            "lower_bound_of_storage_size": None,
            # 锁
            "lock": threading.Lock(),
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["creator"], (Iterable,))

        self.paras = paras
        self.storage = []

    def run(self):
        pass

    def get_lock(self):
        pass
