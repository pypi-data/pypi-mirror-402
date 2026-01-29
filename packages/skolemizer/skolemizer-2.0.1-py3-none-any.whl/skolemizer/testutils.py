"""Utils for testing skolemized rdf nodes.

When creating unit tests of skolemized rdf nodes a uuid will be applied as a substring of the complete skolemization.
Therefore, in order to create stable unit tests one can use the testsutils in order to mock a stable skolemization.

E.g pytest-mock's MockFixture permits mocking of the skolemizer:

Example:
    >>> from pytest_mock import MockFixture
    >>> from skolemizer.testutils import skolemization
    >>>
    >>> catalog = Catalog()
    >>>
    >>> mocker.patch(
    >>>     "skolemizer.Skolemizer.add_skolemization",
    >>>     return_value=skolemization
    >>> )
"""

from typing import List, Union

from skolemizer import Skolemizer

uuid = "284db4d2-80c2-11eb-82c3-83e80baa2f94"
skolemization = Skolemizer.get_baseurl() + ".well-known/skolem/" + uuid

uuid2 = "21043186-80ce-11eb-9829-cf7c8fc855ce"
skolemization2 = Skolemizer.get_baseurl() + ".well-known/skolem/" + uuid2

uuid3 = "279b7540-80ce-11eb-ba1a-7fa81b1658fe"
skolemization3 = Skolemizer.get_baseurl() + ".well-known/skolem/" + uuid3


class SkolemUtils:
    """Testutils for mocking more than one skolemization."""

    skolemization_counter: int
    skolemizations: List

    def __init__(self) -> None:
        """Constructor."""
        self.skolemization_counter = 0
        self.skolemizations = [skolemization, skolemization2, skolemization3]

    def get_skolemization(self) -> Union[str, None]:
        """Pops a skolemization from a stack of max 3 test skolemizations."""
        if self.skolemization_counter == 3:
            return None

        _skolemization = self.skolemizations[self.skolemization_counter]
        self.skolemization_counter = self.skolemization_counter + 1

        return _skolemization
