"""
Utilities to write course scripts

This module implements an automatic adapter for provisionning a
Command Line Interfaces (CLI) from a Python Object Oriented Interface
defined by an object and some of its subobjects.

This is used to implement a generic main function for course scripts,
provisionning a CLI from the course object and its forge.
"""

import argparse
from argparse import ArgumentParser
import inspect
from subprocess import CalledProcessError
from typing import Callable, Optional, Any, List, Dict, cast

from .utils import getLogger
from .course import Course


# Get the value returned by inspect when a function argument has no
# default value (mypy does not like inspect._empty; it indeed is not
# clearly public)
def dummy(x: Any) -> None:
    pass


NODEFAULT = inspect.signature(dummy).parameters["x"].default


def add_parser_arguments_for_function(
    parser: ArgumentParser, function: Callable
) -> None:
    """Inspect the function signature and add the arguments to the parser

    Examples::

        >>> def f(x, y): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> parser.parse_args(["a", "b"])
        Namespace(...)

    To make these examples more testable, we use pprint to display the
    result:

        >>> from pprint import pprint as pp
        >>> pp(vars(parser.parse_args(["a", "b"])))
        {'_function': <function f at ...>, 'x': 'a', 'y': 'b'}

    Arguments with default value:

        >>> def f(foo="default_value"): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> pp(vars(parser.parse_args([])))
        {'_function': <function f at ...>, 'foo': 'default_value'}
        >>> pp(vars(parser.parse_args(["value"])))
        {'_function': <function f at ...>, 'foo': 'value'}
        >>> pp(vars(parser.parse_args(["--foo", "value"])))
        {'_function': <function f at ...>, 'foo': 'value'}

    Mixed arguments:

        >>> def f(x, y=0): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> pp(vars(parser.parse_args(["a", "b"])))
        {'_function': <function f at ...>, 'x': 'a', 'y': 'b'}
        >>> pp(vars(parser.parse_args(["a"])))
        {'_function': <function f at ...>, 'x': 'a', 'y': 0}
        >>> pp(vars(parser.parse_args(["a", "--y", "b"])))
        {'_function': <function f at ...>, 'x': 'a', 'y': 'b'}

    Boolean argument with default `False`:

        >>> def f(force: bool = False): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> pp(vars(parser.parse_args([])))
        {'--force': False, '_function': <function f at ...>}
        >>> pp(vars(parser.parse_args(["--force"])))
        {'--force': True, '_function': <function f at ...>}

    Boolean argument with default `True`:

        >>> def f(force: bool = True): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> pp(vars(parser.parse_args([])))
        {'--force': True, '_function': <function f at ...>}
        >>> pp(vars(parser.parse_args(["--force"])))
        {'--force': True, '_function': <function f at ...>}
        >>> pp(vars(parser.parse_args(["--no-force"])))
        {'--force': False, '_function': <function f at ...>}

    Additional arguments:

        >>> def f(a, b, *args): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> pp(vars(parser.parse_args(["a", "b", "c", "d", "e"])))
        {'*args': ['c', 'd', 'e'],
         '_function': <function f at ...>,
         'a': 'a',
         'b': 'b'}

    Special case: generic keyword arguments with a type of `None`:

        >>> def f(a, b, *args, **kwargs: None): pass
        >>> parser = ArgumentParser(prog='PROG')
        >>> add_parser_arguments_for_function(parser, f)
        >>> pp(vars(parser.parse_args(["a", "b", "--a", "c", "-d", "-f", "g", "--h"])))
        {'*args': ['--a', 'c', '-d', '-f', 'g', '--h'],
         '_function': <function f at ...>,
         'a': 'a',
         'b': 'b'}

    TESTS:

    We test here the underlying "exclusive group" feature of Python's
    argparse library which we use to parse positional or keyword
    arguments. For these, we want to support both "value" and "--foo
    value".

        >>> from argparse import ArgumentParser
        >>> from pprint import pp

    We were using the following idiom which is not robust (see #31 and #117):

        >>> parser = ArgumentParser(prog='PROG')
        >>> exclusive_group = parser.add_mutually_exclusive_group()
        >>> _ = exclusive_group.add_argument("foo", nargs="?", default="default_value")
        >>> _ = exclusive_group.add_argument("--foo", default="default_value", dest="foo")
        >>> pp(vars(parser.parse_args([])))                   # ok
        {'foo': 'default_value'}
        >>> pp(vars(parser.parse_args(["value"])))            # ok
        {'foo': 'value'}
        >>> pp(vars(parser.parse_args(["--foo", "value"])))   # oops!
        {'foo': 'default_value'}

    This seems robust:

        >>> parser = ArgumentParser(prog='PROG')
        >>> exclusive_group = parser.add_mutually_exclusive_group()
        >>> _ = exclusive_group.add_argument("--foo", default="default_value", dest="foo");
        >>> _ = exclusive_group.add_argument("foo", nargs="?", default=argparse.SUPPRESS);
        >>> pp(vars(parser.parse_args([])))
        {'foo': 'default_value'}
        >>> pp(vars(parser.parse_args(["value"])))
        {'foo': 'value'}
        >>> pp(vars(parser.parse_args(["--foo", "value"])))
        {'foo': 'value'}
    """
    parser.set_defaults(_function=function)
    signature = inspect.signature(function)
    after_bool_argument = False
    for key, value in signature.parameters.items():
        if value.annotation is bool:
            parser.add_argument(
                "--" + key,
                action="store_true",
                default=value.default,
                dest="--" + key,
            )
            if value.default:
                parser.add_argument(
                    "--no-" + key,
                    action="store_false",
                    dest="--" + key,
                )
            after_bool_argument = True
        elif value.kind == value.POSITIONAL_ONLY or (
            value.kind == value.POSITIONAL_OR_KEYWORD and value.default == NODEFAULT
        ):
            parser.add_argument(key)
        elif value.kind == value.POSITIONAL_OR_KEYWORD:
            group = parser.add_mutually_exclusive_group()
            group.add_argument(key, nargs="?", default=argparse.SUPPRESS)
            group.add_argument("--" + key, default=value.default, dest=key)
        elif value.kind == value.KEYWORD_ONLY:
            parser.add_argument(
                "--" + key, default=value.default, dest="--" + key, metavar=key.upper()
            )
        elif value.kind == value.VAR_POSITIONAL:
            parser.add_argument("*" + key, nargs="*")
        elif value.kind == value.VAR_KEYWORD:
            if value.annotation is None:
                parser.prefix_chars = ""
            # else:
            #     raise NotImplementedError("Keyword arguments")
        assert (
            value.annotation is bool
            or value.kind == value.VAR_KEYWORD
            or not after_bool_argument
        ), (
            f"{function}: due to a current limitation, for use from the command line, "
            "boolean arguments should come after all positional arguments"
        )


def add_subparsers_for_object_methods(
    subparsers: argparse._SubParsersAction, object: Any
) -> None:
    """
    Inspect the object, and add a subparser for all of its methods

    Return the subparsers

    Examples::

        >>> from pprint import pprint as pp

        >>> class A:
        ...     name = "classA"
        ...     version = "1.0"
        ...     def f(self, x, y):
        ...         "Just a test for the help functions"
        ...         pass
        ...     def g(self, a, b=0):
        ...         pass

        >>> parser = ArgumentParser(prog='PROG')
        >>> subparsers = parser.add_subparsers()
        >>> add_subparsers_for_object_methods(subparsers, A())
        >>> namespace = parser.parse_args(["f", "1", "3"]); namespace
        Namespace(...)
        >>> pp(vars(namespace))
        {'_function': <bound method A.f of <travo.script.A object at ...>>,
         'x': '1',
         'y': '3'}
        >>> pp(vars(parser.parse_args(["g", "2"])))
        {'_function': <bound method A.g of <travo.script.A object at ...>>,
         'a': '2',
         'b': 0}
    """
    for name in dir(object.__class__):
        if name[0] == "_":
            continue
        method = getattr(object, name)
        if not (inspect.ismethod(method) or inspect.isfunction(method)):
            continue
        help = inspect.getdoc(method)
        if help is not None:
            help = help.splitlines()[0]
        parser = subparsers.add_parser(name, help=help, description=help)
        add_parser_arguments_for_function(parser, method)


def add_object_parser(
    parser: ArgumentParser, obj: Any, subobjects: List[Dict] = []
) -> None:
    """
    Command Line Interface from Object Oriented Interface

    This inspects the available methods of `obj`, sets up an
    :class:`ArgumentParser` mimicking it, parses the command line, and
    calls a method of `obj` accordingly. With all the benefits from
    ArgumentParser: automatic help, etc.

    For example, a command line such as:

        script foo bar truc

    will call:

        obj.foo("bar", "truc")

    Examples::

        >>> from pprint import pprint as pp
        >>> class A:
        ...     def a1(self):
        ...         pass
        ...     def a2(self, a21, a22=0):
        ...         pass
        >>> class B:
        ...     def b1(self, b11):
        ...         pass
        >>> class C:
        ...     def c1(self, c11, c12):
        ...         pass

        >>> a = A()
        >>> a.b = B()
        >>> a.b.c = C()

        >>> parser = ArgumentParser(usage="Come play with A")
        >>> add_object_parser(parser,
        ...                          a,
        ...                          subobjects=[
        ...                              dict(name="b",
        ...                                   usage='usage b',
        ...                                   subobjects=[
        ...                                       dict(name="c",
        ...                                            usage='usage c')
        ...                                   ])
        ...                              ])

        >>> parser.parse_args(["a1"])
        Namespace(...)
        >>> pp(vars(parser.parse_args(["a2", "1"])))
        {'_function': <bound method A.a2 of <travo.script.A object at ...>>,
         'a21': '1',
         'a22': 0}

        >>> pp(vars(parser.parse_args(["a2", "1", "2"])))
        {'_function': <bound method A.a2 of <travo.script.A object at ...>>,
         'a21': '1',
         'a22': '2'}
        >>> pp(vars(parser.parse_args(["b", "b1", "2"])))
        {'_function': <bound method B.b1 of <travo.script.B object at ...>>,
         'b11': '2'}
        >>> pp(vars(parser.parse_args(["b", "c", "c1", "1", "2"])))
        {'_function': <bound method C.c1 of <travo.script.C object at ...>>,
         'c11': '1',
         'c12': '2'}

        >>> parser.print_usage()
        usage: Come play with A
        >>> parser.print_help()
        usage: Come play with A
        <BLANKLINE>
        option...s:
          -h, --help  show this help message and exit
        <BLANKLINE>
        Subcommands:
          {a1,a2,b}
            a1
            a2
    """
    subparsers = parser.add_subparsers(prog=parser.prog, title="Subcommands")
    add_subparsers_for_object_methods(subparsers, obj)

    def add_subobject(name: str, subobjects: List = [], **kwargs: Any) -> None:
        subobj = getattr(obj, name)
        subparser = subparsers.add_parser(name, **kwargs)
        add_object_parser(subparser, subobj, subobjects=subobjects)

    for subobject_kwargs in subobjects:
        add_subobject(**subobject_kwargs)


def CLI(
    obj: Any,
    subobjects: List[Dict] = [],
    args: Optional[List[str]] = None,
    **kwargs: Any,
) -> None:
    """
    Automatic CLI adapter

    Adapts the Python Object Oriented Interface defined by `obj` and
    some of its subobjects into a Command Line Interface.
    Function outputs are redirected to the standard output using `print`.

    Examples::

        >>> class A:
        ...     name = "classA"
        ...     version = "1.0"
        ...     def f(self, x, y):
        ...         return(x, y)
        ...     def g(self, x, y, z=1, *args, t=2):
        ...         return(x, y, z, *args, t)
        ...     def h(self, a, b, *args, **kwargs: None):
        ...         return(a, b, *args)
        >>> a = A()
        >>> a.f('x', 'y')
        ('x', 'y')
        >>> CLI(a, args=['f', 'x', 'y'])
        ('x', 'y')

        >>> a.g('x', 'y')
        ('x', 'y', 1, 2)
        >>> CLI(a, args=['g', 'x', 'y'])
        ('x', 'y', 1, 2)

        >>> a.g('x', 'y', 'z', '1', '2', t='t')
        ('x', 'y', 'z', '1', '2', 't')
        >>> CLI(a, args=['g', 'x', 'y', 'z', '1', '2', '--t', 't'])
        ('x', 'y', 'z', '1', '2', 't')

        >>> a.g('x', 'y', t='t', z='z')
        ('x', 'y', 'z', 't')

        >>> CLI(a, args=['g', 'x', 'y', '--t', 't', '--z', 'z'])
        ('x', 'y', 'z', 't')

        >>> CLI(a, args=['g', '--t', 't', '--z', 'z', 'x', 'y'])
        ('x', 'y', 'z', 't')

    Checking for conflicts between positional and keyword::

        >>> a.g('x', 'y', '1', '2', z='z')
        Traceback (most recent call last):
        TypeError: g() got multiple values for argument 'z'
        >>> CLI(a, args=['g', 'x', 'y', '1', '2', '--z', 'z'])
        Traceback (most recent call last):
        ...
        SystemExit: 2

    As a special case, a generic keyword arguments with a type of
    `None` serves as a marker that all command line arguments should
    be considered as positional, regardless of whether they start with
    `-` or not.

        >>> a.h('a', 'b', 'c', '--d', 'e', '--f')
        ('a', 'b', 'c', '--d', 'e', '--f')
        >>> CLI(a, args=['h', 'a', 'b', 'c', '--d', 'e', '--f'])
        ('a', 'b', 'c', '--d', 'e', '--f')

    Subcommand examples:

        >>> class B:
        ...     def b1(self, b11):
        ...         return b11
        >>> class C:
        ...     def c1(self, c11, c12):
        ...         return (c11, c12)

        >>> a.b = B()
        >>> a.b.c = C()
        >>> a.b.b1('x')
        'x'
        >>> subobjects = [
        ...     dict(
        ...         name="b",
        ...         usage="usage b",
        ...         subobjects=[
        ...             dict(
        ...                 name="c",
        ...                 usage="usage c",
        ...             )
        ...         ],
        ...     )
        ... ]
        >>> CLI(a, subobjects=subobjects, args=['b', 'b1', 'x'])
        x
        >>> CLI(a, subobjects=subobjects, args=['b'])
        Traceback (most recent call last):
        ...
        SystemExit: 1
        >>> a.b.c.c1('x', 'y')
        ('x', 'y')
        >>> CLI(a, subobjects=subobjects, args=['b', 'c', 'c1', 'x', 'y'])
        ('x', 'y')
    """
    parser = ArgumentParser(**kwargs)
    add_object_parser(parser, obj, subobjects=subobjects)

    parser.add_argument(
        "--version",
        action="version",
        help="echo version number.",
        version=f"{obj.name} {obj.version}",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--debug",
        dest="loglevel",
        action="store_const",
        const="DEBUG",
        default="INFO",
        help="show debugging information",
    )
    group.add_argument(
        "--silent",
        dest="loglevel",
        action="store_const",
        const="WARNING",
        help="run silently",
    )

    namespace = vars(parser.parse_args(args=args))

    # Handle log level
    log = getattr(obj, "log", getLogger())
    log.setLevel(namespace["loglevel"])
    debug = namespace["loglevel"] == "DEBUG"
    del namespace["loglevel"]

    # Recover the function to call and its arguments
    if "_function" not in namespace:
        parser.print_usage()
        exit(1)

    function = namespace["_function"]
    del namespace["_function"]

    function_args = []
    function_kwargs = {}
    for key, value in namespace.items():
        if key.startswith("--"):
            function_kwargs[key[2:]] = value
        elif key.startswith("*"):
            function_args.extend(value)
        else:
            assert "--" + key not in kwargs
            # TODO this seems to fix a conflicting bug but I'm not sure what I'm doing
            function_args.append(value)
            # function_kwargs[key] = value

    debug = True

    if debug:
        result = function(*function_args, **function_kwargs)
    else:
        try:
            result = function(*function_args, **function_kwargs)
        except (RuntimeError, CalledProcessError) as e:
            log.error(str(e))
            # log.error("Utiliser --debug pour plus de détails")
            exit(2)

    if result is not None:
        print(result)


def main(course: Course, usage: str) -> None:
    """
    A default main function for course scripts

    It automatically adapts the Python Object Oriented Interface for
    the course and its forge into a Command Line Interface.
    """

    # Insert a helper toplevel git subcommand that pass
    # all its arguments to git
    def git(self: Course, *args: str, **kwargs: None) -> None:
        """
        Run git, passing down the forge's credentials
        """
        self.forge.git(args)

    cast(Any, Course).git = git

    CLI(
        course,
        usage=usage,
        subobjects=[
            dict(
                name="forge",
                help="Operations on the forge",
                description="Operations on the forge",
            )
        ],
    )
