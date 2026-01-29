"""
Simple Feature Extraction Example
=================================

This script demonstrates how to:
1. Load a dataset from any file format supported by ASE (xyz, cif, POSCAR, etc.).
2. Adapt the data for the SAGE GraphFeatureExtractor.
3. Compute features for all structures.
4. Save the results to a CSV file.

Usage:
    python simple_extractor.py --path /path/to/your/data.xyz --output features.csv
"""

import argparse
import pandas as pd
import os
import sys
import numpy as np
from typing import List

# Ensure we can import sage_lib if running from source without install
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from sage_lib.partition.partition_analysis.featurizer.core.featurizer import GraphFeatureExtractor

# Try to import ASE
try:
    from ase.io import read
    from ase import Atoms
except ImportError:
    print("Error: This example requires the ASE library. Please install it with `pip install ase`.")
    sys.exit(1)

# =========================================================
# Adapter Class
# =========================================================
class SageStructureAdapter:
    """
    Wraps an ASE Atoms object to mimic the SAGE Partition/Container interface
    expected by GraphFeatureExtractor.
    """
    def __init__(self, atoms: Atoms):
        self._atoms = atoms
        # Create the inner manager that holds the data
        self.AtomPositionManager = self._APM(atoms)

    class _APM:
        def __init__(self, atoms):
            self.atomPositions = atoms.get_positions()
            self.atomLabelsList = atoms.get_chemical_symbols()
            self.latticeVectors = atoms.get_cell()
            
            # Try to get energy, default to 0.0 if not present
            try:
                self.E = atoms.get_potential_energy()
            except:
                self.E = 0.0

# =========================================================
# Dataset Adapter
# =========================================================
class SageDatasetAdapter:
    """
    Wraps a list of SageStructureAdapters to mimic the Partition interface
    required by GraphFeatureExtractor.formation_energy.
    """
    def __init__(self, structures: List[SageStructureAdapter]):
        self.structures = structures
        self._n = len(structures)
        
        # Collect all unique species to define a consistent global order
        all_species = set()
        for s in structures:
            all_species.update(s.AtomPositionManager.atomLabelsList)
        self.species_order = sorted(list(all_species))
        self.species_map = {spec: i for i, spec in enumerate(self.species_order)}

    def __len__(self):
        return self._n

    def __getitem__(self, idx):
        return self.structures[idx]

    def __iter__(self):
        return iter(self.structures)

    def get_all_energies(self) -> np.ndarray:
        return np.array([s.AtomPositionManager.E for s in self.structures])

    def get_all_compositions(self, return_species=True):
        # Build (N, n_species) matrix
        N = len(self.structures)
        M = len(self.species_order)
        X = np.zeros((N, M), dtype=float)
        
        for i, s in enumerate(self.structures):
            labels = s.AtomPositionManager.atomLabelsList
            for lbl in labels:
                if lbl in self.species_map:
                    X[i, self.species_map[lbl]] += 1
        
        if return_species:
            return X, self.species_order
        return X

    def get_species_mapping(self, order="stored"):
        return self.species_map

def load_data(path: str) -> SageDatasetAdapter:
    """Loads structures using ASE and wraps them in a dataset adapter."""
    print(f"Loading data from {path} using ASE...")
    try:
        # Read all configurations (index=':')
        atoms_list = read(path, index=':')
        if not isinstance(atoms_list, list):
            atoms_list = [atoms_list]
        
        print(f"Loaded {len(atoms_list)} structures.")
        
        # Wrap structures
        wrapped_list = [SageStructureAdapter(at) for at in atoms_list]
        
        # Wrap in dataset adapter
        return SageDatasetAdapter(wrapped_list)

    except Exception as e:
        print(f"Error loading file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Simple Feature Extractor")
    parser.add_argument("--path", type=str, required=True, help="Path to structure file (xyz, db, or folder)")
    parser.add_argument("--output", type=str, default="features.csv", help="Output CSV filename")
    parser.add_argument("--n_jobs", type=int, default=1, help="Number of parallel jobs (default: 1)")
    args = parser.parse_args()

    # 1. Load Data
    data = load_data(args.path)
    if not data:
        print("No data loaded. Exiting.")
        sys.exit(0)

    # 2. Initialize Featurizer
    # Define cutoffs for graph construction (in Angstroms)
    cutoffs = [2.6, 3.2]
    
    print("Initializing GraphFeatureExtractor...")
    # mu_dict is None, so formation energy will likely be 0 unless fitted, 
    # but we just want features here.
    extractor = GraphFeatureExtractor(cutoffs=cutoffs, mu_dict=None)

    # 3. Compute Features
    print("Computing features...")
    
    if args.n_jobs > 1 and len(data) > 10:
        # Parallel processing
        from sage_lib.partition.partition_analysis.featurizer.core.featurizer import FeatureBatchProcessor
        processor = FeatureBatchProcessor(extractor, n_jobs=args.n_jobs)
        features_list = processor.process(data)
    else:
        # Serial processing
        features_list = extractor.compute(data)

    # 4. Save to DataFrame
    df = pd.DataFrame(features_list)
    print(f"Computed {len(df)} feature vectors with {df.shape[1]} descriptors each.")
    
    # Remove 'Ef' and 'E' if they are zero/meaningless and user didn't care? 
    # Or keep them. Let's keep them but print a note.
    
    # Preview
    print("\nFeature Preview:")
    print(df.head())

    # Save
    print(f"\nSaving to {args.output}...")
    df.to_csv(args.output, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
