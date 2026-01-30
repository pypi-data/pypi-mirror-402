#! /usr/bin/env python3
''' Algoritmos de ordenação


    >>> from iaed import sorting
    >>> v = [34, 3, 36, 11, 8, 4, 22, 20, 12]
    >>> sorting.dbg = True # ver cada iterada
    >>> sorting.selection(v)

    Em algoritmos recursivos pode ser necessário aumentar o limite de recursão:
    >>> from sys import setrecursionlimit
    >>> setrecursionlimit(50000)
'''
from random import randint
from timeit import timeit

dbg = False # debug
''' para cada iterada colocar a True '''

def run(algorithm, array, pkg = 'iaed.sorting') :
    ''' Execução temporizada
        >>> from iaed import sorting
        >>> sorting.dbg = True # ver cada iterada
        >>> sorting.run("bubble", sorting.mkarray(12,100))
    '''
    return timeit(f"{algorithm}({array})",f"from {pkg} import {algorithm}", number=1)

# from iaed.sorting import bubble
# timeit(f"{algorithm}({array})",f"from __main__ import {algorithm}", number=1)

def mkarray(length, high=1000, low=0) :
    ''' Cria vetor com valores inteiros aleatórios '''
    return [ randint(low, high) for _ in range(length) ]

lower = 'abcdefghijklmnopqrstuvwxyz'
upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
digit = '0123456789'
hexdigit = '0123456789ABCDEF'
charset = lower + upper + digit
charspc = charset + ' '
def rndstr(length, chars = charset):
    ''' Cria uma cadeia de carateres com o comprimento dado (length)
        constituída por carateres do conjunto dado (chars) '''
    out = ''
    for _ in range(length):
        out += chars[randint(0,len(chars)-1)]
    if out[0] == ' ' or out[-1] == ' ':
        return rndstr(length, chars)
    return out

def mkstrvec(length, width, chars = charset):
    ''' Cria um vetor de cadeias de carateres '''
    return [ rndstr(width, chars) for _ in range(length) ]

def bubble0(array) :
    ''' Ordenação por borbulhamento (esq -> dir)'''
    n = len(array)
    for i in range(n) :
        for j in range(n - i - 1) : # left to right
            if array[j] > array[j+1] :
                array[j], array[j+1] = array[j+1], array[j]
        if dbg:
            print(array)
    return array

def bubble1(array) :
    ''' Ordenação por borbulhamento invertido (dir -> esq)'''
    n = len(array) -1
    for i in range(n) :
        for j in range(n, i, -1) : # right to left
            if array[j] < array[j-1] :
                array[j], array[j-1] = array[j-1], array[j]
        if dbg:
            print(array)
    return array

def bubble(array) :
    ''' Ordenação por borbulhamento ótimizado (esq -> dir)'''
    n = len(array)
    for i in range(n) :
        is_sorted = True
        for j in range(n - i - 1) :
            if array[j] > array[j+1] :
                array[j], array[j+1] = array[j+1], array[j]
                is_sorted = False
        if is_sorted :
            break
        if dbg:
            print(array)
    return array

def insertion(array) :
    ''' Ordenação por inserção '''
    for i in range(1, len(array)) :
        item = array[i]
        j = i - 1
        while j >= 0 and array[j] > item :
            array[j + 1] = array[j]
            j -= 1
        array[j + 1] = item
        if dbg:
            print(array)
    return array

# selection([15,14,12,24,18,11,21,48,32])
def selection(array) :
    ''' Ordenação por seleção '''
    for i in range(len(array)) :
        pos = i
        for j in range(i+1, len(array)) :
            if array[pos] > array[j] :
                pos = j
        array[pos], array[i] = array[i], array[pos]
        if dbg:
            print(array)
    return array

def shell(array) :
    ''' Ordenação Shell '''
    h = 1
    while h <= len(array) // 9 :
        h = 3 * h + 1

    while h > 0 :
        for i in range(h, len(array)) :
            j = i
            item = array[i]
            while j >= h and item <= array[j - h]:
                array[j] = array[j - h]
                j -= h
            array[j] = item
        h //= 3
        if dbg:
            print(array)
    return array

def partition(a, l, r) :
    ''' Partição de um vetor no QuickSort '''
    i, j, pivot = l, r -1, a[r]
    while i <= j :
        while a[i] <= pivot and i <= j :
            i += 1
        while pivot <= a[j] and j >= i :
            j -= 1
        if i < j :
            a[i], a[j] = a[j], a[i]
    a[i], a[r] = a[r], a[i]
    return i

def quick(array, l=0, r=None) :
    ''' Ordenação rápida (Quick)'''
    if r is None :
        r = len(array) -1
    if r <= l :
        return array
    # if r-l <= M : return insertion(a, l, r)
    i = partition(array, l, r)
    quick(array, l, i-1)
    quick(array, i+1, r)
    return array

def merge_sorted(a, b) :
    ''' Fusão de dois vetores ordenados '''
    if len(a) == 0 :
        return b
    if len(b) == 0 :
        return a
    ret = []
    i = j = 0
    while len(ret) < len(a) + len(b) :
        if a[i] <= b[j] :
            ret += [ a[i] ]
            i += 1
            if i == len(a) :
                break
        else :
            ret += [ b[j] ]
            j += 1
            if j == len(b) :
                break
    return ret + a[i:] + b[j:]

def merge(array) :
    ''' Ordenação por fusão '''
    if len(array) < 2 :
        return array
    mid = len(array) // 2
    return merge_sorted(merge(array[:mid]), merge(array[mid:]))

def parent(k):
    ''' Índice do elemento hierarquicamente anterior (pai) '''
    return (k+1)//2-1
def left(k):
    ''' Índice do subelemento hieraequicamente à esquerda (filho esquerdo) '''
    return 2*k+1
def right(k):
    ''' Índice do subelemento hieraequicamente à direita (filho direita) '''
    return 2*(k+1)
def fix_down(a, l, r, k) :
    ''' Recolocação descendente do elemento índice k '''
    largest, ileft, iright = k, left(k), right(k)
    if ileft <= r and a[largest] < a[ileft] :
        largest = l + left(k-l)
    if iright <= r and a[largest] < a[iright] :
        largest = l + right(k-l)
    if largest != k :
        a[k], a[largest] = a[largest], a[k]
        fix_down(a, l, r, largest)
def fix_up(vec, k):
    ''' Recolocação ascendente do elemento índice k '''
    while k > 0 and vec[parent(k)] < vec[k]:
        vec[k], vec[parent(k)] = vec[parent(k)], vec[k]
        k = parent(k)
def insert(vec, item):
    ''' Insere um elemento num amontoado '''
    vec += [item]
    fix_up(vec, len(vec)-1)
def remove(vec):
    ''' Remove um elemento de um amontoado '''
    item, vec[0], vec[-1] = vec[0],  vec[-1], vec[0]
    fix_down(vec, 0, len(vec)-2, 0)
    del vec[-1]
    return item
def buildheap(a, l=0, r=None) :
    ''' Constrói um amontoado '''
    if r is None :
        r = len(a)-1
    heapsize = r-l+1
    k = heapsize//2-1
    while k >= l :
        fix_down(a, l, r, l+k)
        k -= 1
def heapsort(a, l=0, r=None) :
    ''' Ordenação por amontoado '''
    if r is None :
        r = len(a)-1
    buildheap(a, l, r)
    if dbg:
        print('build',a)
    while r - l > 0 :
        a[l], a[r] = a[r], a[l]
        r -= 1
        fix_down(a, l, r, l)
        if dbg:
            print(a)
    return a

def distcount(a, M=1000) :
    ''' counting sort with M keys in [0,999] '''
    cnt = [0] * (M+1)
    b = [0] * len(a)
    for i in range(len(a)) :
        cnt[a[i]+1] += 1
    for j in range(M) :
        cnt[j+1] += cnt[j]
    for i in range(len(a)) :
        b[cnt[a[i]]] = a[i]
        cnt[a[i]] += 1
    return b

def distcount2(a, M=1000) :
    ''' backward counting sort with M keys in [0,999] '''
    cnt = [0] * M
    b = [0] * len(a)
    for i in range(len(a)) :
        cnt[a[i]] += 1
    for j in range(M-1) :
        cnt[j+1] += cnt[j]
    for i in range(len(a)) :
        cnt[a[i]] -= 1
        b[cnt[a[i]]] = a[i]
    return b

def radixLSD(a, M, bytesword, digit) :
    ''' Ordenação radix Least Significant Digit (LSD) first

    sort a vector of two (2) decimal (10) digits:
    radixLSD([15,14,12,24,18,11,21,48,32],10,2,lambda x,y: int(str(x)[y]))

    sort a vector of integers upto 6-bits with 2-bits (4 possible values) at a time
    (3-sets of 2-bits is a 6-bit number: between 0 and 63)
    radixLSD(v, 4, 3, lambda x,y: int(('0'*6+bin(x)[2:])[-6:][(y*2:(1+y)*2],2))
    '''
    while bytesword > 0 :
        bytesword -= 1
        count = [0] * (M + 1)
        aux = [0] * len(a)
        for i in range(len(a)) :
            count[digit(a[i], bytesword) + 1] += 1
        for j in range(M) :
            count[j+1] += count[j]
        for i in range(len(a)) :
            aux[count[digit(a[i], bytesword)]] = a[i]
            count[digit(a[i], bytesword)] += 1
        a = list(aux)
        if dbg:
            print(a)
    return a

def quicksortBin(a, l, r, w, bitsword) :
    ''' Binary Quick sort '''
    def digit(a,b) :
        return (a >> (bitsword-b)) & 1
    if r <= l or w > bitsword :
        return None
    i, j = l, r
    while j != i :
        while digit(a[i], w) == 0 and i < j :
            i += 1
        while digit(a[j], w) == 1 and j > i :
            j -= 1
        a[i], a[j] = a[j], a[i]
    if digit(a[r], w) == 0 :
        j += 1
    quicksortBin(a, l, j-1, w+1, bitsword)
    quicksortBin(a, j, r, w+1, bitsword)
    return a

def quicksortBinv(a, l, r, w, bitsword) :
    ''' Binary Quick sort inverted '''
    def digit(a,b) :
        return (a >> b) & 1
    if r <= l or w < 0 :
        return None
    i, j = l, r
    while j != i :
        while digit(a[i], w) == 0 and i < j :
            i += 1
        while digit(a[j], w) == 1 and j > i :
            j -= 1
        a[i], a[j] = a[j], a[i]
    if digit(a[r], w) == 0 :
        j += 1
    quicksortBinv(a, l, j-1, w-1, bitsword)
    quicksortBinv(a, j, r, w-1, bitsword)
    return a

def insertion_sort(array, l=0, r=None):
    ''' Insertion sort for radix MSD '''
    if r is None:
        r = len(array) - 1
    for i in range(l + 1, r + 1):
        item = array[i]
        j = i - 1
        while j >= l and array[j] > item:
            array[j + 1] = array[j]
            j -= 1
        array[j + 1] = item
    return array

def radixMSD(a, l, r, w, bytesword, digit, M, ins=32) :
    ''' Ordenação radix Most Significant Digit (MSD) first

    sort a vector of decimal values (M=10) with up to three (bytesword=3) digits:
    v = [198, 981, 136, 448, 148, 445, 827, 442, 133]
    radixMSD(v, 0, 8, 0, 3, lambda x, y: int(str(x)[y]), 10, ins=0)
    '''
    def bin(x): return l+count[x]
    if r <= l: return a
    if dbg: print('radix:', w, 'digit from', l, 'to', r, '=', a[l:r+1])
    if w > bytesword :
        return a
    if r-l <= ins :
        insertion_sort(a, l, r)
        return a
    count = [0] * (M + 1)
    aux = [0] * (r -l + 1)
    for i in range(len(aux)) :
        count[digit(a[l+i], w) + 1] += 1
    for j in range(M) :
        count[j+1] += count[j]
    for i in range(len(aux)) :
        aux[count[digit(a[l+i], w)]] = a[l+i]
        count[digit(a[l+i], w)] += 1
    for i in range(len(aux)) :
        a[l+i] = aux[i]
    radixMSD(a, l, bin(0)-1, w+1, bytesword, digit, M, ins)
    for j in range(M-1) :
        radixMSD(a, bin(j), bin(j+1)-1, w+1, bytesword, digit, M, ins)
    return a

# insertion_sort array slices and merge_sorted them
# https://github.com/python/cpython/blob/main/Objects/listobject.c #2191
# min_run: https://hg.python.org/cpython/file/tip/Objects/listsort.txt
def timsort(array): # O(n log2 n)
    ''' Ordenação timsort '''
    min_run = 32
    n = len(array)
    for i in range(0, n, min_run): # sort each sliced sub-array
        insertion_sort(array, i, min((i + min_run - 1), n - 1))
    size = min_run
    while size < n: # merge from min_run to n
        for start in range(0, n, size * 2):
            midpoint = start + size - 1
            end = min((start + size * 2 - 1), (n-1))
            merged_array = merge_sorted(
                array[start:midpoint + 1],
                array[midpoint + 1:end + 1])
            array[start:start + len(merged_array)] = merged_array
        size *= 2 # double size at each iteration
    return array

if __name__ == "__main__" :
    from sys import argv, setrecursionlimit
    from time import time
    setrecursionlimit(50000)
    if len(argv) == 1 :
        print('USAGE:', argv[0], ' count [algorithm/value]')
        print('\tSorting: bubble0, bubble1, bubble, insertion, selection,')
        print('\t\tshell, quick, merge, heapsort, distcount, distcount2')
    if len(argv) == 2 :
        v = mkarray(int(argv[1]))
        t = time()
        bubble0(v)
        print('bubble0:', time()-t)
        t = time()
        bubble1(v)
        print('bubble1:', time()-t)
        t = time()
        bubble(v)
        print('bubble:', time()-t)
        t = time()
        insertion(v)
        print('insertion:', time()-t)
        t = time()
        selection(v)
        print('selection:', time()-t)
        t = time()
        shell(v)
        print('shell:', time()-t)
        t = time()
        quick(v)
        print('quick:', time()-t)
        t = time()
        merge(v)
        print('merge:', time()-t)
        t = time()
        heapsort(v)
        print('heap:', time()-t)
        t = time()
        timsort(v)
        print('tim:', time()-t)
        t = time()
        v.sort()
        print('sort:', time()-t)
    if len(argv) == 3 :
        if argv[2].isnumeric() :
            from iaed.search import search, sorted_search, binary_search
            v = mkarray(int(argv[1]))
            v.sort()
            t = time()
            p = search(v, int(argv[2]))
            print('search: #', p, time()-t)
            t = time()
            p = sorted_search(v, int(argv[2]))
            print('sorted: #', p, time()-t)
            t = time()
            p = binary_search(v, int(argv[2]))
            print('binary: #', p, time()-t)
        else :
            f = locals()[argv[2]]
            t = time()
            f(mkarray(int(argv[1])))
            print(argv[2] + ':', time()-t)
