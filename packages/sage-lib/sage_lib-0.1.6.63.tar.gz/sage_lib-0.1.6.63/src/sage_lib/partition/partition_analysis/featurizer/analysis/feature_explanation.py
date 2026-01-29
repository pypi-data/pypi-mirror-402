import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
import os

def analyze_feature_effects(model, X, feature_names=None, output_dir="feature_plots"):
    """
    Performs SHAP analysis to explain feature effects on the model output.
    
    Args:
        model: Trained model (compatible with SHAP, e.g. XGBoost, sklearn trees)
        X: Feature matrix (DataFrame or numpy array)
        feature_names: List of feature names (optional if X is DataFrame)
        output_dir: Directory to save plots
        
    Returns:
        DataFrame containing mean absolute SHAP values (global importance).
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Handle input types
    if isinstance(X, pd.DataFrame):
        X_vals = X.values
        if feature_names is None:
            feature_names = X.columns.tolist()
    else:
        X_vals = X
        if feature_names is None:
            feature_names = [f"Feature {i}" for i in range(X.shape[1])]
            
    print("Computing SHAP values...")
    # TreeExplainer is best for trees (XGBoost, RandomForest, etc.)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_vals)
    
    # 1. Summary Plot (Beeswarm)
    # Shows direction (Red/Blue) and magnitude
    plt.figure()
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "shap_summary_beeswarm.png"), dpi=300)
    plt.close()
    
    # 2. Global Importance Bar Chart
    plt.figure()
    shap.summary_plot(shap_values, X, feature_names=feature_names, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "shap_importance_bar.png"), dpi=300)
    plt.close()
    
    # 3. Dependence Plots for Top Features (Non-linearities/Intervals)
    # Calculate mean abs shap for importance ranking
    if isinstance(shap_values, list): # For classification with multiple classes
        vals = np.abs(shap_values[0]).mean(0)
    else:
        vals = np.abs(shap_values).mean(0)
        
    feature_importance = pd.DataFrame(list(zip(feature_names, vals)),
                                      columns=['col_name','feature_importance_vals'])
    feature_importance.sort_values(by=['feature_importance_vals'],
                                   ascending=False, inplace=True)
    
    top_features = feature_importance['col_name'].head(4).tolist()
    
    print(f"Generating dependence plots for top features: {top_features}")
    for feat in top_features:
        try:
            plt.figure()
            shap.dependence_plot(feat, shap_values, X, feature_names=feature_names, show=False)
            plt.tight_layout()
            # Clean filename
            safe_feat = "".join([c if c.isalnum() else "_" for c in feat])
            plt.savefig(os.path.join(output_dir, f"shap_dependence_{safe_feat}.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"Could not plot dependence for {feat}: {e}")
            
    return feature_importance
