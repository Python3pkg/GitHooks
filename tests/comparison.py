"""Class that helps compare unordered collections"""


class UnOrderedCollectionMatcher:
    """Compare two unordered collections"""
    _comparers = {}

    def __init__(self, expected):
        """Set expected value"""
        self.expected = expected

    def __eq__(self, actual):
        actual_in_expected = set()
        expected_not_actual = set()
        for each_expected in self.expected:
            for each_actual in actual:
                if each_actual in actual_in_expected:
                    continue
                if self.equals(each_expected, each_actual):
                    actual_in_expected.add(each_actual)
                    break
            else:
                expected_not_actual.add(each_expected)
        actual_not_expected = set(actual) - actual_in_expected

        if expected_not_actual:
            return False
        if actual_not_expected:
            return False
        return True

    def __repr__(self):
        return repr(self.expected)

    @classmethod
    def equals(cls, expected, actual):
        """Check if two objects are equal"""
        if type(expected) is not type(actual):
            return False
        try:
            comparer = cls._comparers[type(expected)]
            return comparer(expected, actual)
        except KeyError:
            raise ValueError(
                'Comparison of {} is not supported'.format(type(expected))
            )

    @classmethod
    def register_equalityfunc(cls, type_, equalityfunc):
        """Register equality checker function

        Register function which checks if two object of specified type are
        equal.
        """
        cls._comparers[type_] = equalityfunc
