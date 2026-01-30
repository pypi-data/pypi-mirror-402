''' Pesquisas em grafos

    Exemplo:
    >>> from iaed.graph import bfs, dfs
    >>> gr3 = { 'A': ['B', 'C'], 'B': ['E'], 'C': ['B', 'F'],
        'D': ['C', 'G'], 'E': ['F'], 'F': [], 'G': ['F'] }
    >>> print(bfs(gr3, 'A'))
    >>> print(dfs(gr3))
'''
def bfs(graph: dict, start: str) -> dict:
    ''' Travessia em largura num grafo '''
    out = { start: [0, None] } # node: [ distance, predecessor ]
    queue = (start,)
    while queue:
        node = queue[0]
        queue = queue[1:]
        for dest in graph[node]:
            if dest not in out: # is white
                # is gray
                out[dest] = [out[node][0]+1, node]
                queue += (dest,)
        # is black
    return out


def dfs(graph: dict) -> dict:
    ''' Travessia em profundidade num grafo '''
    def visit(graph, node, out, time, pred = ''):
        ''' Visita um nó do grafo em profundidade '''
        out[node] = [ time, -1, pred] # is gray
        time += 1
        for dest in graph[node]:
            if dest not in out: # is white
                time = visit(graph, dest, out, time, node)
        out[node][1] = time
        return time +1
    out = {} # node: [ discovery, finish, predecessor ]
    time = 1
    for node in graph:
        if node not in out: # is white
            time = visit(graph, node, out, time)
    return out

if __name__ == '__main__':
    from sys import argv
    from ast import literal_eval
    if len(argv) > 1:
        for s in argv[1:]:
            gr = literal_eval(s)
            st = list(gr)
            st.sort()
            print(bfs(gr, st[0]))
            print(dfs(gr))
        exit(0)
    # dictionary of adjacency lists(ordered)
    gr1 = { 'A': ['B', 'C', 'D'], 'B': ['E'], 'C': ['B', 'G'],
        'D': ['C', 'G'], 'E': ['C', 'F'], 'F': ['C', 'H'],
        'G': ['F', 'H', 'I'], 'H': ['E', 'I'], 'I': ['F'] }
    print(bfs(gr1, 'A'))
    print(dfs(gr1))
    gr2 = { 'u': ['v', 'x'], 'v': ['y'], 'w': ['y', 'z'],
        'x': ['v'], 'y': ['x'], 'z': ['z'] }
    print(bfs(gr2, 'u'))
    print(dfs(gr2))
    gr3 = { 'A': ['B', 'C'], 'B': ['E'], 'C': ['B', 'F'],
        'D': ['C', 'G'], 'E': ['F'], 'F': [], 'G': ['F'] }
    print(bfs(gr3, 'A'))
    print(dfs(gr3))
