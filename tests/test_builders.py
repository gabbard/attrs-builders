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


class TestInitializeFromExisting(object):
    def test_initialize_from_existing(self):
        @generate_builder
        @attrs
        class A:
            x = attrib()
            y = attrib()

        original = A(x=5, y=10)
        builder = A.builder().initialize_from(original)
        builder.y = -2
        assert A(x=5, y=-2) == builder.build()


class TestInitializeFromExistingNonPublic(object):
    def test_initialize_from_existing(self):
        @generate_builder
        @attrs
        class A:
            _x = attrib()
            _y = attrib()

        original = A(x=5, y=10)
        builder = A.builder().initialize_from(original)
        builder.y = -2
        assert A(x=5, y=-2) == builder.build()


class TestExceptionIfNonAttrs(object):
    def test_exception_if_non_attrs(self):
        with pytest.raises(RuntimeError,
                           match="@generate_builder can only "
                                 "be applied to attrs classes"):
            @generate_builder
            class A:
                _x = attrib()
                _y = attrib()

