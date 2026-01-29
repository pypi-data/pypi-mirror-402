import numpy as np
from importlib import resources
from ase import Atoms

# Cache de bases ya cargadas
_SC_DATABASES = {}

def _load_sc_database(symbol):
    """
    Load and cache SC cluster database for a given element symbol.
    Example symbols: 'Au', 'Ag'
    """
    symbol = symbol.capitalize()

    if symbol in _SC_DATABASES:
        return _SC_DATABASES[symbol]

    # Construye el nombre del archivo
    filename = f"data/SC_{symbol}_clusters_data.npz"

    # Carga el archivo usando importlib.resources
    try:
        with resources.as_file(resources.files("aegon").joinpath(filename)) as path:
            db = np.load(path, allow_pickle=True)
    except FileNotFoundError as e:
        raise ValueError(
            f"No existe base Sutton–Chen para el símbolo '{symbol}'. "
            f"Se esperaba el archivo: {filename}"
        ) from e

    # Guarda en caché
    _SC_DATABASES[symbol] = db
    return db

def get_sc_cluster(N, symbol='Au'):
    """
    Return a preoptimized Sutton-Chen (SC) cluster as an ASE Atoms object.

    Parameters
    ----------
    N : int
        Number of atoms in the cluster (3 <= N <= 80).
    symbol : str
        Element symbol ('Au', 'Ag', ...)

    Returns
    -------
    ase.Atoms
    """
    symbol = symbol.capitalize()
    db = _load_sc_database(symbol)

    key = f"SC{N:03d}"
    if key not in db:
        raise ValueError(f"No Sutton-Chen structure for {symbol} with N = {N}")

    data = db[key].item()
    atoms = Atoms(symbols=[symbol] * N, positions=data["positions"])
    atoms.info["e"] = data["energy"]
    atoms.info["i"] = data["label"]
    return atoms


def list_available(symbol='Au'):
    """
    Return a sorted list of available cluster sizes for a given element.

    Parameters
    ----------
    symbol : str
        Element symbol ('Au', 'Ag', ...)

    Returns
    -------
    list of int
    """
    symbol = symbol.capitalize()
    db = _load_sc_database(symbol)
    return sorted(int(k[2:]) for k in db.keys())

#from aegon.libutils import writexyzs
#au25 = get_sc_cluster(25, symbol='Au')
#ag25 = get_sc_cluster(25, symbol='Ag')
#writexyzs(au25, "sc25_Au.xyz")
#writexyzs(ag25, "sc25_Ag.xyz")

