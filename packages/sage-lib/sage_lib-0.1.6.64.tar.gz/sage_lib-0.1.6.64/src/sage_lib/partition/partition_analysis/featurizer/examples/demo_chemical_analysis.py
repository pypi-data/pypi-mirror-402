"""
Chemical Feature Relevance Analysis with SAGE
=============================================

This script provides an abstract, complete example of how to perform 
feature analysis on chemical data using the SAGE library.

It demonstrates a standard workflow:
1. Generating/Loading abstract chemical features (element fractions, bond statistics).
2. Cleaning features (removing NaNs, constant columns).
3. Analyzing feature redundancy (Correlation Clustering).
4. Identifying relevant features using Stability Selection (Robust XGBoost).
5. Visualizing/Reporting the critical descriptors.

This example uses synthetic data to simulate a scenario where we want to identify 
which chemical representations (e.g., fractional compositions vs. bond lengths) 
drive a target property like Formation Energy.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.inspection import PartialDependenceDisplay
import shap
import os

# SAGE Library Imports
try:
    from sage_lib.partition.partition_analysis.featurizer.analysis.feature_analysis import (
        clean_features,
        cluster_features,
        pick_representatives,
        stability_selection
    )
    from sage_lib.partition.partition_analysis.featurizer.analysis.xgb_postanalysis import (
        xgb_importances
    )
except ImportError:
    # If running standalone without the full package structure, we might need path adjustments
    import sys
    import os
    sys.path.append(os.path.abspath("../../../../..")) # Adjust based on actual location
    from sage_lib.partition.partition_analysis.featurizer.analysis.feature_analysis import (
        clean_features,
        cluster_features,
        pick_representatives,
        stability_selection
    )
    from sage_lib.partition.partition_analysis.featurizer.analysis.xgb_postanalysis import (
        xgb_importances
    )

def generate_abstract_chemical_data(n_samples=500, random_state=42):
    """
    Generates a synthetic dataset representing chemical features.
    
    The target property 'Formation_Energy' is constructed to depend on 
    specific interactions with optimized points and penalties.
    
    Rules implemented:
    1. Optimal Point: C-H bond length is optimal (lowest energy) at 1.10 Å. Devation increases energy (parabola).
    2. Destabilizing Factor: Oxygen fraction > 0.6 drastically increases energy (instability).
    3. Linear Benefit: Higher Hydrogen fraction linearly decreases energy (stabilizing).
    """
    np.random.seed(random_state)
    
    # 1. Fundamental Chemical Features (Independent Variables)
    frac_C = np.random.uniform(0.1, 0.8, n_samples)
    frac_H = np.random.uniform(0.1, 0.8, n_samples)
    scale = (frac_C + frac_H + np.random.uniform(0.0, 0.2, n_samples))
    frac_C /= scale
    frac_H /= scale
    frac_O = 1.0 - (frac_C + frac_H) # Balance
    
    # 2. Structural Features (Bond lengths in Angstroms)
    # C-H bond length correlates slightly with C fraction but has variance
    mean_dist_CH = 1.09 + (frac_C * 0.1) + np.random.normal(0, 0.05, n_samples)
    mean_dist_OH = 0.96 + np.random.normal(0, 0.05, n_samples)
    
    # 3. Geometric Features
    vol_per_atom = 10.0 + (frac_C * 5.0) + np.random.normal(0, 1.0, n_samples)
    
    # 4. Redundant/Correlated Features
    carbon_content_pct = frac_C * 100.0
    
    # 5. Noise Features
    noise_1 = np.random.rand(n_samples)
    noise_2 = np.random.rand(n_samples)
    
    # 6. Construct Target: Formation Energy (eV/atom)
    formation_energy = np.zeros(n_samples)
    
    # Rule A: Parabolic stability for C-H bond (Optimal at 1.10)
    # E += 20 * (x - 1.10)^2
    formation_energy += 20.0 * (mean_dist_CH - 1.10)**2
    
    # Rule B: Linear stabilization from Hydrogen
    formation_energy -= 2.0 * frac_H
    
    # Rule C: Instability if Oxygen > 0.6 (Step function / penalty)
    formation_energy += np.where(frac_O > 0.6, 5.0, 0.0)
    
    # Add noise
    formation_energy += np.random.normal(0, 0.1, n_samples)
    
    # Create DataFrame
    data = {
        'frac_C': frac_C,
        'frac_H': frac_H,
        'frac_O': frac_O,
        'mean_dist_C-H': mean_dist_CH,
        'mean_dist_O-H': mean_dist_OH,
        'vol_per_atom': vol_per_atom,
        'pct_C': carbon_content_pct, # Redundant
        'noise_metric_1': noise_1,   # Irrelevant
        'noise_metric_2': noise_2    # Irrelevant
    }
    
    X = pd.DataFrame(data)
    y = pd.Series(formation_energy, name="Formation_Energy")
    
    return X, y

def analyze_chemical_relevance(X, y, output_dir="analysis_results"):
    """
    Performs the standard SAGE feature analysis workflow with advanced interpretation.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print("=========================================================")
    print(" SAGE Chemical Feature Analysis & Rule Extraction")
    print("=========================================================")
    
    # 1. Clean & Cluster
    X_clean = clean_features(X, nan_strategy='median', drop_thresh=0.2)
    clusters = cluster_features(X_clean, corr_threshold=0.95)
    representatives = pick_representatives(X_clean, clusters)
    X_reduced = X_clean[representatives]
    print(f" -> Selected Representative Features: {representatives}")

    # 2. Stability Selection
    print("\n[Step 2] Stability Selection (Identifying Robust Drivers)...")
    stability_scores = stability_selection(X_reduced, y.values, n_runs=20)
    relevant_features = stability_scores[stability_scores > 0.4].index.tolist()
    print(f" -> Critical Features identified: {relevant_features}")
    
    # 3. Model Training (for Explanation)
    print("\n[Step 3] Fitting Interpretability Model (XGBoost)...")
    model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05)
    model.fit(X_reduced[relevant_features], y)
    
    # =========================================================
    # ADVANCED ANALYSIS: Finding Optimal Points & Rules
    # =========================================================
    
    # A. SHAP Analysis (Directionality & Contribution)
    print("\n[Step 4] SHAP Analysis (Stability Contributors)...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_reduced[relevant_features])
    
    # Summary Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_reduced[relevant_features], show=False)
    plt.title("SHAP Summary: Feature Impact on Formation Energy")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/shap_summary.png")
    plt.close()
    print(f" -> Saved SHAP summary to {output_dir}/shap_summary.png")
    
    # B. Partial Dependence Plots (PDP) (Finding Optimal Values)
    print("\n[Step 5] Partial Dependence Plots (Finding Optimal Values)...")
    # We plot PDP for the top 3 relevant features
    top_feats = relevant_features[:3] 
    
    fig, ax = plt.subplots(figsize=(12, 4))
    display = PartialDependenceDisplay.from_estimator(
        model, 
        X_reduced[relevant_features], 
        top_feats, 
        kind="average", 
        ax=ax
    )
    plt.suptitle("Partial Dependence: Identifying Optimal Operating Points", y=1.05)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/pdp_optimal_points.png")
    plt.close()
    print(f" -> Saved PDP plots to {output_dir}/pdp_optimal_points.png")
    
    # C. Rule Extraction (Surrogate Decision Tree)
    print("\n[Step 6] Extracting Fundamental Rules (Decision Tree Surrogate)...")
    # We fit a simple Decision Tree to mimic the complex XGBoost model
    # This gives us explicit "If-Then" rules.
    tree = DecisionTreeRegressor(max_depth=3)
    tree.fit(X_reduced[relevant_features], model.predict(X_reduced[relevant_features]))
    
    rules = export_text(tree, feature_names=relevant_features)
    print("\n--- EXTRACTED RULES (Approximation) ---")
    print(rules)
    
    with open(f"{output_dir}/derived_rules.txt", "w") as f:
        f.write(rules)

def main():
    # 1. Generate Data with Hidden Rules
    X, y = generate_abstract_chemical_data(n_samples=500)
    
    # 2. Run Analysis
    analyze_chemical_relevance(X, y)
    
    print("\nAnalysis Complete.")
    print("Check 'analysis_results/' for plots and rule text.")

if __name__ == "__main__":
    main()
