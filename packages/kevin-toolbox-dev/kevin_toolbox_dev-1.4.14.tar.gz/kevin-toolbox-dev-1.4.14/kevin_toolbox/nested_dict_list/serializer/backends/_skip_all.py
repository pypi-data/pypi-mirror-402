from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register(name=":skip:all")
class Skip_All(Backend_Base):

    def write(self, name, var, **kwargs):
        return var

    def read(self, name, **kwargs):
        raise Exception(f'calling skip.read() is prohibited')

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return True

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return False


if __name__ == '__main__':
    import os

    backend = Skip_All(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = 100
    print(backend.write(name=":a:b", var=a))

    b = backend.read(name=":a:b")
    print(b)
