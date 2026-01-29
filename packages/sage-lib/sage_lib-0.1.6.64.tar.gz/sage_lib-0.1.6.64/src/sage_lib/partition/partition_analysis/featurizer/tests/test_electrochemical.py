import numpy as np
import pandas as pd
import sys
import os

# Ensure we can import the new module
sys.path.append(os.getcwd())
# Adjust path to find sage_lib if running from root
sys.path.append(os.path.join(os.getcwd(), 'src'))

from sage_lib.partition.partition_analysis.featurizer.analysis.electrochemical import (
    objective_min_distance_to_electrochemicalhull, 
    analyze_feature_evolution
)

# Mock Dataset
class MockDataset:
    def __init__(self, n_structs=50):
        self.n = n_structs
        self.energies = np.random.uniform(-100, -50, n_structs)
        self.species_labels = ['Cu', 'O', 'H']
        
        # Random compositions
        self.compositions = np.zeros((n_structs, 3), dtype=int)
        for i in range(n_structs):
            self.compositions[i, 0] = np.random.randint(1, 10) # Cu
            self.compositions[i, 1] = np.random.randint(1, 10) # O
            self.compositions[i, 2] = np.random.randint(1, 10) # H
            
    def get_all_energies(self):
        return self.energies
    
    def get_all_compositions(self, return_species=False):
        if return_species:
            return self.compositions, self.species_labels
        return self.compositions

    def get_species_mapping(self, order="stored"):
        return {lbl: i for i, lbl in enumerate(self.species_labels)}

    def __len__(self):
        return self.n

    def __iter__(self):
        # Yield dummy objects that the featurizer compute_features expects?
        # Actually, since we mocked GraphFeatureExtractor, the iteration happens 
        # inside the REAL GraphFeatureExtractor.compute IF we didn't mock it completely.
        # Wait, I mocked GraphFeatureExtractor in `verify_electrochemical_analysis.py`
        # BUT `electrochemical_hull_analysis.py` imports `GraphFeatureExtractor` from `featurizer` module directly.
        
        # In `verify_electrochemical_analysis.py`:
        # import sage_lib...featurizer as real_featurizer
        # real_featurizer.GraphFeatureExtractor = MockGraphFeatureExtractor
        
        # However, `electrochemical_hull_analysis.py` does:
        # from sage_lib.partition.partition_analysis.featurizer.featurizer import GraphFeatureExtractor
        
        # If `electrochemical_hull_analysis` was imported BEFORE I did the monkeypatch, 
        # it holds the original class.
        # I imported `electrochemical_hull_analysis` at the top of `verify_...`.
        # So it has the original class.
        
        # The traceback shows it failing in `electrochemical_hull_analysis.py` line 227 calling `feature_extractor.compute(dataset)`.
        # And then inside `featurizer.py` line 184.
        # This confirms it is using the REAL `GraphFeatureExtractor`, NOT my mock.
        
        # I need to patch `sage_lib.partition.partition_analysis.featurizer.electrochemical_hull_analysis.GraphFeatureExtractor`
        # OR ensure the mock is applied before import (circular import issues potentially)
        # OR patch the instance/class in the target module.
        
        for i in range(self.n):
            yield i # yield dummy items

# Mock Featurizer
# We need to monkeypatch GraphFeatureExtractor used in the script
# or pass a mock/dummy somehow.
# Since the script instantiates GraphFeatureExtractor internally if we don't pass one,
# we need to be careful.
# The script `analyze_feature_evolution` imports GraphFeatureExtractor from featurizer.
# We can mock `sage_lib.partition.partition_analysis.featurizer.core.featurizer.GraphFeatureExtractor`

import sage_lib.partition.partition_analysis.featurizer.core.featurizer as real_featurizer

class MockGraphFeatureExtractor:
    def __init__(self, cutoffs, mu_dict=None):
        pass
        
    def compute(self, dataset, subsample=None):
        # return list of dicts
        # 3 mock features
        rows = []
        for i in range(dataset.n):
            rows.append({
                "id": i,
                "Ef": 0.0,
                "feature_A": np.sin(i),
                "feature_B": np.cos(i),
                "feature_C": np.random.random()
            })
        return rows

# Inject mock
# We must patch it in the MODULE where it is used
import sage_lib.partition.partition_analysis.featurizer.analysis.electrochemical as target_module
target_module.GraphFeatureExtractor = MockGraphFeatureExtractor

def test_objective_function():
    print("Testing objective function...")
    dataset = MockDataset(20)
    ref_mu = {'Cu': -3.5, 'O': -4.2, 'H2O': -14.25}
    
    compute_fn = objective_min_distance_to_electrochemicalhull(
        reference_potentials=ref_mu,
        H_range=(-1.0, 0.5),
        steps=50
    )
    
    fE_matrix, H_values, labels = compute_fn(dataset)
    
    print("Output shapes:", fE_matrix.shape, H_values.shape)
    assert fE_matrix.shape == (20, 50)
    assert len(H_values) == 50
    print("Objective function test passed.")

def test_full_analysis():
    print("Testing full analysis...")
    dataset = MockDataset(20)
    
    # We need to simulate the 'input' being a path or object. 
    # The script expects a path and loads Partition.
    # We should modify the script or just monkeypatch Partition to return our mock.
    
    import sage_lib.partition.partition_analysis.featurizer.analysis.electrochemical as target_module
    
    # Mock Partition class in the target module
    original_partition = target_module.Partition
    target_module.Partition = lambda storage, **kwargs: dataset if storage=='hybrid' else dataset
    
    # Need to handle the 'fallback' read_files call in script if not directory
    # The script does:
    # if os.path.isdir(dataset_path): Partition(hybrid...)
    # else: Partition(memory).read_files(...)
    
    # We will pass a dummy directory path so it takes the first branch
    if not os.path.exists("dummy_dir"): 
        os.makedirs("dummy_dir")
    
    output_dir = "test_electro_output"
    
    try:
        analyze_feature_evolution(
            "dummy_dir", 
            output_dir=output_dir, 
            steps=20, 
            top_n=5
        )
        
        # Check outputs
        assert os.path.exists(os.path.join(output_dir, "hull_energy.png"))
        assert os.path.exists(os.path.join(output_dir, "feature_evolution.csv"))
        assert os.path.exists(os.path.join(output_dir, "feature_evolution_normalized.png"))
        
        df = pd.read_csv(os.path.join(output_dir, "feature_evolution.csv"))
        assert len(df) == 20
        assert "feature_A" in df.columns
        print("Full analysis test passed.")
        
    finally:
        # Cleanup
        target_module.Partition = original_partition
        import shutil
        if os.path.exists("dummy_dir"):
            os.rmdir("dummy_dir")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_objective_function()
    test_full_analysis()
