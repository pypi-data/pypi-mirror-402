''' Operações em árvores equilibradas AVL (Adelson-Velsky and Landis)

    Exemplo:
    >>> from iaed.avl import AVL
    >>> t = AVL()
    >>> for i in (15, 14, 12, 24, 18, 11, 21, 48, 32):
    >>>     t.insert(i)
    >>> t.preorder()
    >>> t.remove(14)
    >>> t.posorder()
'''

from iaed.btree import _node, Btree

class _hnode(_node):
    ''' Nó da árvore com pesos '''
    def __init__(self, value, height=1, left=None, right=None):
        ''' Cria um nó '''
        super().__init__(value, left, right)
        self._height = height
    def height(self, val = ...):
        ''' Peso do nó '''
        if val != ...:
            self._height = val
        return self._height

class AVL(Btree):
    ''' Balanceamento AVL de árvores (Btree) '''
    def __init__(self, keyf = lambda x: x):
        ''' keyf: função que devolve a chave de um nó '''
        super().__init__(keyf)

    @staticmethod
    def _balance(node):
        ''' Balanceamento de um nó '''
        def height(node):
            ''' Devolve a altura de um nó '''
            return node.height() if node else 0

        def update_height(node):
            ''' Atualiza a altura de nó '''
            left = height(node.left())
            right = height(node.right())
            node.height(left+1 if left > right else right+1)

        def rot_l(node):
            ''' Efetua uma rotação simples à esquerda '''
            print('rotL', node.value())
            aux = node.right()
            node.right(aux.left())
            aux.left(node)
            update_height(node)
            update_height(aux)
            return aux

        def rot_r(node):
            ''' Efetua uma rotação simples à direita '''
            print('rotR', node.value())
            aux = node.left()
            node.left(aux.right())
            aux.right(node)
            update_height(node)
            update_height(aux)
            return aux

        def rot_lr(node):
            ''' Efetua uma rotação dupla esquerda-direita '''
            print('rotLR', node.value())
            if not node:
                return None
            node.left(rot_l(node.left()))
            return rot_r(node)

        def rot_rl(node):
            ''' Efetua uma rotação dupla direita-esquerda '''
            print('rotRL', node.value())
            if not node:
                return None
            node.right(rot_r(node.right()))
            return rot_l(node)

        def balance_factor(node):
            ''' Devolve o desiqulíbrio de um nó '''
            if not node:
                return 0
            return height(node.left()) - height(node.right())

        if not node:
            return None
        factor = balance_factor(node)
        if factor > 1:
            if balance_factor(node.left()) >= 0:
                node = rot_r(node)
            else:
                node = rot_lr(node)
        elif factor < -1:
            if balance_factor(node.right()) <= 0:
                node = rot_l(node)
            else:
                node = rot_rl(node)
        else:
            update_height(node)
        return node

    def insert(self, value):
        ''' Operação de inserção '''

        def _insert(node, keyf, value):
            ''' Insere o nó com balanceamento '''
            if not node: # new node
                return _hnode(value)
            cmp = keyf(value) - keyf(node.value())
            if not cmp: # replace node
                return _hnode(value)
            if cmp < 0: # go left
                node.left(_insert(node.left(), keyf, value))
            else: # go right
                node.right(_insert(node.right(), keyf, value))
            return AVL._balance(node)
        self._tree = _insert(self._tree, self._keyf, value)

    def remove(self, key):
        ''' Operação de remoção '''
        def _remove(node, keyf, key):
            ''' Remove o nó com balanceamento '''
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
            return AVL._balance(node)
        self._tree = _remove(self._tree, self._keyf, key)

if __name__ == '__main__':
    t=AVL()
    for i in (15,14,12,24,18,11,21,48,32):
        t.insert(i)
    t.preorder()
    t.remove(14)
    t.posorder()
