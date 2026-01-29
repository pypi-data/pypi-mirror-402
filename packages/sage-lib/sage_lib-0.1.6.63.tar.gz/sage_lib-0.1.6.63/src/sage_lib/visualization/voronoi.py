"""
Voronoi Analysis Module
=======================

Computes Wigner-Seitz cells and Voronoi tessellation for periodic atomic structures.
Uses 3x3x3 supercell replication with SciPy's Qhull wrapper to handle periodic boundaries.

Classes:
    VoronoiResult: Data container for analysis results.

Functions:
    compute_voronoi: Main entry point.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import numpy as np
import scipy.spatial

@dataclass
class VoronoiResult:
    """Container for Voronoi analysis results."""
    volumes: np.ndarray          # Shape (N,), atomic volumes
    neighbors: List[List[int]]   # Adjacency list of topological neighbors
    face_areas: List[List[float]]# Surface area of shared faces
    total_face_area: np.ndarray  # Shape (N,), Sum of face areas
    coordination: np.ndarray     # Shape (N,), topological coordination number (len(neighbors))

def compute_voronoi(positions: np.ndarray, lattice: np.ndarray, radii: Optional[List[float]] = None) -> VoronoiResult:
    """
    Computes Voronoi tessellation for a periodic system.

    Args:
        positions (np.ndarray): (N, 3) Atomic positions (Cartesian).
        lattice (np.ndarray): (3, 3) Lattice vectors (rows).
        radii (list, optional): Atomic radii for radical Voronoi (Power Diagram). 
                                Currently ignored by standard Voronoi.

    Returns:
        VoronoiResult: The analysis data.
    """
    N = len(positions)
    
    # 1. Create 3x3x3 Supercell
    # We replicate the unit cell to ensure atoms on boundaries have correct neighbors.
    # Indices: -1, 0, 1 for each dimension.
    
    shifts = []
    
    # Generate lattice translation vectors
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            for k in [-1, 0, 1]:
                shift_vec = i * lattice[0] + j * lattice[1] + k * lattice[2]
                shifts.append(shift_vec)
                
    shifts = np.array(shifts)  # (27, 3)
    
    # Replicate positions
    # super_pos shape: (27*N, 3)
    # Structure: [Frame0(N) | Frame1(N) | ... ]
    # The "original" cell is the one with shift (0,0,0), which corresponds to index 13 in our loop if sorted,
    # but we just construct it sequentially. 
    
    super_pos_list = []
    # This array maps super_idx -> original_idx (0..N-1)
    super_mapping = []
    
    central_image_offset = -1 # Start index of central image in super_pos
    
    current_offset = 0
    for s_idx, shift in enumerate(shifts):
        is_central = np.allclose(shift, 0)
        if is_central:
            central_image_offset = current_offset
            
        pos_shifted = positions + shift
        super_pos_list.append(pos_shifted)
        super_mapping.extend(range(N))
        current_offset += N
        
    super_pos = np.vstack(super_pos_list)
    
    # 2. Compute Voronoi
    # qhull_options="Qbb Qc Qz" could be useful for numerical stability?
    # Defaults usually work fine for general density.
    voro = scipy.spatial.Voronoi(super_pos)
    
    # 3. Extract Results for Central Atoms
    # The central image atoms are at indices [central_image_offset : central_image_offset + N]
    
    start = central_image_offset
    end = central_image_offset + N
    
    volumes = np.zeros(N)
    neighbors = [[] for _ in range(N)]
    face_areas = [[] for _ in range(N)]
    coordination = np.zeros(N, dtype=np.int32)
    
    for i in range(N):
        super_idx = start + i
        region_idx = voro.point_region[super_idx]
        region = voro.regions[region_idx]
        
        # Check if region is closed (doesn't contain -1)
        if -1 in region or len(region) == 0:
            # Should not happen in a properly surrounded supercell
            volumes[i] = 0.0
            continue
            
        # Compute Volume
        # A region is a list of vertex indices.
        # SciPy doesn't give volume directly for 3D, we must compute it from ConvexHull of vertices.
        verts = voro.vertices[region]
        
        try:
            hull = scipy.spatial.ConvexHull(verts)
            volumes[i] = hull.volume
        except Exception:
            # Fallback for degenerate cells
            volumes[i] = 0.0
            
    # Optimizing Neighbor Search:
    # Iterate through all ridges once, check if they involve our central atoms.
    # voro.ridge_points: (num_ridges, 2)
    # voro.ridge_vertices: list of vertex indices for each ridge (to compute area)
    
    # Map: super_idx -> original_idx
    # But we explicitly only care about neighbors of atoms in the CENTRAL image.
    
    # Pre-lookup for speed
    is_central = np.zeros(len(super_pos), dtype=bool)
    is_central[start:end] = True
    
    # Iterate ridges
    for ridge_idx, (p1, p2) in enumerate(voro.ridge_points):
        # We only care if p1 or p2 is in the central image.
        # Case 1: p1 is central, p2 is neighbor
        # Case 2: p2 is central, p1 is neighbor
        # Note: Voronoi graph is undirected.
        
        if is_central[p1]:
            idx_central = p1 - start
            idx_neighbor = super_mapping[p2]
            
            # Compute Face Area
            # ridge_vertices is a list of vertex indices indices in voro.vertices
            r_verts_idx = voro.ridge_vertices[ridge_idx]
            if -1 in r_verts_idx or not r_verts_idx:
                area = 0.0
            else:
                # Compute area of polygon
                rv = voro.vertices[r_verts_idx]
                if len(rv) < 3:
                     area = 0.0
                else:
                    # Generic 3D polygon area
                    area = 0.0
                    v0 = rv[0]
                    for k in range(1, len(rv)-1):
                        v1 = rv[k]
                        v2 = rv[k+1]
                        area += 0.5 * np.linalg.norm(np.cross(v1-v0, v2-v0))
                        
            neighbors[idx_central].append(idx_neighbor)
            face_areas[idx_central].append(area)
            
        if is_central[p2]:
            idx_central = p2 - start
            idx_neighbor = super_mapping[p1]
            
            # Recompute area for the other side (symmetric)
            r_verts_idx = voro.ridge_vertices[ridge_idx]
            if -1 in r_verts_idx or not r_verts_idx:
                area = 0.0
            else:
                rv = voro.vertices[r_verts_idx]
                if len(rv) < 3: area = 0.0
                else:
                    area = 0.0
                    v0 = rv[0]
                    for k in range(1, len(rv)-1):
                        v1 = rv[k]
                        v2 = rv[k+1]
                        area += 0.5 * np.linalg.norm(np.cross(v1-v0, v2-v0))
            
            neighbors[idx_central].append(idx_neighbor)
            face_areas[idx_central].append(area)

    # Finalize
    total_face_area = np.zeros(N)
    for i in range(N):
        coordination[i] = len(neighbors[i])
        total_face_area[i] = sum(face_areas[i])
        
    return VoronoiResult(
        volumes=volumes,
        neighbors=neighbors,
        face_areas=face_areas,
        total_face_area=total_face_area,
        coordination=coordination
    )
