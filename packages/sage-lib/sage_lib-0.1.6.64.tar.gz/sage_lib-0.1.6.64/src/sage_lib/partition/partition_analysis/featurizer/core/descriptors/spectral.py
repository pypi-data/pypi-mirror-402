# =============================
# descriptors_spectral.py
# =============================

import numpy as np
import networkx as nx

class SpectralDescriptors:
    @staticmethod
    def spectral_invariants(G, prefix, k=20):
        n = G.number_of_nodes()
        if n == 0:
            return {f"{prefix}_lambda2": 0, f"{prefix}_spectral_entropy": 0}
        L = nx.laplacian_matrix(G).astype(float).todense()
        evals = np.linalg.eigvalsh(L)
        evals = np.sort(np.maximum(evals, 1e-12))
        if len(evals) > k:
            evals = evals[:k]
        lam2 = evals[1] if len(evals) > 1 else 0
        p = evals / np.sum(evals)
        sent = -np.sum(p * np.log(p))
        return {f"{prefix}_lambda2": float(lam2), f"{prefix}_spectral_entropy": float(sent)}

    @staticmethod
    def local_spectral_entropy(G, prefix, radius=2):
        """
        Calculates stats (mean, std) of spectral entropy for local ego-graphs.
        """
        nodes = list(G.nodes())
        n = len(nodes)
        if n == 0:
            return {}

        entropies = []
        for node in nodes:
            # Extract local ego_graph (radius=radius)
            # Undirected
            sub = nx.ego_graph(G, node, radius=radius)
            if sub.number_of_nodes() < 2:
                entropies.append(0.0)
                continue
            
            # Simple Von Neumann entropy approx on laplacian eigenvalues
            L = nx.laplacian_matrix(sub).astype(float).todense()
            try:
                evals = np.linalg.eigvalsh(L)
                evals = np.sort(np.maximum(evals, 1e-12))
                
                # Normalize density matrix proxy from laplacian?
                # Usually Von Neumann entropy is -Trace(rho log rho). 
                # For graph structural entropy, we use p_i = lambda_i / sum(lambda).
                total_ev = np.sum(evals)
                if total_ev > 1e-9:
                    p = evals / total_ev
                    ent = -np.sum(p * np.log(p))
                    entropies.append(ent)
                else:
                    entropies.append(0.0)
            except:
                entropies.append(0.0)
                
        entropies = np.array(entropies)
        return {
            f"{prefix}_local_spect_entropy_mean": float(np.mean(entropies)),
            f"{prefix}_local_spect_entropy_std": float(np.std(entropies))
        }

