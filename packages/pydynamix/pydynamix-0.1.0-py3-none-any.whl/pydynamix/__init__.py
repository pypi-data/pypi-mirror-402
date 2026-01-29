import re, os, dis, sys, types, inspect, textwrap
from functools import update_wrapper
from types import ModuleType

class ModuleVariableShield(types.ModuleType):

    def __setattr__(self, name, value):
        if not hasattr(self, "_shield_ready"):
            object.__setattr__(self, name, value)
            return
        if (os.path.abspath(sys._getframe(1).f_code.co_filename) != os.path.abspath(__file__)
        and name not in {"setvar", "getvar", "takevar", "delvar", "clearvars", "export", "GreatLambda"}):
            raise ValueError("Variable Shield detected unwanted actions")
        super().__setattr__(name, value)

    def setvar(self, name, value):
        self.__variables[name] = value

    def getvar(self, name, default):
        return self.__variables.get(name, default)

    def takevar(self, name):
        return self.__variables[name]

    def delvar(self, name):
        del self.__variables[name]

    def clearvars(self):
        self.__variables = {}

    class GreatLambda:

        __slots__ = ("__executor","__globals","__is_async","__sig","__closure","__cached_function")
        def __setattr__(self, name, value):
            frame = inspect.currentframe()
            try: caller_file = os.path.abspath(frame.f_back.f_code.co_filename)
            finally: del frame
            if (caller_file != os.path.abspath(inspect.getsourcefile(type(self)) or inspect.getfile(type(self)))
                and name not in {'_GreatLambda__executor','_GreatLambda__globals','_GreatLambda__sig','_GreatLambda__asnc','_GreatLambda__closure'}):
                raise ValueError('Setting Attributes is restricted for this class')
            object.__setattr__(self, name, value)

        def __init__(self):
            self.__executor = ""
            self.__globals = {"__builtins__": __builtins__}
            self.__is_async = False
            self.__sig = inspect.Signature()
            self.__cached_function = None
            self.__closure = ()

        def asnc(self, value: bool = False):
            self.__is_async = value
            self.__cached_function = None
            return self

        if sys.version_info >= (3, 11):
            def func_level_exec(self, code: str, globals=None, *, closure=None):
                self.__closure = closure
                self.__executor = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]','',code)
                if globals is not None:
                    self.__globals = globals
                self.__cached_function = None
                return self
        else:
            def func_level_exec(self, code: str, globals=None):
                self.__executor = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]','',code)
                if globals is not None:
                    self.__globals = globals
                self.__cached_function = None
                return self

        def setargs(self, sig: inspect.Signature):
            self.__sig = sig
            self.__cached_function = None
            return self

        @property
        def function(self):
            if self.__cached_function is not None:
                return self.__cached_function

            params = ", ".join(self.__sig.parameters)
            body = textwrap.indent(self.__executor, "    ")

            src = f"{'async ' if self.__is_async else ''}"f"def _greatlambda({params}):\n{body}"
            ns = {}
            if sys.version_info >= (3, 11):
                exec(src, self.__globals, ns, closure=self.__closure)
            else:
                exec(src, self.__globals, ns)
            func = ns["_greatlambda"]
            func.__signature__ = self.__sig
            update_wrapper(func, func)
            self.__cached_function = func
            return func

    def export(self, **childmapping):
        globs = inspect.currentframe().f_back.f_globals
        for name in list(globs):
            if name not in {'__annotations__', '__builtins__', '__cached__', '__dict__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__path__', '__spec__'}:
                globs.pop(name, None)
        globs.update(childmapping)

    def extend(self, cls1, cls2, /, **extra_attributes):
        return type(cls1.__name__, (cls1, cls2,), extra_attributes)

    def resulted_execution(self, source, /, globals = None, locals = None, *, closure = None):
        if globals is None or globals == {}: globals = {"__builtins__": __builtins__}
        if locals is None or locals == {}: locals = globals
        if closure is not None and sys.version_info >= (3, 11): exec(source, globals, locals, closure=closure)
        else: exec(source, globals, locals)
        result_obj = type('ExecutionResults', (object,), {})()
        result_obj.locals = locals
        result_obj.globals = globals
        result_obj.code = source
        if sys.version_info >= (3, 11):
            result_obj.closure = closure
            result_obj.rexec = lambda globals = globals, locals = locals, *, closure = closure: self.resulted_execution(source, globals, locals, closure=closure)
        else:
            result_obj.rexec = lambda globals = globals, locals = locals: self.resulted_execution(source, globals, locals)
        result_obj.module = type('ModuleType', (object,), {})()
        for name, val in locals.items(): setattr(result_obj.module, name, val)
        return result_obj

    def scope_context(self, obj):
        glbs = inspect.currentframe().f_back.f_globals
        oldglbs = glbs.copy()
        scope_shield = True
        class ScopeContext:
            def __enter__(self):
                glbs.update(vars(obj))
                class Scoper:
                    def obj(self): return obj
                    def dir(self): return dir(obj)
                    def vars(self): return vars(obj)

                    def end_access(self):
                        for name in dir(obj):
                            glbs.pop(name, None)

                    def disable_scope_shield(self):
                        nonlocal scope_shield
                        self.end_access()
                        scope_shield = False
                return Scoper()

            def __exit__(self, *_):
                if scope_shield:
                    glbs.clear()
                    glbs.update(oldglbs)

        return ScopeContext()
    
    class constructor:
        def __init__(self, func):
            self.__func = func

        def __call__(self, *args, **kwds):
                func = self.__func
                new_globals = func.__globals__.copy()
                new_globals['self'] = type('ConstructorObject', (object,), {})
                new_func = types.FunctionType(func.__code__,new_globals,func.__name__,func.__defaults__,func.__closure__)
                new_func(new_globals['self'], *args, **kwds)
                return new_globals['self']()

sys.modules[__name__].__class__ = ModuleVariableShield

object.__setattr__(sys.modules[__name__], "_ModuleVariableShield__variables", {})

object.__setattr__(sys.modules[__name__], "_shield_ready", True)
