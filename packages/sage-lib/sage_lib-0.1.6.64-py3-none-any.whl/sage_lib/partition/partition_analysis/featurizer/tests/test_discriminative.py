
import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_analysis import find_discriminative_features

class TestDiscriminativeAnalysis(unittest.TestCase):
    
    def setUp(self):
        np.random.seed(42)
        N = 100
        # Feature A: High for Low Energy (Good), Low for High Energy (Bad)
        # Feature B: Random noise
        
        # Energy: 0 to 1
        y = np.linspace(0, 1, N)
        
        # Feature A correlates negatively with Energy (High A = Low Energy = Good)
        f_a = 1.0 - y + np.random.normal(0, 0.1, N)
        
        # Feature B is random
        f_b = np.random.rand(N)
        
        self.X = pd.DataFrame({'Feat_A': f_a, 'Feat_B': f_b})
        self.y = y

    def test_find_discriminative_features(self):
        results = find_discriminative_features(self.X, self.y, q_lower=0.2, q_upper=0.8)
        
        self.assertFalse(results.empty)
        # Feat_A should have high absolute score
        # Feat_B should be low
        
        score_a = results.loc['Feat_A', 'discriminative_score']
        score_b = results.loc['Feat_B', 'discriminative_score']
        
        # A should be positive (Mean Low (High Val) - Mean High (Low Val)) > 0
        self.assertTrue(score_a > 1.0, f"Score for A should be high, got {score_a}")
        self.assertTrue(abs(score_b) < 1.0, f"Score for B should be low, got {score_b}")
        
    def test_empty_groups_handling(self):
        # Pass quantiles that result in empty groups
        try:
             # q_lower= -0.1 impossible -> empty low group
            res = find_discriminative_features(self.X, self.y, q_lower=-0.1, q_upper=1.1)
            self.assertTrue(res.empty)
        except Exception as e:
            self.fail(f"Function crashed on empty groups: {e}")

if __name__ == '__main__':
    unittest.main()
