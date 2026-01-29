import itertools
import numbers
import sympy as sp


class Index:
    def __init__(self, name):
        self.name = str(name)

    def __repr__(self):
        return self.name

    def __pos__(self):
        return UpIndex(self.name)

    def __neg__(self):
        return DownIndex(self.name)


class _NoLabel:
    pass


NO_LABEL = _NoLabel()


class UpIndex:
    def __init__(self, label=NO_LABEL):
        self.label = label

    def __repr__(self):
        return f"^{self.label}"


class DownIndex:
    def __init__(self, label=NO_LABEL):
        self.label = label

    def __repr__(self):
        return f"_{self.label}"


class CoordIndex(Index):
    def __init__(self, name, coord_pos):
        super().__init__(name)
        self.coord_pos = coord_pos


class Up:
    def __call__(self, label=NO_LABEL):
        return UpIndex(label)


class Down:
    def __call__(self, label=NO_LABEL):
        return DownIndex(label)


U = Up()

D = Down()

u = U
d = D


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


def _norm_sig(sig, rank):
    if len(sig) != rank:
        raise ValueError(f"Assinatura tem tamanho {len(sig)} mas rank e {rank}.")
    out = []
    for s in sig:
        if s in (U, Up, "U", "u", "^", +1, True):
            out.append(U)
        elif s in (D, Down, "D", "d", "_", -1, False):
            out.append(D)
        else:
            raise ValueError(f"Elemento de assinatura invalido: {s!r}. Use U/D.")
    return tuple(out)


def _validate_signature(signature, rank):
    if not isinstance(signature, (tuple, list)):
        raise TypeError("signature deve ser tupla/lista, ex.: (U,D,D).")
    if len(signature) != rank:
        raise ValueError(f"signature tem tamanho {len(signature)}, mas rank={rank}.")
    return _norm_sig(signature, rank)


def table(func, dim, rank):
    shape = (dim,) * rank
    flat = [func(*idx) for idx in itertools.product(range(dim), repeat=rank)]
    return sp.ImmutableDenseNDimArray(flat, shape)


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


class Tensor:
    def __init__(self, components, space, signature, name=None, label=None):
        self.components = sp.Array(components)
        self.rank = self.components.rank()
        self.signature = _validate_signature(signature, self.rank)
        self.space = space
        self.name = name if name is not None else space._next_tensor_name()
        self.label = label if label is not None else self.name
        self._cache = {self.signature: self.components}

    def _as_scalar(self):
        if self.rank != 0:
            raise TypeError("Operacao escalar so e valida para tensores de rank 0.")
        return sp.sympify(self.components[()])

    def fmt(self, expr=None):
        if expr is None:
            if self.rank == 0:
                target = sp.expand(sp.simplify(self._as_scalar()))
                return Tensor(sp.Array(target), self.space, signature=self.signature, name=self.name, label=self.label)
            if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
                arr = sp.ImmutableDenseNDimArray(self.components)
                target = arr.applyfunc(lambda v: sp.expand(sp.simplify(v)))
            else:
                target = sp.expand(sp.simplify(self.components))
            return Tensor(target, self.space, signature=self.signature, name=self.name, label=self.label)
        if isinstance(expr, Tensor):
            return expr.fmt()
        if isinstance(expr, IndexedTensor):
            return expr.fmt()
        return sp.expand(sp.simplify(expr))

    def subs(self, *args, **kwargs):
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [v.subs(*args, **kwargs) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = self.components.subs(*args, **kwargs)
        return Tensor(target, self.space, signature=self.signature, name=self.name, label=self.label)

    @property
    def expr(self):
        return self._as_scalar()

    @property
    def args(self):
        return self._as_scalar().args

    def _sympy_(self):
        if self.rank != 0:
            raise sp.SympifyError(self)
        return self._as_scalar()

    def _repr_latex_(self):
        if self.rank == 0:
            expr = self._as_scalar()
            if hasattr(expr, "_repr_latex_"):
                return expr._repr_latex_()
            return sp.latex(expr)
        if hasattr(self.components, "_repr_latex_"):
            return self.components._repr_latex_()
        return sp.latex(self.components)

    def __call__(self, *sig):
        if len(sig) == 1 and isinstance(sig[0], (tuple, list)):
            sig = tuple(sig[0])
        if sig and any(isinstance(s, Index) for s in sig):
            raise TypeError("Use +a/-b para indices com variancia explicita.")
        if sig and all(isinstance(s, (UpIndex, DownIndex)) for s in sig):
            if len(sig) != self.rank:
                raise ValueError("Numero de indices nao bate com o rank do tensor.")
            up = [None] * self.rank
            down = [None] * self.rank
            for i, idx in enumerate(sig):
                if isinstance(idx, UpIndex):
                    up[i] = idx.label
                else:
                    down[i] = idx.label
            return self.idx(up=up, down=down)
        arr = self.as_signature(sig, simplify=False)
        return Tensor(arr, self.space, signature=sig, name=self.name, label=self.label)

    def __getitem__(self, indices):
        if not isinstance(indices, tuple):
            indices = (indices,)
        if any(isinstance(idx, (UpIndex, DownIndex, Index)) for idx in indices):
            if any(isinstance(idx, Index) for idx in indices):
                raise TypeError("Use +a/-b para indices com variancia explicita.")
            if not all(isinstance(idx, (UpIndex, DownIndex)) for idx in indices):
                raise TypeError("Use apenas +a/-b (ou U(a)/D(b)) para indexar o tensor.")
            if len(indices) != self.rank:
                raise ValueError("Numero de indices nao bate com o rank do tensor.")
            up = [None] * self.rank
            down = [None] * self.rank
            for i, idx in enumerate(indices):
                if isinstance(idx, UpIndex):
                    up[i] = idx.label
                elif isinstance(idx, DownIndex):
                    down[i] = idx.label
            indexed = self.idx(up=up, down=down)
            labels = indexed.labels
            if len(set(labels)) != len(labels):
                return self.space.contract(indexed)
            return indexed
        return self.components[indices]

    def __add__(self, other):
        if isinstance(other, Tensor) and other.rank != self.rank:
            raise ValueError(
                f"Soma exige tensores com o mesmo rank ({self.rank} vs {other.rank})."
            )
        if self.rank == 0:
            if isinstance(other, IndexedTensor) and other.tensor.rank != 0:
                raise ValueError(
                    f"Soma exige tensores com o mesmo rank ({self.rank} vs {other.tensor.rank})."
                )
            if isinstance(other, Tensor):
                return self._as_scalar() + other._as_scalar()
            return self._as_scalar() + other
        if isinstance(other, Tensor):
            if other.space is not self.space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            if other.signature != self.signature:
                raise ValueError("Assinaturas diferentes; soma exige mesma assinatura.")
            labels = getattr(self, "_labels", None)
            other_labels = getattr(other, "_labels", None)
            if labels is not None or other_labels is not None:
                if labels is None or other_labels is None:
                    raise ValueError("Soma exige tensores com rotulos compatíveis.")
                if set(labels) != set(other_labels):
                    raise ValueError("Soma exige tensores com os mesmos rotulos.")
                if labels != other_labels:
                    perm = [other_labels.index(lab) for lab in labels]
                    other_components = sp.permutedims(other.components, perm)
                else:
                    other_components = other.components
                result = Tensor(self.components + other_components, self.space, signature=self.signature)
                result._labels = list(labels)
                return result
            return Tensor(self.components + other.components, self.space, signature=self.signature)
        return NotImplemented

    def __radd__(self, other):
        if self.rank == 0:
            return other + self._as_scalar()
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Tensor) and other.rank != self.rank:
            raise ValueError(
                f"Subtracao exige tensores com o mesmo rank ({self.rank} vs {other.rank})."
            )
        if self.rank == 0:
            if isinstance(other, IndexedTensor) and other.tensor.rank != 0:
                raise ValueError(
                    f"Subtracao exige tensores com o mesmo rank ({self.rank} vs {other.tensor.rank})."
                )
            if isinstance(other, Tensor):
                return self._as_scalar() - other._as_scalar()
            return self._as_scalar() - other
        if isinstance(other, Tensor):
            if other.space is not self.space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            if other.signature != self.signature:
                raise ValueError("Assinaturas diferentes; subtracao exige mesma assinatura.")
            labels = getattr(self, "_labels", None)
            other_labels = getattr(other, "_labels", None)
            if labels is not None or other_labels is not None:
                if labels is None or other_labels is None:
                    raise ValueError("Subtracao exige tensores com rotulos compatíveis.")
                if set(labels) != set(other_labels):
                    raise ValueError("Subtracao exige tensores com os mesmos rotulos.")
                if labels != other_labels:
                    perm = [other_labels.index(lab) for lab in labels]
                    other_components = sp.permutedims(other.components, perm)
                else:
                    other_components = other.components
                result = Tensor(self.components - other_components, self.space, signature=self.signature)
                result._labels = list(labels)
                return result
            return Tensor(self.components - other.components, self.space, signature=self.signature)
        return NotImplemented

    def __rsub__(self, other):
        if self.rank == 0:
            return other - self._as_scalar()
        return NotImplemented

    def __mul__(self, other):
        if self.rank == 0:
            scalar = self._as_scalar()
            if isinstance(other, Tensor):
                if other.space is not self.space:
                    raise ValueError("Tensores pertencem a TensorSpaces distintos.")
                scaled = scalar * other.components
                return Tensor(scaled, other.space, signature=other.signature)
            if isinstance(other, IndexedTensor):
                if other.tensor.space is not self.space:
                    raise ValueError("Tensores pertencem a TensorSpaces distintos.")
                scaled = scalar * other.components
                tensor = Tensor(scaled, other.tensor.space, signature=other.signature)
                indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(other.labels))
                indexed._label_history = set(getattr(other, "_label_history", set()))
                return indexed
            return scalar * other
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = sp.sympify(other) * self.components
            return Tensor(scaled, self.space, signature=self.signature)
        if isinstance(other, Tensor):
            if other.rank == 0:
                scaled = other._as_scalar() * self.components
                return Tensor(scaled, self.space, signature=self.signature)
            if other.space is not self.space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            TP = sp.tensorproduct(self.components, other.components)
            new_sig = self.signature + other.signature
            return Tensor(TP, self.space, signature=new_sig)
        if isinstance(other, IndexedTensor) and hasattr(self, "_labels"):
            indexed = IndexedTensor(self, self.components, self.signature, list(self._labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return self.space.contract(indexed, other)
        return NotImplemented

    def __rmul__(self, other):
        if self.rank == 0:
            return other * self._as_scalar()
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = sp.sympify(other) * self.components
            return Tensor(scaled, self.space, signature=self.signature)
        if isinstance(other, Tensor):
            if other.rank == 0:
                scaled = other._as_scalar() * self.components
                return Tensor(scaled, self.space, signature=self.signature)
            if other.space is not self.space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            TP = sp.tensorproduct(other.components, self.components)
            new_sig = other.signature + self.signature
            return Tensor(TP, self.space, signature=new_sig)
        if isinstance(other, IndexedTensor) and hasattr(self, "_labels"):
            indexed = IndexedTensor(self, self.components, self.signature, list(self._labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return self.space.contract(other, indexed)
        return NotImplemented

    def __truediv__(self, other):
        if self.rank == 0:
            return self._as_scalar() / other
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = self.components / sp.sympify(other)
            return Tensor(scaled, self.space, signature=self.signature)
        return NotImplemented

    def __rtruediv__(self, other):
        if self.rank == 0:
            return other / self._as_scalar()
        return NotImplemented

    def __pow__(self, power):
        if self.rank == 0:
            return self._as_scalar() ** power
        return NotImplemented

    def __neg__(self):
        if self.rank == 0:
            return -self._as_scalar()
        return NotImplemented

    @property
    def comp(self):
        return self.components

    def _move_front_axis_to(self, A, pos):
        rank = A.rank()
        perm = []
        rest = list(range(1, rank))
        for i in range(rank):
            if i == pos:
                perm.append(0)
            else:
                perm.append(rest.pop(0))
        return sp.permutedims(A, perm)

    def _raise_at(self, A, pos):
        if self.space.metric_inv is None:
            raise ValueError("Metric inverse nao definido para subir indices.")
        TP = sp.tensorproduct(self.space.metric_inv, A)
        C = sp.tensorcontraction(TP, (1, pos + 2))
        return self._move_front_axis_to(C, pos)

    def _lower_at(self, A, pos):
        if self.space.metric is None:
            raise ValueError("Metric nao definida para descer indices.")
        TP = sp.tensorproduct(self.space.metric.components, A)
        C = sp.tensorcontraction(TP, (1, pos + 2))
        return self._move_front_axis_to(C, pos)

    def as_signature(self, target_signature, simplify=False):
        target_signature = _validate_signature(target_signature, self.rank)
        if target_signature in self._cache:
            return self._cache[target_signature]

        A = self._cache[self.signature]
        sig_cur = list(self.signature)
        for pos in range(self.rank):
            want = target_signature[pos]
            have = sig_cur[pos]
            if have is want:
                continue
            if have is D and want is U:
                A = self._raise_at(A, pos)
                sig_cur[pos] = U
            elif have is U and want is D:
                A = self._lower_at(A, pos)
                sig_cur[pos] = D
            else:
                raise RuntimeError("Estado impossivel na conversao de assinatura.")

        if simplify:
            A = sp.simplify(A)
        self._cache[target_signature] = A
        return A

    def nabla(self, order=1, deriv_position="prepend"):
        return self.space.nabla(self, order=order, deriv_position=deriv_position)

    def d(self, coord, deriv_position="append"):
        if isinstance(coord, UpIndex):
            raise ValueError("Indice de derivada deve ser covariante.")
        if isinstance(coord, (Index, DownIndex)):
            label = coord.name if isinstance(coord, Index) else coord.label
            if label is None or label is NO_LABEL:
                raise ValueError("Indice de derivada deve ter rotulo explicito.")
            coords = self.space.coords
            shape = self.components.shape
            dim = self.space.dim
            if deriv_position == "append":
                new_shape = shape + (dim,)
                flat = []
                for idx in itertools.product(*(range(s) for s in shape)):
                    for k, sym in enumerate(coords):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = self.signature + (D,)
            elif deriv_position == "prepend":
                new_shape = (dim,) + shape
                flat = []
                for k, sym in enumerate(coords):
                    for idx in itertools.product(*(range(s) for s in shape)):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = (D,) + self.signature
            else:
                raise ValueError("deriv_position deve ser 'append' ou 'prepend'.")
            target = sp.ImmutableDenseNDimArray(flat, new_shape)
            out = Tensor(target, self.space, signature=new_sig, name=None, label=self.label)
            out._labels = list(getattr(self, "_labels", [])) + [label] if deriv_position == "append" else [label] + list(getattr(self, "_labels", []))
            return out

        sym = self.space._coord_symbol(coord)
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [sp.diff(v, sym) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = sp.diff(self.components, sym)
        return Tensor(target, self.space, signature=self.signature, name=None, label=self.label)

    def contract(self, pos1, pos2, use_metric=True):
        if pos1 == pos2:
            raise ValueError("pos1 e pos2 devem ser indices distintos.")
        if not (0 <= pos1 < self.rank and 0 <= pos2 < self.rank):
            raise IndexError("pos1/pos2 fora do rank do tensor.")

        sig = list(self.signature)
        s1 = sig[pos1]
        s2 = sig[pos2]
        A = self.components

        if s1 is s2:
            if not use_metric:
                raise ValueError("Indices com mesma variancia exigem use_metric=True.")
            if s1 is D:
                A = self.as_signature(
                    tuple(U if i == pos2 else s for i, s in enumerate(sig))
                )
                sig[pos2] = U
            else:
                A = self.as_signature(
                    tuple(D if i == pos2 else s for i, s in enumerate(sig))
                )
                sig[pos2] = D

        contracted = sp.tensorcontraction(A, (pos1, pos2))
        new_sig = tuple(s for i, s in enumerate(sig) if i not in (pos1, pos2))
        return Tensor(contracted, self.space, signature=new_sig)

    def idx(self, up=None, down=None):
        rank = self.rank
        if up is None and down is None:
            up = [None] * rank
            down = [None] * rank
        elif up is None or down is None:
            raise ValueError("Forneca up e down com o mesmo tamanho do rank.")

        up = list(up)
        down = list(down)
        if len(up) != rank or len(down) != rank:
            raise ValueError("up/down devem ter tamanho igual ao rank do tensor.")

        labels = []
        target_sig = []
        for i in range(rank):
            up_i = _parse_label(up[i], self.space)
            down_i = _parse_label(down[i], self.space)
            if up_i is not None and down_i is not None:
                raise ValueError("Indice nao pode ser up e down na mesma posicao.")
            if up_i is None and down_i is None:
                target_sig.append(self.signature[i])
                labels.append(self.space._next_label())
            elif up_i is not None:
                target_sig.append(U)
                labels.append(self.space._next_label() if up_i is NO_LABEL else up_i)
            else:
                target_sig.append(D)
                labels.append(self.space._next_label() if down_i is NO_LABEL else down_i)

        A = self.as_signature(tuple(target_sig), simplify=False)
        indexed = IndexedTensor(self, A, tuple(target_sig), labels)
        indexed._label_history = set(getattr(self, "_label_history", set()))
        return indexed

    def up(self, *labels):
        labels = _complete_indices_right(labels, self.rank)
        return _IndexBuilder(self, up=labels, has_up=True)

    def down(self, *labels):
        labels = _complete_indices_right(labels, self.rank)
        return _IndexBuilder(self, down=labels, has_down=True)


class Metric(Tensor):
    pass


class ConnectionTensor(Tensor):
    def as_signature(self, target_signature, simplify=False):
        target_signature = _validate_signature(target_signature, self.rank)
        if target_signature != self.signature:
            raise ValueError("Conexao nao suporta subir/descer indices.")
        return self.components


class IndexedTensor:
    def __init__(self, tensor, components, signature, labels):
        self.tensor = tensor
        self.components = components
        self.signature = signature
        self.labels = labels

    def _repr_latex_(self):
        if hasattr(self.components, "_repr_latex_"):
            return self.components._repr_latex_()
        return sp.latex(self.components)

    def d(self, coord, deriv_position="append"):
        labels = list(self.labels)
        if isinstance(coord, UpIndex):
            raise ValueError("Indice de derivada deve ser covariante.")
        if isinstance(coord, Index):
            raise ValueError("Use +a/-b para indices com variancia explicita.")
        if isinstance(coord, DownIndex):
            lab = coord.label
            if lab is None or lab is NO_LABEL:
                raise ValueError("Indice de derivada deve ter rotulo explicito.")
            coords = self.tensor.space.coords
            shape = self.components.shape
            dim = self.tensor.space.dim
            if deriv_position == "append":
                new_shape = shape + (dim,)
                flat = []
                for idx in itertools.product(*(range(s) for s in shape)):
                    for k, sym in enumerate(coords):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = self.signature + (D,)
                new_labels = labels + [lab]
            elif deriv_position == "prepend":
                new_shape = (dim,) + shape
                flat = []
                for k, sym in enumerate(coords):
                    for idx in itertools.product(*(range(s) for s in shape)):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = (D,) + self.signature
                new_labels = [lab] + labels
            else:
                raise ValueError("deriv_position deve ser 'append' ou 'prepend'.")
            target = sp.ImmutableDenseNDimArray(flat, new_shape)
            tensor = Tensor(target, self.tensor.space, signature=new_sig)
            return IndexedTensor(tensor, tensor.components, tensor.signature, new_labels)

        sym = self.tensor.space._coord_symbol(coord)
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [sp.diff(v, sym) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = sp.diff(self.components, sym)
        tensor = Tensor(target, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, labels)

    def __repr__(self):
        return repr(self.components)

    def fmt(self, expr=None):
        if expr is None:
            if self.tensor.rank == 0:
                target = sp.expand(sp.simplify(self.tensor._as_scalar()))
            elif isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
                arr = sp.ImmutableDenseNDimArray(self.components)
                target = arr.applyfunc(lambda v: sp.expand(sp.simplify(v)))
            else:
                target = sp.expand(sp.simplify(self.components))
            tensor = Tensor(target, self.tensor.space, signature=self.signature)
            return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
        if isinstance(expr, Tensor):
            return expr.fmt()
        if isinstance(expr, IndexedTensor):
            return expr.fmt()
        return sp.expand(sp.simplify(expr))

    def subs(self, *args, **kwargs):
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [v.subs(*args, **kwargs) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = self.components.subs(*args, **kwargs)
        tensor = Tensor(target, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __eq__(self, other):
        if isinstance(other, IndexedTensor):
            other_sig = other.signature
            other_space = other.tensor.space
            other_components = other.components
        elif isinstance(other, Tensor):
            other_sig = other.signature
            other_space = other.space
            other_components = other.components
        else:
            return NotImplemented
        if other_space is not self.tensor.space:
            raise ValueError("Tensores pertencem a TensorSpaces distintos.")
        if other_sig != self.signature:
            raise ValueError("Assinaturas diferentes; igualdade exige mesma assinatura.")
        return self.components == other_components

    def __call__(self, *idx):
        rank = len(self.signature)
        if len(idx) > rank:
            raise ValueError("Numero de indices nao bate com o rank do tensor.")
        if len(idx) == rank:
            return self.components[idx]
        slicer = idx + (slice(None),) * (rank - len(idx))
        return self.components[slicer]

    def get(self, *idx):
        return self.__call__(*idx)

    def _resolve_position(self, idx):
        if isinstance(idx, int):
            if not (0 <= idx < len(self.signature)):
                raise IndexError("Indice fora do rank do tensor.")
            return idx
        if isinstance(idx, (UpIndex, DownIndex)):
            label = idx.label
        elif isinstance(idx, Index):
            raise ValueError("Use +a/-b para indices com variancia explicita.")
        else:
            raise ValueError("Use +a/-b para indices com variancia explicita.")
        matches = [i for i, lab in enumerate(self.labels) if lab == label]
        if len(matches) != 1:
            raise ValueError(f"Indice {label!r} nao encontrado ou duplicado.")
        return matches[0]

    def _swap_axes(self, pos1, pos2):
        perm = list(range(len(self.signature)))
        perm[pos1], perm[pos2] = perm[pos2], perm[pos1]
        return sp.permutedims(self.components, perm)

    def symmetric(self, idx1, idx2):
        pos1 = self._resolve_position(idx1)
        pos2 = self._resolve_position(idx2)
        if pos1 == pos2:
            raise ValueError("Indices devem ser distintos.")
        if self.signature[pos1] is not self.signature[pos2]:
            raise ValueError("Indices com variancia diferente nao podem ser simetrizados.")
        swapped = self._swap_axes(pos1, pos2)
        arr = sp.Rational(1, 2) * (self.components + swapped)
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def antisymmetric(self, idx1, idx2):
        pos1 = self._resolve_position(idx1)
        pos2 = self._resolve_position(idx2)
        if pos1 == pos2:
            raise ValueError("Indices devem ser distintos.")
        if self.signature[pos1] is not self.signature[pos2]:
            raise ValueError("Indices com variancia diferente nao podem ser antissimetrizados.")
        swapped = self._swap_axes(pos1, pos2)
        arr = sp.Rational(1, 2) * (self.components - swapped)
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __mul__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = other * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, Tensor) and other.rank == 0:
            scaled = other._as_scalar() * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, IndexedTensor):
            space = self.tensor.space
            if other.tensor.space is not space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            history = set(getattr(self, "_label_history", set()))
            other_history = set(getattr(other, "_label_history", set()))
            reused = history & set(other.labels)
            if reused:
                raise ValueError(f"Indice {sorted(reused)[0]} reutilizado apos contracao.")
            reused = other_history & set(self.labels)
            if reused:
                raise ValueError(f"Indice {sorted(reused)[0]} reutilizado apos contracao.")
            if set(self.labels) & set(other.labels):
                return space.contract(self, other)
            TP = sp.tensorproduct(self.components, other.components)
            new_sig = self.signature + other.signature
            new_labels = list(self.labels) + list(other.labels)
            tensor = Tensor(TP, space, signature=new_sig)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, new_labels)
            indexed._label_history = history | other_history
            return indexed
        if isinstance(other, Tensor) and hasattr(other, "_labels"):
            space = self.tensor.space
            if other.space is not space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            indexed = IndexedTensor(other, other.components, other.signature, list(other._labels))
            indexed._label_history = set(getattr(other, "_label_history", set()))
            return space.contract(self, indexed)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = other * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, Tensor) and other.rank == 0:
            scaled = other._as_scalar() * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, IndexedTensor):
            space = other.tensor.space
            if self.tensor.space is not space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            history = set(getattr(self, "_label_history", set()))
            other_history = set(getattr(other, "_label_history", set()))
            reused = history & set(other.labels)
            if reused:
                raise ValueError(f"Indice {sorted(reused)[0]} reutilizado apos contracao.")
            reused = other_history & set(self.labels)
            if reused:
                raise ValueError(f"Indice {sorted(reused)[0]} reutilizado apos contracao.")
            if set(self.labels) & set(other.labels):
                return space.contract(other, self)
            TP = sp.tensorproduct(other.components, self.components)
            new_sig = other.signature + self.signature
            new_labels = list(other.labels) + list(self.labels)
            tensor = Tensor(TP, space, signature=new_sig)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, new_labels)
            indexed._label_history = history | other_history
            return indexed
        if isinstance(other, Tensor) and hasattr(other, "_labels"):
            space = other.space
            if self.tensor.space is not space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            indexed = IndexedTensor(other, other.components, other.signature, list(other._labels))
            return space.contract(indexed, self)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, sp.Basic) and not isinstance(other, (Tensor, IndexedTensor)):
            if len(self.signature) == 0:
                return self.components[()] + other
            return NotImplemented
        if isinstance(other, IndexedTensor):
            other_sig = other.signature
            other_space = other.tensor.space
            other_components = other.components
            other_labels = list(other.labels)
        elif isinstance(other, Tensor):
            other_sig = other.signature
            other_space = other.space
            other_components = other.components
            other_labels = list(getattr(other, "_labels", []))
        else:
            return NotImplemented
        if len(other_sig) != len(self.signature):
            raise ValueError(
                f"Soma exige tensores com o mesmo rank ({len(self.signature)} vs {len(other_sig)})."
            )
        if other_space is not self.tensor.space:
            raise ValueError("Tensores pertencem a TensorSpaces distintos.")
        labels = list(self.labels)
        if other_labels:
            if set(other_labels) != set(labels):
                raise ValueError("Soma exige os mesmos rotulos.")
            perm = [other_labels.index(lab) for lab in labels]
            other_components = sp.permutedims(other_components, perm)
            other_sig = tuple(other_sig[i] for i in perm)
        if other_sig != self.signature:
            raise ValueError("Assinaturas diferentes; soma exige mesma assinatura.")
        arr = self.components + other_components
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, IndexedTensor):
            other_sig = other.signature
            other_space = other.tensor.space
            other_components = other.components
            other_labels = list(other.labels)
        elif isinstance(other, Tensor):
            other_sig = other.signature
            other_space = other.space
            other_components = other.components
            other_labels = list(getattr(other, "_labels", []))
        else:
            return NotImplemented
        if len(other_sig) != len(self.signature):
            raise ValueError(
                f"Subtracao exige tensores com o mesmo rank ({len(self.signature)} vs {len(other_sig)})."
            )
        if other_space is not self.tensor.space:
            raise ValueError("Tensores pertencem a TensorSpaces distintos.")
        labels = list(self.labels)
        if other_labels:
            if set(other_labels) != set(labels):
                raise ValueError("Subtracao exige os mesmos rotulos.")
            perm = [other_labels.index(lab) for lab in labels]
            other_components = sp.permutedims(other_components, perm)
            other_sig = tuple(other_sig[i] for i in perm)
        if other_sig != self.signature:
            raise ValueError("Assinaturas diferentes; subtracao exige mesma assinatura.")
        arr = self.components - other_components
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __rsub__(self, other):
        if not isinstance(other, IndexedTensor):
            return NotImplemented
        return other.__sub__(self)

    def __truediv__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = self.components / sp.sympify(other)
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = sp.sympify(other) / self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
        return NotImplemented


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


class TensorFactory:
    def __init__(self, space):
        self.space = space

    def __call__(self, tensor, index=None, name=None, label=None):
        return TensorSpace.tensor(self.space, tensor, index=index, name=name, label=label)

    def coord_index(self, names):
        return self.space.coord_index(names)

    def from_function(self, func, signature, name=None, label=None):
        return self.space.from_function(func, signature, name=name, label=label)

    def from_array(self, array, signature, name=None, label=None):
        return self.space.from_array(array, signature, name=name, label=label)

    def generic(self, name, signature, coords=None, label=None):
        return self.space.generic(name, signature, coords=coords, label=label)

    def zeros(self, signature, name=None, label=None):
        return self.space.zeros(signature, name=name, label=label)

    def scalar(self, expr, name=None, label=None):
        return self.space.scalar(expr, name=name, label=label)


class _IndexBuilder:
    def __init__(self, tensor, up=None, down=None, has_up=False, has_down=False):
        self.tensor = tensor
        self.up = [None] * tensor.rank if up is None else list(up)
        self.down = [None] * tensor.rank if down is None else list(down)
        self.has_up = has_up
        self.has_down = has_down

    def up(self, *labels):
        labels = _complete_indices_right(labels, self.tensor.rank)
        if self.has_down:
            return self.tensor.idx(up=labels, down=self.down)
        return _IndexBuilder(self.tensor, up=labels, down=self.down, has_up=True, has_down=self.has_down)

    def down(self, *labels):
        labels = _complete_indices_right(labels, self.tensor.rank)
        if self.has_up:
            return self.tensor.idx(up=self.up, down=labels)
        return _IndexBuilder(self.tensor, up=self.up, down=labels, has_up=self.has_up, has_down=True)


def _parse_label(label, space):
    if label is NO_LABEL:
        return NO_LABEL
    if label in ("_", ".", "empty", None):
        return None
    if isinstance(label, Index):
        return label.name
    if isinstance(label, str):
        return label.strip()
    return str(label)


def _complete_indices_right(labels, rank):
    labels = list(labels)
    if len(labels) > rank:
        raise ValueError("Numero de indices nao bate com o rank do tensor.")
    labels.extend([None] * (rank - len(labels)))
    return labels


def _parse_tensor_token(token):
    name = ""
    seq = []
    i = 0
    while i < len(token) and token[i].isalnum():
        name += token[i]
        i += 1
    while i < len(token):
        if token[i] in ("^", "_"):
            var = token[i]
            i += 1
            if i < len(token) and token[i] == "{":
                block, i = _read_block(token, i)
                labels = _split_indices(block)
            else:
                start = i
                while i < len(token) and token[i].isalnum():
                    i += 1
                if start == i:
                    raise ValueError("Esperado indice apos '^' ou '_'.")
                labels = [token[start:i]]
            for lab in labels:
                seq.append((var, lab))
        else:
            i += 1
    return name, seq


def _expand_indices(rank, up_labels=None, down_labels=None):
    if down_labels is None and up_labels is not None:
        if all(isinstance(item, tuple) and len(item) == 2 for item in up_labels):
            seq = list(up_labels)
            if len(seq) != rank:
                raise ValueError("Numero de indices nao bate com o rank do tensor.")
            up_full = [None] * rank
            down_full = [None] * rank
            for i, (var, lab) in enumerate(seq):
                if var == "^":
                    up_full[i] = lab
                elif var == "_":
                    down_full[i] = lab
                else:
                    raise ValueError(f"Variancia invalida: {var!r}. Use '^' ou '_'.")
            return up_full, down_full
    up_labels = [] if up_labels is None else list(up_labels)
    down_labels = [] if down_labels is None else list(down_labels)
    if len(up_labels) + len(down_labels) != rank:
        raise ValueError("Numero de indices nao bate com o rank do tensor.")
    up_full = [None] * rank
    down_full = [None] * rank
    for i, lab in enumerate(up_labels):
        up_full[i] = lab
    for i, lab in enumerate(down_labels):
        down_full[len(up_labels) + i] = lab
    return up_full, down_full


def _read_block(s, i):
    if s[i] != "{":
        raise ValueError("Esperado '{' na expressao de indices.")
    depth = 0
    start = i + 1
    i += 1
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            if depth == 0:
                return s[start:i], i + 1
            depth -= 1
        i += 1
    raise ValueError("Bloco de indices nao fechado.")


def _split_indices(block):
    out = []
    for part in block.split(","):
        part = part.strip()
        if part in ("", "_", ".", "empty"):
            out.append(NO_LABEL)
        else:
            out.append(part)
    return out


class SpaceTime(TensorSpace):
    pass


class Manifold(TensorSpace):
    pass


def greek(name):
    mapping = {
        "alpha": "𝛼",
        "beta": "𝛽",
        "gamma": "𝛾",
        "delta": "𝛿",
        "epsilon": "𝜀",
        "zeta": "𝜁",
        "eta": "𝜂",
        "theta": "𝜃",
        "iota": "𝜄",
        "kappa": "𝜅",
        "lambda": "𝜆",
        "mu": "𝜇",
        "nu": "𝜈",
        "xi": "𝜉",
        "omicron": "𝜊",
        "pi": "𝜋",
        "rho": "𝜌",
        "sigma": "𝜎",
        "tau": "𝜏",
        "upsilon": "𝜐",
        "phi": "𝜑",
        "chi": "𝜒",
        "psi": "𝜓",
        "omega": "𝜔",
        "partial": "𝜕",
        "varepsilon": "𝜖",
        "vartheta": "𝜗",
        "varpi": "𝜘",
        "varphi": "𝜙",
        "varrho": "𝜚",
        "varsigma": "𝜛",
    }
    key = str(name).strip().lower()
    if key not in mapping:
        raise ValueError(f"Letra grega desconhecida: {name!r}.")
    return mapping[key]


def example_indexing():
    x, y = sp.symbols("x y")
    space = TensorSpace(2, (x, y))
    a, b, c = space.index("a b c")
    T = space.generic("T", (U, D))
    g = space.generic("g", (U, U))
    return T[U(a), D(b)] * g[U(b), U(c)]
