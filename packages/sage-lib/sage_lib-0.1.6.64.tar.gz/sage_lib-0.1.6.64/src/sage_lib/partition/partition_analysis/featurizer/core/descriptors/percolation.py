# =============================
# descriptors_percolation.py
# =============================
"""
Descriptors measuring percolation, cluster sizes, and core/boundary fractions.
"""

import numpy as np
import networkx as nx
from typing import Dict, Any

class PercolationDescriptors:
    """
    Class for calculating percolation and domain properties.
    """

    @staticmethod
    def cluster_sizes(G: nx.Graph, prefix: str) -> Dict[str, float]:
        """
        Calculates size of the largest connected cluster for each species (chemical percolation).
        
        Args:
            G: NetworkX graph with 'element' node attributes.
            prefix: Prefix for feature names.
            
        Returns:
            Dictionary with largest_cluster_frac for each element.
        """
        n_total = G.number_of_nodes()
        if n_total == 0:
            return {}
            
        # Group nodes by element
        nodes_by_element = {}
        for n, data in G.nodes(data=True):
            el = data.get('element', 'X')
            nodes_by_element.setdefault(el, []).append(n)
            
        stats = {}
        
        for el, nodes in nodes_by_element.items():
            # Create subgraph of only this element
            subgraph = G.subgraph(nodes)
            
            if subgraph.number_of_nodes() == 0:
                frac = 0.0
            else:
                # Find largest connected component in this subgraph
                largest_cc = max(nx.connected_components(subgraph), key=len)
                frac = len(largest_cc) / n_total # Fraction of TOTAL system size
                
            stats[f"{prefix}_largest_{el}_cluster_frac"] = float(frac)
            
        return stats

    @staticmethod
    def core_boundary_fraction(G: nx.Graph, prefix: str, k_core: int = 2) -> Dict[str, float]:
        """
        Calculates the fraction of nodes in the k-core (dense region) vs boundary.
        
        Args:
            G: NetworkX graph.
            prefix: Prefix features.
            k_core: k value for k-core decomposition (min degree in subgraph).
            
        Returns:
            Dictionary with core_frac and boundary_frac.
        """
        n_total = G.number_of_nodes()
        if n_total == 0:
            return {f"{prefix}_core_frac": 0.0, f"{prefix}_boundary_frac": 0.0}
            
        try:
            # k-core is the maximal subgraph where every node has degree >= k
            # remove self loops just in case, though usually simple graphs
            G_simple = G
            if not isinstance(G, nx.Graph): # Directed/Multi
                 G_simple = nx.Graph(G)
            G_simple.remove_edges_from(nx.selfloop_edges(G_simple))
            
            core_subgraph = nx.k_core(G_simple, k=k_core)
            n_core = core_subgraph.number_of_nodes()
            
            frac_core = n_core / n_total
            frac_boundary = 1.0 - frac_core
            
            return {
                f"{prefix}_core_frac": float(frac_core),
                f"{prefix}_boundary_frac": float(frac_boundary)
            }
        except Exception:
            # Fallback if k-core fails (e.g. k too high)
            return {f"{prefix}_core_frac": 0.0, f"{prefix}_boundary_frac": 1.0}
