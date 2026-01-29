import types
import unittest
from typing import *

from iterflat.core import iterflat


class TestIterflat(unittest.TestCase):
    def test_depth_1_flattens_one_level(self: Self) -> None:
        data: list
        data = [[1, 2], [3], []]
        self.assertEqual(list(iterflat(data, depth=1)), [1, 2, 3])

    def test_depth_2_flattens_two_levels(self: Self) -> None:
        data: list
        data = [[[1], [2, 3]], [[4]], []]
        self.assertEqual(list(iterflat(data, depth=2)), [1, 2, 3, 4])

    def test_inv(self: Self) -> None:
        data: list
        data = [[[1], [2, 3]], [[4]], []]
        for n in range(5):
            self.assertEqual(list(iterflat(iterflat(data, depth=-n), depth=n)), data)

    def test_depth_0_iterates_input(self: Self) -> None:
        data: tuple
        data = (1, 2, 3)
        self.assertEqual(list(iterflat(data, depth=0)), [1, 2, 3])

    def test_depth_minus_1_yields_data_as_single_element(self: Self) -> None:
        data: list
        out: list
        data = [1, 2, 3]
        out = list(iterflat(data, depth=-1))
        self.assertEqual(out, [data])  # data yielded as a single item

    def test_depth_less_than_minus_1_wraps_again(self: Self) -> None:
        data: list
        inner: list
        out: list
        data = [1, 2]
        out = list(iterflat(data, depth=-2))
        # Should yield exactly one element, which itself is a generator
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], types.GeneratorType)
        # Iterating that inner generator should give [data]
        inner = list(out[0])
        self.assertEqual(inner, [data])

    def test_supports_index_custom_type(self: Self) -> None:
        class DepthLike:
            def __index__(self: Self) -> int:
                return 1  # act like depth=1

        data: list
        data = [[10], [20, 30]]
        self.assertEqual(list(iterflat(data, depth=DepthLike())), [10, 20, 30])

    def test_generator_input_with_depth_0(self: Self) -> None:
        def gen():
            for i in range(3):
                yield i

        self.assertEqual(list(iterflat(gen(), depth=0)), [0, 1, 2])

    def test_strings(self: Self) -> None:
        # depth=0 iterates the string
        self.assertEqual(list(iterflat("ab", depth=0)), ["a", "b"])
        # depth=-1 treats the whole string as a single element
        self.assertEqual(list(iterflat("ab", depth=-1)), ["ab"])
        # depth=1 over a list of strings flattens one level into characters
        self.assertEqual(list(iterflat(["ab", "c"], depth=1)), ["a", "b", "c"])

    def test_type_error_when_nested_item_not_iterable_for_positive_depth(
        self: Self,
    ) -> None:
        # For depth=1, inner items must be iterable; ints are not, so this should raise
        with self.assertRaises(TypeError):
            list(iterflat([1, 2], depth=1))

    def test_empty_input(self: Self) -> None:
        self.assertEqual(list(iterflat([], depth=0)), [])
        self.assertEqual(list(iterflat([], depth=1)), [])
        self.assertEqual(list(iterflat([], depth=2)), [])

    def test_large_depth_exact(self: Self) -> None:
        # Perfectly nested 3 levels
        data: list
        data = [[[[1], [2]], [[3]]]]
        self.assertEqual(list(iterflat(data, depth=3)), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
