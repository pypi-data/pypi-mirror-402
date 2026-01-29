"""
Metrics module for network topology analysis.
"""

import warnings
from typing import List, Dict, Optional, Any

import networkx as nx
import numpy as np
from numpy.typing import NDArray
import scipy.sparse as sp  # type: ignore[import-untyped]

from topolib.topology import Topology


class Metrics:
    """
    Provides static methods for computing metrics on network topologies.

    All methods receive a Topology instance.

    Methods
    -------
    node_degree(topology)
        Calculates the degree of each node.
    average_node_degree(topology)
        Calculates the average node degree.
    diameter(topology)
        Calculates the network diameter (in hops).
    diameter_hops(topology)
        Calculates the network diameter in hops.
    diameter_kms(topology)
        Calculates the network diameter in kilometers.
    network_density(topology)
        Calculates the network density.
    average_shortest_path_length(topology)
        Calculates the average shortest path length (in hops).
    average_shortest_path_length_hops(topology)
        Calculates the average shortest path length in hops.
    average_shortest_path_length_kms(topology)
        Calculates the average shortest path length in kilometers.
    clustering_coefficient(topology)
        Calculates the average clustering coefficient.
    edge_betweenness_stats(topology)
        Calculates min, mean, and max edge betweenness centrality.
    node_betweenness_stats(topology)
        Calculates min, mean, and max node betweenness centrality.
    global_efficiency(topology)
        Calculates the global efficiency.
    spectral_radius(topology)
        Calculates the spectral radius.
    algebraic_connectivity(topology)
        Calculates the algebraic connectivity.
    weighted_spectral_distribution(topology)
        Calculates the weighted spectral distribution.
    average_link_length(topology)
        Calculates the average physical link length.
    betweenness_centrality(topology)
        Calculates betweenness centrality for each node.
    closeness_centrality(topology)
        Calculates closeness centrality for each node.
    eigenvector_centrality(topology)
        Calculates eigenvector centrality for each node.
    edge_betweenness_centrality(topology)
        Calculates edge betweenness centrality for each link.
    link_length_stats(topology)
        Calculates statistics (min, max, avg) of link lengths.
    connection_matrix(topology)
        Builds the adjacency matrix.
    """

    @staticmethod
    def node_degree(topology: "Topology") -> Dict[int, int]:
        """
        Calculates the degree of each node in the topology.

        For bidirectional links (where both A->B and B->A exist),
        each node's degree is incremented only once per connection.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: degree}
        :rtype: dict[int, int]
        """
        degree = {n.id: 0 for n in topology.nodes}
        # Use a set to track processed link pairs to avoid double counting
        processed_pairs: set[tuple[int, int]] = set()

        for link in topology.links:
            # Create a normalized pair (smaller_id, larger_id) to detect bidirectional links
            pair: tuple[int, int] = (
                min(link.source.id, link.target.id),
                max(link.source.id, link.target.id),
            )

            if pair not in processed_pairs:
                processed_pairs.add(pair)
                degree[link.source.id] += 1
                degree[link.target.id] += 1

        return degree

    @staticmethod
    def link_length_stats(topology: "Topology") -> Dict[str, Optional[float]]:
        """
        Calculates the minimum, maximum, and average link lengths.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary with keys 'min', 'max', 'avg'.
        :rtype: dict[str, float | None]
        """
        lengths = [l.length for l in topology.links]
        if not lengths:
            return {"min": None, "max": None, "avg": None}
        return {
            "min": min(lengths),
            "max": max(lengths),
            "avg": sum(lengths) / len(lengths),
        }

    @staticmethod
    def connection_matrix(topology: "Topology") -> List[List[int]]:
        """
        Builds the adjacency matrix of the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Adjacency matrix (1 if connected, 0 otherwise).
        :rtype: list[list[int]]
        """
        id_to_idx = {n.id: i for i, n in enumerate(topology.nodes)}
        size = len(topology.nodes)
        matrix = [[0] * size for _ in range(size)]
        for link in topology.links:
            i = id_to_idx[link.source.id]
            j = id_to_idx[link.target.id]
            matrix[i][j] = 1
            matrix[j][i] = 1
        return matrix

    @staticmethod
    def average_node_degree(topology: "Topology") -> float:
        """
        Calculates the average node degree of the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average node degree
        :rtype: float
        """
        degrees = Metrics.node_degree(topology)
        if not degrees:
            return 0.0
        return sum(degrees.values()) / len(degrees)

    @staticmethod
    def diameter(topology: "Topology") -> Optional[int]:
        """
        Calculates the network diameter (longest shortest path) in hops.

        .. deprecated::
            This method is deprecated and will be removed in a future version.
            Use :meth:`diameter_hops` instead for explicit hop-based measurement,
            or :meth:`diameter_kms` for distance-based measurement.
            The explicit naming makes the measurement unit clearer.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Network diameter in hops, or None if network is disconnected
        :rtype: int | None
        """
        warnings.warn(
            "diameter() is deprecated and will be removed in a future version. "
            "Use diameter_hops() for hop-based measurement or diameter_kms() for distance-based measurement.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Metrics.diameter_hops(topology)

    @staticmethod
    def diameter_hops(topology: "Topology") -> Optional[int]:
        """
        Calculates the network diameter (longest shortest path) in hops.

        The diameter is the maximum shortest path length between any pair of nodes,
        measured in number of hops (links traversed).

        Note: This is the recommended method for computing diameter in hops.
        For distance-based measurement, use :meth:`diameter_kms`.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Network diameter in hops, or None if network is disconnected
        :rtype: int | None
        """
        G = topology.graph.to_undirected()
        if not nx.is_connected(G):
            return None
        return nx.diameter(G)

    @staticmethod
    def diameter_kms(topology: "Topology") -> Optional[float]:
        """
        Calculates the network diameter (longest shortest path) in kilometers.

        Uses the physical distance (length attribute) of links to compute
        the longest shortest path distance.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Network diameter in kilometers, or None if network is disconnected
        :rtype: float | None
        """
        G = topology.graph.to_undirected()
        if not nx.is_connected(G):
            return None

        # Create a weighted graph using link lengths
        weighted_graph: "nx.Graph[int]" = nx.Graph()
        for node in topology.nodes:
            weighted_graph.add_node(node.id)

        for link in topology.links:
            if weighted_graph.has_edge(link.source.id, link.target.id):
                # Keep the minimum length if multiple links exist
                current_weight = weighted_graph[link.source.id][link.target.id][
                    "weight"
                ]
                weighted_graph[link.source.id][link.target.id]["weight"] = min(
                    current_weight, link.length
                )
            else:
                weighted_graph.add_edge(
                    link.source.id, link.target.id, weight=link.length
                )

        # Compute all pairs shortest path lengths
        max_distance = 0.0
        for source in weighted_graph.nodes():
            lengths = nx.single_source_dijkstra_path_length(
                weighted_graph, source, weight="weight"
            )
            for target, distance in lengths.items():
                if source != target:
                    max_distance = max(max_distance, distance)

        return max_distance if max_distance > 0 else None

    @staticmethod
    def average_shortest_path_length(topology: "Topology") -> Optional[float]:
        """
        Calculates the average shortest path length between all pairs of nodes in hops.

        .. deprecated::
            This method is deprecated and will be removed in a future version.
            Use :meth:`average_shortest_path_length_hops` instead for explicit hop-based measurement,
            or :meth:`average_shortest_path_length_kms` for distance-based measurement.
            The explicit naming makes the measurement unit clearer.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average shortest path length in hops, or None if network is disconnected
        :rtype: float | None
        """
        warnings.warn(
            "average_shortest_path_length() is deprecated and will be removed in a future version. "
            "Use average_shortest_path_length_hops() for hop-based measurement or "
            "average_shortest_path_length_kms() for distance-based measurement.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Metrics.average_shortest_path_length_hops(topology)

    @staticmethod
    def average_shortest_path_length_hops(topology: "Topology") -> Optional[float]:
        """
        Calculates the average shortest path length between all pairs of nodes in hops.

        This method computes the mean of all shortest path lengths in the network,
        where each path length is measured in number of hops (links traversed).

        Note: This is the recommended method for computing average path length in hops.
        For distance-based measurement, use :meth:`average_shortest_path_length_kms`.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average shortest path length in hops, or None if network is disconnected
        :rtype: float | None
        """
        G = topology.graph.to_undirected()
        if not nx.is_connected(G):
            return None
        return nx.average_shortest_path_length(G)

    @staticmethod
    def average_shortest_path_length_kms(topology: "Topology") -> Optional[float]:
        """
        Calculates the average shortest path length between all pairs of nodes in kilometers.

        Uses the physical distance (length attribute) of links to compute
        the average shortest path distance.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average shortest path length in kilometers, or None if network is disconnected
        :rtype: float | None
        """
        G = topology.graph.to_undirected()
        if not nx.is_connected(G):
            return None

        # Create a weighted graph using link lengths
        weighted_graph: "nx.Graph[int]" = nx.Graph()
        for node in topology.nodes:
            weighted_graph.add_node(node.id)

        for link in topology.links:
            if weighted_graph.has_edge(link.source.id, link.target.id):
                # Keep the minimum length if multiple links exist
                current_weight = weighted_graph[link.source.id][link.target.id][
                    "weight"
                ]
                weighted_graph[link.source.id][link.target.id]["weight"] = min(
                    current_weight, link.length
                )
            else:
                weighted_graph.add_edge(
                    link.source.id, link.target.id, weight=link.length
                )

        return nx.average_shortest_path_length(weighted_graph, weight="weight")

    @staticmethod
    def clustering_coefficient(topology: "Topology") -> float:
        """
        Calculates the average clustering coefficient of the network.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average clustering coefficient
        :rtype: float
        """
        G = topology.graph.to_undirected()
        return nx.average_clustering(G)

    @staticmethod
    def algebraic_connectivity(topology: "Topology") -> float:
        """
        Calculates the algebraic connectivity (second smallest eigenvalue of the Laplacian matrix).

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Algebraic connectivity
        :rtype: float
        """
        G = topology.graph.to_undirected()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            return nx.algebraic_connectivity(G)

    @staticmethod
    def average_link_length(topology: "Topology") -> Optional[float]:
        """
        Calculates the average physical link length in the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average link length
        :rtype: float | None
        """
        return Metrics.link_length_stats(topology)["avg"]

    @staticmethod
    def betweenness_centrality(topology: "Topology") -> Dict[int, float]:
        """
        Calculates the betweenness centrality for each node.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: betweenness_centrality}
        :rtype: dict[int, float]
        """
        G = topology.graph.to_undirected()
        return nx.betweenness_centrality(G)

    @staticmethod
    def closeness_centrality(topology: "Topology") -> Dict[int, float]:
        """
        Calculates the closeness centrality for each node.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: closeness_centrality}
        :rtype: dict[int, float]
        """
        G = topology.graph.to_undirected()
        return nx.closeness_centrality(G)  # type: ignore[no-any-return]

    @staticmethod
    def eigenvector_centrality(topology: "Topology") -> Dict[int, float]:
        """
        Calculates the eigenvector centrality for each node.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: eigenvector_centrality}
        :rtype: dict[int, float]
        """
        G = topology.graph.to_undirected()
        try:
            return nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            return nx.eigenvector_centrality(G, max_iter=10000)

    @staticmethod
    def edge_betweenness_centrality(
        topology: "Topology",
    ) -> Dict[tuple[int, int], float]:
        """
        Calculates the edge betweenness centrality for each link.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {(source_id, target_id): edge_betweenness}
        :rtype: dict[tuple[int, int], float]
        """
        G = topology.graph.to_undirected()
        return nx.edge_betweenness_centrality(G)

    @staticmethod
    def network_density(topology: "Topology") -> float:
        """
        Calculates the network density (ratio of actual edges to maximum possible edges).
        Formula: ND = 2m / (n(n-1)) where m is number of edges and n is number of nodes.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Network density
        :rtype: float
        """
        G = topology.graph.to_undirected()
        return float(nx.density(G))  # type: ignore[arg-type]

    @staticmethod
    def edge_betweenness_stats(topology: "Topology") -> Dict[str, float]:
        """
        Calculates statistics (min, mean, max) of edge betweenness centrality.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary with keys 'min', 'mean', 'max'
        :rtype: dict[str, float]
        """
        edge_bc = Metrics.edge_betweenness_centrality(topology)
        if not edge_bc:
            return {"min": 0.0, "mean": 0.0, "max": 0.0}

        values = list(edge_bc.values())
        return {
            "min": min(values),
            "mean": sum(values) / len(values),
            "max": max(values),
        }

    @staticmethod
    def node_betweenness_stats(topology: "Topology") -> Dict[str, float]:
        """
        Calculates statistics (min, mean, max) of node betweenness centrality.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary with keys 'min', 'mean', 'max'
        :rtype: dict[str, float]
        """
        node_bc = Metrics.betweenness_centrality(topology)
        if not node_bc:
            return {"min": 0.0, "mean": 0.0, "max": 0.0}

        values = list(node_bc.values())
        return {
            "min": min(values),
            "mean": sum(values) / len(values),
            "max": max(values),
        }

    @staticmethod
    def global_efficiency(topology: "Topology") -> float:
        """
        Calculates the global efficiency of the network.
        Formula: E_glob = 1/(n(n-1)) * sum(1/d(u,v)) for all u != v

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Global efficiency
        :rtype: float
        """
        G = topology.graph.to_undirected()
        return nx.global_efficiency(G)

    @staticmethod
    def spectral_radius(topology: "Topology") -> float:
        """
        Calculates the spectral radius (largest absolute eigenvalue of adjacency matrix).

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Spectral radius
        :rtype: float
        """
        G = topology.graph.to_undirected()
        # Use to_scipy_sparse_array to avoid deprecation warnings
        adj_sparse: Any = nx.to_scipy_sparse_array(G)
        # Convert to dense numpy array for eigenvalue calculation
        adj_array: NDArray[np.float64] = adj_sparse.toarray()
        eigenvalues: Any = np.linalg.eigvals(adj_array)
        return float(np.max(np.abs(eigenvalues)))

    @staticmethod
    def weighted_spectral_distribution(topology: "Topology") -> float:
        """
        Calculates the weighted spectral distribution of the normalized Laplacian.
        Formula: WSD(G) = sum((1-k) * N_f(lambda_L^D = k)) for k in K

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Weighted spectral distribution
        :rtype: float
        """
        G = topology.graph.to_undirected()
        # Compute normalized Laplacian eigenvalues
        # Use scipy.sparse.csgraph to avoid NetworkX deprecation warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            laplacian_sparse: Any = nx.normalized_laplacian_matrix(G)
        # Convert to dense numpy array for eigenvalue calculation
        laplacian_array: NDArray[np.float64]
        is_sparse: bool = sp.issparse(laplacian_sparse)
        if is_sparse:
            laplacian_array = laplacian_sparse.toarray()
        else:
            laplacian_array = np.array(laplacian_sparse)
        eigenvalues: NDArray[np.float64] = np.linalg.eigvalsh(laplacian_array)

        # Bin eigenvalues and compute weighted sum
        hist, bin_edges = np.histogram(eigenvalues, bins=50)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        wsd = np.sum((1 - bin_centers) * hist)

        return float(wsd)
