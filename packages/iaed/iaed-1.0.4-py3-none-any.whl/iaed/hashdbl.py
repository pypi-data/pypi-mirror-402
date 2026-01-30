''' Tabelas de dispersão por dispersão dupla (double-hashing)

    Exemplo para uma tabela de dimensão 11 sem redimensionamento (dens=1):
    >>> from iaed.hashdbl import DblHash
    >>> x = DblHash(size=11,dens=1)
    >>> for n in (15,14,12,24,18,11,21,48,32):
    >>>     x.insert(n)
    >>> print(x)
'''

class DblHash:
    ''' Dispersão por dispersão dupla (double-hashing) '''
    class Del:
        ''' deleted value '''
    def __init__(self, keyf = lambda x: x, dbl = lambda x: 3*x+1, dens = .5,
        hashf = hash, size = 199):
        ''' keyf: função que devolve o valor de um elemento
            dbl: função de hashing secundária
            dens: densidade limite para redimensionamento
            hashf: função de hashing primária
            size: dimensão inicial da tabela '''
        self._keyf = keyf
        self._dbl = dbl
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
        for val in tab:
            if val is not None:
                self.insert(val)

    def insert(self, value):
        ''' Insere um elemento '''
        i = self._hashf(self._keyf(value)) % self._size
        k = self._dbl(self._keyf(value))
        while self._tab[i] is not None and self._tab[i] != self.Del:
            i = (i + k) % self._size
        self._tab[i] = value
        self._busy += 1
        if self._busy / self._size > self._dens:
            self._expand()

    def remove(self, value):
        ''' Remove um elemento '''
        i = self._hashf(self._keyf(value)) % self._size
        k = self._dbl(self._keyf(value))
        while self._tab[i] is not None:
            if self._tab[i] != self.Del and \
                self._keyf(self._tab[i]) == self._keyf(value):
                break
            i = (i + k) % self._size
        if self._tab[i] is not None:
            self._tab[i] = self.Del
            self._busy -= 1

    def search(self, key):
        ''' Procura um elemento '''
        i = self._hashf(key) % self._size
        k = self._dbl(key)
        while self._tab[i] is not None:
            if self._tab[i] != self.Del and self._keyf(self._tab[i]) == key:
                return self._tab[i]
            i = (i + k) % self._size
        return None

    def __repr__(self):
        ''' Devolve a representação interna da tabela '''
        out = ''
        for i, val in enumerate(self._tab):
            if val is None:
                continue
            out += str(i) + ': ' + str(val) + '\n'
        return out + str(self._size) + ', ' + str(self._busy) + ', ' + str(self._dens)

    def __getitem__(self, index):
        ''' Devolve o n-ésimo elemento da tabela '''
        return self._tab[index] if 0 <= index < self._size else None

if __name__ == '__main__':
    x = DblHash(size=11,dens=1)
    for n in (15,14,12,24,18,11,21,48,32):
        x.insert(n)
    print(x)
