import unittest
from collections.abc import MutableMapping, MutableSequence, MutableSet
from typing import *

import datahold


class TestDataholdGenerics(unittest.TestCase):
    def _assert_is_generic(
        self: Self,
        cls: type,
        n_type_params: int,
    ) -> None:
        """
        Helper: assert that `cls[...]` works and that typing.get_origin/get_args
        see it as a proper generic alias of `cls`.
        """
        sample_types: tuple[type]
        params: tuple[type]
        alias: Any
        origin: Any
        args: Any
        exc: BaseException
        # Pick some arbitrary distinct types for the parameters
        sample_types = (int, str, float, bytes)

        params = sample_types[:n_type_params]
        try:
            alias = cls[params if n_type_params > 1 else params[0]]
        except TypeError as exc:  # not subscriptable ⇒ not generic
            self.fail(f"{cls.__name__} is not generic: {exc!r}")

        origin = get_origin(alias)
        args = get_args(alias)

        self.assertIs(
            origin,
            cls,
            f"get_origin({cls.__name__}[...]) is {origin!r}, expected {cls!r}",
        )
        self.assertEqual(
            args,
            params,
            f"get_args({cls.__name__}[...]) is {args!r}, expected {params!r}",
        )

    # --- Data* ---

    def test_DataDict_is_generic_and_mapping(self: Self) -> None:
        self._assert_is_generic(datahold.DataDict, 2)
        self.assertTrue(
            issubclass(datahold.DataDict, MutableMapping),
            "DataDict should subclass collections.abc.MutableMapping",
        )

    def test_DataList_is_generic_and_sequence(self: Self) -> None:
        self._assert_is_generic(datahold.DataList, 1)
        self.assertTrue(
            issubclass(datahold.DataList, MutableSequence),
            "DataList should subclass collections.abc.MutableSequence",
        )

    def test_DataSet_is_generic_and_set(self: Self) -> None:
        self._assert_is_generic(datahold.DataSet, 1)
        self.assertTrue(
            issubclass(datahold.DataSet, MutableSet),
            "DataSet should subclass collections.abc.MutableSet",
        )

    # --- Hold* ---

    def test_HoldDict_is_generic(self: Self) -> None:
        # Expect key + value type parameters, like a dict
        self._assert_is_generic(datahold.HoldDict, 2)

    def test_HoldList_is_generic(self: Self) -> None:
        self._assert_is_generic(datahold.HoldList, 1)

    def test_HoldSet_is_generic(self: Self) -> None:
        self._assert_is_generic(datahold.HoldSet, 1)

    # --- Okay* ---

    def test_OkayDict_is_generic(self: Self) -> None:
        self._assert_is_generic(datahold.OkayDict, 2)
        # Also ensure it’s still a mapping
        self.assertTrue(
            issubclass(datahold.OkayDict, MutableMapping),
            "OkayDict should behave like a mapping",
        )

    def test_OkayList_is_generic(self: Self) -> None:
        self._assert_is_generic(datahold.OkayList, 1)
        self.assertTrue(
            issubclass(datahold.OkayList, MutableSequence),
            "OkayList should behave like a sequence",
        )

    def test_OkaySet_is_generic(self: Self) -> None:
        self._assert_is_generic(datahold.OkaySet, 1)
        self.assertTrue(
            issubclass(datahold.OkaySet, MutableSet),
            "OkaySet should behave like a set",
        )


if __name__ == "__main__":
    unittest.main()
