import unittest
from typing import *

from datahold import core
from datahold.core import *


class TestData(unittest.TestCase):
    def test_constructor(self: Self) -> None:
        with self.assertRaises(Exception):
            DataDict()
        with self.assertRaises(Exception):
            DataList()
        with self.assertRaises(Exception):
            DataSet()


class TestHold(unittest.TestCase):
    def test_constructor(self: Self) -> None:
        HoldDict()
        HoldList()
        HoldSet()


class TestDoc(unittest.TestCase):
    def test_doc(self: Self) -> None:
        name: str
        s: str
        t: str
        for s in ("Data", "Hold"):
            for t in ("Object", "Dict", "List", "Set"):
                name = s + t
                with self.subTest(name=name):
                    self.go(name=name)

    def go(self: Self, name: str) -> None:
        a: Any
        b: Any
        doc: Any
        error: Any
        obj: Any
        y: Any
        y = getattr(core, name)
        for a in dir(y):
            b = getattr(y, a)
            if not callable(b) and not isinstance(b, property):
                continue
            if getattr(b, "__isabstractmethod__", False):
                continue
            if a == "__subclasshook__":
                continue
            doc = getattr(b, "__doc__", None)
            error = "%r inside %r has no docstring" % (a, name)
            self.assertNotEqual(doc, None, error)
        try:
            obj = y()
        except TypeError:
            return
        with self.assertRaises(AttributeError):
            obj.foo = 42


if __name__ == "__main__":
    unittest.main()
