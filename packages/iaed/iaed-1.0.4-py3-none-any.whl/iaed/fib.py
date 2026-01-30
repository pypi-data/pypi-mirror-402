''' Termos da sequência de Fibonacci

    >>> from iaed import fib
    >>> fib.recurs(35)
    >>> fib.iter(35)
'''
from time import time

def recurs(n):
    ''' Cálculo recursivo do N-ésimo termo da sequência de Fibonacci '''
    if n < 2:
        return n
    return recurs(n - 2) + recurs(n - 1)

def iter(n):
    ''' Cálculo iterativo do N-ésimo termo da sequência de Fibonacci '''
    a, b = 0, 1
    while n > 1:
        a, b, n = b, a+b, n-1
    return b

def test(n):
    start = time()
    print("recurs", recurs(n), "em", time()-start, "seg")
    start = time()
    print("iter", iter(n), "em", time()-start, "seg")
