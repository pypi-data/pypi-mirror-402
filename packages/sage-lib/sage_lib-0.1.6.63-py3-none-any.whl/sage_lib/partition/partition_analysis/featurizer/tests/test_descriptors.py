
import pytest
import numpy as np
import networkx as nx
from sage_lib.partition.partition_analysis.featurizer.core.descriptors.topology import TopologyDescriptors
from sage_lib.partition.partition_analysis.featurizer.core.descriptors.chemistry import ChemistryDescriptors
from sage_lib.partition.partition_analysis.featurizer.core.descriptors.order import OrderDescriptors
from sage_lib.partition.partition_analysis.featurizer.core.descriptors.correlation import CorrelationDescriptors
from sage_lib.partition.partition_analysis.featurizer.core.descriptors.percolation import PercolationDescriptors
from sage_lib.partition.partition_analysis.featurizer.core.descriptors.spectral import SpectralDescriptors

@pytest.fixture
def sample_graph():
    """Created a simple graph with element attributes."""
    G = nx.Graph()
    # Triangle: 0(Ni)-1(O)-2(Ni)-0(Ni)
    G.add_node(0, element="Ni", Z=28)
    G.add_node(1, element="O", Z=8)
    G.add_node(2, element="Ni", Z=28)
    
    G.add_edge(0, 1, weight=2.0) # Ni-O
    G.add_edge(1, 2, weight=1.8) # O-Ni
    G.add_edge(0, 2, weight=2.5) # Ni-Ni
    return G

@pytest.fixture
def empty_graph():
    return nx.Graph()

# --- Topology Tests ---
def test_topology_degree(sample_graph):
    stats = TopologyDescriptors.degree_stats(sample_graph, "test")
    assert "test_deg_mean" in stats
    assert stats["test_deg_mean"] == 2.0  # All have degree 2

def test_topology_degree_by_species(sample_graph):
    stats = TopologyDescriptors.degree_stats_by_species(sample_graph, "test")
    # Ni nodes: 0, 2 -> both degree 2
    # O node: 1 -> degree 2
    assert "test_deg_mean_Ni" in stats
    assert stats["test_deg_mean_Ni"] == 2.0
    assert "test_deg_mean_O" in stats
    assert stats["test_deg_mean_O"] == 2.0

def test_topology_cycles(sample_graph):
    stats = TopologyDescriptors.cycle_stats(sample_graph, "test")
    assert stats["test_n_cycles"] == 1

# --- Chemistry Tests ---
def test_chemistry_edge_fractions(sample_graph):
    stats = ChemistryDescriptors.edge_fractions(sample_graph, "test")
    # Edges: Ni-O, Ni-O, Ni-Ni -> Total 3
    # Ni-O: 2/3
    # Ni-Ni: 1/3
    assert abs(stats["test_frac_Ni-O"] - 2/3) < 1e-5
    assert abs(stats["test_frac_Ni-Ni"] - 1/3) < 1e-5

def test_chemistry_distances_by_pair(sample_graph):
    stats = ChemistryDescriptors.edge_distance_stats_by_pair(sample_graph, "test")
    # Ni-O lengths: 2.0 and 1.8 -> mean 1.9, std 0.1
    # Ni-Ni lengths: 2.5 -> mean 2.5, std 0.0
    assert abs(stats["test_d_mean_Ni-O"] - 1.9) < 1e-5
    assert abs(stats["test_d_std_Ni-O"] - 0.1) < 1e-5
    assert abs(stats["test_d_mean_Ni-Ni"] - 2.5) < 1e-5

# --- Order Tests ---
def test_order_assortativity(sample_graph):
    stats = OrderDescriptors.assortativity(sample_graph, "test")
    # Degree assortativity for a regular graph (all deg=2) is usually restricted or nan
    # Attribute assortativity:
    # 0(Ni) -- 1(O) (diff)
    # 1(O) -- 2(Ni) (diff)
    # 0(Ni) -- 2(Ni) (same)
    # It handles it without crashing
    assert "test_assort_chem" in stats

def test_order_entropy(sample_graph):
    stats = OrderDescriptors.graph_entropy(sample_graph, "test")
    # All degrees are 2. Distribution: p(k=2) = 1.0. Entropy = 0.
    assert "test_deg_entropy" in stats
    assert abs(stats["test_deg_entropy"] - 0.0) < 1e-5

def test_order_entropy_varied():
    G = nx.Graph()
    # 4 nodes. 0-1, 1-2, 2-3
    # Degs: 0(1), 1(2), 2(2), 3(1) -> [1, 2, 2, 1]
    # Counts: {1: 2, 2: 2} -> P(1)=0.5, P(2)=0.5
    # Entropy = - (0.5 ln 0.5 + 0.5 ln 0.5) = ln 2 approx 0.693
    G.add_edges_from([(0,1), (1,2), (2,3)])
    
    stats = OrderDescriptors.graph_entropy(G, "test")
    assert abs(stats["test_deg_entropy"] - np.log(2)) < 1e-5

# --- Empty Graph Robustness ---
def test_empty_graph(empty_graph):
    t_stats = TopologyDescriptors.degree_stats_by_species(empty_graph, "t")
    assert t_stats == {}
    
    c_stats = ChemistryDescriptors.edge_distance_stats_by_pair(empty_graph, "c")
    assert c_stats == {}
    
    o_stats = OrderDescriptors.assortativity(empty_graph, "o")
    assert o_stats["o_assort_chem"] == 0.0
    assert o_stats["o_assort_deg"] == 0.0

# --- Correlation Tests ---
def test_correlation_autocorrelation(sample_graph):
    # Node 0(Ni) -- 1(O) -- 2(Ni) -- 0
    # Degs: all 2. Zs: Ni(28), O(8).
    # k=1: (0,1), (1,2), (0,2). Pairs: (Ni,O), (O,Ni), (Ni,Ni).
    # Z-correlation should be < 1 because mixed neighbours.
    stats = CorrelationDescriptors.spatial_autocorrelation(sample_graph, "test", k_max=2)
    assert "test_corr_Z_k1" in stats
    assert "test_k_corr_Z" in stats

def test_correlation_decay():
    # Linear chain: 0-1-2-3-4
    # Property values 10, 8, 6, 4, 2
    G = nx.path_graph(5)
    for n in G.nodes:
        G.nodes[n]['Z'] = 10 - 2*n
    
    stats = CorrelationDescriptors.spatial_autocorrelation(G, "test", k_max=3)
    # Autocorrelation should be high positive for k=1 (10-8, 8-6...)
    # And persist.
    assert stats["test_corr_Z_k1"] > 0.0

# --- Percolation Tests ---
def test_percolation_clusters(sample_graph):
    # Ni: {0, 2} connected directly? Yes (0-2 edge).
    # O: {1}.
    # Ni cluster size = 2. Total N=3. Frac = 0.666
    # O cluster size = 1. Frac = 0.333
    stats = PercolationDescriptors.cluster_sizes(sample_graph, "test")
    assert abs(stats["test_largest_Ni_cluster_frac"] - 2/3) < 1e-5
    assert abs(stats["test_largest_O_cluster_frac"] - 1/3) < 1e-5

def test_percolation_core_boundary():
    # 4-clique (all deg 3) -> 3-core.
    G = nx.complete_graph(4)
    stats = PercolationDescriptors.core_boundary_fraction(G, "test", k_core=2)
    # All nodes in 2-core (since deg=3 >= 2)
    assert stats["test_core_frac"] == 1.0
    assert stats["test_boundary_frac"] == 0.0

# --- Spectral Local Tests ---
def test_spectral_local_entropy(sample_graph):
    # Ego graph of radius 2 covers whole graph for triangle.
    stats = SpectralDescriptors.local_spectral_entropy(sample_graph, "test", radius=2)
    assert "test_local_spect_entropy_mean" in stats
    assert stats["test_local_spect_entropy_std"] >= 0.0

