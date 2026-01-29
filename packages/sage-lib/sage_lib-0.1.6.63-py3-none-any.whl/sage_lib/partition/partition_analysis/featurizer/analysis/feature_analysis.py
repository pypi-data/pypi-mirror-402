# =============================
# feature_analysis.py
# =============================
"""
Tools for analyzing, clustering, and selecting important features.

This module provides functions for:
- Correlation-based feature clustering.
- Representative feature selection.
- PCA dimensionality analysis.
- Stability selection using XGBoost.
- Cleaning feature sets (removing NaNs and constants).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import pairwise_distances
from xgboost import XGBRegressor


# ============================================================
# 1) Correlation-based clustering of descriptors
# ============================================================
def cluster_features(X: pd.DataFrame, corr_threshold: float = 0.85) -> Dict[int, List[str]]:
    """
    Groups redundant features using hierarchical clustering on (1 - |corr|).

    Args:
        X: Feature DataFrame.
        corr_threshold: Correlation threshold above which features are considered similar.

    Returns:
        Dictionary mapping cluster IDs to lists of feature names.
    """
    # Compute absolute correlation matrix
    corr = np.abs(X.corr())
    dist = 1 - corr.values  # Distance matrix = 1 - |corr|

    # Hierarchical clustering
    model = AgglomerativeClustering(
        metric='precomputed',
        linkage='average',
        distance_threshold=1 - corr_threshold,
        n_clusters=None
    )

    labels = model.fit_predict(dist)

    clusters = {}
    for i, label in enumerate(labels):
        clusters.setdefault(label, []).append(X.columns[i])

    return clusters


# ============================================================
# 2) Select representative feature per cluster
# ============================================================
def pick_representatives(X: pd.DataFrame, clusters: Dict[int, List[str]]) -> List[str]:
    """
    Picks one representative feature per cluster. 
    Strategy is to pick the feature with the highest variance within the cluster.

    Args:
        X: Feature DataFrame.
        clusters: Dictionary of clusters {cluster_id: [features]}.

    Returns:
        List of representative feature names.
    """
    representatives = []

    for cid, feats in clusters.items():
        if len(feats) == 1:
            representatives.append(feats[0])
            continue

        # Choose feature with highest variance
        variances = X[feats].var().sort_values(ascending=False)
        rep = variances.index[0]
        representatives.append(rep)

    return representatives


# ============================================================
# 3) PCA dimensionality analysis (optional)
# ============================================================
def pca_dimensionality(X: pd.DataFrame, explained_variance: float = 0.95) -> Tuple[int, np.ndarray]:
    """
    Determine the effective dimensionality feature space using PCA.

    Args:
        X: Feature DataFrame.
        explained_variance: Target cumulative variance ratio (0 < v <= 1).

    Returns:
        d: Number of components needed to reach target variance.
        cum: Cumulative explained variance ratio array.
    """
    pca = PCA().fit(X)
    cum = np.cumsum(pca.explained_variance_ratio_)
    d = np.searchsorted(cum, explained_variance) + 1
    return d, cum


# ============================================================
# 4) Stability selection on collapsed space
# ============================================================
def stability_selection(
    X: pd.DataFrame,
    y: np.ndarray,
    n_runs: int = 30,
    sample_fraction: float = 0.7,
    random_state: int = 123,
) -> pd.Series:
    """
    Perform stability selection by repeatedly training XGBoost on subsamples.

    Args:
        X: Feature DataFrame.
        y: Target array.
        n_runs: Number of bootstrap iterations.
        sample_fraction: Fraction of data to use in each iteration.
        random_state: Random see base.

    Returns:
        Pandas Series of stability scores (0 to 1), sorted descending.
    """
    N = len(X)
    features = X.columns
    counts = np.zeros(len(features))

    for k in range(n_runs):
        np.random.seed(random_state + k)
        
        # Bootstrap subsample indices
        idx = np.random.choice(N, int(N * sample_fraction), replace=True)

        Xs = X.iloc[idx]
        ys = y[idx]

        model = XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state + k,
            n_jobs=1 
        )
        model.fit(Xs, ys)

        imp = model.get_booster().get_score(importance_type="gain")

        for fname in imp:
            if fname in features:
                counts[X.columns.get_loc(fname)] += 1

    stability = counts / n_runs
    return pd.Series(stability, index=features).sort_values(ascending=False)


# ============================================================
# CLEANING: remove NaNs + constant features
# ============================================================
def clean_features(X: pd.DataFrame, nan_strategy: str = "median", drop_thresh: float = 0.2) -> pd.DataFrame:
    """
    Clean descriptor matrix.
    
    1. Drops features with > drop_thresh NaNs.
    2. Fills remaining NaNs (median or zero).
    3. Drops constant (zero-variance) features.

    Args:
        X: Feature DataFrame.
        nan_strategy: 'median' or 'zero'.
        drop_thresh: Drop column if NaN fraction > this value.

    Returns:
        Cleaned Pandas DataFrame.
    """
    # 1) Drop features with too many NaNs
    nan_frac = X.isna().mean()
    to_drop = nan_frac[nan_frac > drop_thresh].index.tolist()
    if len(to_drop) > 0:
        print(f"Dropping {len(to_drop)} features with too many NaNs.")
        X = X.drop(columns=to_drop)

    # 2) Replace remaining NaNs
    if nan_strategy == "median":
        X = X.fillna(X.median())
    elif nan_strategy == "zero":
        X = X.fillna(0)
    else:
        raise ValueError(f"Invalid nan_strategy: {nan_strategy}")

    # 3) Drop constant (zero-variance) features
    variances = X.var()
    const = variances[variances == 0].index.tolist()
    if len(const) > 0:
        print(f"Dropping {len(const)} constant features.")
        X = X.drop(columns=const)

    return X


def compute_feature_behavior_matrix(
    model: Any,
    X: pd.DataFrame,
    permutation_importance: Dict[str, float],
    stability_scores: Dict[str, float],
    gain_importance: Dict[str, float],
    cover_importance: Dict[str, float],
    weight_importance: Dict[str, float],
    pdp_curves: Optional[Dict[str, np.ndarray]] = None
) -> Tuple[np.ndarray, List[str]]:
    """
    Build a feature-behavior matrix where each row encodes various importance metrics
    and behavior signatures for clustering features by "how they affect the model".

    Returns:
        Matrix M (n_features x n_metrics) and list of feature names.
    """

    features = X.columns
    n = len(features)

    # Normalize all metrics before concatenation
    def normalize(v):
        v = np.array(v, dtype=float)
        if np.std(v) == 0:
            return v * 0
        return (v - np.mean(v)) / (np.std(v) + 1e-12)

    # Build matrix
    behavior_vectors = []

    for f in features:
        vec = []

        # Permutation importance
        vec.append(permutation_importance.get(f, 0.0))

        # Stability selection
        vec.append(stability_scores.get(f, 0.0))

        # XGBoost split statistics
        vec.append(gain_importance.get(f, 0.0))
        vec.append(cover_importance.get(f, 0.0))
        vec.append(weight_importance.get(f, 0.0))

        # PDP (if provided)
        if pdp_curves is not None and f in pdp_curves:
            vec.extend(normalize(pdp_curves[f]))

        behavior_vectors.append(vec)

    # Convert to matrix
    M = np.array(behavior_vectors)
    M = StandardScaler().fit_transform(M)

    return M, list(features)


def cluster_by_model_behavior(behavior_matrix: np.ndarray, feature_names: List[str], n_clusters: Optional[int] = None) -> Dict[int, List[str]]:
    """
    Cluster features based on their model-behavior signatures using Agglomerative Clustering.

    Args:
        behavior_matrix: Matrix from compute_feature_behavior_matrix.
        feature_names: List of feature names corresponding to rows.
        n_clusters: Number of clusters. If None, determines automatically.

    Returns:
        Dictionary of clusters {cluster_id: [features]}.
    """

    # Compute pairwise distances (optional debug step, but used inside clustering implicitly)
    # D = pairwise_distances(behavior_matrix, metric='euclidean')

    if n_clusters is None:
        # Automatic mode requires distance_threshold
        clustering = AgglomerativeClustering(
            metric='euclidean',
            linkage='ward',
            distance_threshold=0.0,  # allow full tree for exploration
            n_clusters=None          # <-- REQUIRED for automatic mode in newer sklearn if dist_threshold set
        )
        # Note: scikit-learn logic for n_clusters=None + distance_threshold=0 returns N clusters.
        # User likely intended distance_threshold to be something else or just getting the tree.
        # However, preserving original logic logic structure. 
        # Actually original code had distance_threshold=0.0 and n_clusters=None, 
        # which effectively returns a cluster for every point unless cut.
        # Let's trust the logic structure but note it might over-cluster without a real threshold.
    else:
        clustering = AgglomerativeClustering(
            metric='euclidean',
            linkage='ward',
            n_clusters=n_clusters
        )

    labels = clustering.fit_predict(behavior_matrix)

    clusters = {}
    for f, c in zip(feature_names, labels):
        clusters.setdefault(c, []).append(f)

    return clusters
