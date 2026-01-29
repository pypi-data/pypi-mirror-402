import os
import time
import importlib.util
from kevin_toolbox.computer_science.algorithm.decorator import restore_original_work_path
from kevin_toolbox.computer_science.algorithm.cache_manager import Cache_Manager

if importlib.util.find_spec("cPickle") is not None:
    # 如果安装有 cPickle，可以更快处理串行化
    import cPickle as pickle
else:
    import pickle


class Cache_Manager_for_Iterator:
    """
        适用于迭代器/生成器的缓存管理器
            通过构建基于磁盘的缓存（首先迭代读取迭代器/生成器的内容，并将这些块 chunk 分别保存为二进制文件）
            以及基于内存的缓存（然后在内存中开辟出一个缓存列表空间，用于保存最常调用的 chunk）
            来加速 迭代器/生成器 内容的读取

        工作流程：
            首先构建基于磁盘的缓存，将分块读取到数据保存为二进制文件；
                相关变量：
                    iterator:       迭代器/生成器
                    folder_path:    保存二进制文件的路径
                                        默认保存在 ./temp/cache_name/ 下
                                        当给定的 folder_path 内容不为空时，将尝试直接构建 file_dict
                    file_dict:      二进制文件的文件名与序号的对应关系表
                                        例如：{ 0: "0.pkl", 1: "1.pkl", 2: "2.pkl", ...}
                                        其中 index 0 对应于文件 ./temp/cache_name/0.pkl
            然后在进行读取时，将先到基于内存的缓存 memo_cache_manager 中寻找是否已经有需要的 chunk 分块，如果没有则到前面 file_dict 中读取，同时更新 memo_cache_manager
                相关变量：
                    memo_cache_manager： 基于内存的缓存，由 Cache_Manager 构建，指定有更新策略等
                                        其中 key 是 chunk 分块的 index，value 是对应的保存在内存中的变量

        支持以下几种方式来：
            以迭代器的形式进行顺序读取
            以指定序号的形式进行随机读取
    """

    def __init__(self, **kwargs):
        """
            设定关键参数
            参数：
                iterator:               迭代器/生成器
                folder_path:            <path> 构建基于磁盘的缓存时，保存二进制文件的路径
                paras_for_memo_cache：   <dict> 构建基于内存的缓存的参数
            其他参数：
                b_strict_mode:          <boolean> 禁止同时设置 iterator 和给定一个非空的 folder_path
                                            默认为 True 开启，此时同时设置将报错。
                                            当设置为 False 时，同时设置将以 folder_path 中的二进制文件为准
                b_del_cache_when_exit:  <boolean> 退出时删除生成的缓存二进制文件
                                            只有在设置了 iterator 的前提下，才会触发。
                                            （对于非本实例生成的文件，比如只给定了非空的 folder_path，不做删除。）
                                            默认为 True 开启。
        """

        # 默认参数
        paras = {
            "iterator": None,
            "folder_path": None,
            "paras_for_memo_cache": dict(upper_bound=20, refactor_size=0.7, strategy=":by_last_time:LRU",
                                         cache=":in_memory:Memo"),
            "b_strict_mode": True,
            "b_del_cache_when_exit": True,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        # paras_for_memo_cache
        assert isinstance(paras["paras_for_memo_cache"], (dict,))
        paras["paras_for_memo_cache"]["strategy"] = ":by_last_time:LRU"
        # 同时非空
        b_folder_not_empty = isinstance(paras["folder_path"], (str,)) and paras[
            "folder_path"] is not None and os.path.exists(paras["folder_path"]) and len(
            os.listdir(paras["folder_path"])) > 0
        if paras["iterator"] is not None and b_folder_not_empty:
            # iterator 非空，folder_path 非空
            if paras["b_strict_mode"]:
                # 不能同时设置
                raise Exception(f"Error: folder_path and iterator cannot be set at the same time\n"
                                f"iterator {paras['iterator']} is given when "
                                f"there is already content in folder_path {paras['folder_path']}!")
            else:
                # 以 folder_path 为准
                paras["iterator"] = None
        # 同时为空
        if paras["iterator"] is None and paras["folder_path"] is None:
            raise Exception(f"Error: folder_path and iterator cannot be empty at the same time\n"
                            f"both iterator and folder_path are not given!")

        # 构建基于磁盘的缓存
        file_dict = dict()
        if paras["iterator"] is not None:
            # 根据 iterator 生成
            if paras["folder_path"] is None:
                paras["folder_path"] = os.path.join(os.getcwd(), "temp", str(time.time()))
            if not os.path.exists(paras["folder_path"]):
                os.makedirs(paras["folder_path"])
            file_dict = self.generate_chuck_files(paras["iterator"], paras["folder_path"])
        elif b_folder_not_empty:
            # 尝试直接根据已有文件构建 file_dict
            file_dict = self.find_chuck_files(paras["folder_path"])

        # 构建基于内存的缓存
        self.memo_cache_manager = Cache_Manager(**paras["paras_for_memo_cache"])

        self.file_dict = file_dict
        self.paras = paras

        # 记录最后读取的index
        self.index = -1

    # ------------------------------------ 基于磁盘的缓存 ------------------------------------ #

    @staticmethod
    @restore_original_work_path
    def generate_chuck_files(iterator, folder_path):
        """
            构建基于磁盘的缓存
                将 iterator 每次迭代产生的结果以二进制文件的形式（文件名为 {index}.pkl）保存到 folder_path 指向的目录中，
                并将这些文件名保存到索引 file_dict
        """
        os.chdir(folder_path)
        file_dict = dict()
        for i, chuck in enumerate(iterator):
            file_name = f"{i}.pkl"
            with open(file_name, 'wb') as f:
                pickle.dump(chuck, f)
            file_dict[i] = file_name
        return file_dict

    @staticmethod
    @restore_original_work_path
    def find_chuck_files(folder_path):
        """
            建立到磁盘缓存的索引
                从 folder_path 中找到已有的二进制文件，并将这些文件名保存到索引 file_dict
        """
        os.chdir(folder_path)
        file_dict = dict()
        count = 0
        while True:
            file_name = f"{count}.pkl"
            if os.path.isfile(file_name):
                file_dict[count] = file_name
            else:
                break
            count += 1
        return file_dict

    def __read_from_files(self, index):
        """
            从磁盘中读取
                根据 index 到索引 file_dict 中找出对应的文件名，然后读取文件
        """
        file_path = os.path.join(self.paras["folder_path"], self.file_dict[index])
        with open(file_path, 'rb') as f:
            chunk = pickle.load(f)
        return chunk

    # ------------------------------------ 读取 ------------------------------------ #

    def read(self, index):
        assert 0 <= index < len(self), \
            KeyError(f"Error: index {index} not in [0, {len(self)})")
        if self.memo_cache_manager.has(key=index):
            # 直接从内存中读取
            chunk = self.memo_cache_manager.get(key=index)
        else:
            # 到磁盘读取
            chunk = self.__read_from_files(index)
            # 添加到缓存
            self.memo_cache_manager.add(key=index, value=chunk)
        self.index = index
        return chunk

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
        return len(self.file_dict)

    def __del__(self):
        if self.paras["iterator"] is not None and self.paras["b_del_cache_when_exit"] and self.paras["b_strict_mode"]:
            # 在 b_strict_mode 开启，且 iterator 非空的情况下 self.file_dict 中的二进制文件一定是根据 iterator 生成的
            # 删除文件
            pwd_bak = os.getcwd()
            os.chdir(self.paras["folder_path"])
            for key, value in self.file_dict.items():
                os.remove(value)
            os.chdir(pwd_bak)
            # 删除空文件夹
            if not os.listdir(self.paras["folder_path"]):
                os.removedirs(self.paras["folder_path"])


if __name__ == '__main__':
    "测试 Cache_Manager_for_Iterator"
    cache_manager = Cache_Manager_for_Iterator(
        iterator=range(10),
        b_del_cache_when_exit=True,
        paras_for_memo_cache=dict(upper_bound=3, refactor_size=3, strategy=":by_last_time:LRU")
    )
    print(cache_manager.file_dict)
    print(cache_manager.memo_cache_manager.metadata_s)
    for i in range(3):
        print(cache_manager.read(0))
    for i in range(2):
        print(cache_manager.read(3))
    for i in range(1):
        print(cache_manager.read(6))
    for i in range(4):
        print(cache_manager.read(9))
    print(cache_manager.memo_cache_manager.metadata_s)
