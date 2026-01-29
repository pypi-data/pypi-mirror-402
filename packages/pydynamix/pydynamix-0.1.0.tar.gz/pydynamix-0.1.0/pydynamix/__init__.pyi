"""
# pydynamix

> **A powerful dynamic execution and code manipulation library.**

This module provides advanced tools for dynamic code execution, variable management,
and metaprogramming capabilities in Python. It enables secret variable storage,
dynamic execution with result capture, scope manipulation, lambda creation, and
class extension.

Key Features:
    - Secret variable storage and retrieval (`setvar`, `getvar`, `delvar`, `clearvars`)
    - Dynamic code execution with results (`resulted_execution`)
    - Scope context management (`scope_context`)
    - Anonymous function generation (`GreatLambda`)
    - Class extension and composition (`extend`)
    - Module export control (`export`)
    - Custom object construction decorator (`constructor`)

Classes:\n
**ReadOnly**: Contains nested type-only classes for typing purposes.
    - **ExecutionResults**: Represents results from dynamic code execution.
    - **Scoper**: Provides scope attribute access and management.
    - **ScopeContext**: Context manager for scope attribute revelation.
**GreatLambda**: Builder for creating advanced anonymous functions.
**constructor**: Decorator for constructing objects via function definitions.

Functions:
    `setvar`: Store a variable secretly.
    `getvar`: Retrieve a secretly stored variable with optional default.
    `delvar`: Delete a specific secret variable by name.
    `clearvars`: Clear all secret variables.
    `takevar`: Retrieve a secret variable or raise `KeyError` if not found.
    `resulted_execution`: Execute code dynamically and capture execution results.
    `extend`: Extend a class with attributes from another class.
    `scope_context`: Create a context manager for accessing object attributes.
    `export`: Define which variables a module should export.
"""

from typing import Any, Callable, Union, TypeVar, Iterable, Protocol, Type
from types import CoroutineType, CodeType, CellType, ModuleType, MappingProxyType
from inspect import Signature
from collections.abc import Buffer as ReadableBuffer
import sys, pydynamix

def setvar(name: str, value) -> None:
    """Sets a variable secretly with a `name` and a `value`, e.g.:\n\n```python\nsetvar('secret', 'abc123')\nprint(getvar('secret')) # abc123\nclearvars() # it's better to always clear variables after creating them to keep secretness\n```"""

def getvar(name: str, default=None) -> Any:
    """Gets the variable stored by `setvar`, it is a safe version from `takevar` (see the `default` argument), e.g.:\n\n```python\nsetvar('secret', 'abc123')\nprint(getvar('secret')) # abc123\nclearvars() # it's better to always clear variables after creating them to keep secretness\n```"""

def delvar(name: str) -> None:
    """Instead of clearing all variables with `clearvars` and affecting other users, Use `delvar` to delete a variable stored by `setvar` by name, e.g.:\n\n```python\nsetvar('secret', 'abc123')\nprint(getvar('secret')) # abc123\ndelvar('secret') # delete the secretly stored variable\n```"""

def clearvars() -> None:
    """Clears all variables stored by `setvar`, e.g.: \n\n```python\nsetvar('secret 1', 'abcdefg')\nsetvar('secret 2', 'abcd123')\nclearvars() # clears all variables stored previously\n```"""

def takevar(name: str):
    """Gets the variable stored by `setvar`, It raises a KeyError if it wasn't found e.g.:\n\n```python\ntry:\n\ttakevar('variable') # I didn't store it with `setvar`\nexcept KeyError as e:\n\tprint('KeyError:', e) # KeyError: 'variable'\n```"""

class ReadOnly:
    """The classes inside this class don't even exist, they are just for typing"""
    class ExecutionResults:
        if sys.version_info >= (3, 11):
            @staticmethod
            def rexecution_function(globals: dict[str, Any] | None = None, locals: dict[str, object] | None = None, *, closure: tuple[CellType, ...] | None = None) -> ReadOnly.ExecutionResults:
                """Re-execute the same code with different arguments, e.g.:\n\n```python\nresulted_execution("x = 10\\ny = x + 5\\nprint(x, y)").rexec()\n# prints 10, 15 twice\n```"""
        else:
            @staticmethod
            def rexecution_function(globals: dict[str, Any] | None = None, locals: dict[str, object] | None = None) -> ReadOnly.ExecutionResults:
                """Re-execute the same code with different arguments, e.g.:\n\n```python\nresulted_execution("x = 10\\ny = x + 5\\nprint(x, y)").rexec()\n# prints 10, 15 twice\n```"""

        code: str | ReadableBuffer | CodeType
        locals: dict[str, object] | None
        globals: dict[str, Any] | None
        if sys.version_info >= (3, 11):
            closure: tuple[CellType, ...] | None
        rexec = rexecution_function
        module: ModuleType

    class Scoper:
        def dir(self) -> Iterable[str]: """Implements dir(obj)"""
        def obj(self) -> Any: """The object you passed as an argument in the `scope_context` function"""
        def vars(self) -> dict[str, Any] | MappingProxyType[str, Any]: """Implements vars(obj)"""
        def end_access(self): """Ends the access to the objects attributes"""
        def disable_scope_shield(self): """It doesn't treat the scope as a local scope so the object attributes will still exist."""

    class ScopeContext:

        def __enter__(self) -> ReadOnly.Scoper: """Implement the object attribute revealing operation."""

class GreatLambda:
    """Used to make Great Anonymous functions, Here is a Sync Example:\n\n```python\nf = (\n\tGreatLambda()\n\t\t.setargs(inspect.Signature([\n\t\t\tinspect.Parameter("x", inspect.Parameter.POSITIONAL_ONLY),\n\t\t]))\n\t\t.func_level_exec("return x * 2")\n\t\t.function\n)\nprint(f(5)) # 10"""
    def setargs(self, sig: Signature) -> GreatLambda: """Set the arguments of the function using `inspect.Signature`"""
    if sys.version_info >= (3, 11):
        def func_level_exec(self, code: str | ReadableBuffer | CodeType, /, globals: dict[str, Any] | None = None, *, closure: tuple[CellType, ...] | None = None) -> GreatLambda: """Here, you type the body of the function, It has the same arguments like the one in `exec`"""
    else:
        def func_level_exec(self, code: str | ReadableBuffer | CodeType, /, globals: dict[str, Any] | None = None) -> GreatLambda: """Here, you type the body of the function, It has the same arguments like the one in `exec`"""
    def asnc(self, asnc: bool = False) -> GreatLambda: """Decide whether your function should be sync or async (async -> `True`, sync -> `False`)"""

    @property
    def function(self) -> Union[Callable[..., Any], Callable[..., CoroutineType[Any, Any, Any]]]: """THE MOST IMPORTANT: The resulted function"""

def export(**childmapping: Any) -> None: """Sets the variables that the module should export, e.g.:\n\n```python\nexport(foo=my_function, bar=my_var, abc=123)"""

if sys.version_info >= (3, 11):
    def resulted_execution(source: str | ReadableBuffer | CodeType, /, globals: dict[str, Any] | None = None, locals: dict[str, object] | None = None, *, closure: tuple[CellType, ...] | None = None) -> ReadOnly.ExecutionResults: """Dynamic Execution with Results, e.g.:\n\n```python\nresult = resulted_execution("def my_function(a,b): return a + b")\n```\nNow, the `result` variable contains the following attributes:\n\n- `result.locals`\n- `result.globals`\n- `result.code`\n- `result.closure`\n- `result.module` (object with attributes mapped from locals)\n- `result.rexec()` for re-execution"""
else:
    def resulted_execution(source: str | ReadableBuffer | CodeType, /, globals: dict[str, Any] | None = None, locals: dict[str, object] | None = None) -> ReadOnly.ExecutionResults: """Dynamic Execution with Results, e.g.:\n\n```python\nresult = resulted_execution("def my_function(a,b): return a + b")\n```\nNow, the `result` variable contains the following attributes:\n\n- `result.locals`\n- `result.globals`\n- `result.code`\n- `result.closure`\n- `result.module` (object with attributes mapped from locals)\n- `result.rexec()` for re-execution"""

__T1__ = TypeVar('__T1__')
__T2__ = TypeVar('__T2__')

def extend(cls1: __T1__, cls2: __T2__, /, **extra_attributes) -> __T1__|__T2__: """Extends `cls1` with `cls2` by adding `cls2` to the bases of `cls1`, and it also extends a namespace of attributes (`**extra_attributes`), e.g.:\n\n```python\nclass A:\n\tdef start(self):\n\t\tprint("let's go!")\nclass B:\n\tdef end(self):\n\t\tprint("Bye!")\nC = extend(A, B, abc=123)\nC().start() # let's go!\nC().end() # Bye!\nprint(C.abc) # 123"""

def scope_context(obj) -> ReadOnly.ScopeContext: """Returns an object that is when used with the `with` keyword (entered) It reveals all object's attributes at the `with` scope, and it returns an object that is called `Scoper` has 5 methods `dir()`, `vars()`, `obj()`, `end_access()` (to the attributes) and `disable_scope_shield` from being local-only so the attributes are still available even after exiting the context and using `disable_scope_shield` will also `end_access`, e.g.:\n\n```python\nwith scope_context(resulted_execution("message='Hello World'\\nadd = lambda a, b: a + b\\nclass MyClass:\\n\\tdef __init__(self): print('MyClass initialized!')")) as scoper:\n\tprint('LOCALS:\\n\\n', locals, '\\n\\nCODE:\\n\\n', code, '\\n\\nMODULE:\\n\\n', module)\n\tprint(module.message, module.add(2, 3), module.MyClass())\n\tscoper.end_access()\n\ttry:\n\t\tmodule\n\texcept NameError as e:\n\t\tprint(e)\n\tnontemp = "This won't be temp by disable_scope_shield"\n\tscoper.disable_scope_shield()\nprint(nontemp) # This won't be ...\n```"""

class constructor:
    """construct an object using this decorator with a function e.g.:\n\n```python\n@constructor\ndef construct(self):\n\tself.x = 123\n\tself.data = [5]\nobj = construct()\nprint(obj.x)\nobj.data.append(1)\nprint(obj.data)\n```"""
    def __init__(self, func): """construct an object using this decorator with a function e.g.:\n\n```python\n@constructor\ndef construct(self):\n\tself.x = 123\n\tself.data = [5]\nobj = construct()\nprint(obj.x)\nobj.data.append(1)\nprint(obj.data)\n```"""
    def __call__(self, *args, **kwds) -> object: ...
