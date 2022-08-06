from algorithms import *


if __name__ == "__main__":
    """adjacency = [
        [0, 1, 1, 1],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ]"""
    """adjacency = [
        [0, 1, 1],
        [0, 0, 1],
        [1, 0, 0],
    ]
    divisor = Divisor([16, -4, -5, 0])
    graph = Graph(adjacency)"""
    graph = Graph.cycle(5)
    graph.forceFlow(0)
    graph.visualize()
    print(graph.jac(vertex=0))
    graph.forceFlow(0, makeSink=False)
    graph.visualize()
    print(graph.jac(vertex=0))
    # print({i: bruteCheckGraphs(Graph.cycle(i)) for i in range(3, 60)})
    # graph.visualize()
        # print(f"Graph {idx}", graph.jac())
        # current.visualize()
    # graph.visualize()
    # cyclediv = fireCycle(graph, divisor)
    # print(cyclediv)
    # grediv = greedy(graph, divisor)
    # print(grediv)
    # graph.visualize(grediv[2])
    # qdiv = qReduced(graph, divisor)
    # print(qdiv)
    # graph.visualize(qdiv[2])

    # print(graph.jac(divisor))
    # print(graph.pic(divisor))
    """for v in range(len(graph)):
        print(f"Jacobian at vertex {v}:", graph.jac(vertex=v))
    print("Picard Group:", graph.pic())"""
