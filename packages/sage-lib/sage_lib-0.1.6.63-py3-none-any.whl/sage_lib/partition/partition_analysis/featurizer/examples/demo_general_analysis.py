
import pandas as pd
import numpy as np
from sage_lib.partition.partition_analysis.featurizer.analysis.feature_analysis import (
    clean_features,
    cluster_features,
    pick_representatives,
    pca_dimensionality,
    stability_selection,
    compute_feature_behavior_matrix,
    cluster_by_model_behavior
)

def main():
    # 1. Generate Dummy Data
    # ----------------------
    np.random.seed(42)
    N = 100
    # Create 3 base features
    f1 = np.random.rand(N)
    f2 = np.random.rand(N)
    f3 = np.random.rand(N)
    
    # Create correlated features (redundant)
    f1_copy = f1 + np.random.normal(0, 0.01, N) # Highly correlated with f1
    f2_copy = f2 * 2 + np.random.normal(0, 0.01, N) # Highly correlated with f2
    
    # Create a constant feature and one with NaNs
    f_const = np.zeros(N)
    f_nan = f3.copy()
    f_nan[0:30] = np.nan # 30% NaNs

    X = pd.DataFrame({
        'feat_1': f1, 
        'feat_1_copy': f1_copy,
        'feat_2': f2, 
        'feat_2_copy': f2_copy,
        'feat_3': f3,
        'feat_const': f_const,
        'feat_nan': f_nan
    })
    
    # Target variable for stability selection
    y = f1 * 2 + f2 - f3 + np.random.normal(0, 0.1, N)

    print("--- Original DataFrame Shape:", X.shape)
    print(X.head())

    # 2. Clean Features
    # -----------------
    # This will drop constant features and those with too many NaNs (default thresh=0.2)
    print("\n--- Cleaning Features ---")
    X_clean = clean_features(X, nan_strategy="median", drop_thresh=0.2)
    print("Shape after cleaning:", X_clean.shape)
    print("Columns:", X_clean.columns.tolist())
    # feat_const should be dropped (variance=0)
    # feat_nan should be dropped (30% NaN > 20% thresh)

    # 3. Correlation Clustering
    # -------------------------
    print("\n--- Clustering Features (by Correlation) ---")
    clusters = cluster_features(X_clean, corr_threshold=0.90)
    for cid, feats in clusters.items():
        print(f"Cluster {cid}: {feats}")

    # 4. Pick Representatives
    # -----------------------
    print("\n--- Picking Representatives ---")
    reps = pick_representatives(X_clean, clusters)
    print("Representative features:", reps)

    # 5. PCA Dimensionality
    # ---------------------
    print("\n--- PCA Analysis ---")
    d, cum_var = pca_dimensionality(X_clean, explained_variance=0.95)
    print(f"Dimensions needed for 95% variance: {d}")

    # 6. Stability Selection
    # ----------------------
    print("\n--- Stability Selection (XGBoost) ---")
    stability = stability_selection(X_clean, y, n_runs=5) # 5 runs for speed
    print("Stability Scores:\n", stability)

    # 7. Feature Behavior Matrix
    # --------------------------
    # We need some dummy importance dictionaries for the example
    features = X_clean.columns.tolist()
    perm_imp = {f: np.random.rand() for f in features}
    gain_imp = {f: np.random.rand() for f in features}
    cover_imp = {f: np.random.rand() for f in features}
    weight_imp = {f: np.random.rand() for f in features}
    stab_scores = stability.to_dict()

    print("\n--- Feature Behavior Matrix & Clustering ---")
    M, feature_names = compute_feature_behavior_matrix(
        model=None, # Not used inside the function currently
        X=X_clean,
        permutation_importance=perm_imp,
        stability_scores=stab_scores,
        gain_importance=gain_imp,
        cover_importance=cover_imp,
        weight_importance=weight_imp
    )
    
    # Cluster strictly based on behavior
    behavior_clusters = cluster_by_model_behavior(M, feature_names, n_clusters=2)
    print("Behavior Cluster {cid}: {feats}")

    # 8. Discriminative Analysis (Good vs Bad)
    # ----------------------------------------
    # from sage_lib.partition.partition_analysis.featurizer.analysis.feature_analysis import find_discriminative_features
    print("\n--- Discriminative Analysis (Good vs Bad Energy) ---")
    # Using small quantiles for this small dataset
    print("Skipping: find_discriminative_features not available in this version")
    # disc_df = find_discriminative_features(X_clean, y, q_lower=0.3, q_upper=0.7)
    # print(disc_df.head())

    # 9. SHAP Feature Explanation
    # ---------------------------
    from sage_lib.partition.partition_analysis.featurizer.analysis.feature_explanation import analyze_feature_effects
    from xgboost import XGBRegressor
    
    print("\n--- SHAP Feature Explanation ---")
    # Refit model on clean data
    model = XGBRegressor(n_estimators=100, max_depth=3)
    model.fit(X_clean, y)
    
    # Run analysis
    try:
        explanation_df = analyze_feature_effects(model, X_clean, output_dir="example_shap_plots")
        print("SHAP Global Importance:")
        print(explanation_df.head())
        print("Plots saved to 'example_shap_plots/'")
    except Exception as e:
        print(f"SHAP analysis failed (missing shap library?): {e}")

if __name__ == "__main__":
    main()
