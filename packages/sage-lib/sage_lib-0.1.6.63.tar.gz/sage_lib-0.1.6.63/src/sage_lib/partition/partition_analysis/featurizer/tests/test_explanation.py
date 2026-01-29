
import unittest
import pandas as pd
import numpy as np
import sys
import os
import shutil
import xgboost as xgb

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_explanation import analyze_feature_effects

class TestFeatureExplanation(unittest.TestCase):
    
    def setUp(self):
        np.random.seed(42)
        N = 50
        # Quadratic relationship: y = x^2
        x = np.linspace(-2, 2, N)
        y = x**2 + np.random.normal(0, 0.1, N)
        
        self.X = pd.DataFrame({'Feat_Quad': x, 'Feat_Noise': np.random.rand(N)})
        self.y = y
        
        # Train simple model
        self.model = xgb.XGBRegressor(n_estimators=10, max_depth=2)
        self.model.fit(self.X, self.y)
        
        self.output_dir = "test_shap_plots"

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_shap_analysis_runs(self):
        """Test that SHAP analysis runs and generates plots"""
        try:
            df = analyze_feature_effects(self.model, self.X, output_dir=self.output_dir)
        except Exception as e:
            self.fail(f"SHAP analysis crashed: {e}")
            
        # Check if plots were created
        self.assertTrue(os.path.exists(self.output_dir))
        files = os.listdir(self.output_dir)
        self.assertTrue(len(files) > 0, "No plots generated")
        
        # Check if we got importance dataframe
        self.assertFalse(df.empty)
        self.assertIn('Feat_Quad', df['col_name'].values)

if __name__ == '__main__':
    unittest.main()
