import os
import copy
import numpy as np
import warnings
from kevin_toolbox.data_flow.file.kevin_notation.converter import Converter, CONVERTER_FOR_WRITER
from kevin_toolbox.data_flow.file import kevin_notation

if getattr(np, "VisibleDeprecationWarning", None) is not None:
    warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)


class Kevin_Notation_Writer:
    """
        遵守 kevin_notation 格式的数据文本写入器（格式要求参见本模块下的 readme）
            支持分批次向文件写入内容
    """

    def __init__(self, **kwargs):
        """
            设定关键参数

            必要参数：
                file_path:          <string> 文件路径
            写入相关参数：
                mode:               <string> 写入模式
                                        支持以下模式：
                                            "w":    从头开始写入
                                            "a":    从末尾续写（要求文件已经具有 metadata）
                paras_for_open:     <paras dict> open() 函数的补充参数（除 mode 以外）
                converter:          <instance of kevin_toolbox.Converter> converter is a dictionary-like data structure
                                            consisting of <string>:<func> pairs，
                                            用于根据指定数据类型选取适当的函数来处理输入数据。
                sep：                <string> 默认的分隔符
                                            默认使用 \t
                comment_flag：       <string> 默认的注释标志符
                                            默认为 None，表示不支持使用注释。
                                            建议使用 \\ 作为注释标志符

            工作流程：
                                               __init__(mode="w") ──► stage=0 ──► metadata_begin()
                                                                                         │
                                                                                         ▼
                   write_metadata(key, value) or writer.metadata=dict(key=value) ◄───► stage=1
                                                                                         │
                                                                                         ▼
                                                 contents_begin() ◄── stage=2 ◄── metadata_end()
                                                        │
                                                        ▼
                              __init__(mode="a") ──► stage=3 ◄───► write_contents(value) or writer.contents=value
                                                        │
                                                        ▼
                                                  contents_end() ───► stage=4

        """

        # 默认参数
        paras = {
            # 必要参数
            "file_path": None,
            # 写入模式相关参数
            "mode": "w",
            "paras_for_open": dict(encoding='utf-8'),
            # 可选参数
            "converter": CONVERTER_FOR_WRITER,
            "sep": "\t",
            "comment_flag": None
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        #
        paras["file_path"] = os.path.abspath(paras["file_path"])
        os.makedirs(os.path.split(paras["file_path"])[0], exist_ok=True)
        #
        assert paras["mode"] in ["w", "a"]
        #
        assert isinstance(paras["paras_for_open"], (dict,))
        paras["paras_for_open"]["mode"] = paras["mode"]
        #
        assert isinstance(paras["converter"], (Converter, dict,))
        assert isinstance(paras["sep"], (str,))
        assert isinstance(paras["comment_flag"], (str, type(None)))

        self.paras = paras

        # metadata
        self.metadata = dict()
        # 文件对象
        self.file = None

        if paras["mode"] == "a":
            # 采用追加写模式
            # 尝试打开已有文件
            assert os.path.isfile(self.paras["file_path"])
            try:
                # 要求 metadata 已被写入
                reader = kevin_notation.Reader(file_path=self.paras["file_path"])
            except Exception as e:
                raise Exception(
                    f'file {self.paras["file_path"]} existed, but is not a standard kevin_toolbox document!')
            self.metadata = copy.deepcopy(reader.metadata)
            del reader
            # 获取文件对象
            self.file = open(self.paras["file_path"], **self.paras["paras_for_open"])
            # 初始状态码
            beg_stage = 3
        else:
            # 采用覆盖写模式
            self.metadata["sep"] = self.paras["sep"]
            self.metadata["comment_flag"] = self.paras["comment_flag"]
            # 获取文件对象
            self.file = open(self.paras["file_path"], **self.paras["paras_for_open"])
            # 写入文件标记
            self.file.write(f"# --kevin_notation--\n\n")
            # 初始状态码
            beg_stage = 0

        # 变量
        # state 状态码
        #   0：关闭所有写操作
        #   1：正在写 metadata
        #   2：正在写 contents
        self.state = dict(stage=beg_stage)

    # ------------------------------------ metadata ------------------------------------ #

    def metadata_begin(self):
        # 流程检查
        assert self.state["stage"] == 0, \
            f'Error: need to invoke __init__(mode="w") first!'
        self.state["stage"] = 1

        self.file.write(f"# --metadata--\n")
        self._write_metadata("sep", self.paras["sep"])
        if self.paras["comment_flag"] is not None:
            self._write_metadata("comment_flag", self.paras["comment_flag"])
        self.file.flush()

    def _write_metadata(self, key, value):
        """
            通过键值对的形式写入一个 metadata

            参数：
                key：            键
                value：          值/值以及该键值对的其他信息。
                                    支持两种方式指定:
                                        <list or tuple> 直接指定 value 的值，写入方式参考默认值
                                        <dict> 一个包含 value 以及额外指定写入方式参数的字典
                                            {"value": <list or tuple>, "sep": ..., }
        """
        paras = dict()
        if isinstance(value, (dict,)):
            assert "value" in value
            paras = value
            value = paras.pop("value")
        elif not isinstance(value, (list, tuple,)):
            value = [value]
        assert isinstance(value, (list, tuple,))
        #
        sep = paras.get("sep", self.paras['sep'])
        assert isinstance(sep, (str,))

        # check
        if "column_num" in self.metadata:
            if key in ["column_name", "column_type"]:
                assert len(value) == self.metadata["column_num"]

        # write
        # key
        self.file.write(f"# {key}")
        if len(paras) > 0:
            self.file.write(f" ({','.join([f'{k}={v}' for k, v in paras.items()])})")
        self.file.write(f"\n")
        # value
        self.file.write(f"{sep.join([f'{v}' for v in value])}\n")

        # metadata
        value = list(value)
        self.metadata[key] = value[0] if len(value) == 1 and key not in ["column_name", "column_type"] else value
        #
        if key in ["column_name", "column_type"]:
            self.metadata["column_num"] = len(value)
        self.file.flush()

    def write_metadata(self, **kwargs):
        """
            写入 metadata（供外部调用）

            支持两种方式进行写入：
                write_metadata(key, value)
                write_metadata(metadata)    其中 metadata 是包含多组 key,value 的 dict。等效于多次调用第一种方式进行写入。

            注意，由于对默认分隔符的设定和写入已经在一开始的初始化和 metadata_begin() 时完成了，因此本函数将直接跳过/忽略 key="sep" 的情况。
        """
        # 流程检查
        if self.state["stage"] == 0:
            self.metadata_begin()
        assert self.state["stage"] == 1, \
            Exception(f"Error: please call metadata_begin() before _write_metadata!")

        paras = kwargs

        if "metadata" in paras:
            assert isinstance(paras["metadata"], (dict,))
            for key, value in paras["metadata"].items():
                if key != "sep":
                    self._write_metadata(key=key, value=value)
        elif "key" in paras:
            assert isinstance(paras["key"], (str,)) and "value" in paras
            if paras["key"] != "sep":
                self._write_metadata(key=paras["key"], value=paras["value"])
        else:
            raise ValueError("Requires parameter 'key, value' or 'metadata'")

    def metadata_end(self):
        # 流程检查
        assert self.state["stage"] == 1
        self.state["stage"] = 2

        self.file.write(f"\n")
        self.file.flush()

    # ------------------------------------ contents ------------------------------------ #

    def contents_begin(self):
        # 流程检查
        assert self.state["stage"] == 2, \
            f"Error: need to close the last metadata writing!"
        self.state["stage"] = 3

        self.file.write(f"# --contents--\n")
        self.file.flush()

    def _write_contents(self, row_ls):
        """
            通过 row_ls 以行的形式写入 contents

            参数：
                row_ls：          <list / list of list/tuple>  一行、或者多行的内容，将按照内部保存的 column_type 进行转换。
        """
        if len(row_ls) == 0:
            return

        row_ls = np.array(row_ls)
        if row_ls.ndim <= 1:
            row_ls = row_ls.reshape((1, -1))

        if "column_num" in self.metadata:
            assert row_ls.shape[-1] == self.metadata["column_num"], \
                f"{row_ls.shape}"

        # 转换并写入
        if "column_type" in self.metadata:
            type_ls = self.metadata["column_type"]
        else:
            type_ls = ["default"] * len(row_ls.shape[-1])

        for row in row_ls:
            row = [self.paras["converter"][type_](r) for type_, r in zip(type_ls, row)]
            line = f"{self.metadata['sep'].join(row)}\n"
            self.file.write(line)
        self.file.flush()

    def write_contents(self, **kwargs):
        """
            写入 contents（供外部调用）

            参数：
                row_ls:                     <list / list of list/tuple>  按 行 组织的待写入内容
                                                例如：
                                                    多行：
                                                        [[0, 0.96, "variational"],
                                                         [1, 0.56, "formal"],
                                                         ...]
                                                    单行：
                                                        [0, 0.96, "variational"]
                                                将按照在列表中顺序进行解释，
                                                使用内部保存的 column_type=["int","float","str"] 进行转换。
                column_dict:                <dict of key:column_name value:list> 按 列 组织的待写入内容
                                                例如：
                                                    多行：
                                                        {
                                                            "epoch": [0, 1, ...],
                                                            "acc": [0.96, 0.56, ...],
                                                            "conv_type": ["variational", "formal", ...],
                                                        }
                                                    单行：
                                                        { "epoch": 0, "acc": 0.96, "conv_type": "variational" }
                                                按照内部保存的 column_name=["epoch","acc","conv_type"] 进行解释，
                                                使用内部保存的 column_type=["int","float","str"] 进行转换。
                            以上两种参数分别对应着两种方式，二选一即可：
                                write_contents(row_ls)
                                write_contents(column_dict)
                b_single_line:              <boolean> 强制使用单行来解释。
                                                默认不指定，此时将依次尝试多行和单行模式进行写入。
                            建议指定。
        """
        # 流程检查
        if self.state["stage"] == 1:
            self.metadata_end()
        if self.state["stage"] == 2:
            self.contents_begin()
        assert self.state["stage"] == 3, \
            Exception(f"Error: please call contents_begin() before write_contents!")

        paras = kwargs

        if "row_ls" in paras:
            try:
                # 解释为多行
                assert paras.get("b_single_line", None) in (None, False)
                self._write_contents(row_ls=paras["row_ls"])
            except:
                # 解释为单行
                assert paras.get("b_single_line", None) in (None, True)
                self._write_contents(row_ls=[paras["row_ls"]])
        elif "column_dict" in paras:
            assert isinstance(paras["column_dict"], (dict,))
            try:
                # 解释为多行
                assert paras.get("b_single_line", None) in (None, False)
                temp = [len(paras["column_dict"][k]) for k in self.metadata["column_name"]]
                if temp:
                    assert max(temp) == min(temp), f"Error: the length of each column is not equal!"
                row_ls = list(zip(*[paras["column_dict"][k] for k in self.metadata["column_name"]]))
            except:
                # 解释为单行
                assert paras.get("b_single_line", None) in (None, True)
                row_ls = [[paras["column_dict"][k] for k in self.metadata["column_name"]], ]
            self._write_contents(row_ls=row_ls)
        else:
            raise ValueError("Requires parameter 'row_ls' or 'column_dict'")

    def contents_end(self):
        # 流程检查
        assert self.state["stage"] == 3
        self.state["stage"] = 4

        self.file.flush()

    # ------------------------------------ magic func ------------------------------------ #

    # self.key = value
    def __setattr__(self, key, value):
        """
            支持直接通过 self.key = value 的方式来写入 metadata 和 contents
                （不建议使用该方式）
        """
        if "state" not in self.__dict__:
            # state 未被设置，未完成初始化
            super().__setattr__(key, value)
        else:
            if self.state["stage"] == 1:
                if key == "metadata":
                    self.write_metadata(metadata=value)
                else:
                    self.write_metadata(key=key, value=value)
            elif self.state["stage"] == 3:
                if key.endswith("single_line"):
                    b_single_line = True
                elif key.endswith("multi_line"):
                    b_single_line = False
                else:
                    b_single_line = None
                #
                if key.startswith("row_ls"):
                    self.write_contents(row_ls=value, b_single_line=b_single_line)
                elif key.startswith("column_dict"):
                    self.write_contents(column_dict=value, b_single_line=b_single_line)
                else:  # 兼容旧版本
                    warnings.warn(
                        f"Writing to contents with keys named other than row_ls and column_dict "
                        f"will no longer be supported in a future release", DeprecationWarning)
                    try:
                        self.write_contents(row_ls=value, b_single_line=b_single_line)
                    except:
                        self.write_contents(column_dict=value, b_single_line=b_single_line)
            else:
                raise ValueError(f"Error: please call metadata_begin() or contents_begin() before write!")

    # with 上下文管理器
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self

    def __del__(self):
        try:
            del self.paras, self.state
            self.file.close()
        except Exception as e:
            print(e)
