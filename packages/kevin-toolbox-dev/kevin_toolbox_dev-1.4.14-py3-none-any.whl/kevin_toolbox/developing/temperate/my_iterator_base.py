from abc import ABC, abstractmethod
from .sequence_map_base import Sequence_Map_Base
from .iterator_base import Iterator_Base


class My_Iterator_Base(Sequence_Map_Base, Iterator_Base):
    """
        Iterator + Generator 的“pro”版本
            支持 iter(self) 迭代
                self.set_range(beg,end) 设定迭代起点、终点
                self.pass_by(num)    跳过若干个值
            支持 self[index] 取值、len(self) 获取长度属性
    """

    # def __init__(self):
    #     self.beg, self.end, self.index = 0, 0, 0

    @abstractmethod
    def set_range(self, beg, end):
        # self.beg = beg
        # self.end = end
        pass

    @abstractmethod
    def pass_by(self, num):
        # self.index += num
        pass

    @staticmethod
    def round_by_range(beg, end, offset):
        """
            返回 index = beg + offset
        """
        assert isinstance(offset, (int,)), \
            TypeError(f"indices must be integers, not {type(offset)}")
        offset = offset if offset >= 0 else end - beg + offset
        assert 0 <= offset < end - beg, \
            IndexError(f"index {offset} out of range [{0},{end - beg})")
        return beg + offset
