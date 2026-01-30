''' Tabelas de dispersão por encadeamento externo (external-hashing)

    Exemplo para uma tabela de dimensão 11 sem redimensionamento (dens=1):
    >>> from iaed.hashext import ExtHash
    >>> x = ExtHash(size=11,dens=1)
    >>> for n in (15,14,12,24,18,11,21,48,32):
    >>>     x.insert(n)
    >>> print(x)
'''

class ExtHash:
    ''' Dispersão por encadeamento externo '''
    def __init__(self, keyf = lambda x: x, dens = .5, hashf = hash, size = 199):
        ''' keyf: função que devolve o valor de um elemento
            dens: densidade limite para redimensionamento
            hashf: função de hashing
            size: dimensão inicial da tabela '''
        self._keyf = keyf
        self._hashf = hashf
        self._size = size
        self._dens = dens
        self._tab = [None] * size
        self._busy = 0

    def _expand(self):
        ''' Redimensiona a tabela '''
        tab = self._tab
        self._size = self._size * 2 + 1
        self._tab = [None] * self._size
        self._busy = 0
        if __debug__:
            print("expand to", self._size)
        for row in tab:
            if row:
                for elem in row:
                    self.insert(elem)

    def insert(self, value):
        ''' Insere um elemento '''
        idx = self._hashf(self._keyf(value)) % self._size
        if self._tab[idx]:
            self._tab[idx] += [ value ]
        else:
            self._tab[idx] = [ value ]
        self._busy += 1
        if self._busy / self._size > self._dens:
            self._expand()

    def remove(self, value):
        ''' Remove um elemento '''
        idx = self._hashf(self._keyf(value)) % self._size
        if value in self._tab[idx]:
            self._tab[idx].remove(value)

    def search(self, key):
        ''' Procura um elemento '''
        idx = self._hashf(key) % self._size
        if not self._tab[idx]:
            return None
        for item in self._tab[idx]:
            if self._keyf(item) == key:
                return item
        return None

    def __repr__(self):
        ''' Devolve a representação interna da tabela '''
        out = ''
        for i, line in enumerate(self._tab):
            if not line:
                continue
            out += str(i) + ': '
            for j, val in enumerate(line):
                if j:
                    out += ', '
                out += str(val)
            out += '\n'
        return out + str(self._size) + ', ' + str(self._busy) + ', ' + str(self._dens)

    def __getitem__(self, index):
        ''' Devolve o n-ésimo elemento da tabela (lista de valores) '''
        return self._tab[index] if 0 <= index < self._size else None

if __name__ == '__main__':
    x = ExtHash(size=11,dens=1)
    for n in (15,14,12,24,18,11,21,48,32):
        x.insert(n)
    print(x)
