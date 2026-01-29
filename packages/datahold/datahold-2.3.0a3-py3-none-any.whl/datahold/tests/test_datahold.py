import unittest
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
)
from collections.abc import Set as AbstractSet
from inspect import isabstract
from typing import Any, Self

from frozendict import frozendict

from datahold.core.BaseDataDict import BaseDataDict
from datahold.core.BaseDataList import BaseDataList
from datahold.core.BaseDataObject import BaseDataObject
from datahold.core.BaseDataSet import BaseDataSet
from datahold.core.BaseHoldDict import BaseHoldDict
from datahold.core.BaseHoldList import BaseHoldList
from datahold.core.BaseHoldObject import BaseHoldObject
from datahold.core.BaseHoldSet import BaseHoldSet
from datahold.core.DataDict import DataDict
from datahold.core.DataList import DataList
from datahold.core.DataObject import DataObject
from datahold.core.DataSet import DataSet
from datahold.core.FrozenDataDict import FrozenDataDict
from datahold.core.FrozenDataList import FrozenDataList
from datahold.core.FrozenDataObject import FrozenDataObject
from datahold.core.FrozenDataSet import FrozenDataSet
from datahold.core.FrozenHoldDict import FrozenHoldDict
from datahold.core.FrozenHoldList import FrozenHoldList
from datahold.core.FrozenHoldObject import FrozenHoldObject
from datahold.core.FrozenHoldSet import FrozenHoldSet
from datahold.core.HoldDict import HoldDict
from datahold.core.HoldList import HoldList
from datahold.core.HoldObject import HoldObject
from datahold.core.HoldSet import HoldSet


class TestAbstractness(unittest.TestCase):
    def test_abstract_classes(self: Self) -> None:
        # data
        self.assertTrue(isabstract(DataObject))
        self.assertTrue(isabstract(DataDict))
        self.assertTrue(isabstract(DataList))
        self.assertTrue(isabstract(DataSet))

        self.assertTrue(isabstract(FrozenDataObject))
        self.assertTrue(isabstract(FrozenDataDict))
        self.assertTrue(isabstract(FrozenDataList))
        self.assertTrue(isabstract(FrozenDataSet))

        # hold
        self.assertFalse(isabstract(FrozenHoldObject))
        # self.assertFalse(isabstract(HoldObject))

    def test_concrete_classes(self: Self) -> None:
        FrozenHoldDict({"a": 1})
        FrozenHoldList([1, 2])
        FrozenHoldSet({1, 2})

        HoldDict({"a": 1})
        HoldList([1, 2])
        HoldSet({1, 2})


class TestInheritance(unittest.TestCase):
    def test_dict_inheritance(self: Self) -> None:
        # base → concrete
        self.assertTrue(issubclass(DataDict, DataObject))
        self.assertTrue(issubclass(FrozenDataDict, FrozenDataObject))
        self.assertTrue(issubclass(HoldDict, HoldObject))
        self.assertTrue(issubclass(FrozenHoldDict, FrozenHoldObject))

        # non-frozen data inherit from frozen
        self.assertTrue(issubclass(DataDict, BaseDataDict))
        self.assertTrue(issubclass(HoldDict, BaseHoldDict))

    def test_list_inheritance(self: Self) -> None:
        self.assertTrue(issubclass(DataList, DataObject))
        self.assertTrue(issubclass(FrozenDataList, FrozenDataObject))
        self.assertTrue(issubclass(HoldList, HoldObject))
        self.assertTrue(issubclass(FrozenHoldList, FrozenHoldObject))

        self.assertTrue(issubclass(DataList, BaseDataList))
        self.assertTrue(issubclass(HoldList, BaseHoldList))

    def test_set_inheritance(self: Self) -> None:
        self.assertTrue(issubclass(DataSet, DataObject))
        self.assertTrue(issubclass(FrozenDataSet, FrozenDataObject))
        self.assertTrue(issubclass(HoldSet, HoldObject))
        self.assertTrue(issubclass(FrozenHoldSet, FrozenHoldObject))

        self.assertTrue(issubclass(DataSet, BaseDataSet))
        self.assertTrue(issubclass(HoldSet, BaseHoldSet))


class TestProtocols(unittest.TestCase):
    def test_mapping_protocols_x(self: Self) -> None:
        x: FrozenHoldDict
        x = FrozenHoldDict({"a": 1})

        self.assertIsInstance(x, Mapping)
        self.assertNotIsInstance(x, MutableMapping)

    def test_mapping_protocols_y(self: Self) -> None:
        y: HoldDict
        y = HoldDict({"a": 1})

        self.assertIsInstance(y, Mapping)
        self.assertIsInstance(y, MutableMapping)

    def test_sequence_protocols_x(self: Self) -> None:
        f: FrozenHoldList
        f = FrozenHoldList([1, 2, 3])

        self.assertIsInstance(f, Sequence)
        self.assertNotIsInstance(f, MutableSequence)

    def test_sequence_protocols_y(self: Self) -> None:
        m: HoldList
        m = HoldList([1, 2, 3])
        self.assertIsInstance(m, Sequence)
        self.assertIsInstance(m, MutableSequence)

    def test_set_protocols(self: Self) -> None:
        f: FrozenHoldSet
        m: HoldSet
        f = FrozenHoldSet({1, 2, 3})
        m = HoldSet({1, 2, 3})

        self.assertIsInstance(f, AbstractSet)
        self.assertNotIsInstance(f, MutableSet)

        self.assertIsInstance(m, AbstractSet)
        self.assertIsInstance(m, MutableSet)


class TestDataAttribute(unittest.TestCase):
    def test_dict_data_is_immutable_mapping(self: Self) -> None:
        f: FrozenHoldDict
        m: HoldDict
        obj: Any
        f = FrozenHoldDict({"a": 1})
        m = HoldDict({"a": 1})

        for obj in (f, m):
            self.assertIsInstance(obj.data, frozendict)

            # try to mutate underlying data
            with self.assertRaises((TypeError, AttributeError)):
                obj.data["b"] = 2

    def test_list_data_is_tuple(self: Self) -> None:
        f: FrozenHoldList
        m: HoldList
        o: Any
        f = FrozenHoldList([1, 2, 3])
        m = HoldList([1, 2, 3])

        for o in (f, m):
            self.assertIsInstance(o.data, tuple)
            with self.assertRaises(Exception):
                o.data.append(4)

    def test_set_data_is_frozenset(self: Self) -> None:
        f: FrozenHoldSet
        m: HoldSet
        obj: Any
        f = FrozenHoldSet({1, 2, 3})
        m = HoldSet({1, 2, 3})

        for obj in (f, m):
            self.assertIsInstance(obj.data, frozenset)
            with self.assertRaises(AttributeError):
                obj.data.add(4)


class TestFrozenMutability(unittest.TestCase):
    def test_frozen_dict_cannot_mutate(self: Self) -> None:
        f: FrozenHoldDict
        f = FrozenHoldDict({"a": 1})
        with self.assertRaises((TypeError, AttributeError)):
            f["b"] = 2
        with self.assertRaises((TypeError, AttributeError)):
            f.pop("a", None)

    def test_frozen_list_cannot_mutate(self: Self) -> None:
        f: FrozenHoldList
        f = FrozenHoldList([1, 2, 3])
        with self.assertRaises((TypeError, AttributeError)):
            f.append(4)
        with self.assertRaises((TypeError, AttributeError)):
            f.pop()

    def test_frozen_set_cannot_mutate(self: Self) -> None:
        f: FrozenHoldSet
        f = FrozenHoldSet({1, 2, 3})
        with self.assertRaises((TypeError, AttributeError)):
            f.add(4)
        with self.assertRaises((TypeError, AttributeError)):
            f.remove(1)


class TestMutableBehavior(unittest.TestCase):
    def test_hold_dict_mutates_and_syncs_data(self: Self) -> None:
        x: HoldDict
        x = HoldDict({"a": 1})
        x["b"] = 2
        self.assertEqual(x["b"], 2)
        self.assertEqual(x.data["b"], 2)

    def test_hold_list_mutates_and_syncs_data(self: Self) -> None:
        x: HoldList
        x = HoldList([1, 2])
        x.append(3)
        self.assertEqual(list(x), [1, 2, 3])
        self.assertEqual(x.data, (1, 2, 3))

    def test_hold_set_mutates_and_syncs_data(self: Self) -> None:
        s: HoldSet
        s = HoldSet({1, 2})
        s.add(3)
        self.assertTrue(3 in s)
        self.assertTrue(3 in s.data)


class TestCopy(unittest.TestCase):
    def test_frozen_have_no_copy(self: Self) -> None:
        self.assertFalse(hasattr(FrozenHoldDict({"a": 1}), "copy"))
        self.assertFalse(hasattr(FrozenHoldList([1, 2]), "copy"))
        self.assertFalse(hasattr(FrozenHoldSet({1, 2}), "copy"))

    def test_frozen_have_no_copy_2(self: Self) -> None:
        """
        Frozen classes should not define their own copy method.
        (If a parent class or wrapped object exposes one, we ignore that.)
        """
        cls: Any
        args: Any
        obj: Any
        copy_obj: Any
        for cls, args in (
            (FrozenHoldDict, ({"a": 1},)),
            (FrozenHoldList, ([1, 2],)),
            (FrozenHoldSet, ({1, 2},)),
        ):
            # They must not *define* copy themselves
            self.assertNotIn("copy", cls.__dict__)

            # Optional: if they *do* expose copy on the instance, it should not
            # create a mutable variant; you can drop this if you prefer.
            obj = cls(*args)
            if hasattr(obj, "copy"):
                copy_obj = obj.copy()
                self.assertIsInstance(copy_obj, cls)

    def test_mutable_copy_returns_same_type_and_is_shallow(self: Self) -> None:
        d: HoldDict
        d_copy: HoldDict
        d = HoldDict({"a": {"x": 1}})
        d_copy = d.copy()
        self.assertIsInstance(d_copy, type(d))
        self.assertIsNot(d_copy, d)
        self.assertEqual(dict(d_copy), dict(d))

        # shallow: inner object is shared
        d["a"]["x"] = 2
        self.assertEqual(d_copy["a"]["x"], 2)

    def test_list_copy(self: Self) -> None:
        lst: HoldList
        lst_copy: HoldList
        lst = HoldList([[1], [2]])
        lst_copy = lst.copy()
        self.assertIsInstance(lst_copy, type(lst))
        self.assertIsNot(lst_copy, lst)
        self.assertEqual(list(lst_copy), list(lst))

        lst[0].append(99)
        self.assertEqual(lst_copy[0], [1, 99])

    def test_set_copy(self: Self) -> None:
        s: HoldSet
        s_copy: HoldSet
        s = HoldSet({1, 2, 3})
        s_copy = s.copy()
        self.assertIsInstance(s_copy, type(s))
        self.assertIsNot(s_copy, s)
        self.assertEqual(set(s_copy), set(s))

        s.add(4)
        self.assertNotIn(4, s_copy)


if __name__ == "__main__":
    unittest.main()
