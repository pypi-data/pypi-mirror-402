import itertools
import sympy as sp

from .tensors import (
    CoordIndex,
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
    _expand_indices,
    _parse_tensor_token,
    _validate_signature,
    d,
    table,
    u,
)


class ConnectionStrategy:
    def build(self, space):
        raise NotImplementedError


class CurvatureStrategy:
    def build(self, space, gamma_components):
        raise NotImplementedError


class LyraConnectionStrategy(ConnectionStrategy):
    def build(self, space):
        if space.metric is None:
            return None

        dim = space.dim
        coords = space.coords
        g = space.metric.components
        g_inv = space.metric_inv
        phi = space.scale.expr if isinstance(space.scale, Tensor) else space.scale
        M = space.nonmetricity
        tau = space.torsion
        chris = space.christoffel2

        def connection_element(b, n, l):
            return (
                1 / phi * chris[b, n, l]
                - sp.Rational(1, 2) * M(U, D, D)[b, n, l]
                + 1 / (phi) * (
                    sp.KroneckerDelta(b, l) * 1 / phi * sp.diff(phi, coords[n])
                    - sum(1 / phi * g[n, l] * g_inv[b, s] * sp.diff(phi, coords[s]) for s in range(dim))
                )
                + sp.Rational(1, 2) * sum(
                    g_inv[m, b] * (
                        tau(D, D, D)[l, m, n] - tau(D, D, D)[n, l, m] - tau(D, D, D)[m, l, n]
                    )
                    for m in range(dim)
                )
            )

        return table(connection_element, dim=dim, rank=3)


class LyraCurvatureStrategy(CurvatureStrategy):
    def build(self, space, gamma_components):
        if gamma_components is None or space.metric is None:
            return None, None, None, None

        dim = space.dim
        coords = space.coords
        Gamma = gamma_components
        phi = space.phi.expr if isinstance(space.phi, Tensor) else space.phi

        def curvature_element(l, a, m, n):
            return (
                1 / (phi**2) * sp.diff(phi * Gamma[l, a, n], coords[m])
                - 1 / (phi**2) * sp.diff(phi * Gamma[l, a, m], coords[n])
                + sum(Gamma[r, a, n] * Gamma[l, r, m] for r in range(dim))
                - sum(Gamma[r, a, m] * Gamma[l, r, n] for r in range(dim))
            )

        Riem = space.from_function(curvature_element, signature=(U, D, D, D), name="Riemann", label="R")

        def ricci_element(a, m):
            return sp.simplify(sum(Riem(U, D, D, D).comp[l, a, m, l] for l in range(dim)))

        Ricc = space.from_function(ricci_element, signature=(D, D), name="Ricci", label="Ric")

        g_inv = space.metric_inv
        scalar_R = sp.simplify(sum(g_inv[a, b] * Ricc.comp[a, b] for a in range(dim) for b in range(dim)))

        def einstein_element(a, b):
            return sp.simplify(Ricc.comp[a, b] - sp.Rational(1, 2) * space.g.components[a, b] * scalar_R)

        Ein = space.from_function(einstein_element, signature=(D, D), name="Einstein", label="G")
        scalar_curvature = space.scalar(scalar_R, name="R", label="R")
        return Riem, Ricc, Ein, scalar_curvature


class FixedConnectionStrategy(ConnectionStrategy):
    def __init__(self, connection):
        self.connection = sp.Array(connection) if connection is not None else None

    def build(self, space):
        return self.connection


class TensorSpace:
    def __init__(
        self,
        coords,
        dim=None,
        metric=None,
        metric_inv=None,
        connection=None,
        connection_strategy=None,
        curvature_strategy=None,
    ):
        self.dim = dim if dim else len(coords)
        self.coords = tuple(coords)
        self._tensor_count = 0
        self._label_count = 0
        self._registry = {}
        self.metric = Metric(sp.Array(metric), self, signature=(D, D), name="g", label="g") if metric is not None else None
        self._metric_inv = None
        if metric is not None:
            self._metric_inv = (
                sp.Array(metric_inv) if metric_inv is not None else sp.Array(sp.Matrix(metric).inv())
            )
        self.metric_tensor = None
        self.metric_inv_tensor = None
        self.g = None
        self._detg = None
        self.christoffel2 = None
        self.christoffel1 = None
        if self.metric is not None:
            self.metric_tensor = self.register(self.metric)
        if self._metric_inv is not None:
            self.metric_inv_tensor = self.register(
                Tensor(self._metric_inv, self, signature=(U, U), name="g_inv", label="g_inv")
            )
        if connection is not None and connection_strategy is None:
            self.connection_strategy = FixedConnectionStrategy(connection)
        else:
            self.connection_strategy = connection_strategy or LyraConnectionStrategy()
        self.curvature_strategy = curvature_strategy or LyraCurvatureStrategy()
        self.gamma = Connection(connection) if connection is not None else Connection(None)
        self.scale = self.scalar(1, name="phi", label="phi")
        self.phi = self.scale
        self.torsion = self.zeros((D, D, D), name="tau", label="tau")
        self.nonmetricity = self.zeros((U, D, D), name="M", label="M")
        self.metric_compatible = None
        self.tensor = TensorFactory(self)
        self.riemann = None
        self.ricci = None
        self.einstein = None
        self.scalar_curvature = None
        self.update()

    def _coord_symbol(self, coord):
        if isinstance(coord, int):
            return self.coords[coord]
        if isinstance(coord, sp.Basic):
            if coord in self.coords:
                return coord
            raise ValueError("Coordenada desconhecida.")
        if isinstance(coord, str):
            for c in self.coords:
                if str(c) == coord:
                    return c
            raise ValueError("Coordenada desconhecida.")
        raise TypeError("Coordenada deve ser int, simbolo ou string.")

    def coord_index(self, names):
        if isinstance(names, str):
            parts = [p for p in names.replace(",", " ").split() if p]
        else:
            parts = list(names)
        if len(parts) != self.dim:
            raise ValueError("Numero de indices deve ser igual a dim.")
        return tuple(CoordIndex(str(p), i) for i, p in enumerate(parts))

    def set_metric(self, metric, metric_inv=None):
        self.metric = Metric(sp.Array(metric), self, signature=(D, D), name="g", label="g")
        if metric_inv is None:
            self._metric_inv = sp.Array(sp.Matrix(metric).inv())
        else:
            self._metric_inv = sp.Array(metric_inv)
        self.metric_tensor = self.register(self.metric)
        self.metric_inv_tensor = self.register(
            Tensor(self._metric_inv, self, signature=(U, U), name="g_inv", label="g_inv")
        )

    @property
    def metric_inv(self):
        if self._metric_inv is None and self.metric is not None:
            self._metric_inv = sp.Array(sp.Matrix(self.metric.components).inv())
            self.metric_inv_tensor = self.register(
                Tensor(self._metric_inv, self, signature=(U, U), name="g_inv", label="g_inv")
            )
        return self._metric_inv

    @property
    def detg(self):
        if self._detg is None and self.metric is not None:
            self._detg = sp.simplify(sp.Matrix(self.metric.components).det())
        return self._detg

    @property
    def connection(self):
        return self.gamma.components

    def _next_tensor_name(self):
        self._tensor_count += 1
        return f"T{self._tensor_count}"

    def _next_label(self):
        self._label_count += 1
        return f"_{self._label_count}"

    def register(self, tensor):
        self._registry[tensor.name] = tensor
        return tensor

    def get(self, name):
        return self._registry.get(name)

    def set_connection(self, connection):
        self.connection_strategy = FixedConnectionStrategy(connection)
        self.gamma = Connection(connection)

    def set_scale(self, phi=None, coord_index=None):
        if phi is None:
            if coord_index is None:
                coord_index = 1 if len(self.coords) > 1 else 0
            phi = sp.Function("phi")(self.coords[coord_index])
        self.scale = self.scalar(phi, name="phi", label="phi")
        self.phi = self.scale
        return self.scale

    def set_torsion(self, torsion_tensor):
        if isinstance(torsion_tensor, Tensor):
            if torsion_tensor.space is not self:
                raise ValueError("Torsion tensor pertence a outro TensorSpace.")
            self.torsion = torsion_tensor
        else:
            self.torsion = self.from_array(torsion_tensor, signature=(D, D, D))
        return self.torsion

    def set_nonmetricity(self, nonmetricity_tensor):
        if isinstance(nonmetricity_tensor, Tensor):
            if nonmetricity_tensor.space is not self:
                raise ValueError("Non-metricity tensor pertence a outro TensorSpace.")
            self.nonmetricity = nonmetricity_tensor
        else:
            self.nonmetricity = self.from_array(nonmetricity_tensor, signature=(U, D, D))
        return self.nonmetricity

    def set_metric_compatibility(self, compatible=True):
        self.metric_compatible = bool(compatible)
        return self.metric_compatible

    def _update_metric_related(self):
        self.g = self.metric
        if self.metric is None:
            self._detg = None
            self.christoffel2 = None
            self.christoffel1 = None
            return

        g = self.metric.components
        coords = self.coords
        dim = self.dim
        self._detg = sp.simplify(sp.Matrix(g).det())

        chris1 = [[[
            sp.Rational(1, 2)
            * (
                sp.diff(g[a, c], coords[b])
                + sp.diff(g[a, b], coords[c])
                - sp.diff(g[b, c], coords[a])
            )
            for c in range(dim)
        ] for b in range(dim)] for a in range(dim)]
        self.christoffel1 = ConnectionTensor(sp.Array(chris1), self, signature=(D, D, D), name="christoffel1")

        g_inv = self.metric_inv
        chris2 = [[[
            sum(g_inv[a, D] * self.christoffel1[D, b, c] for D in range(dim))
            for c in range(dim)
        ] for b in range(dim)] for a in range(dim)]
        self.christoffel2 = ConnectionTensor(sp.Array(chris2), self, signature=(U, D, D), name="christoffel2")

    def _update_connection(self):
        if self.connection_strategy is None:
            self.gamma = Connection(None)
            return
        Gamma = self.connection_strategy.build(self)
        self.gamma = Connection(Gamma) if Gamma is not None else Connection(None)

    def _update_riemann(self):
        if self.curvature_strategy is None:
            self.riemann = None
            self.ricci = None
            self.einstein = None
            self.scalar_curvature = None
            return
        riem, ricc, ein, scalar = self.curvature_strategy.build(self, self.gamma.components)
        self.riemann = riem
        self.ricci = ricc
        self.einstein = ein
        self.scalar_curvature = scalar

    def update(self, include=None, exclude=()):
        available = {
            "scale",
            "metric",
            "detg",
            "christoffel",
            "connection",
            "riemann",
            "ricci",
            "einstein",
        }
        if include is None:
            steps = set(available)
        else:
            steps = set(include)
        steps -= set(exclude)

        if "metric" in steps or "detg" in steps or "christoffel" in steps:
            self._update_metric_related()
        if "connection" in steps:
            self._update_connection()
        if "riemann" in steps or "ricci" in steps or "einstein" in steps:
            self._update_riemann()

    def from_function(self, func, signature, name=None, label=None):
        rank = len(signature)
        signature = _validate_signature(signature, rank)
        shape = (self.dim,) * rank
        flat = [func(*idx) for idx in itertools.product(range(self.dim), repeat=rank)]
        arr = sp.ImmutableDenseNDimArray(flat, shape)
        return self.register(Tensor(arr, self, signature=signature, name=name, label=label))

    def from_array(self, array, signature, name=None, label=None):
        if not isinstance(array, (sp.Array, sp.ImmutableDenseNDimArray)):
            array = sp.Array(array)
        rank = len(array.shape)
        signature = _validate_signature(signature, rank)
        if not isinstance(array, sp.ImmutableDenseNDimArray):
            array = sp.ImmutableDenseNDimArray(array)
        return self.register(Tensor(array, self, signature=signature, name=name, label=label))

    def zeros(self, signature, name=None, label=None):
        signature = _validate_signature(signature, len(signature))
        shape = (self.dim,) * len(signature)
        arr = sp.ImmutableDenseNDimArray([0] * (self.dim ** len(signature)), shape)
        return self.register(Tensor(arr, self, signature=signature, name=name, label=label))

    def scalar(self, expr, name=None, label=None):
        return self.register(Tensor(sp.Array(expr), self, signature=(), name=name, label=label))

    def tensor(self, tensor, index=None, name=None, label=None):
        if isinstance(tensor, IndexedTensor):
            base = Tensor(tensor.components, self, signature=tensor.signature, name=name, label=label)
            base._labels = list(tensor.labels)
            if hasattr(tensor, "_label_history"):
                base._label_history = set(tensor._label_history)
        elif isinstance(tensor, Tensor):
            if tensor.space is not self:
                raise ValueError("Tensor pertence a outro TensorSpace.")
            base = Tensor(tensor.components, self, signature=tensor.signature, name=name or tensor.name, label=label)
            if hasattr(tensor, "_labels"):
                base._labels = list(tensor._labels)
            if hasattr(tensor, "_label_history"):
                base._label_history = set(tensor._label_history)
        else:
            raise TypeError("tensor deve ser Tensor ou IndexedTensor.")

        if index is None:
            return base

        if not hasattr(base, "_labels"):
            raise ValueError("Tensor nao possui rotulos para reordenar.")

        if not isinstance(index, (tuple, list)):
            index = (index,)
        if len(index) != base.rank:
            raise ValueError("Numero de indices nao bate com o rank do tensor.")

        target_labels = []
        target_sig = []
        for idx in index:
            if isinstance(idx, UpIndex):
                target_labels.append(idx.label)
                target_sig.append(U)
            elif isinstance(idx, DownIndex):
                target_labels.append(idx.label)
                target_sig.append(D)
            else:
                raise TypeError("Use apenas +a/-b (ou U(a)/D(b)) no index.")

        if any(lab is None or lab is NO_LABEL for lab in target_labels):
            raise ValueError("Indices devem ter rotulos explicitos para reordenacao.")

        labels = list(base._labels)
        if set(target_labels) != set(labels):
            raise ValueError("Reordenacao exige os mesmos rotulos de indices.")

        perm = [labels.index(lab) for lab in target_labels]
        for pos, want in enumerate(target_sig):
            if want is None:
                continue
            have = base.signature[perm[pos]]
            if have is not want:
                raise ValueError("Variancia incompatível na reordenacao.")

        reordered = sp.permutedims(base.components, perm)
        new_sig = tuple(base.signature[i] for i in perm)
        result = Tensor(reordered, self, signature=new_sig, name=base.name, label=base.label)
        result._labels = list(target_labels)
        return result

    def generic(self, name, signature, coords=None, label=None):
        signature = _validate_signature(signature, len(signature))
        coords = self.coords if coords is None else tuple(coords)
        rank = len(signature)
        shape = (self.dim,) * rank

        def comp(*idx):
            suf = "".join(map(str, idx))
            return sp.Function(f"{name}{suf}")(*coords)

        flat = [comp(*idx) for idx in itertools.product(range(self.dim), repeat=rank)]
        arr = sp.ImmutableDenseNDimArray(flat, shape)
        return self.register(Tensor(arr, self, signature=signature, name=name, label=label or name))

    def nabla(self, tensor, order=1, deriv_position="prepend"):
        """
        Derivada covariante de Lyra:
        ∇_k T = (1/phi) ∂_k T + Σ Γ^{a_i}{}_{m k} T^{...m...} - Σ Γ^{m}{}_{b_j k} T_{...m...}
        """
        if not isinstance(order, int) or order < 1:
            raise ValueError("order deve ser inteiro >= 1.")
        if self.connection is None:
            raise ValueError("Defina a conexao (Gamma^a_{bc}) em TensorSpace.")
        if isinstance(tensor, Tensor):
            if tensor.space is not self:
                raise ValueError("Tensor pertence a outro TensorSpace.")
        else:
            try:
                expr = sp.sympify(tensor)
            except (TypeError, ValueError) as exc:
                raise TypeError("nabla aceita Tensor ou expressao sympy.") from exc
            tensor = Tensor(sp.Array(expr), self, signature=())

        dim = self.dim
        coords = self.coords
        Gamma = self.connection
        T = tensor.components
        rank = tensor.rank
        sig = tensor.signature

        shape = (dim,) * (rank + 1)
        out_flat = []

        for full_idx in itertools.product(range(dim), repeat=rank + 1):
            if deriv_position == "append":
                idx = full_idx[:-1]
                k = full_idx[-1]
            elif deriv_position == "prepend":
                k = full_idx[0]
                idx = full_idx[1:]
            else:
                raise ValueError("deriv_position deve ser 'append' ou 'prepend'.")

            phi = self.phi.expr if isinstance(self.phi, Tensor) else self.phi
            base = (1 / phi) * sp.diff(T[idx], coords[k])
            idx_list = list(idx)

            for pos, s in enumerate(sig):
                if s is U:
                    acc = 0
                    for m in range(dim):
                        idx_list[pos] = m
                        acc += Gamma[idx[pos], m, k] * T[tuple(idx_list)]
                    base += acc
                else:
                    acc = 0
                    for m in range(dim):
                        idx_list[pos] = m
                        acc += Gamma[m, idx[pos], k] * T[tuple(idx_list)]
                    base -= acc
                idx_list[pos] = idx[pos]

            out_flat.append(sp.simplify(base))

        out = sp.ImmutableDenseNDimArray(out_flat, shape)
        if deriv_position == "append":
            new_sig = sig + (D,)
        else:
            new_sig = (D,) + sig
        result = Tensor(out, self, signature=new_sig, name=None, label=tensor.label)
        if order == 1:
            return result
        return self.nabla(result, order=order - 1, deriv_position=deriv_position)

    def gradient(self, tensor, deriv_position="prepend"):
        return self.nabla(tensor, order=1, deriv_position=deriv_position)

    def divergence(self, tensor, position=0, deriv_position="prepend"):
        if not isinstance(tensor, Tensor):
            raise TypeError("divergence exige Tensor.")
        if tensor.rank < 1:
            raise ValueError("divergence exige tensor de rank >= 1.")
        if not isinstance(position, int) or not (0 <= position < tensor.rank):
            raise ValueError("position deve apontar para um indice do tensor.")

        nabla_t = self.nabla(tensor, order=1, deriv_position=deriv_position)
        if deriv_position == "prepend":
            deriv_axis = 0
            tensor_axis = 1 + position
        elif deriv_position == "append":
            deriv_axis = nabla_t.rank - 1
            tensor_axis = position
        else:
            raise ValueError("deriv_position deve ser 'append' ou 'prepend'.")
        return nabla_t.contract(deriv_axis, tensor_axis)

    def laplacian(self, tensor, deriv_position="prepend"):
        nabla2 = self.nabla(tensor, order=2, deriv_position=deriv_position)
        if deriv_position == "prepend":
            return nabla2.contract(0, 1)
        if deriv_position == "append":
            return nabla2.contract(nabla2.rank - 2, nabla2.rank - 1)
        raise ValueError("deriv_position deve ser 'append' ou 'prepend'.")

    def ricci_scalar(self):
        if self.ricci is None or self.metric_inv is None or self.scalar_curvature is None:
            self.update(include=("riemann", "ricci", "einstein"))
        if self.scalar_curvature is not None:
            return self.scalar_curvature
        if self.ricci is None or self.metric_inv is None:
            raise ValueError("Ricci tensor ou metrica nao definida.")
        dim = self.dim
        scalar_R = sp.simplify(sum(self.metric_inv[a, b] * self.ricci.comp[a, b] for a in range(dim) for b in range(dim)))
        return self.scalar(scalar_R, name="R", label="R")

    def kretschmann_scalar(self):
        if self.riemann is None or self.metric is None or self.metric_inv is None:
            self.update(include=("riemann", "ricci", "einstein"))
        if self.riemann is None:
            raise ValueError("Riemann tensor nao definido.")
        dim = self.dim
        R_down = self.riemann.as_signature((D, D, D, D))
        R_up = self.riemann.as_signature((U, U, U, U))
        total = 0
        for a, b, c, d in itertools.product(range(dim), repeat=4):
            total += R_down[a, b, c, d] * R_up[a, b, c, d]
        return self.scalar(sp.simplify(total), name="K", label="K")

    def euler_density(self, normalize=False):
        if self.dim != 2:
            raise ValueError("Euler density implementada apenas para dim=2.")
        if self.metric is None:
            raise ValueError("Metrica nao definida para Euler density.")
        scalar_R = self.ricci_scalar()
        density = sp.simplify(scalar_R.components[()] * sp.sqrt(self.detg))
        if normalize:
            density = sp.simplify(density / (4 * sp.pi))
        return self.scalar(density, name="Euler", label="Euler")

    def index(self, names):
        if isinstance(names, str):
            parts = [p for p in names.replace(",", " ").split() if p]
        else:
            parts = list(names)
        out = []
        for p in parts:
            if p in ("_", ".", "empty", None):
                out.append(None)
            else:
                out.append(Index(str(p)))
        return out[0] if len(out) == 1 else tuple(out)

    def contract(self, *indexed_tensors):
        if not indexed_tensors:
            raise ValueError("Informe ao menos um tensor indexado.")

        tensors = [it if isinstance(it, IndexedTensor) else it.idx() for it in indexed_tensors]
        A = tensors[0].components
        sig = list(tensors[0].signature)
        labels = list(tensors[0].labels)
        history = set()
        for t in tensors:
            history.update(getattr(t, "_label_history", set()))
            history.update(getattr(t.tensor, "_label_history", set()))

        for t in tensors[1:]:
            A = sp.tensorproduct(A, t.components)
            sig.extend(t.signature)
            labels.extend(t.labels)

        label_map = {}
        for pos, (lab, s) in enumerate(zip(labels, sig)):
            if lab is None:
                continue
            label_map.setdefault(lab, []).append((pos, s))

        pairs = []
        to_remove = set()
        contracted_labels = set()
        for lab, occ in label_map.items():
            if len(occ) == 1:
                continue
            if len(occ) != 2:
                raise ValueError(f"Indice {lab} aparece {len(occ)} vezes.")
            (p1, s1), (p2, s2) = occ
            if s1 is s2:
                raise ValueError(f"Indice {lab} aparece com mesma variancia.")
            pairs.append((p1, p2))
            to_remove.update([p1, p2])
            contracted_labels.add(lab)

        for lab in labels:
            if lab is not None and lab in history:
                raise ValueError(f"Indice {lab} reutilizado apos contracao.")

        if pairs:
            A = sp.tensorcontraction(A, *pairs)

        new_sig = tuple(s for i, s in enumerate(sig) if i not in to_remove)
        new_labels = [lab for i, lab in enumerate(labels) if i not in to_remove]
        result = Tensor(A, self, signature=new_sig, name=None, label=None)
        result._labels = new_labels
        result._label_history = history | contracted_labels
        return result

    def eval_contract(self, expr):
        tensors = []
        for token in expr.split():
            name, seq_labels = _parse_tensor_token(token)
            tensor = self.get(name)
            if tensor is None:
                raise ValueError(f"Tensor '{name}' nao registrado.")
            up_full, down_full = _expand_indices(tensor.rank, seq_labels)
            indexed = tensor.idx(up=up_full, down=down_full)
            tensors.append(indexed)
        return self.contract(*tensors)


class ConnectionTensor(Tensor):
    def as_signature(self, target_signature, simplify=False):
        target_signature = _validate_signature(target_signature, self.rank)
        if target_signature != self.signature:
            raise ValueError("Conexao nao suporta subir/descer indices.")
        return self.components


class Connection:
    def __init__(self, components):
        self.components = sp.Array(components) if components is not None else None

    def _repr_latex_(self):
        if self.components is None:
            return r"\text{Connection}(\varnothing)"
        if hasattr(self.components, "_repr_latex_"):
            return self.components._repr_latex_()
        return sp.latex(self.components)

    def _repr_html_(self):
        return self._repr_latex_()

    def __getitem__(self, idx):
        if self.components is None:
            raise ValueError("Conexao nao definida.")
        return self.components[idx]


class SpaceTime(TensorSpace):
    pass


class Manifold(TensorSpace):
    pass


def gradient(tensor, space=None, deriv_position="prepend"):
    from .diff_ops import gradient as _gradient

    return _gradient(tensor, space=space, deriv_position=deriv_position)


def divergence(tensor, space=None, position=0, deriv_position="prepend"):
    from .diff_ops import divergence as _divergence

    return _divergence(tensor, space=space, position=position, deriv_position=deriv_position)


def laplacian(tensor, space=None, deriv_position="prepend"):
    from .diff_ops import laplacian as _laplacian

    return _laplacian(tensor, space=space, deriv_position=deriv_position)


def ricci_scalar(tensor=None, space=None):
    from .invariants import ricci_scalar as _ricci_scalar

    return _ricci_scalar(tensor=tensor, space=space)


def kretschmann_scalar(tensor=None, space=None):
    from .invariants import kretschmann_scalar as _kretschmann_scalar

    return _kretschmann_scalar(tensor=tensor, space=space)


def euler_density(tensor=None, space=None, normalize=False):
    from .invariants import euler_density as _euler_density

    return _euler_density(tensor=tensor, space=space, normalize=normalize)


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
    "gradient",
    "kretschmann_scalar",
    "laplacian",
    "ricci_scalar",
    "u",
]
