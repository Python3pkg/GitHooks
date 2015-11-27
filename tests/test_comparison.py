import unittest

from tests.comparison import UnOrderedCollectionMatcher


class UnOrderedCollectionMatcherTestCase(unittest.TestCase):
    """Check if UnOrderedCollectionMatcher properly matches elements"""
    def test_equality(self):
        """Collection elements should be matched regardless of its ordering"""
        class Obj:
            """Non comparable object"""
            # pylint: disable=R0903
            def __init__(self, attr):
                self.attr = attr

            def __repr__(self):
                return '<Obj: attr={}>'.format(repr(self.attr))

        UnOrderedCollectionMatcher.register_equalityfunc(
            Obj,
            lambda x, y: x.attr == y.attr
        )

        equals = (
            [[Obj(1)], [Obj(1)]],
            [[Obj(1), Obj(2), Obj(3)], [Obj(1), Obj(2), Obj(3)]],
            [[Obj(1), Obj(2), Obj(3)], [Obj(2), Obj(3), Obj(1)]]
        )
        not_equals = (
            [[Obj(1)], [Obj(2)]],
            [[Obj(1), Obj(2), Obj(3)], [Obj(3), Obj(2)]],
            [[Obj(1), Obj(2)], [Obj(2), Obj(1), Obj(3)]]
        )
        for expected, actual in equals:
            expected = UnOrderedCollectionMatcher(expected)
            self.assertEqual(expected, actual)
        for expected, actual in not_equals:
            expected = UnOrderedCollectionMatcher(expected)
            self.assertNotEqual(expected, actual)
