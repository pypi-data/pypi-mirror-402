from typing import Tuple


class MathTup:

    def __init__(self, tup: Tuple[float, float]):
        self.tuple = tup

    @property
    def x(self):
        return self.tuple[0]

    @property
    def y(self):
        return self.tuple[1]

    @staticmethod
    def __get_tup(obj2):
        if isinstance(obj2, MathTup):
            return obj2.tuple
        elif isinstance(obj2, tuple):
            return obj2
        raise Exception("No Tuple")

    def __add__(self, obj2):
        other_tup = self.__get_tup(obj2)
        this_tup = self.tuple
        return MathTup((this_tup[0] + other_tup[0], this_tup[1] + other_tup[1]))

    def __sub__(self, obj2):
        other_tup = self.__get_tup(obj2)
        this_tup = self.tuple
        return MathTup((this_tup[0] - other_tup[0], this_tup[1] - other_tup[1]))

    def __eq__(self, obj2):
        return self.tuple == self.__get_tup(obj2)

    def __neg__(self):
        return MathTup((-self.tuple[0], -self.tuple[1]))

    def __str__(self):
        return str(self.tuple)

    def __mul__(self, other):
        if isinstance(other, (float, int)):
            return MathTup((self.x * other, self.y * other))
        raise Exception(f"Cannot multiply with {type(other)}")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __getitem__(self, index):
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError


def main():
    print(MathTup((1, 2)) + MathTup((3, 4)))
    print(MathTup((1, 1)) * 10)


if __name__ == "__main__":
    main()
