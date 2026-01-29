import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from typing import Dict, Tuple, List, Set, Optional, Callable, Any

# Import necessary SAGE modules
try:
    from sage_lib.partition.partition_analysis.featurizer.core.featurizer import GraphFeatureExtractor
    from sage_lib.partition.partition_analysis.featurizer.analysis.feature_analysis import clean_features
    from sage_lib.partition.Partition import Partition
except ImportError:
    # Fallback/Mock imports for standalone testing if sage_lib is not in path
    print("Warning: sage_lib definition not found, some features might rely on mocks.")
    pass

def objective_min_distance_to_electrochemicalhull(
    reference_potentials: Dict[str, float],
    H_range: Tuple[float, float] = (-1.0, 0.5),
    steps: int = 100,
    unique_labels: Optional[Set[str]] = None,
) -> Callable[[Any], Tuple[np.ndarray, np.ndarray, List[str]]]:
    """
    Creates an objective function that calculates the minimal distance of each structure
    to the convex hull across a range of applied electrochemical potentials (U).

    The electron chemical potential is varied via the CHE formalism:
        mu_e(U) = - e * U + pH- and p_H2-dependent terms.

    Args:
        reference_potentials: Dictionary of fixed chemical potentials, e.g. {'Cu': -3.5, 'O': -4.2}.
                             These serve as the baseline for non-variable species.
        H_range: (H_min, H_max) range of applied potential (in eV).
        steps: Number of discrete U values to sample between H_min and H_max.
        unique_labels: Set of unique element labels. If None, inferred from reference_potentials.

    Returns:
        compute: A callable function that takes a dataset and returns:
                 (fE_matrix, H_values, labels)
    """
    # 1) Unique labels: infer from reference_potentials keys if not provided
    if unique_labels is None:
        # Exclude 'H2O' as it's a compound, assume keys are elements
        unique_labels = {lbl for lbl in reference_potentials.keys()}.union({'O','H'}) - {'H2O'}
    
    unique_labels_list = sorted(list(unique_labels))
    unique_labels_dict = { u:i for i, u in enumerate(unique_labels_list) }
    M = len(unique_labels_list)

    def compute(dataset: Any) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Compute min distance to convex hull for each structure across sampled U values.
        
        Args:
            dataset: SAGE Partition or object with get_all_energies/compositions.
            
        Returns:
            fE_array: Array of shape (N_structs, steps) with formation energies.
            H_values: Array of sampled potential values.
            unique_labels_list: List of species labels used.
        """

        # 2) Build composition matrix X and energy array y
        y = np.array(dataset.get_all_energies())
        species, species_order = dataset.get_all_compositions(return_species=True)
        
        # Map storage species order to our unique_labels_list order
        mapping = dataset.get_species_mapping(order="stored") # {label: storage_index}
        
        # idx[k] = storage index of the k-th label in unique_labels_list
        idx = np.full(len(unique_labels_list), -1, dtype=int)
        for k, lbl in enumerate(unique_labels_list):
            if lbl in mapping:
                idx[k] = mapping[lbl]
        
        # X matrix: (N_structs, M_labels)
        X = np.zeros((species.shape[0], M), dtype=species.dtype)
        
        # Only copy columns that exist in the dataset
        valid_mask = (idx >= 0)
        if np.any(valid_mask):
             X[:, valid_mask] = species[:, idx[valid_mask]]

        # 3) CHE adjustment
        # Adjust stoichiometry for Computational Hydrogen Electrode (CHE)
        # Reaction: H2O <-> 2H + O
        if 'H' in unique_labels_dict and 'O' in unique_labels_dict:
            idx_H = unique_labels_dict['H']
            idx_O = unique_labels_dict['O']
            # We are counting "excess H" relative to H2O stoichiometry
            X[:, idx_H] -= 2 * X[:, idx_O]
        
        # Reference chemical potentials for fixed species
        base_mu = np.array([reference_potentials.get(lbl, 0.0) for lbl in unique_labels_list])
        
        # If O is present, its base potential is set to H2O's potential (CHE shift)
        if 'O' in unique_labels_dict:
             base_mu[ unique_labels_dict['O'] ] = reference_potentials.get('H2O', 0.0)

        # Formation energy reference: E_formation_ref = E_total - sum(N_i * mu_i_base)
        fE_ref = y - X.dot(base_mu)
        
        # Variable term: nH * mu_H(U)
        if 'H' in unique_labels_dict:
             nH = X[:, unique_labels_dict['H']]
        else:
             nH = np.zeros(len(y))

        # Sample H potentials
        H_values = np.linspace(H_range[0], H_range[1], steps)

        # Vectorized formation energies (N_structs, steps)
        # fE(U) = fE_ref - nH * U
        fE_array = fE_ref[:, None] - nH[:, None] * H_values[None, :]
        
        return fE_array, H_values, unique_labels_list

    return compute

def analyze_feature_evolution(
    dataset_path: str,
    output_dir: str = "electrochemical_analysis",
    reference_potentials: Optional[Dict[str, float]] = None,
    H_range: Tuple[float, float] = (-1.0, 0.5),
    steps: int = 100,
    top_n: int = 10,
    feature_cutoffs: List[float] = [2.6, 3.2]
):
    """
    Analyzes how features of the most stable structures evolve as the chemical potential changes.
    
    Args:
        dataset_path: Path to the dataset (root folder for HybridStorage).
        output_dir: Directory to save results and plots.
        reference_potentials: Dictionary of reference chemical potentials.
        H_range: Range of potentials to scan.
        steps: Number of steps in the scan.
        top_n: Number of most stable structures to average features over.
        feature_cutoffs: Cutoffs for feature extraction graphs.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load Data
    print(f"Loading dataset from {dataset_path}...")
    if os.path.isdir(dataset_path):
         dataset = Partition(storage='hybrid', local_root=dataset_path, access='ro')
    else:
         # Fallback for single files
         dataset = Partition(storage='memory')
         dataset.read_files(dataset_path)

    # 2. Compute Stability Surface
    print("Computing stability surface...")
    if reference_potentials is None:
        reference_potentials = {'Cu': -3.5, 'O': -4.2, 'H2O': -14.25}

    compute_fn = objective_min_distance_to_electrochemicalhull(
        reference_potentials=reference_potentials,
        H_range=H_range,
        steps=steps
    )
    
    # fE_matrix: (N_structs, steps)
    fE_matrix, H_values, labels = compute_fn(dataset)
    
    # 2b. Compute Hull at each step
    # For each step (column), the hull is defined by the minimum energy
    hull_energy = fE_matrix.min(axis=0) # (steps,)
    
    # Distances to hull
    dist_matrix = fE_matrix - hull_energy[None, :]
    
    # 3. Compute Features (or load cached)
    print("Computing structural features...")
    feature_extractor = GraphFeatureExtractor(cutoffs=feature_cutoffs)
    
    feature_cache_path = os.path.join(output_dir, "features.csv")
    if os.path.exists(feature_cache_path):
        print(f"Loading features from cache {feature_cache_path}")
        df_features = pd.read_csv(feature_cache_path)
    else:
        # Check optimization opportunity: only compute relevant structures?
        # For simplicity, we compute all.
        features_list = feature_extractor.compute(dataset)
        df_features = pd.DataFrame(features_list)
        df_features.to_csv(feature_cache_path, index=False)

    # 4. Analyze Feature Evolution
    print("Analyzing feature evolution...")
    
    # Filter for numeric features only
    feature_names = [c for c in df_features.columns if c not in ["id", "Ef", "E"]]
    feature_names = df_features[feature_names].select_dtypes(include=[np.number]).columns.tolist()
    
    evolution_data = {fname: np.zeros(steps) for fname in feature_names}
    ground_state_ids = np.zeros(steps, dtype=int)

    for i in range(steps):
        # Identify top N stable structures at this potential H_values[i]
        distances = dist_matrix[:, i]
        # sort indices by distance
        sorted_idx = np.argsort(distances)
        top_idx = sorted_idx[:top_n]
        
        ground_state_ids[i] = top_idx[0]
        
        # Get subset of features and compute mean
        subset = df_features.iloc[top_idx]
        means = subset[feature_names].mean(axis=0)
        
        for fname in feature_names:
            evolution_data[fname][i] = means[fname]

    # 5. Plotting
    print("Generating plots...")
    
    # Plot 1: Hull Energy vs Potential
    plt.figure(figsize=(8, 5))
    plt.plot(H_values, hull_energy, label="Hull Energy")
    plt.xlabel("Chemical Potential H (eV)")
    plt.ylabel("Formation Energy (eV/atom)")
    plt.title("Electrochemical Hull Stability")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(os.path.join(output_dir, "hull_energy.png"))
    plt.close()
    
    # Plot 2: Feature Evolution
    plt.figure(figsize=(10, 6))
    for fname in feature_names:
        y_vals = evolution_data[fname]
        # Normalize to 0-1 range for visualization if variance is not 0
        if y_vals.max() > y_vals.min():
            y_norm = (y_vals - y_vals.min()) / (y_vals.max() - y_vals.min())
            plt.plot(H_values, y_norm, label=fname, alpha=0.7)
    
    plt.xlabel("Chemical Potential H (eV)")
    plt.ylabel("Normalized Feature Value")
    plt.title(f"Feature Evolution (Top {top_n} stable structures)")
    if len(feature_names) < 15:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "feature_evolution_normalized.png"))
    plt.close()
    
    # Save raw data
    evolution_df = pd.DataFrame(evolution_data)
    evolution_df["H_potential"] = H_values
    evolution_df.to_csv(os.path.join(output_dir, "feature_evolution.csv"), index=False)
    
    print("Analysis complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Electrochemical Hull Feature Analysis")
    parser.add_argument("--data", type=str, required=True, help="Path to dataset (folder for HybridStorage)")
    parser.add_argument("--output", type=str, default="electrochemical_analysis", help="Output directory")
    args = parser.parse_args()
    
    analyze_feature_evolution(args.data, output_dir=args.output)
