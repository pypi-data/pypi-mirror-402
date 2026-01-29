
import traceback
from fattrace import install

def fn1():
    a = 1
    b = 0
    fn2(a,b)

def fn2(a,b):
    return a/b


install()
fn1()
