from abc import ABC, abstractmethod


class Iterator_Base(ABC):

    @abstractmethod
    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self):
        value = 1
        return value
