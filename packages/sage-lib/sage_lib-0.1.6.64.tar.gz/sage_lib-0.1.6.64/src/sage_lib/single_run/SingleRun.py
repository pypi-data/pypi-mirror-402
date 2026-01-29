try:
    from .SingleRunDFT import SingleRunDFT
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing SingleRunDFT: {str(e)}\n")
    del sys

class SingleRun(SingleRunDFT):  # Note: The class name is intentionally generalized and does not include "DFT".
    """
    A general class representing a single run simulation.

    Although this class inherits from SingleRunDFT, it is intended to serve as a more general 
    simulation container not restricted to Density Functional Theory (DFT). It manages various 
    simulation components such as atomic positions, input/output file handling, k-points, potentials,
    and additional handlers.

    Attributes
    ----------
    _loaded : dict
        Dictionary to track loaded modules or data.
    _AtomPositionManager : object
        Manager instance responsible for handling atomic positions.
    _Out_AtomPositionManager : object or None
        Manager for output atomic positions (if applicable).
    _InputFileManager : object or None
        Manager for input file operations.
    _KPointsManager : object or None
        Manager for handling k-point information in reciprocal space.
    _PotentialManager : object or None
        Manager for potential data used in the simulation.
    _BashScriptManager : object or None
        Manager for generating or executing bash scripts.
    _vdw_kernel_Handler : object or None
        Handler for van der Waals kernel processing.
    _OutFileManager : object or None
        Manager for output file operations.
    _WaveFileManager : object or None
        Manager for wavefunction file handling.
    _ChargeFileManager : object or None
        Manager for charge density file operations.
    """

    _ALIAS_REGISTRY = {
        "atoms": {
            "attr": "_AtomPositionManager",
            # "constructor" removed; delegated to AtomPositionManager property
        },
        "atom": {
             "attr": "_AtomPositionManager",
        },
        "out_atoms": {
            "attr": "_Out_AtomPositionManager",
            "constructor": "AtomPositionManager_constructor",
            "kwargs": lambda self: {"file_location": self.file_location},
        },
        "kpoints": {
            "attr": "_KPointsManager",
            "constructor": "KPointsManager_constructor",
            "kwargs": lambda self: {},
        },
        "potentials": {
            "attr": "_PotentialManager",
            "constructor": "PotentialManager_constructor",
            "kwargs": lambda self: {},
        },
        "vdw": {
            "attr": "_vdw_kernel_Handler",
            "constructor": "vdw_kernel_constructor",
            "kwargs": lambda self: {},
        },
        "inputs": {
            "attr": "_InputFileManager",
            # Add constructor here if/when available, or leave purely for alias mapping
        },
        "outputs": {
            "attr": "_OutFileManager",
        },
        "waves": {
            "attr": "_WaveFileManager",
        },
        "charges": {
            "attr": "_ChargeFileManager",
        },
        "scripts": {
            "attr": "_BashScriptManager",
        },
    }

    def __init__(self, file_location: str = None, name: str = None, **kwargs):
        """
        Initialize a SingleRun simulation instance.

        This constructor calls the parent initializer and sets up various internal managers 
        that are required to manage simulation inputs and outputs.

        Parameters
        ----------
        file_location : str, optional
            The file path used to locate initial configuration data.
        name : str, optional
            A unique identifier for the simulation instance.
        **kwargs
            Additional keyword arguments passed to the base class.
        """
        super().__init__(name=name, file_location=file_location)

        # Dictionary to store loaded modules or data for later use.
        self._loaded = {}
        self.file_location = file_location

        # Initialize the AtomPositionManager to None to support lazy loading
        self._AtomPositionManager = None
        
        # Initialize additional managers to None; these can be instantiated later as needed.
        self._Out_AtomPositionManager = None
        self._InputFileManager = None
        self._KPointsManager = None
        self._PotentialManager = None
        self._BashScriptManager = None
        self._vdw_kernel_Handler = None
        self._OutFileManager = None
        self._WaveFileManager = None
        self._ChargeFileManager = None

    def __getattr__(self, name):
        registry = getattr(self, "_ALIAS_REGISTRY", {})

        if name not in registry:
            return super().__getattr__(name)

        entry = registry[name]
        attr = entry["attr"]

        value = getattr(self, attr, None)

        if value is None and name == "atoms":
            return self.AtomPositionManager

        # Lazy instantiation
        if value is None and "constructor" in entry:
            ctor_name = entry["constructor"]
            ctor = getattr(self, ctor_name)
            kwargs = entry.get("kwargs", lambda self: {})(self)
            value = ctor(**kwargs)
            setattr(self, attr, value)

        return value

    def __setattr__(self, name, value):
        registry = self.__dict__.get("_ALIAS_REGISTRY") or getattr(self, "_ALIAS_REGISTRY", None)

        if registry and name in registry:
            super().__setattr__(registry[name]["attr"], value)
        else:
            super().__setattr__(name, value)

    @property
    def AtomPositionManager(self):
        """
        Safe lazy property for AtomPositionManager.
        Guarantees it is never None when accessed via this property.
        """
        if self._AtomPositionManager is None:
            self._AtomPositionManager = self.AtomPositionManager_constructor(self.file_location)
        return self._AtomPositionManager

    @AtomPositionManager.setter
    def AtomPositionManager(self, value):
        self._AtomPositionManager = value

    @property
    def aliases(self):
        """
        Return a dictionary of current aliases and their status.
        """
        return {
            alias: {
                "internal": entry["attr"],
                "initialized": getattr(self, entry["attr"], None) is not None,
                "lazy": "constructor" in entry,
            }
            for alias, entry in self._ALIAS_REGISTRY.items()
        }

    def read_structure(self, file_location, source, *args, **kwargs):
        """
        Read the structure from a file and update the AtomPositionManager.

        This method initializes the AtomPositionManager using the provided file location and 
        then reads the structural data using the specified source format. If any errors occur 
        during this process, they are caught and a message is printed.

        Parameters
        ----------
        file_location : str
            The path to the file containing the structure information.
        source : str
            A string identifier for the structure format or the reading method.
        *args
            Additional positional arguments.
        **kwargs
            Additional keyword arguments.
        """
        try:
            # Reinitialize the AtomPositionManager for the given file location.
            self.atoms = self.AtomPositionManager_constructor(file_location)
            # Read the structure using the specified source.
            self.atoms.read(source=source, file_location=file_location)
        except Exception as e:
            print(f"Failed to read {file_location} as {source}: {e}")

    def export_structure(self, file_location, source, *args, **kwargs):
        """
        Export the current structure to a file.

        This method reinitializes the AtomPositionManager for the given file location and then 
        exports the structure data in the specified format. Any encountered exceptions are caught 
        and reported via a printed message.

        Parameters
        ----------
        file_location : str
            The path to the file where the structure will be exported.
        source : str
            A string identifier for the structure format or the export method.
        *args
            Additional positional arguments.
        **kwargs
            Additional keyword arguments.
        """
        try:
            # Reinitialize the AtomPositionManager for the given file location.
            self.atoms = self.AtomPositionManager_constructor(file_location)
            # Export the structure using the specified source.
            self.atoms.export(source=source, file_location=file_location)
        except Exception as e:
            print(f"Failed to export {file_location} as {source}: {e}")

