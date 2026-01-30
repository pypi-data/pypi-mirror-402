''' Algoritmos de pesquisa

    Exemplo:
    >>> from iaed import search
    >>> from random import randint
    >>> l = [ randint(0, 100) for _ in range (20) ]
    >>> search.search(l, 12)
    >>> l.sort()
    >>> search.sorted_search(l, 12)
    >>> search.binary_search(l, 12)
'''
from random import randint
from time import time

def binary_search(array, value, l=0, r=None) : # array must be sorted
    ''' Pesquisa binária em vetor ordenado '''
    if r is None:
        r = len(array) # return index or None
    print(l, r)
    if r <= l :
        return None
    mid = l + (r - l) // 2
    if array[mid] == value :
        return mid
    if array[mid] > value :
        return binary_search(array, value, l, mid-1)
    return binary_search(array, value, mid+1, r)

def sorted_search(array, value) : # array must be sorted
    ''' Pesquisa linear ordenada '''
    for pos, val in enumerate(array) :
        if val == value :
            return pos
        if val > value :
            return None # give up
    return None

def search(array, value) :
    ''' Pesquisa linear '''
    for pos, val in enumerate(array) :
        if val == value :
            return pos
    return None

def mklistset(length=10000, high=100000):
    ''' Cria um vetor de 'length' inteiros entre 0 e 'high' '''
    s = set([randint(0, high) for _ in range(length)])
    return s, list(s)

def search_set(s, vec):
    ''' Procura num conjunto 's' cada um dos elementos em 'vec'.
        Retorna o tempo gasto (seg) e o número de elementos encontrados.'''
    count = 0
    start = time()
    for x in range(vec):
        if x in s:
            count += 1
    return time - start, count

def search_list(l, vec):
    ''' Procura numa lista 'l' cada um dos elementos em 'vec'.
        Retorna o tempo gasto (seg) e o número de elementos encontrados.'''
    count = 0
    start = time()
    for x in range(vec):
        if x in l:
            count += 1
    return time - start, count

def search_test(length=10000, count=10000):
    ''' Compara tempos de pesquisa em lista e set. '''
    l, s = mklistset(length)
    _, vec = mklistset(count)
    print("set", search_set(s, vec))
    print("list", search_list(l, vec))
