from abc import ABC, abstractmethod


class Strategy_Base(ABC):
    """
        缓存管理策略的基类

        要求实现：
            - notified_by_write_of_cache()
            - notified_by_read_of_cache()
            - notified_by_remove_of_cache()
            - notified_by_clear_of_cache()
            - 返回需要删除的条目的键的列表 suggest()
            - 清空所有内容 clear()
        等方法。

        其中 notified_by_xxx_of_cache 系列方法用于接受在 Cache_Manager 中的通讯，比如 notified_by_write_of_cache 方法
            将在 Cache_Manager 中每次调用 cache 的 write 方法时被调用。利用这些通讯接口，使得策略管理器可以提前追踪、感知条目的变化，
            从而进行一些预处理操作，以免在后续需要其提出重构建议时，才当场进行过大的计算量。
    """

    @abstractmethod
    def notified_by_write_of_cache(self, key, value, metadata):
        pass

    @abstractmethod
    def notified_by_read_of_cache(self, key, value, metadata):
        pass

    @abstractmethod
    def notified_by_remove_of_cache(self, key, metadata):
        pass

    @abstractmethod
    def notified_by_clear_of_cache(self):
        self.clear()

    @abstractmethod
    def suggest(self, refactor_size) -> list:
        """返回需要删除的条目的键的列表"""
        pass

    @abstractmethod
    def clear(self):
        pass
