# Lyra Geometry

Lyra Geometry is a Python library for symbolic differential geometry with a
focus on tensor spaces, connections, and curvature in Lyra geometry. It is
built on SymPy to support exact tensor manipulation in scripts and notebooks.

## Highlights

- Tensor spaces with index notation (up/down indices).
- Lyra connection and curvature tensors derived from a metric.
- Automatic Einstein summation for repeated labels.
- Covariant derivatives, torsion, and non-metricity support.
- Friendly API designed for interactive exploration.

## Requirements

- Python >= 3.9
- SymPy >= 1.12

## Installation

```bash
python -m pip install lyra-geometry
```

For local development:

```bash
python -m pip install -e .[dev]
```

## Getting started

Create a space with a metric, then inspect its basic objects:

```python
import sympy as sp
import lyra_geometry as pl

x, y = sp.symbols("x y", real=True)
metric = sp.diag(x + 2*y, x**2 * y)

st = pl.SpaceTime(coords=(x, y), metric=metric)

st.g          # metric tensor
st.metric_inv # inverse metric matrix
st.detg       # determinant of the metric
```

## Indices, raising/lowering, and components

Use index labels and variance markers to access components:

```python
a, b, c = st.index("a b c")

st.g[-a, -b]  # g_ab
st.g[+a, +b]  # g^ab

st.g[-a, -b](0, 0)  # component access
```

## Generic tensors and contraction

Create symbolic tensors and let repeated labels contract automatically:

```python
v = st.tensor.generic("v", (pl.U,))
w = st.tensor.generic("w", (pl.D,))

scalar = v[+a] * w[-a]  # automatic contraction
```

Explicit contraction and a simple index-string parser are also available:

```python
st.contract(v[+a], w[-a])
st.eval_contract("v^a w_a")
```

## Covariant derivative

The Lyra covariant derivative adds one covariant index:

```python
dv = st.nabla(v)
dv.signature  # (D, U)
dv[-b, +a](0, 0)
```

## Connection and curvature

When a metric is provided, the Lyra connection and curvature tensors are
computed automatically:

```python
st.gamma            # Gamma^a_{bc}
st.riemann          # Riemann tensor
st.ricci            # Ricci tensor
st.einstein         # Einstein tensor
st.scalar_curvature # scalar curvature
```

## Scale, torsion, and non-metricity

You can set a scale field and provide torsion/non-metricity explicitly:

```python
phi = sp.Function("phi")(x)
st.set_scale(phi)

st.set_torsion(st.zeros((pl.D, pl.D, pl.D)))
st.set_nonmetricity(st.zeros((pl.U, pl.D, pl.D)))

st.update()
```

## Custom connection strategies

If you already have Gamma components, you can fix the connection manually:

```python
Gamma0 = sp.ImmutableDenseNDimArray([0] * (2**3), (2, 2, 2))

st2 = pl.SpaceTime(
    coords=(x, y),
    metric=sp.diag(1, 1),
    connection_strategy=pl.FixedConnectionStrategy(Gamma0),
)

st2.gamma
```

## Simplification with fmt

Use `fmt()` to expand and simplify expressions:

```python
st.ricci.fmt()
st.einstein.fmt()
st.scalar_curvature.fmt()
```

## Notebook examples

The notebook `examples/example.ipynb` walks through:

- A quick tutorial of the core API.
- Schwarzschild spacetime: metric, connection, and curvature tensors.
- FLRW spacetime: metric, curvature, and covariant derivative of a scalar.
- A spherically symmetric LyST solution with scale field and field equations.

## Project structure

- `src/lyra_geometry/core.py`: core implementation.
- `src/lyra_geometry/__init__.py`: public exports and version.
- `examples/example.ipynb`: tutorial and physics examples.
- `tests/`: pytest smoke tests.

## Development and testing

```bash
python -m pytest
```

## License

MIT. See `LICENSE`.
