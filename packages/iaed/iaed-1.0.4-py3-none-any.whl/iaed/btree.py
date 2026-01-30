''' Operações em árvores de pesquisa binárias (BST) [não equilibradas]

    Exemplo:
    >>> from iaed.btree import Btree
    >>> x = Btree()
    >>> for i in (12, 6, 8, 16, 24, 7, 15, 2, 21):
    >>>     x.insert(i)
    >>> x.preorder()
    >>> x.posorder()
    >>> x.order()
'''

class _node:
    ''' Nó da árvore '''
    def __init__(self, value, left=None, right=None):
        ''' Cria um nó '''
        self._value = value
        self._left = left
        self._right = right
    def value(self, val = ...):
        ''' Valor do nó '''
        if val != ...:
            self._value = val
        return self._value
    def left(self, val = ...):
        ''' Sub-nó esquerdo '''
        if val != ...:
            self._left = val
        return self._left
    def right(self, val = ...):
        ''' Sub-nó direito '''
        if val != ...:
            self._right = val
        return self._right

class Btree:
    ''' Árvore binária '''
    def __init__(self, keyf = lambda x: x):
        ''' keyf: função que devolve a chave de um nó '''
        self._tree = None
        self._keyf = keyf

    def insert(self, value):
        ''' Operação de inserção '''
        def _insert(node, keyf, value):
            ''' Insere um nó numa subárvore '''
            if not node: # new node
                return _node(value)
            cmp = keyf(value) - keyf(node.value())
            if not cmp: # replace node
                return _node(value)
            if cmp < 0: # go left
                node.left(_insert(node.left(), keyf, value))
            else: # go right
                node.right(_insert(node.right(), keyf, value))
            return node
        self._tree = _insert(self._tree, self._keyf, value)

    def search(self, key):
        ''' Operação de procura '''
        def _search(node, keyf, key):
            ''' Procura um nó numa subárvore '''
            if not node:
                return None
            cmp = key - keyf(node.value())
            if not cmp:
                return node.value()
            if cmp < 0:
                return _search(node.left(), keyf, key)
            return _search(node.right(), keyf, key)
        return _search(self._tree, self._keyf, key)

    def max(self):
        ''' Devolve o valor do maior nó da árvore '''
        node = self._tree
        if not node:
            return None
        while node.right():
            node = node.right()
        return node.value()

    def min(self):
        ''' Devolve o valor do menor nó da árvore '''
        node = self._tree
        if not node:
            return None
        while node.left():
            node = node.left()
        return node.value()

    def remove(self, key):
        ''' Operação de remoção '''
        def _remove(node, keyf, key):
            ''' Remove um nó de uma subárvore '''
            if not node:
                return None
            cmp = key - keyf(node.value())
            if cmp < 0:
                node.left(_remove(node.left(), keyf, key))
            elif cmp > 0:
                node.right(_remove(node.right(), keyf, key))
            else:
                if node.left() and node.right(): # caso 3
                    aux = node.left() # find highest value
                    while aux.right():
                        aux = aux.right()
                    aux._value, node._value = node.value(), aux.value()
                    node.left(_remove(node.left(), keyf, aux.value()))
                else:
                    if not node.left() and not node.right():
                        node = None
                    elif not node.left():
                        node = node.right()
                    else:
                        node = node.left()
            return node
        self._tree = _remove(self._tree, self._keyf, key)

    def count(self):
        ''' Devolve o número de nós numa árvore '''
        def _count(node):
            ''' Devolve o número de subnós de um nó '''
            if not node:
                return 0
            return 1 + _count(node.left()) + _count(node.right())
        return _count(self._tree)

    def height(self):
        ''' Devolve a altura máxima de uma árvore '''
        def _height(node):
            ''' Devolve a altura máxima de um nó '''
            if not node:
                return 0 # -1 for height(leaf)==0
            hleft = _height(node.left())
            hright = _height(node.right())
            return hleft+1 if hleft > hright else hright+1
        return _height(self._tree)

    def preorder(self, visit = print):
        ''' Efetua uma travessia pré-order '''
        def _preorder(node, visit):
            ''' Visita um nó em pré-order '''
            if node:
                visit(node.value())
                _preorder(node.left(), visit)
                _preorder(node.right(), visit)
        _preorder(self._tree, visit)

    def posorder(self, visit = print):
        ''' Efetua uma travessia pós-order '''
        def _posorder(node, visit):
            ''' Visita um nó em pós-order '''
            if node:
                _posorder(node.left(), visit)
                _posorder(node.right(), visit)
                visit(node.value())
        _posorder(self._tree, visit)

    def order(self, visit = print):
        ''' Efetua uma travessia in-order '''
        def _inorder(node, visit):
            ''' Visita um nó em in-order '''
            if node:
                _inorder(node.left(), visit)
                visit(node.value())
                _inorder(node.right(), visit)
        _inorder(self._tree, visit)

if __name__ == '__main__':
    x = Btree()
    x.insert(12)
    x.insert(6)
    x.insert(8)
    x.insert(16)
    x.insert(24)
    from io import StringIO
    import sys
    out = sys.stdout
    sys.stdout = StringIO()
    assert x.count() == 5, "count test"
    assert x.height() == 3, "height test"
    assert x.min() == 6, "min test"
    assert x.max() == 24, "max test"
    assert x.search(8) == 8, "search test"
    assert x.search(7) is None, "fail search test"
    x.preorder()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "12\n6\n8\n16\n24\n", "preorder test"
    sys.stdout = StringIO()
    x.posorder()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "8\n6\n24\n16\n12\n", "posorder test"
    sys.stdout = StringIO()
    x.order()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "6\n8\n12\n16\n24\n", "inorder test"
    sys.stdout = StringIO()
    x.remove(12)
    x.preorder()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "8\n6\n16\n24\n", "remove root test"
    sys.stdout = StringIO()
    x.remove(16)
    x.preorder()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "8\n6\n24\n", "remove right test"
    sys.stdout = StringIO()
    x.insert(123)
    x.insert(16)
    x.insert(12)
    x.remove(16)
    x.preorder()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "8\n6\n24\n12\n123\n", "remove left test"
    sys.stdout = StringIO()
    x.remove(123)
    x.preorder()
    sys.stdout.seek(0)
    assert sys.stdout.read() == "8\n6\n24\n12\n", "remove left test"
    sys.stdout = out
    print("OK")
