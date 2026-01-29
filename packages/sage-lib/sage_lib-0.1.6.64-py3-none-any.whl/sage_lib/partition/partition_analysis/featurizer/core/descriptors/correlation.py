# =============================
# descriptors_correlation.py
# =============================
"""
Descriptors measuring spatial autocorrelation and characteristic length scales in the graph.
"""

import numpy as np
import networkx as nx
from typing import Dict, Any, List
from scipy.optimize import curve_fit

class CorrelationDescriptors:
    """
    Class for calculating spatial correlations of node properties at varying topological distances.
    """

    @staticmethod
    def spatial_autocorrelation(G: nx.Graph, prefix: str, k_max: int = 4) -> Dict[str, float]:
        """
        Calculates autocorrelation of node properties (Degree, Z) at distances k=1..k_max.
        Also computes correlation length by fitting exponential decay.
        
        Args:
            G: NetworkX graph with 'Z' (atomic number) node attributes.
            prefix: Prefix for feature names.
            k_max: Maximum topological distance to check.
            
        Returns:
            Dictionary with corr_phi_k and k_corr_phi features.
        """
        if G.number_of_nodes() < 2:
             return _empty_correlation_dict(prefix, k_max)

        # 1. Prepare Node Properties vectors
        nodes = list(G.nodes())
        n_map = {node: i for i, node in enumerate(nodes)}
        
        # Properties: Degree (deg) and Atomic Number (Z)
        degs = np.array([d for _, d in G.degree()])
        Zs = np.array([G.nodes[n].get('Z', 0) for n in nodes])
        
        # Calculate global statistics (mean, var)
        # Note: Using population variance (ddof=0) for consistency with Pearson def
        deg_mean, deg_std = np.mean(degs), np.std(degs)
        Z_mean, Z_std = np.mean(Zs), np.std(Zs)
        
        # Pre-normalize properties: phi' = (phi - mu) / sigma
        # This simplifies loop calc: E[phi'_i * phi'_j] is the correlation
        deg_norm = np.zeros_like(degs, float)
        Z_norm = np.zeros_like(Zs, float)
        
        if deg_std > 1e-9: deg_norm = (degs - deg_mean) / deg_std
        if Z_std > 1e-9:   Z_norm = (Zs - Z_mean) / Z_std

        # 2. Compute Correlations for k=1..k_max
        # We need pairs (i, j) at distance k.
        
        # Initialize accumulators
        correlations_deg = {}
        correlations_Z = {}
        
        # Because doing all-pairs shortest paths is O(N^2), 
        # and BFS from every node is O(N(N+E)), this is acceptable for typical molecular graphs (~100-1000 nodes).
        # We accumulate sums of products.
        
        layer_sums_deg = {k: 0.0 for k in range(1, k_max + 1)}
        layer_sums_Z   = {k: 0.0 for k in range(1, k_max + 1)}
        layer_counts   = {k: 0   for k in range(1, k_max + 1)}
        
        # Iterate over all nodes as sources
        for i_idx, source in enumerate(nodes):
            # BFS to find distances
            lengths = nx.single_source_shortest_path_length(G, source, cutoff=k_max)
            
            for target, dist in lengths.items():
                if dist == 0: continue # self
                
                # We only count each pair once. To enforce loop i < j or similar logic:
                # But iterating all sources visits (i, j) then later (j, i).
                # We can just sum everything and divide by total * 2? Or just sum.
                # Standard Pearson for N pairs: sum(x*y)/N. 
                # Here we visit (i,j) and (j,i), so we will have 2*Count pairs.
                
                j_idx = n_map[target]
                
                layer_sums_deg[dist] += deg_norm[i_idx] * deg_norm[j_idx]
                layer_sums_Z[dist]   += Z_norm[i_idx]   * Z_norm[j_idx]
                layer_counts[dist]   += 1

        # Finalize correlations
        results = {}
        
        # Arrays for fitting (k values and correlation values)
        k_vals = []
        C_deg_vals = []
        C_Z_vals = []

        for k in range(1, k_max + 1):
            count = layer_counts[k]
            if count > 0:
                # Average product
                c_deg = layer_sums_deg[k] / count
                c_Z   = layer_sums_Z[k]   / count
            else:
                c_deg = 0.0
                c_Z   = 0.0
            
            results[f"{prefix}_corr_deg_k{k}"] = float(c_deg)
            results[f"{prefix}_corr_Z_k{k}"]   = float(c_Z)

            k_vals.append(k)
            C_deg_vals.append(c_deg)
            C_Z_vals.append(c_Z)

        # 3. Fit Correlation Length (Exponetial Decay)
        # C(k) = exp(-k / xi)  --> ln(C) = -k * (1/xi)
        # We only fit if we have positive correlations (or take abs? usually C(k) decays positive for ordering)
        
        results[f"{prefix}_k_corr_deg"] = _fit_correlation_length(k_vals, C_deg_vals)
        results[f"{prefix}_k_corr_Z"]   = _fit_correlation_length(k_vals, C_Z_vals)
        
        return results

def _empty_correlation_dict(prefix, k_max):
    d = {}
    for k in range(1, k_max + 1):
        d[f"{prefix}_corr_deg_k{k}"] = 0.0
        d[f"{prefix}_corr_Z_k{k}"] = 0.0
    d[f"{prefix}_k_corr_deg"] = 0.0
    d[f"{prefix}_k_corr_Z"] = 0.0
    return d

def _fit_correlation_length(k_vals, C_vals):
    """
    Fits C(k) ~ exp(-k / xi). Returns xi.
    Strategy: Linear regression on log(C).
    """
    # Filter valid points for log (C > 0.01 to avoid noise/zeros)
    # Scale: If C(k) <= 0, correlation is lost/anticorrelated.
    
    x_fit = []
    y_fit = []
    
    for k, c in zip(k_vals, C_vals):
        if c > 1e-4:
            x_fit.append(k)
            y_fit.append(np.log(c))
        else:
            # If correlation drops to 0 or negative, we stop fitting or assume decay is complete.
            # Stopping is safer for finding characteristic length of the coherent domain.
            break
            
    if len(x_fit) < 2:
        # Decays instantly or only 1 point -> length is small (e.g. < 1)
        # Return something small but non-zero if C[0] was high, or 0 if C[0] was 0.
        if len(C_vals) > 0 and C_vals[0] > 0.1:
            return 0.5 # Sub-neighbor correlation
        return 0.0

    try:
        # Slope m = -1 / xi  =>  xi = -1 / m
        slope, intercept = np.polyfit(x_fit, y_fit, 1)
        if slope >= 0:
            return 10.0 # No decay / increasing correlation? Saturation.
        
        xi = -1.0 / slope
        return float(xi)
    except:
        return 0.0
