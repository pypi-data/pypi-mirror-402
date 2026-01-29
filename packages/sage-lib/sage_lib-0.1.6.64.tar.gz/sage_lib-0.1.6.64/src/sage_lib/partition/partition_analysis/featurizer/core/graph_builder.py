# =============================
# graph_builder.py
# =============================
"""
Module for constructing NetworkX graphs from atomic structures.

This module provides the `GraphBuilder` class, which handles neighbor list calculations
and graph assembly based on specified cutoff distances.
"""

import numpy as np
import networkx as nx
from ase.neighborlist import neighbor_list
from ase.data import atomic_numbers
from ase import Atoms
from typing import Dict, List, Any

# Properties for common elements (extended as needed)
element_props: Dict[str, Dict[str, int]] = {
    "Ni": {"Z": 28}, "Fe": {"Z": 26}, "V": {"Z": 23},
    "O": {"Z": 8}, "H": {"Z": 1}, "K": {"Z": 19}
}

class GraphBuilder:
    """Class for building graph representations of atomic structures."""
    
    def __init__(self, cutoffs: List[float]):
        """
        Initialize the GraphBuilder.

        Args:
            cutoffs: List of cutoff radii (in Angstroms) for defining edges.
                     A separate graph will be built for each cutoff.
        """
        self.cutoffs = cutoffs

    def build(self, container: Any) -> Dict[float, nx.Graph]:
        """
        Build graphs for a given structure across all defined cutoffs.

        Args:
            container: An object containing structure data (AtomPositionManager or similar).
                       Must have attributes: atomPositions, atomLabelsList, latticeVectors.

        Returns:
            Dictionary where keys are cutoff values and values are NetworkX Graphs.
        """
        graphs = {}
        # Access internal SAGE structure format
        positions = container.AtomPositionManager.atomPositions
        symbols = container.AtomPositionManager.atomLabelsList
        cell = container.AtomPositionManager.latticeVectors
        
        Zs = [atomic_numbers.get(s, 0) for s in symbols]

        # Convert to ASE Atoms for robust neighbor list calculation
        atoms = Atoms(
            symbols=symbols,
            positions=positions,
            cell=cell,
            pbc=True
        )
        
        for c in self.cutoffs:
            # 'd' returns distance array
            i_idx, j_idx, _, dist = neighbor_list("ijDd", atoms, c)
            
            G = nx.Graph()
            # Add nodes with attributes
            for i, s in enumerate(symbols):
                G.add_node(i, element=s, Z=Zs[i])
            
            # Add edges with distance weights
            # neighbor_list implies i < j check is needed for undirected graph to avoid duplicates 
            # if we iterate all pairs. neighbor_list returns both (i,j) and (j,i).
            for i, j, d in zip(i_idx, j_idx, dist):
                if i < j:
                    G.add_edge(i, j, weight=float(d))
            
            graphs[c] = G
            
        return graphs
