
from sage_lib.partition.partition_analysis.featurizer.core.featurizer import GraphFeatureExtractor
from ase import Atoms
import pytest

def test_feature_calculation():
    """
    Test how to use the code to calculate features for a single structure.
    """
    print("\n=== Test: Calculating Features for a Single Structure ===")
    
    # 1. Create a dummy structure (e.g., Water molecule)
    atoms = Atoms('H2O', positions=[[0, 0, 0], [0, 0, 0.96], [0, 0.96, 0]])
    atoms.pbc = True
    atoms.cell = [10, 10, 10]
    
    # Fake energy (needed for formation energy calculation if not provided externally)
    # The extractor uses `atoms.AtomPositionManager.E`.
    # Let's mock that attribute.
    class MockAPM:
        def __init__(self, atoms_obj):
            self.E = -14.25 # eV
            # GraphBuilder expects positions, labels, lattice
            self.atomPositions = atoms_obj.get_positions()
            self.atomLabelsList = atoms_obj.get_chemical_symbols()
            self.latticeVectors = atoms_obj.get_cell()

    atoms.AtomPositionManager = MockAPM(atoms)
    
    # 2. Initialize Featurizer
    cutoffs = [2.6, 3.2]
    # We must provide chemical potentials if we want formation energy
    mu_dict = {'H': -3.5, 'O': -7.0} 
    
    feature_extractor = GraphFeatureExtractor(cutoffs, mu_dict=mu_dict)
    
    # 3. Compute Features
    try:
        features = feature_extractor.compute_features(atoms)
        
        print("Features computed successfully!")
        print(f"Number of features: {len(features)}")
        # Basic assertions
        assert len(features) > 0
        assert "c2.60_deg_mean" in features
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        raise e

if __name__ == "__main__":
    test_feature_calculation()
