
import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_reduction import cluster_features_by_correlation, pca_energy

class TestFeatureReduction(unittest.TestCase):
    
    def setUp(self):
        np.random.seed(42)
        self.N = 50
        self.f1 = np.random.rand(self.N)
        self.f2 = np.random.rand(self.N)
        self.f_const = np.zeros(self.N)
        self.f_nan = self.f1.copy()
        self.f_nan[0:10] = np.nan # Some NaNs
        
        self.X = pd.DataFrame({
            'A': self.f1,
            'A_strong': self.f1 * 2, # Correlated
            'B': self.f2,
            'Const': self.f_const,
            'NaNs': self.f_nan
        })

    def test_clustering_handles_nans(self):
        """Test that clustering doesn't crash with Constant features (NaN correlation)"""
        # The 'Const' feature produces NaN correlation with others.
        # This tests our fix in feature_reduction.py
        try:
            clusters = cluster_features_by_correlation(self.X, threshold=0.9)
        except Exception as e:
            self.fail(f"clustering crashed with NaNs/Constant features: {e}")
            
        # Verify result structure
        self.assertIsInstance(clusters, dict)
        self.assertTrue(len(clusters) > 0)
        
    def test_pca_handles_nans(self):
        """Test that PCA doesn't crash with NaNs in data"""
        try:
            d, cum = pca_energy(self.X)
        except Exception as e:
            self.fail(f"PCA crashed with NaNs in data: {e}")
            
        self.assertTrue(d > 0)
        self.assertEqual(len(cum), self.X.shape[1])

if __name__ == '__main__':
    unittest.main()
