# =============================
# descriptors_order.py
# =============================
"""
Descriptors measuring order, disorder, and mixing patterns in the graph.
"""

import numpy as np
import networkx as nx
from typing import Dict, Any

class OrderDescriptors:
    """
    Class for calculating order and disorder metrics such as assortativity and entropy.
    """

    @staticmethod
    def assortativity(G: nx.Graph, prefix: str) -> Dict[str, float]:
        """
        Calculates graph assortativity coefficients.
        
        Args:
            G: NetworkX graph with 'element' node attributes.
            prefix: Prefix for feature names.
            
        Returns:
            Dictionary with degree and attribute assortativity.
        """
        if G.number_of_edges() == 0:
            return {
                f"{prefix}_assort_deg": 0.0,
                f"{prefix}_assort_chem": 0.0
            }

        # 1. Degree Assortativity
        try:
            r_deg = nx.degree_assortativity_coefficient(G)
            if np.isnan(r_deg): r_deg = 0.0
        except:
            r_deg = 0.0

        # 2. Attribute (Chemical) Assortativity
        try:
            r_chem = nx.attribute_assortativity_coefficient(G, "element")
            if np.isnan(r_chem): r_chem = 0.0
        except:
            r_chem = 0.0

        return {
            f"{prefix}_assort_deg": float(r_deg),
            f"{prefix}_assort_chem": float(r_chem)
        }

    @staticmethod
    def graph_entropy(G: nx.Graph, prefix: str) -> Dict[str, float]:
        """
        Calculates Shannon entropy of the degree distribution (structural disorder).
        H = - sum( p(k) * log(p(k)) ) where p(k) is the fraction of nodes with degree k.
        """
        n = G.number_of_nodes()
        if n == 0:
            return {f"{prefix}_deg_entropy": 0.0, f"{prefix}_deg_entropy_norm": 0.0}

        degrees = [d for _, d in G.degree()]
        
        # Count occurrences of each degree
        from collections import Counter
        counts = Counter(degrees)
        
        # p(k) = N_k / N
        probs = np.array(list(counts.values()), dtype=float) / n
        
        entropy = -np.sum(probs * np.log(probs))
        
        # Normalized entropy (relative to max entropy log(N))
        # Max entropy is log(N) if every node has a unique degree (which isn't always possible)
        # or log(max_possible_degrees). 
        # Usually normalized by log(N) is a safe upper bound for discrete distributions of size N.
        norm_entropy = entropy / np.log(n) if n > 1 else 0.0

        return {
            f"{prefix}_deg_entropy": float(entropy),
            f"{prefix}_deg_entropy_norm": float(norm_entropy)
        }
