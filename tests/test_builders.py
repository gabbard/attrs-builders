import pytest

from attr import attrs
from attrsbuilders import generate_builder


class TestMinimalUsageWithLocalClass(object):
    def test_build(self):
        @generate_builder
        @attrs
        class A:
            pass

        builder = A.builder()
        assert 5 == builder.build()
