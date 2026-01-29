from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register(name=":skip:simple")
class Skip_Simple(Backend_Base):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.w_cache_s = dict(able=None, id_=None)

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)
        return var

    def read(self, name, **kwargs):
        raise Exception(f'calling skip.read() is prohibited')

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        if id(var) != self.w_cache_s["id_"]:
            self.w_cache_s["able"] = False
            if isinstance(var, (int, float, str, type(None))):
                self.w_cache_s["able"] = True
            elif isinstance(var, (tuple,)):
                self.w_cache_s["able"] = all(isinstance(i, (int, float, str, type(None))) for i in var)
            self.w_cache_s["id_"] = id(var)
        return self.w_cache_s["able"]

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return False


if __name__ == '__main__':
    import os

    backend = Skip_Simple(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = None
    print(backend.write(name=":a:b", var=a))

    b = backend.read(name=":a:b")
    print(b)
