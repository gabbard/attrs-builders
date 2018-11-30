from __future__ import absolute_import, division, print_function

import hashlib
import linecache


class _BuilderBuilder(object):
    def __init__(self, cls):
        self._cls = cls
        self._builder_name = 'Builder'
        self._build_method_name = 'build'
        self._builder_method_name = 'builder'

    def build(self):
        cls = self._cls

        builder_cls = self._find_builder(cls)

        if not builder_cls:
            builder_cls = type(cls)("Builder", (), {})
            setattr(cls, self._builder_name, builder_cls)

        self._patch_builder(builder_cls)
        setattr(self._cls, self._builder_method_name,
                self._add_method_dunders(self._make_builder_method()))

        return cls

    def _find_builder(self, outer_cls):
        if hasattr(outer_cls, self._builder_name):
            return getattr(outer_cls, self._builder_name)
        else:
            return None

    def _patch_builder(self, builder_cls):
        setattr(builder_cls, '__init__',
                self._add_method_dunders(self._make_init()))
        setattr(builder_cls, self._build_method_name,
                self._add_method_dunders(self._make_build()))

    def _make_init(self):
        # We cache the generated init methods for the same kinds of attributes.
        sha1 = hashlib.sha1()
        #sha1.update(repr(attrs).encode("utf-8"))
        sha1.update(repr("foo").encode("utf-8"))
        unique_filename = "<attrsbuilder generated init {0}>".format(sha1.hexdigest())

        script = "\n".join(["def __init__(self):",
                  "\tprint('hello world')"])

        local_variables = {}
        bytecode = compile(script, unique_filename, "exec")
        eval(bytecode, {}, local_variables)

        # In order of debuggers like PDB being able to step through the code,
        # we add a fake linecache entry.
        linecache.cache[unique_filename] = (
            len(script),
            None,
            script.splitlines(True),
            unique_filename,
        )

        __init__ = local_variables["__init__"]
        return __init__

    def _make_build(self):
        # We cache the generated init methods for the same kinds of attributes.
        sha1 = hashlib.sha1()
        # sha1.update(repr(attrs).encode("utf-8"))
        sha1.update(repr("foobuild").encode("utf-8"))
        unique_filename = "<attrsbuilder generated build {0}>".format(sha1.hexdigest())

        script = "\n".join([
                "def build(self):",
                "\tprint('goodbye world')",
                "\treturn 5"])

        local_variables = {}
        bytecode = compile(script, unique_filename, "exec")
        eval(bytecode, {}, local_variables)

        # In order of debuggers like PDB being able to step through the code,
        # we add a fake linecache entry.
        linecache.cache[unique_filename] = (
            len(script),
            None,
            script.splitlines(True),
            unique_filename,
        )

        build = local_variables["build"]
        return build

    def _make_builder_method(self):
        # We cache the generated init methods for the same kinds of attributes.
        sha1 = hashlib.sha1()
        # sha1.update(repr(attrs).encode("utf-8"))
        sha1.update(repr("foobuilder").encode("utf-8"))
        unique_filename = "<attrsbuilder generated builder {0}>".format(sha1.hexdigest())

        # this requires keeping a reference around to this BuilderBuilder, but I am not sure
        # how to instantiate inner classes of local classes otherwise
        def builder():
            return getattr(self._cls, self._builder_name)()

        # warning: this is fake and used only for the linecache. The actual code executed is above
        script = "\n".join([
                f"def {self._builder_method_name}():",
                f"\treturn {self._cls.__qualname__}.{self._builder_name}()"])

        # In order of debuggers like PDB being able to step through the code,
        # we add a fake linecache entry.
        linecache.cache[unique_filename] = (
            len(script),
            None,
            script.splitlines(True),
            unique_filename,
        )

        return builder

    def _add_method_dunders(self, method):
        """
        Add __module__ and __qualname__ to a *method* if possible.

        Copied from _make.py in attrs
        """
        try:
            method.__module__ = self._cls.__module__
        except AttributeError:
            pass

        try:
            method.__qualname__ = ".".join(
                (self._cls.__qualname__, method.__name__)
            )
        except AttributeError:
            pass

        return method


def generate_builder(
        maybe_cls=None
):
    def wrap(cls):
        builder_builder = _BuilderBuilder(cls)
        if getattr(cls, "__class__", None) is None:
            raise TypeError("attrsbuilder only works with new-style classes.")

        return builder_builder.build()

    # maybe_cls's type depends on the usage of the decorator.  It's a class
    # if it's used as `@builder` but ``None`` if used as `@builder()`.
    if maybe_cls is None:
        return wrap
    else:
        return wrap(maybe_cls)