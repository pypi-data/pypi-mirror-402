"""Lyra Geometry: symbolic differential geometry tools built on SymPy."""

from .core import (
    Connection,
    ConnectionStrategy,
    ConnectionTensor,
    CurvatureStrategy,
    FixedConnectionStrategy,
    LyraConnectionStrategy,
    LyraCurvatureStrategy,
    Manifold,
    SpaceTime,
    TensorSpace,
)
from .diff_ops import divergence, gradient, laplacian
from .invariants import euler_density, kretschmann_scalar, ricci_scalar
from .tensors import (
    D,
    Down,
    DownIndex,
    Index,
    IndexedTensor,
    Metric,
    NO_LABEL,
    Tensor,
    TensorFactory,
    U,
    Up,
    UpIndex,
    d,
    u,
)
from .utils import example_indexing, greek

__all__ = [
    "Connection",
    "ConnectionStrategy",
    "ConnectionTensor",
    "CurvatureStrategy",
    "D",
    "Down",
    "DownIndex",
    "FixedConnectionStrategy",
    "Index",
    "IndexedTensor",
    "LyraConnectionStrategy",
    "LyraCurvatureStrategy",
    "Manifold",
    "Metric",
    "NO_LABEL",
    "SpaceTime",
    "Tensor",
    "TensorFactory",
    "TensorSpace",
    "U",
    "Up",
    "UpIndex",
    "d",
    "divergence",
    "euler_density",
    "example_indexing",
    "gradient",
    "greek",
    "kretschmann_scalar",
    "laplacian",
    "ricci_scalar",
    "u",
]

__version__ = "0.1.15"
