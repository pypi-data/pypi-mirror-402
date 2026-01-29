import numpy as np
from importlib import resources
from ase import Atoms

# Load the compressed Lennard-Jones cluster dataset included in the package
with resources.as_file(resources.files("aegon").joinpath("data/libdata_lj.npz")) as path:
    _LJ_DATA = np.load(path, allow_pickle=True)

def get_lj_cluster(N, symbol="Mo"):
    """
    Return a preoptimized Lennard-Jones (LJ) cluster as an ASE Atoms object.

    Parameters
    ----------
    N : int
        Number of atoms in the cluster (3 <= N <= 150).
    symbol : str, optional
        Atomic symbol for all atoms in the cluster (default is 'Mo').

    Returns
    -------
    ase.Atoms
        ASE Atoms object representing the requested LJ cluster.

    Raises
    ------
    ValueError
        If the requested cluster size is not available.

    Notes
    -----
    The data were obtained from the Wales database of optimized Lennard-Jones
    clusters (sizes 3–150). Each cluster includes:
        - Optimized Cartesian coordinates
        - Total Lennard-Jones potential energy
        - Cluster label (e.g., 'LJ038')
    """
    key = f"LJ{N:03d}"
    if key not in _LJ_DATA:
        raise ValueError(f"No Lennard-Jones structure available for N = {N}")

    data = _LJ_DATA[key].item()
    atoms = Atoms(symbols=[symbol] * N, positions=data["positions"])
    atoms.info['e'] = data["energy"]
    atoms.info['i'] = data["label"]
    return atoms

def list_available():
    """
    Return a sorted list of available cluster sizes.

    Returns
    -------
    list of int
        Cluster sizes available in the database.
    """
    return sorted(int(k[2:]) for k in _LJ_DATA.keys())
