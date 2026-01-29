from abc import ABC, abstractmethod
import os
import numpy as np
from kevin_toolbox.data_flow.core.reader import File_Iterative_Reader
from kevin_toolbox.data_flow.core.cache import Cache_Manager_for_Iterator


class Unified_Reader_Base(ABC):
    """
        按行读取数据的抽象基类
            支持通过对以
            - 内存变量
            - 持久化磁盘文件
            等多种方式保存的数据进行
            - 顺序读取
            - 随机读取

        几种读取方式之间，具有以下的优先级：
            1.内存变量
                直接用切片的方式从内存中读取。
                    相关参数：
                        var：      np.array with dtype=object
                优点：速度最快。
                缺点：内存占用大。（当数据过大无法一次性读取到内存中时，将使用下一种方法读取）
            2.持久化磁盘文件（二进制缓存）
                通过缓存管理器 Cache_Manager_for_Iterator 来进行读取
                    相关参数：
                        folder_path:    保存data的二进制缓存文件目录
                        chunk_size:     data块的大小
            3.持久化磁盘文件（数据文件）
                首先构建分批次读取文件内容的迭代器（默认使用 File_Iterative_Reader）
                然后通过适用于迭代器/生成器的缓存管理器 Cache_Manager_for_Iterator 来提高读取效率并支持随机读取。
                    相关参数：
                        file_path:      保存data的文件
                        folder_path:    保存data的二进制缓存文件目录（目录内容必须为空，否则报错）
                        chunk_size:     data块的大小
        需要实现的抽象方法：
            # 读取数据
            __get_file_iterative_reader( file_path, chunk_size )
                如何迭代读取文件到内存
                    要求返回一个迭代读取文件内容的生成器、迭代器（默认使用 File_Iterative_Reader）
            __get_cache_manager( iterator )
                （默认使用 Cache_Manager_for_Iterator）
            # 数据处理
            __deal_data( data )
                对输出前的数据进行什么处理

        数据流：
         __get_file_iterative_reader() ==> file_iterative_reader
                                                    ||
                     __get_cache_manager() ==> cache_manager
                                                    ||
                                             file =====>  file_data     var
                                                            ||          ||
                                                            ==============
                                                                    ||
                                                       __deal_data( data )
                                                                    ||
                                                                   outputs
    """

    def __init__(self, *args, **kwargs):
        """
            设定关键参数
            参数：
                var：      np.array with dtype=object
                folder_path:    保存data的二进制缓存文件目录
                file_path:      保存data的文件路径
                chunk_size:     data块的大小
                                    根据内存限制来自定义设定，默认为1k
            其他参数：

        """

        # 默认参数
        paras = {
            # 方式1
            "var": None,
            # 方式2、3
            "folder_path": None,
            "file_path": None,
            "chunk_size": 1000,
        }

        # 获取参数
        paras.update(kwargs)

        # 判断采用哪种方式
        mode = [key for key, value in {0: "var", 1: "folder_path", 2: "file_path"}.items() if
                paras.get(value, None) is not None]
        assert len(mode) > 0
        self.mode = min(mode)  # 优先选取第一种模式

        if self.mode != 0:
            # 校验参数
            paras["chunk_size"] = int(paras["chunk_size"])
            # 提前准备
            if paras["file_path"] is not None:
                assert os.path.isfile(paras["file_path"]), \
                    Exception(f"Error: file {paras['file_path']} not exists!")
                reader = self.get_file_iterative_reader(**paras)
            else:
                reader = None
            paras["manager"] = self.get_cache_manager(reader, paras["folder_path"])

        self.paras = paras

        # 其他变量
        self.index = -1

    # ------------------------------------ 读取数据 ------------------------------------ #

    @abstractmethod
    def get_file_iterative_reader(self, file_path, chunk_size, **kwargs):
        """
            如何迭代读取文件到内存
                要求返回一个按照 chunk_size 来迭代读取文件内容的生成器、迭代器（默认使用 File_Iterative_Reader）
        """
        reader = File_Iterative_Reader(file_path=file_path, chunk_size=chunk_size,
                                       drop=False, loop_num=1,
                                       convert_func=lambda x: np.array(x))
        return reader

    @abstractmethod
    def get_cache_manager(self, iterator, folder_path):
        """
            默认使用 Cache_Manager_for_Iterator
        """
        manager = Cache_Manager_for_Iterator(
            iterator=iterator, folder_path=folder_path,
            paras_for_memo_cache=dict(upper_bound=20, refactor_size=0.7, strategy=":by_last_time:LRU"))
        return manager

    def read(self, *args, **kwargs):
        if "begin" in kwargs or isinstance(args[0], (int,)):
            data = self.__read_continuously(*args, **kwargs)
        elif "id_ls" in kwargs or isinstance(args[0], (list,)):
            data = self.__read_discretely(*args, **kwargs)
        else:
            raise ValueError
        data = self.deal_data(data)

        return data

    def __read_continuously(self, begin, end=None, *args, **kwargs):
        """
            连续地读取某个区间 [begin, end)
        """
        end = begin + 1 if end is None else end
        assert begin < end

        if begin >= len(self):
            return np.array([])

        if self.mode == 0:
            data = self.paras["var"][begin:end]
        else:
            # 找出区间涉及的chunk
            chunk_ls = []
            chunk_id_beg = min(begin // self.paras["chunk_size"], max(len(self.paras["manager"]) - 1, 0))
            chunk_id_end = min(end // self.paras["chunk_size"] + 1, len(self.paras["manager"]))
            for chunk_id in range(chunk_id_beg, chunk_id_end):
                chunk_ls.append(self.paras["manager"].read(chunk_id))
            # 合并
            if len(chunk_ls) > 0:
                chunks = np.concatenate(chunk_ls, axis=0)
            else:
                chunks = np.array([])
            # 截取
            offset = begin - begin % self.paras["chunk_size"]
            data = chunks[begin - offset:end - offset]

        self.index = end - 1

        return data

    def __read_discretely(self, id_ls, *args, **kwargs):
        """
            离散地读取元素
        """
        assert max(id_ls) < len(self)

        if self.mode == 0:
            data = self.paras["var"][tuple(id_ls),]
        else:
            item_ls = [None] * len(id_ls)
            item_id_ls = np.array(id_ls)
            chunk_id_ls = item_id_ls // self.paras["chunk_size"]
            # 在涉及的chunk中，依次找出对应的 item
            for chunk_id in set(chunk_id_ls):
                chunk = self.paras["manager"].read(chunk_id)
                for i, (cid, iid) in enumerate(zip(chunk_id_ls, item_id_ls)):
                    if cid == chunk_id:
                        item_ls[i] = chunk[(iid % self.paras["chunk_size"],),]
            assert None not in item_ls, \
                Exception(f"Error: Unable to read the {item_ls.index(None)}th element!")
            # 合并
            data = np.concatenate(item_ls, axis=0)

        self.index = max(id_ls)

        return data

    # ------------------------------------ 查找数据 ------------------------------------ #

    def find(self, value, try_to_build_hash_table=True, beg_index=0):
        """
            查找元素第一次出现的序号。
                本次改进：
                原始版本中每次查找都是O(n)的，效率太低。
                因此加入通过hash表来支持检索的功能，从而将效率提高到O(1)。
            参数：
                value：              要检索的元素。
                beg_index:          从哪个序号（包含给定元素）开始检索。
                                        默认为0。
                try_to_build_hash_table:      尝试构建hash表，一次构建，后面可以反复利用，从而加速检索。
        """
        assert isinstance(beg_index, (int,)) and 0 <= beg_index < len(self), \
            f"beg_index should be integer between [0,{len(self)}), but get a {beg_index}!"

        # 尝试创建 hash 表
        if try_to_build_hash_table and "__hash_table" not in self.paras:
            try:
                self.index = -1
                hash_table = dict()
                for i, j in enumerate(self):
                    v = j[0]
                    if v not in hash_table:
                        hash_table[v] = [i]
                    else:
                        hash_table[v].append(i)
                self.paras["__hash_table"] = hash_table
                print("Hash table was successfully built.")
            except:
                print("Warn: Failed to build hash table!")

        if "__hash_table" in self.paras:
            index_ls = self.paras["__hash_table"].get(value, [])
            for index in index_ls:
                # 可以改成二分查找
                if beg_index <= index:
                    return index
        else:
            self.index = beg_index - 1
            for i, j in enumerate(self):
                if j == value:
                    return i
        return None

    # ------------------------------------ 数据处理 ------------------------------------ #

    @abstractmethod
    def deal_data(self, data):
        """
            对输出前的数据进行什么处理
        """
        return data

    # ------------------------------------ 其他 ------------------------------------ #

    # 迭代器，通过 next(self) 调用
    def __next__(self):
        if self.index < len(self) - 1:
            return self.read(self.index + 1)
        else:
            self.index = -1
            raise StopIteration

    # 支持 for 循环调用
    def __iter__(self):
        return self

    # 通过 len(self) 调用
    def __len__(self):
        if len(self.shape) > 0:
            return self.shape[0]
        else:
            return 0

    # self.shape
    @property
    def shape(self):
        if "shape" not in self.paras:
            if self.mode == 0:
                self.paras["shape"] = list(self.paras["var"].shape)
            else:
                if len(self.paras["manager"]) > 0:
                    last_chunk = self.paras["manager"].read(len(self.paras["manager"]) - 1)
                    shape = list(last_chunk.shape)
                    shape[0] += (len(self.paras["manager"]) - 1) * self.paras["chunk_size"]
                    self.paras["shape"] = shape
                else:
                    self.paras["shape"] = []
        return self.paras["shape"]
