import pytest

from attr import attrs, attrib
from attrsbuilders import generate_builder


class TestMinimalUsageWithLocalClass(object):
    def test_build(self):
        @generate_builder
        @attrs
        class A:
            pass

        builder = A.builder()
        assert A() == builder.build()


class TestDirectSetOfFields(object):
    def test_build(self):
        @generate_builder
        @attrs
        class A:
            x = attrib()
            y = attrib()

        builder = A.builder()
        builder.x = "foo"
        builder.y = "bar"
        assert A(x="foo", y="bar") == builder.build()

