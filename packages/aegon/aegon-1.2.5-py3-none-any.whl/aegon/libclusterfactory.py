import numpy as np
from importlib import resources
from ase import Atoms

# ============================================================
# Internal utilities
# ============================================================

def _load_npz(filename):
    """
    Load an .npz file from aegon/data/.
    """
    try:
        with resources.as_file(resources.files("aegon").joinpath(f"data/{filename}")) as path:
            return np.load(path, allow_pickle=True)
    except FileNotFoundError:
        raise ValueError(f"Data file not found: data/{filename}")


def _atoms_from_entry(data, N, symbol):
    """
    Build an ASE Atoms object from a database entry.
    """
    atoms = Atoms(symbols=[symbol] * N, positions=data["positions"])
    atoms.info["energy"] = data["energy"]
    atoms.info["label"] = data["label"]
    return atoms

# ============================================================
# ClusterFactory Core
# ============================================================

class ClusterFactory:

    # Cached databases to avoid reloading from disk
    _LJ_DATA = None
    _SC_DATA = {}   # key: symbol → db

    # Supported models (LJ and SC for now)
    _SUPPORTED_MODELS = {"LJ", "SC"}

    # ---------------------- Public API ----------------------

    @classmethod
    def get(cls, N, model, element=None):
        """
        Unified entry point for obtaining a cluster.

        Parameters
        ----------
        N : int
            Number of atoms.
        model : str
            "LJ" or "SC"
        element : str, optional
            Atomic symbol (required for SC).
        """
        model = model.upper()

        if model not in cls._SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model '{model}'. Supported models: {cls._SUPPORTED_MODELS}")

        if model == "LJ":
            return cls._get_lj(N, element or "Mo")  # default LJ element is Mo

        elif model == "SC":
            if element is None:
                raise ValueError("Element must be specified for SC clusters.")
            return cls._get_sc(N, element)

    @classmethod
    def list_available(cls, model, element=None):
        """
        List available cluster sizes for a given model.

        Parameters
        ----------
        model : str
            "LJ" or "SC"
        element : str, optional
            Required for SC.
        """
        model = model.upper()

        if model not in cls._SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model '{model}'.")

        if model == "LJ":
            return cls._list_available_lj()

        elif model == "SC":
            if element is None:
                raise ValueError("Element must be specified for SC clusters.")
            return cls._list_available_sc(element)

    # ---------------------- LJ subsystem ----------------------

    @classmethod
    def _load_lj_database(cls):
        """
        Load the LJ database once.
        """
        if cls._LJ_DATA is None:
            cls._LJ_DATA = _load_npz("libdata_lj.npz")
        return cls._LJ_DATA

    @classmethod
    def _get_lj(cls, N, symbol):
        db = cls._load_lj_database()
        key = f"LJ{N:03d}"

        if key not in db:
            raise ValueError(f"No LJ cluster available for N = {N}")

        data = db[key].item()
        return _atoms_from_entry(data, N, symbol)

    @classmethod
    def _list_available_lj(cls):
        db = cls._load_lj_database()
        return sorted(int(k[2:]) for k in db.keys())

    # ---------------------- SC subsystem ----------------------

    @classmethod
    def _load_sc_database(cls, element):
        element = element.capitalize()

        if element not in cls._SC_DATA:
            filename = f"SC_{element}_clusters_data.npz"
            cls._SC_DATA[element] = _load_npz(filename)

        return cls._SC_DATA[element]

    @classmethod
    def _get_sc(cls, N, element):
        element = element.capitalize()
        db = cls._load_sc_database(element)

        key = f"SC{N:03d}"
        if key not in db:
            raise ValueError(f"No SC cluster available for element {element} with N = {N}")

        data = db[key].item()
        return _atoms_from_entry(data, N, element)

    @classmethod
    def _list_available_sc(cls, element):
        element = element.capitalize()
        db = cls._load_sc_database(element)
        return sorted(int(k[2:]) for k in db.keys())
