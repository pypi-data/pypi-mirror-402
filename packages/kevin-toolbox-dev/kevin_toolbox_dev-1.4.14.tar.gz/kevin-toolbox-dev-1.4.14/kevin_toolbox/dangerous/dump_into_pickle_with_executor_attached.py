import os
import pickle
from kevin_toolbox.computer_science.data_structure import Executor


class Egg:
    """
        一个以 executor 为“蛋壳”，包裹着内容 var 的“鸡蛋”。
            在 pickle 模块对其进行“孵化”时，将会首先“执行”“蛋壳”，然后再获取其内容。
    """
    def __init__(self, executor, var=None):
        self.executor = executor
        self.var = var

    def __reduce__(self):
        """
            该函数系 pickle 供给用户用于指定反序列化的，将在 pickle 解释该对象时被自动执行
                https://docs.python.org/3/library/pickle.html
        """
        assert self.executor is not None

        func, args_, kwargs_ = self.executor.parse()

        return (eval, ("(func(*args_, **kwargs_), var)[-1]",
                       {"func": func, "args_": args_, "kwargs_": kwargs_, "var": self.var}),)


def dump_into_pickle_with_executor_attached(var, executor, output_path):
    """
        将输入的变量 var 打包成一个附带着 executor 的 pickle 文件

        何为附带着 executor 的 pickle 文件，它具有什么特性？
            - 读取/解释该 pickle 文件时，将自动触发并执行其附带的 executor。
                    executor 系 kevin_toolbox.computer_science.data_structure.Executor 的一个实例，
                    它允许你以静态方式描述并保存一个执行过程，然后在你需要的地方再进行调用。
            - 从该 pickle 文件读取得到的结果，与普通地将 var 保存成 pickle 文件读取得到的结果完全一致。

            警告！ 该函数并不对 executor 的执行内容负责，因此可能产生对执行环境危害性极大的 pickle 文件！

            比如：
                import os
                from kevin_toolbox.computer_science.data_structure import Executor

                # 创建一个 executor，执行它会调用命令在用户目录下创建一个文件（这个命令也可以换成任何更加危险的命令，小朋友不要学坏哦）
                executor = Executor(func=os.system, args=["touch ~/test.txt"])
                build_pickle_to_run(executor, output_path="~/egg")

            然后在另一个进程中尝试读取该 pickle 文件：
                import pickle

                pickle.load(open("~/egg","rb"))
            它将会自动执行前面的 executor。

        参数：
            var:                需要被打包的变量
            executor:           <Executor> 需要打包的执行器
            output_path:        <str> 输出 pickle 文件的保存路径
    """
    assert isinstance(executor, (Executor,))

    egg = Egg(executor=executor, var=var)

    os.makedirs(os.path.split(output_path)[0], exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(egg, f)
