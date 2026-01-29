from abc import ABC, abstractmethod


class Sequence_Map_Base(ABC):

    @abstractmethod
    def __getitem__(self, item):
        return self[item]

    @abstractmethod
    def __len__(self):
        return len(self)
