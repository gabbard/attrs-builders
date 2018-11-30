from __future__ import absolute_import, division, print_function

import hashlib
import linecache

from attr import NOTHING

# utility methods from https://github.com/isi-vista/vistautils/blob/master/vistautils/class_utils.py

def _fully_qualified_name(clazz):
    """
    Gets the fully-qualified name of a class.
    This is the package name, plus the module name, plus the class name (including parent
    classes for nested classes), joined by `.`s.  For builtin types or module-less types,
    the package and module portions are omitted.
    This implementation is indebted to https://stackoverflow.com/a/13653312/413345
    """
    module = clazz.__module__
    # we compared to str.__class__.__module__ so that we don't include the
    # "builtin." prefix for built-in types
    if module is None or module == str.__class__.__module__:
        return clazz.__qualname__
    return module + "." + clazz.__qualname__


def _fully_qualified_name_of_type(obj):
    """
    Gets the fully-qualified name of the type of this object.
    This is the package name, plus the module name, plus the class name (including parent
    classes for nested classes), joined by `.`s.  For builtin types or module-less types,
    the package and module portions are omitted.
    This implementation is indebted to https://stackoverflow.com/a/13653312/413345
    """
    return _fully_qualified_name(obj.__class__)


class _BuilderBuilder(object):
    def __init__(self, cls):
        self._cls = cls
        self._builder_name = 'Builder'
        self._build_method_name = 'build'
        self._builder_method_name = 'builder'
        self._from_method_name = 'initialize_from'

    def build(self):
        cls = self._cls

        builder_cls = self._find_builder(cls)

        if not builder_cls:
            builder_cls = type(cls)("Builder", (), {})
            builder_cls.__qualname__ = f"{cls.__qualname__}.{self._builder_name}"
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
        setattr(builder_cls, '__repr__',
                self._add_method_dunders(self._make_repr()))
        if self._from_method_name:
            setattr(builder_cls, self._from_method_name,
                    self._add_method_dunders(self._make_from_method()))

    def _make_init(self):
        # We cache the generated init methods for the same kinds of attributes.
        sha1 = hashlib.sha1()
        #sha1.update(repr(attrs).encode("utf-8"))
        sha1.update(repr("foo").encode("utf-8"))
        unique_filename = "<attrsbuilder generated init {0}>".format(sha1.hexdigest())

        lines = ["def __init__(self):"]

        for attribute in self._cls.__attrs_attrs__:
            if attribute.init:
                lines.append(f"\tself.{attribute.name} = NOTHING")
        # in case none of the attributes are initialized
        lines.append("\tpass")

        script = "\n".join(lines)

        local_variables = {}
        bytecode = compile(script, unique_filename, "exec")
        eval(bytecode, {"NOTHING": NOTHING}, local_variables)

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

    def _make_from_method(self):
        # We cache the generated init methods for the same kinds of attributes.
        sha1 = hashlib.sha1()
        #sha1.update(repr(attrs).encode("utf-8"))
        sha1.update(repr("foo").encode("utf-8"))
        unique_filename = "<attrsbuilder generated {method_name} {sha}>".format(
            sha=sha1.hexdigest(), method_name=self._from_method_name)

        lines = ["def {from_method_name}(self, source_object):".format(
            from_method_name=self._from_method_name)]

        for attribute in self._cls.__attrs_attrs__:
            if attribute.init:
                lines.append("\tself.{attribute_name} = getattr(source_object, '{attribute_name}')"
                             .format(attribute_name=attribute.name))
        lines.append("\treturn self")

        script = "\n".join(lines)

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

        from_method = local_variables[self._from_method_name]
        return from_method

    def _make_build(self):
        # We cache the generated init methods for the same kinds of attributes.
        sha1 = hashlib.sha1()
        # sha1.update(repr(attrs).encode("utf-8"))
        sha1.update(repr("foobuild").encode("utf-8"))
        unique_filename = "<attrsbuilder generated build {0}>".format(sha1.hexdigest())

        def build(builder_self):
            kw_args = {}
            # TODO: handle the case of defaults which are functions
            for attribute in self._cls.__attrs_attrs__:
                if attribute.init:
                    builder_att_val = getattr(builder_self, attribute.name)
                    if builder_att_val is not NOTHING:
                        # this will pass only if the user explicitly set it. Otherwise,
                        # we don't specify it so that the attr class's default will be used
                        kw_args[attribute.name] = builder_att_val
            return self._cls(**kw_args)

        lines = ["def build(self):", "\treturn {self._cls.__qualname__}("]
        first = True
        for attribute in self._cls.__attrs_attrs__:
            if attribute.init:
                if not first:
                    initial_comma = ", "
                else:
                    initial_comma = ""
                first = False

                lines.append(f"\t\t{initial_comma}{attribute.name} = self.{attribute.name}")
        lines.append("\t\t)")

        #local_variables = {}
        #bytecode = compile(script, unique_filename, "exec")
        #eval(bytecode, {}, local_variables)

        # In order of debuggers like PDB being able to step through the code,
        # we add a fake linecache entry.
        script = "\n".join(lines)
        linecache.cache[unique_filename] = (
            len(script),
            None,
            script.splitlines(True),
            unique_filename,
        )

        return build

    def _make_repr(outer_self):
        def __repr__(self):
            ret = [_fully_qualified_name_of_type(self), "("]
            first = True
            for attribute in outer_self._cls.__attrs_attrs__:
                if attribute.init:
                    if first:
                        first = False
                    else:
                        ret.append(", ")
                    ret.extend((attribute.name, "=", repr(getattr(self, attribute.name))))
            ret.append(")")
            return "".join(ret)
        return __repr__

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