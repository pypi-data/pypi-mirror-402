
import pandas as pd
import numpy as np
from sage_lib.partition.partition_analysis.featurizer.analysis.feature_reduction import cluster_features_by_correlation

def main():
    print("Testing feature_reduction.py with NaNs/Constant features...")
    
    # Generate Dummy Data
    np.random.seed(42)
    N = 50
    f1 = np.random.rand(N)
    # f_const is constant -> variance 0 -> correlation NaN
    f_const = np.zeros(N) 
    
    X = pd.DataFrame({
        'A': f1,
        'Constant': f_const
    })
    
    # This should produce NaN in correlation matrix for 'Constant'
    print("Correlation Matrix:\n", X.corr())
    
    try:
        clusters = cluster_features_by_correlation(X, threshold=0.9)
        print("\nClustering successful!")
        for cid, cols in clusters.items():
            print(f"Cluster {cid}: {cols}")
    except Exception as e:
        print(f"\nTest Failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
