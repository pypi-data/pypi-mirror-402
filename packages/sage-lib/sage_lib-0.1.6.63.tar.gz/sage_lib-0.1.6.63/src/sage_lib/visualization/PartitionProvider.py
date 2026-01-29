# ------------------------------------------------------------
# sage_lib/visualization/PartitionProvider.py
# ------------------------------------------------------------
"""
Adapter class that wraps a `sage_lib.partition.Partition` object
to provide a uniform interface for visualization tools.

This class translates the data structures and naming conventions
used in `Partition` into a standardized protocol that
`browse_structures()` or any 3D viewer can consume directly.
"""

import numpy as np


class PartitionProvider:
    """
    Wraps your `sage_lib.partition.Partition` object to match the
    `StructureProvider` protocol expected by visualization utilities.
    """

    def __init__(self, partition):
        """
        Parameters
        ----------
        partition : sage_lib.partition.Partition
            The Partition object containing atomic configurations.
        """
        self.p = partition

    # ------------------------------------------------------------
    # Basic container interface
    # ------------------------------------------------------------
    def __len__(self) -> int:
        """Return the number of structure containers."""
        return self.p.size

    def __getitem__(self, idx: int):
        """Enable indexing: provider[i] → structure i."""
        return self.get(idx)

    # ------------------------------------------------------------
    # Data accessors
    # ------------------------------------------------------------
    def get_all_E(self):
        """Return an array of total energies for all structures."""
        return np.array(self.p.get_all_energies())

    def get_all_compositions(self, return_species=False):
        """Return an array of compositions for all structures."""
        return self.p.get_all_compositions(return_species=return_species)

    def get_all_Ef(self):
        """
        Compute formation energies by linear regression:
        E ≈ C·μ  →  Ef = E - C·μ
        """
        res = self.get_all_compositions(return_species=True)
        if isinstance(res, tuple):
             C, _ = res
        else:
             C = res
        
        E = np.zeros( C.shape[0] )
        Eall = self.get_all_E()
        E[:Eall.shape[0]] = Eall
        if len(C) == 0 or len(E) == 0:
            return np.array([])
        mu, *_ = np.linalg.lstsq(C, E, rcond=None)  # fit chemical potentials
        E_fit = C @ mu
        Ef = E - E_fit
        return Ef

    def get_all_metadata(self, key):
        """
        Delegate metadata retrieval to the partition, with fallback/priority 
        for per-structure AtomPositionManager.metadata.
        """
        # Try fetching from partition first (fast path if implemented efficiently there)
        try:
             # Some providers might not have this or it returns None
             # Some providers might not have this or it returns None
             if key != 'composition':
                 val = self.p.get_all_metadata(key)
                 if val is not None and len(val) == self.p.size:
                     return val
        except Exception:
            pass

        if key in ['E', 'energy', 'F', 'Ef']:
            # Check for specific methods on the partition
            if hasattr(self.p, 'get_all_Ef'):
                try:
                    vals = self.p.get_all_Ef()
                    if vals is not None and len(vals) == self.p.size:
                        return vals
                except Exception:
                    pass
            
            if hasattr(self.p, 'get_all_energies'):
                try:
                    vals = self.p.get_all_energies()
                    if vals is not None and len(vals) == self.p.size:
                        return vals
                except Exception:
                    pass

        if key == 'natoms':
            # Retrieve number of atoms for each container
            natoms = []
            for i in range(self.p.size):
                c = self.p.containers[i]
                if hasattr(c, 'get_number_of_atoms'):
                    natoms.append(c.get_number_of_atoms())
                elif hasattr(c, 'atoms') and hasattr(c.atoms, 'get_number_of_atoms'):
                    natoms.append(c.atoms.get_number_of_atoms())
                else:
                    natoms.append(0)
            return natoms

        if key == 'composition':
            # Retrieve composition (element counts) for each container -> List of Dicts
            comps = []
            for i in range(self.p.size):
                c = self.p.containers[i]
                comp = {}
                atoms = None
                if hasattr(c, 'atoms'):
                    atoms = c.atoms
                
                if atoms is not None:
                     # Try to get symbols
                    symbols = []
                    if hasattr(atoms, 'get_chemical_symbols'):
                        symbols = atoms.get_chemical_symbols()
                    elif hasattr(atoms, 'get_atomic_numbers'):
                        # Fallback if manual mapping needed, but symbols preferred
                        # For now assume symbols works or provided list
                        pass
                    
                    if len(symbols) > 0:
                        from collections import Counter
                        comp = dict(Counter(symbols))
                
                comps.append(comp)
            return comps

        # Fallback: Manually iterate containers
        # This covers: 'generation', 'F', 'T', 'operation', 'parents', etc.
        values = []
        for i in range(self.p.size):
            c = self.p.containers[i]
            val = None
            if hasattr(c, 'AtomPositionManager'):
                apm = c.AtomPositionManager
                # Check metadata dict
                if hasattr(apm, 'metadata') and isinstance(apm.metadata, dict):
                    val = apm.metadata.get(key)
                    # Debug: Print keys for first structure to help diagnose missing data
                    if i == 0 and val is None:
                        print(f"[DEBUG] Structure 0 metadata keys: {list(apm.metadata.keys())}")
                
                # Fallback to info_system (old location for some keys?)
                if val is None and hasattr(apm, 'info_system') and isinstance(apm.info_system, dict):
                    val = apm.info_system.get(key)
            
            values.append(val)
        return values

    # ------------------------------------------------------------
    # Structure-level accessor
    # ------------------------------------------------------------
    def get(self, idx: int):
        """
        Get a single structure from the partition.

        Returns
        -------
        positions : np.ndarray, shape (N, 3)
            Atomic Cartesian coordinates [Å].
        lattice : np.ndarray, shape (3, 3)
            Lattice vectors as rows [Å].
        energy : float
            Total energy (eV).
        elements : list[str]
            Element symbols corresponding to each atom.
        colors : list[str] or None
            Optional per-atom color information (can be None).
        radii : list[float] or None
            Optional atomic radii (can be None).
        """
        c = self.p.containers[idx]
        APM = c.AtomPositionManager

        lattice = np.array(APM.latticeVectors)
        positions = np.array(APM.atomPositions)
        elements = list(APM.atomLabelsList)
        energy = getattr(APM, "E", 0.0) or 0.0

        # Optional placeholders for visual styling
        colors = None
        radii = None

        return positions, lattice, float(energy), elements, colors, radii



        c = self.p[idx]
        if hasattr(c, 'AtomPositionManager'):
            c.AtomPositionManager.wrap()




