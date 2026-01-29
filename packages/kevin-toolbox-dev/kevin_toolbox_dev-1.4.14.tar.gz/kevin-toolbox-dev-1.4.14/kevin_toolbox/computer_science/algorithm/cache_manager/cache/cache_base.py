from abc import ABC, abstractmethod


class Cache_Base(ABC):
    """
        缓存结构的基类

        要求实现：
            - 读取 _read_freely()
            - 写入 _write_freely()
            - 清除单个条目 _remove_freely()
            - 判断是否命中 has()
            - 获取缓存已占空间 len()
            - 清空所有内容 clear()
            - 加载和保存状态 load_state_dict(), state_dict()
        等方法。

        对外提供：
            - 只读取已有条目 read()
            - 只写入不存在条目 write()
            - 只清除已存在的单个条目 remove()
            - 判断是否命中 has()
            - 获取缓存已占空间 len()
            - 清空所有内容 clear()
            - 加载和保存状态 load_state_dict(), state_dict()
        等接口。
    """

    def read(self, key):
        """只允许读取已存在的条目"""
        if self.has(key=key):
            return self._read_freely(key=key)
        else:
            raise KeyError(f"key {key} not found")

    def write(self, key, value):
        """只允许写入不已存在的条目"""
        if not self.has(key=key):
            self._write_freely(key=key, value=value)
        else:
            raise KeyError(f"key {key} already exists")

    def remove(self, key):
        """只允许删除已存在的条目"""
        if self.has(key=key):
            self._remove_freely(key=key)
        else:
            raise KeyError(f"key {key} not found")

    @abstractmethod
    def _read_freely(self, key):
        pass

    @abstractmethod
    def _write_freely(self, key, value):
        pass

    @abstractmethod
    def _remove_freely(self, key):
        pass

    @abstractmethod
    def has(self, key) -> bool:
        pass

    @abstractmethod
    def len(self) -> int:
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def load_state_dict(self, state_dict):
        pass

    @abstractmethod
    def state_dict(self, b_deepcopy=True):
        pass

    def __getitem__(self, key):
        # self[key]
        return self.read(key=key)

    def __setitem__(self, key, value):
        # self[key] = value
        self.write(key=key, value=value)

    def __contains__(self, key):
        # if key in self:
        #     return True
        # else:
        #     return False
        return self.has(key=key)

    def __len__(self):
        # len(self)
        return self.len()
