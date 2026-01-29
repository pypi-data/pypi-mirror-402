import os
import pickle
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register()
class Pickle_(Backend_Base):
    name = ":pickle"

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        with open(os.path.join(self.paras["folder"], f'{name}.pkl'), 'wb') as f:
            pickle.dump(var, f)
        return dict(backend=Pickle_.name, name=name)

    def read(self, name, **kwargs):
        assert self.readable(name=name)

        with open(os.path.join(self.paras["folder"], f'{name}.pkl'), 'rb') as f:
            var = pickle.load(f)
        return var

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return True

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return os.path.isfile(os.path.join(self.paras["folder"], f'{name}.pkl'))


if __name__ == '__main__':
    import torch
    backend = Pickle_(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = torch.randn(100, device=torch.device("cuda"))
    print(backend.write(name=":a:b", var=a))

    b = backend.read(name=":a:b")
    print(b)
