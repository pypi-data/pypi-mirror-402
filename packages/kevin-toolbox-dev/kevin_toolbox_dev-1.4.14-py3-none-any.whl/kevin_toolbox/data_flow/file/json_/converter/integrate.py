def integrate(converters):
    """
        将 converters 整合为一个 converter
    """

    def wrap(x):
        if callable(converters):
            x = converters(x)
        elif isinstance(converters, (list, tuple,)):
            for converter in converters:
                assert callable(converter)
                x = converter(x)
        return x

    return wrap
