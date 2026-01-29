#!/usr/bin/env python3

import os
import os.path
import sys, traceback, types, linecache
from functools import partial
from colors import red, blue, yellow, green

def err(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)
    pass


def get(o,key):
    if isinstance(o, dict):
        return o[key]
    else:
        return getattr(o, key)


def remove_array(thing):
    available_arraylike_fields = [
        name
        for name in ["dtype","shape","device","layout"]
        if hasattr(thing, name)
    ]
    if len(available_arraylike_fields) > 0:
        return "<"+" ".join([
            type(thing).__name__,
            *[ str(getattr(thing,name)) for name in available_arraylike_fields ]])+">"
    else:
        return thing


def print_locals(o,
                 threshold:int=3,
                 include_self:bool=True,
                 include_private:bool=False,
                 ignore:set[str]=set(),
                 ignore_type:set[type]=set(),
                 ):
    maxlinelen=1000
    maxlen=20
    ignore_type = set(ignore_type)
    ignore = set(ignore)
    ignore_type |= {types.FunctionType, types.ModuleType, type}

    def include(o,key) -> bool:
        "Filter rule for inclusion. If it returns false, the object and the key will be ignored."
        return (include_private or not key.startswith("__"))  \
          and (key not in ignore)                             \
          and (not isinstance(get(o,key),tuple(ignore_type)))

    def printer(thing):
        if isinstance(thing,list):
            if len(thing) > threshold:
                return [printer(remove_array(o)) for o, _ in [*list(zip(thing, range(threshold))),(f"...<{len(thing)-threshold} more>",None)]]
            else:
                return [printer(remove_array(o)) for o in thing]
        elif isinstance(thing,tuple):
            if len(thing) > threshold:
                return tuple([printer(remove_array(o)) for o in [*list(zip(thing, range(threshold))),(f"...<{len(thing)-threshold} more>",None)]])
            else:
                return tuple([printer(remove_array(o)) for o in thing])
        elif isinstance(thing,dict):
            return {k:printer(remove_array(v)) for k,v in thing.items()}
        elif isinstance(thing,str):
            msg = "...(truncated by fattrace)..."
            if len(thing) >= 500:
                to_show = (500-len(msg))//2
                return thing[:to_show]+msg+thing[-to_show:]
            else:
                return thing
        elif isinstance(thing,bytes):
            return thing[:500]
        else:
            return remove_array(thing)

    def multi_indent(width,string):
        lines = [ line[:maxlinelen] for line in string.splitlines() ]
        return ("\n"+" "*width).join(lines)

    try:
        zip(o)
    except TypeError:
        print(o)
        return

    for key in o:
        try:
            if include(o,key):
                maxlen = max(maxlen,len(key))
                if include_self and (key == "self"):
                    __self = get(o,key)
                    for key in vars(__self):
                        if include(__self,key):
                            maxlen = max(maxlen,len(key)+5) # + 5 for "self."
        except Exception as e:
            print(e)
            pass

    maxlen += 10                # buffer

    for key in o:
        if include(o,key):
            try:
                err("{} = {}".format(yellow(str(key)).rjust(maxlen+4), # +4 for ANSI color
                                     multi_indent(maxlen-2,repr(printer(get(o,key)))))) # +4+3 for " = "
            except Exception as e:
                err("{} = Error printing {} : {}".format(red(str(key)).rjust(maxlen+4),
                                                         type(get(o,key)),
                                                         e))
            if include_self and (key == "self"):
                __self = get(o,key)
                try:
                    vars_dict = vars(__self)
                except TypeError as e: # vars() argument must have __dict__ attribute
                    err("{} = Error printing self : {}".format(red(str(key)).rjust(maxlen+4), e))
                    continue

                for key in vars_dict:
                    if include(__self,key):
                        try:
                            err("{} = {}".format((green("self")+"."+yellow(str(key))).rjust(maxlen+13), # 5+2*4 for double ANSI color
                                                 multi_indent(maxlen-2,repr(printer(get(__self,key))))))
                        except Exception as e:
                            err("{} = Error printing {} : {}".format(red("self."+str(key)).rjust(maxlen+4),
                                                                     type(get(__self,key)),
                                                                     e))


def is_under_cwd(path):
    pwd = os.getcwd()
    return pwd == os.path.commonpath([pwd, os.path.abspath(path)])


def __format(type, value, tb,
             threshold:int=3,
             include_self:bool=True,
             include_private:bool=False,
             include_external:bool=False,
             ignore:set[str]=set(),
             ignore_type:set[type]=set(),
             ):
    err("Fat Traceback (most recent call last):")

    for f, f_lineno in traceback.walk_tb(tb):
        co = f.f_code
        f_filename = co.co_filename
        f_name = co.co_name
        linecache.lazycache(f_filename, f.f_globals)
        f_locals = f.f_locals
        f_line = linecache.getline(f_filename, f_lineno).strip()

        if include_external or is_under_cwd(f_filename):
            err(" ",
                green("File"),
                os.path.relpath(f_filename),
                green("line"),
                f_lineno,
                green("function"),
                f_name,":",f_line)
            print_locals(f_locals,
                         threshold       = threshold,
                         include_self    = include_self,
                         include_private = include_private,
                         ignore          = ignore,
                         ignore_type     = ignore_type,)
            err()
        else:
            err(" ",
                yellow("Skipped"),
                green("File"),
                os.path.relpath(f_filename),
                green("line"),
                f_lineno,
                green("function"),
                f_name,":",f_line,
                )

    err()
    err(*(traceback.format_exception_only(type,value)))


def format(exit=True,
           threshold:int=3,
           include_self:bool=True,
           include_private:bool=False,
           include_external:bool=False,
           ignore:set[str]=set(),
           ignore_type:set[type]=set(),
           ):
    type, value, tb = sys.exc_info()
    __format(type, value, tb,
             threshold        = threshold,
             include_self     = include_self,
             include_private  = include_private,
             include_external = include_external,
             ignore           = ignore,
             ignore_type      = ignore_type,)
    if exit:
        sys.exit(1)


def install(threshold:int=3,
            include_self:bool=True,
            include_private:bool=False,
            include_external:bool=False,
            ignore:set[str]=set(),
            ignore_type:set[type]=set(),
            ):
    sys.excepthook = partial(
        __format,
        threshold        = threshold,
        include_self     = include_self,
        include_private  = include_private,
        include_external = include_external,
        ignore           = ignore,
        ignore_type      = ignore_type,)



