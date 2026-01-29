# =============================
# featurizer.py
# =============================
"""
Core feature extraction module for managing graph-based descriptors and formation energy calculations.

This module provides the `GraphFeatureExtractor` class, which orchestrates the conversion
of atomic structures into graphs and the subsequent calculation of topological, chemical,
and spectral descriptors. It also includes helper classes for complexity analysis,
normalization, and batch processing.
"""

from typing import Dict, List, Optional, Tuple, Any, Union, Iterable

import numpy as np
import networkx as nx
import pandas as pd
from multiprocessing import Pool
from tqdm import tqdm

from .graph_builder import GraphBuilder
from .descriptors.topology import TopologyDescriptors
from .descriptors.chemistry import ChemistryDescriptors
from .descriptors.spectral import SpectralDescriptors
from .descriptors.order import OrderDescriptors
from .descriptors.correlation import CorrelationDescriptors
from .descriptors.percolation import PercolationDescriptors


# ==============================================
# GraphComplexityDescriptors
# ==============================================
class GraphComplexityDescriptors:
    """Helper class for calculating graph complexity metrics."""
    
    @staticmethod
    def global_complexity(G: nx.Graph, prefix: str) -> Dict[str, float]:
        """
        Calculate global complexity metrics for a graph.

        Args:
            G: The NetworkX graph to analyze.
            prefix: feature name prefix to use for output keys.

        Returns:
            Dictionary of complexity features (n_comp, diameter, radius, core_max).
        """
        feats = {}
        if G.number_of_nodes() == 0:
            feats[f"{prefix}_n_comp"] = 0
            feats[f"{prefix}_diameter"] = 0
            feats[f"{prefix}_radius"] = 0
            feats[f"{prefix}_core_max"] = 0
            return feats

        comps = list(nx.connected_components(G))
        feats[f"{prefix}_n_comp"] = len(comps)
        
        # Calculate properties on the largest connected component
        largest_nodes = max(comps, key=len)
        largest = G.subgraph(largest_nodes)

        try:
            feats[f"{prefix}_diameter"] = nx.diameter(largest)
        except Exception:
            feats[f"{prefix}_diameter"] = 0
            
        try:
            feats[f"{prefix}_radius"] = nx.radius(largest)
        except Exception:
            feats[f"{prefix}_radius"] = 0

        core = nx.core_number(G)
        feats[f"{prefix}_core_max"] = max(core.values()) if core else 0

        return feats


# ==============================================
# FeatureAssembler (dense matrices)
# ==============================================
class FeatureAssembler:
    """Helper for assembling list of dicts into a consistent NumPy matrix."""
    
    def __init__(self):
        self.columns: Optional[List[str]] = None

    def to_matrix(self, rows: List[Dict[str, float]]) -> Tuple[np.ndarray, List[str]]:
        """
        Convert a list of feature dictionaries to a dense matrix.
        
        Args:
            rows: List of feature dictionaries.
            
        Returns:
            Tuple of (numpy data matrix, column names list).
        """
        df = pd.DataFrame(rows)
        if self.columns is None:
            self.columns = list(df.columns)
        # Ensure consistent column ordering
        df = df[self.columns]
        return df.values, self.columns


# ==============================================
# FeatureNormalizer
# ==============================================
class FeatureNormalizer:
    """Standard scaler implementation for feature normalization."""
    
    def __init__(self):
        self.mean: Optional[np.ndarray] = None
        self.std: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> None:
        """Compute the mean and std to be used for later scaling."""
        self.mean = X.mean(axis=0)
        # Add small epsilon to avoid division by zero
        self.std = X.std(axis=0) + 1e-12

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Perform standardization by centering and scaling."""
        if self.mean is None or self.std is None:
            raise ValueError("FeatureNormalizer must be fit before transform.")
        return (X - self.mean) / self.std

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit to data, then transform it."""
        self.fit(X)
        return self.transform(X)


# ==============================================
# FeatureBatchProcessor (parallel)
# ==============================================
class FeatureBatchProcessor:
    """Handles parallel processing of features for large datasets."""
    
    def __init__(self, extractor: 'GraphFeatureExtractor', n_jobs: int = 4, batch_size: int = 64):
        """
        Args:
            extractor: Instance of GraphFeatureExtractor to use.
            n_jobs: Number of parallel processes.
            batch_size: Number of items per batch.
        """
        self.extractor = extractor
        self.n_jobs = n_jobs
        self.batch_size = batch_size

    def process(self, partition: Iterable) -> List[Dict[str, Any]]:
        """
        Run the extractor in parallel on the partition.
        
        Args:
            partition: Iterable container of atomic structures (dataset).
            
        Returns:
            List of feature dictionaries.
        """
        # Convert partition to list-like if necessary to slice, or create generator chunks
        # Assuming partition supports indexing or is a list
        if not hasattr(partition, '__getitem__') or not hasattr(partition, '__len__'):
             # If it's a raw generator, we might need to materialize it
             partition = list(partition)
             
        batches = [partition[i:i+self.batch_size] for i in range(0, len(partition), self.batch_size)]

        rows = []
        with Pool(self.n_jobs) as P:
            # P.imap preserves order
            for result in tqdm(P.imap(self.extractor._compute_batch, batches), total=len(batches), desc="Batch Processing"):
                rows.extend(result)
        return rows


class GraphFeatureExtractor:
    """
    Main class for extracting graph-based machine learning features from atomic structures.
    """
    
    def __init__(self, cutoffs: List[float], mu_dict: Optional[Dict[str, float]] = None):
        """
        Initialize the feature extractor.

        Args:
            cutoffs: List of cutoff distances (in Angstroms) for neighbor lists.
            mu_dict: Dictionary of chemical potentials {element: eV}.
                     If None, chemical potentials must be fitted or provided later
                     to calculate formation energy.
        """
        self.builder = GraphBuilder(cutoffs)
        self.cutoffs = cutoffs
        self.mu = mu_dict   # chemical potentials
        self.Ef: Optional[np.ndarray] = None # Cached formation energies

    # ------------------------------------
    # ENERGY EXTRACTOR
    # ------------------------------------
    def _extract_energy(self, atoms: Any) -> float:
        """
        Extract total energy from atoms object.
        
        Args:
            atoms: ASE Atoms object (or similar).
            
        Returns:
            Total energy (eV).
        """
        # Attempts to extract total energy from AtomPositionManager.E
        # This assumes the custom SAGE object structure
        if hasattr(atoms, "AtomPositionManager"):
             return float(atoms.AtomPositionManager.E)
        # Fallback for standard ASE atoms if calculator is attached
        if hasattr(atoms, "get_potential_energy"):
            try:
                return atoms.get_potential_energy()
            except:
                pass
        return 0.0

    def formation_energy(self, dataset: Any, 
                         unique_labels: Optional[List[str]] = None, 
                         reference_potentials: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Calculate formation energy for a dataset of structures.
        
        fE = (E_total - sum(n_i * mu_i)) / N_atoms

        Args:
            dataset: The dataset containing structures.
            unique_labels: List of species labels to consider. If None, infers from dataset.
            reference_potentials: Custom chemical potentials to use override defaults/fitting.

        Returns:
            Array of formation energies per atom.
        """
        
        def _fit_mu_lstsq(X: np.ndarray, y: np.ndarray) -> np.ndarray:
            """Fit chemical potentials using Least Squares."""
            # Columns with zero variance carry no information; keep them but set μ=0.
            col_var = X.var(axis=0)
            informative = col_var > 0.0
            mu = np.zeros(X.shape[1], dtype=float)
            if np.any(informative):
                mu_inf, *_ = np.linalg.lstsq(X[:, informative].astype(float),
                                             y.astype(float),
                                             rcond=None)
                mu[informative] = mu_inf
            return mu

        # Energies
        y = np.asarray(dataset.get_all_energies(), dtype=float)
        y = np.nan_to_num(y, nan=0.0)
        N = y.shape[0]

        # Compositions and species ordering
        X_all, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")

        # Choose labels
        labels = list(unique_labels) if unique_labels is not None else list(species_order)

        # Build X for the selected labels (missing labels => zero column)
        idx = np.fromiter((mapping.get(lbl, -1) for lbl in labels), dtype=int, count=len(labels))
        valid = (idx >= 0)

        X = np.zeros((N, len(labels)), dtype=float)
        if np.any(valid):
            X[:, valid] = X_all[:, idx[valid]]

        # μ vector
        # Priority: 1. Provided reference_potentials argument
        #           2. self.mu (if set)
        #           3. Fit from data
        
        target_mu_source = reference_potentials if reference_potentials is not None else self.mu

        if target_mu_source is None:
            mu_vec = _fit_mu_lstsq(X, y)
        else:
            mu_vec = np.array([target_mu_source.get(lbl, 0.0) for lbl in labels], dtype=float)

        # Formation energy
        fE = y - X.dot(mu_vec)
        # Avoid division by zero
        n_atoms = np.sum(X, axis=1)
        n_atoms[n_atoms == 0] = 1.0 
        
        return fE / n_atoms

    # ------------------------------------
    # FIT CHEMICAL POTENTIALS FROM DATASET
    # ------------------------------------
    def fit_mu(self, structures: Any, percentile: int = 20) -> Dict[str, float]:
        """
        Fit chemical potentials from full dataset using low-energy structures.
        Stores result in self.mu.
        
        Args:
            structures: Dataset of structures.
            percentile: Percentile of lowest energy structures to use for fitting.
            
        Returns:
            Fitted dictionary of chemical potentials.
        """
        # Note: This imports inside method to avoid circular deps if descriptors_chemistry uses this
        from .descriptors.chemistry import fit_weighted_chemical_potentials
        self.mu = fit_weighted_chemical_potentials(structures, percentile=percentile)
        return self.mu

    # ------------------------------------
    # COMPUTE FEATURES FOR A SINGLE STRUCTURE
    # ------------------------------------
    def compute(self, partition: Any, subsample: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Compute features for a dataset (Partition).
        
        Args:
            partition: The dataset to iterate over.
            subsample: If provided, only process the first N items.
            
        Returns:
            List of feature dictionaries.
        """
        rows = []
        # Pre-calculating formation energy for the whole batch
        self.Ef = self.formation_energy(partition)

        for i, c in enumerate(tqdm(partition, desc="Computing features")):
            if isinstance(subsample, int) and i >= subsample:
                break
            feats = self.compute_features(c)
            feats["id"] = i
            # Check bounds for Ef in case partition length mismatches subsample logic
            if i < len(self.Ef):
                feats["Ef"] = self.Ef[i]
            else:
                feats["Ef"] = 0.0

            rows.append(feats)
        return rows


    # ------------------------------------
    # COMPUTE FEATURES FOR MANY STRUCTURES
    # ------------------------------------
    def compute_features(self, container: Any) -> Dict[str, Any]:
        """
        Compute all graph features for a single structure container.
        
        Args:
            container: Wrapper around an atomic structure (AtomPositionManager or Atoms).
            
        Returns:
            Dictionary of all computed features.
        """
        # graph construction
        graphs = self.builder.build(container)
        feats = {}

        # multi-cutoff graph descriptors
        for c, G in graphs.items():
            p = f"c{c:.2f}"

            # --- B. Topological Descriptors ---
            feats.update(TopologyDescriptors.degree_stats(G, p))
            feats.update(TopologyDescriptors.degree_stats_by_species(G, p))
            feats.update(TopologyDescriptors.cycle_stats(G, p))
            feats.update(TopologyDescriptors.clustering(G, p))
            feats.update(TopologyDescriptors.path_stats(G, p))

            # --- C. Chemical Descriptors ---
            feats.update(ChemistryDescriptors.edge_fractions(G, p))
            feats.update(ChemistryDescriptors.edge_distance_stats(G, p))
            feats.update(ChemistryDescriptors.edge_distance_stats_by_pair(G, p))

            # --- D. Spectral Descriptors ---
            feats.update(SpectralDescriptors.spectral_invariants(G, p))
            feats.update(SpectralDescriptors.local_spectral_entropy(G, p))

            # --- E. Order/Disorder Descriptors [NEW] ---
            feats.update(OrderDescriptors.assortativity(G, p))
            feats.update(OrderDescriptors.graph_entropy(G, p))

            # --- F. Multi-Scale & Percolation [NEW] ---
            feats.update(CorrelationDescriptors.spatial_autocorrelation(G, p, k_max=4))
            feats.update(PercolationDescriptors.cluster_sizes(G, p))
            feats.update(PercolationDescriptors.core_boundary_fraction(G, p))


        # ------------------------------------
        #  ENERGY + FORMATION ENERGY
        # ------------------------------------
        feats["E"] = self._extract_energy(container)

        return feats

    # ---------------------------
    def _compute_batch(self, batch: List[Any]) -> List[Dict[str, Any]]:
        """
        Internal method for processing a batch in parallel mode.
        """
        rows = []
        for c in batch:
            rows.append(self.compute_features(c))
        return rows


    # ---------------------------
    def compute_many_df(self, structures: Any) -> pd.DataFrame:
        """
        Compute features for a dataset and return as a Pandas DataFrame.
        """
        return pd.DataFrame(self.compute(structures))

    def plot_graph(self, G: nx.Graph) -> None:
        """Debug helper to plot a graph."""
        import matplotlib.pyplot as plt
        
        pos = nx.spring_layout(G)  # automatic layout
        nx.draw(G, pos, node_size=1, width=0.5)
        plt.show()


if __name__ == "__main__":
    pass