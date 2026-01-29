from __future__ import annotations

import array
import ast
import hashlib
import json
import math
import mmap
import os
import struct
import sys
from pathlib import Path
from typing import Any

from .utils import tokenize

SparseVector = list[tuple[int, float]]


def _stable_hash_bytes(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def _hash_index_and_sign(feature: str, *, dims: int, salt: str) -> tuple[int, float]:
    if dims <= 0:
        raise ValueError(f"dims must be > 0 (got {dims})")
    h = _stable_hash_bytes(f"{salt}:{feature}")
    idx = int.from_bytes(h[:4], "little", signed=False) % dims
    sign = 1.0 if (h[4] & 1) == 0 else -1.0
    return idx, sign


def l2_normalize_sparse(pairs: SparseVector) -> SparseVector:
    if not pairs:
        return []
    norm_sq = 0.0
    for _, v in pairs:
        norm_sq += float(v) * float(v)
    if norm_sq <= 0.0:
        return []
    inv = 1.0 / math.sqrt(norm_sq)
    return [(i, float(v) * inv) for i, v in pairs]


def sparse_dot(a: SparseVector, b: SparseVector) -> float:
    """Dot product of two sparse vectors with sorted indices."""
    i = 0
    j = 0
    out = 0.0
    while i < len(a) and j < len(b):
        ai, av = a[i]
        bi, bv = b[j]
        if ai == bi:
            out += float(av) * float(bv)
            i += 1
            j += 1
        elif ai < bi:
            i += 1
        else:
            j += 1
    return out


def hash_embed(
    text: str,
    *,
    dims: int,
    salt: str = "hash-embed-v1",
    include_char_ngrams: bool = True,
    char_ngram: int = 3,
    char_ngram_weight: float = 0.5,
) -> SparseVector:
    """Deterministic hashing-based embedding for offline PoC use.

    Notes:
    - Not a semantic embedding model; intended to make vector pipelines testable
      without external dependencies.
    - Output is L2-normalized.
    """
    tokens = tokenize(text)
    if not tokens:
        return []

    acc: dict[int, float] = {}

    def _add(feature: str, weight: float) -> None:
        idx, sign = _hash_index_and_sign(feature, dims=dims, salt=salt)
        acc[idx] = acc.get(idx, 0.0) + (sign * float(weight))

    for t in tokens:
        _add(f"tok:{t}", 1.0)
        if include_char_ngrams and char_ngram > 0:
            s = t.strip().lower()
            if len(s) >= char_ngram:
                for k in range(0, len(s) - char_ngram + 1):
                    _add(f"chr:{s[k : k + char_ngram]}", char_ngram_weight)

    pairs: SparseVector = sorted(acc.items(), key=lambda kv: kv[0])
    return l2_normalize_sparse(pairs)


def coerce_query_vector(
    query_vector: Any,
    *,
    dims: int,
    normalize: bool = True,
) -> SparseVector:
    """Accept dense (list[float]) or sparse ([[i,v],...]) query vectors."""
    if query_vector is None:
        return []

    if isinstance(query_vector, list) and query_vector and all(
        isinstance(x, (int, float)) for x in query_vector
    ):
        dense = [float(x) for x in query_vector]
        if len(dense) != int(dims):
            raise ValueError(f"query_vector length {len(dense)} != dims {dims}")
        pairs = [(i, v) for i, v in enumerate(dense) if float(v) != 0.0]
        pairs.sort(key=lambda kv: kv[0])
        return l2_normalize_sparse(pairs) if normalize else pairs

    if isinstance(query_vector, list):
        pairs: SparseVector = []
        for item in query_vector:
            if (
                isinstance(item, (list, tuple))
                and len(item) == 2
                and isinstance(item[0], int)
                and isinstance(item[1], (int, float))
            ):
                i = int(item[0])
                if i < 0 or i >= int(dims):
                    raise ValueError(f"sparse index out of range: {i} (dims={dims})")
                pairs.append((i, float(item[1])))
            else:
                raise ValueError("invalid sparse query_vector entry; expected [index,value]")
        pairs.sort(key=lambda kv: kv[0])
        # de-dupe by summing collisions
        compact: SparseVector = []
        for i, v in pairs:
            if compact and compact[-1][0] == i:
                compact[-1] = (i, compact[-1][1] + v)
            else:
                compact.append((i, v))
        return l2_normalize_sparse(compact) if normalize else compact

    raise ValueError("query_vector must be a dense list[float] or sparse [[i,v],...]")


def read_vectors_jsonl(
    path: Path,
    *,
    dims: int,
    normalize: bool = False,
) -> dict[str, SparseVector]:
    out: dict[str, SparseVector] = {}
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
            except Exception as e:
                raise ValueError(f"invalid JSONL at {path}:{line_no}: {e}") from e
            if not isinstance(rec, dict):
                continue
            cid = rec.get("chunk_id")
            vec = rec.get("vector")
            if not isinstance(cid, str) or not cid.strip():
                continue
            if vec is None:
                continue
            coerced = coerce_query_vector(vec, dims=int(dims), normalize=normalize)
            out[cid] = coerced
    return out


def write_vectors_jsonl(path: Path, vectors_by_id: dict[str, SparseVector]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for cid in sorted(vectors_by_id.keys()):
            f.write(json.dumps({"chunk_id": cid, "vector": vectors_by_id[cid]}, ensure_ascii=False) + "\n")


def _norm_dtype(dtype: str) -> str:
    d = str(dtype or "").strip().lower()
    if d in ("f4", "float32", "fp32"):
        return "float32"
    if d in ("f8", "float64", "fp64"):
        return "float64"
    raise ValueError(f"unsupported dtype: {dtype!r}")


def _norm_endianness(endianness: str) -> str:
    e = str(endianness or "").strip().lower()
    if e in ("little", "le", "<"):
        return "little"
    if e in ("big", "be", ">"):
        return "big"
    raise ValueError(f"unsupported endianness: {endianness!r}")


def _dtype_itemsize(dtype: str) -> int:
    d = _norm_dtype(dtype)
    return 4 if d == "float32" else 8


def _dtype_typecode(dtype: str) -> str:
    d = _norm_dtype(dtype)
    return "f" if d == "float32" else "d"


def _need_byteswap(*, endianness: str) -> bool:
    want_little = _norm_endianness(endianness) == "little"
    native_little = sys.byteorder == "little"
    return want_little != native_little


def _npy_descr(*, dtype: str, endianness: str) -> str:
    d = _norm_dtype(dtype)
    e = _norm_endianness(endianness)
    prefix = "<" if e == "little" else ">"
    return f"{prefix}{'f4' if d == 'float32' else 'f8'}"


def write_vectors_bin(
    path: Path,
    *,
    chunk_ids: list[str],
    vectors_by_id: dict[str, SparseVector],
    dims: int,
    dtype: str,
    endianness: str,
) -> None:
    """Write dense row-major vectors to a raw .bin payload (no header)."""
    if int(dims) <= 0:
        raise ValueError(f"dims must be > 0 (got {dims})")

    typecode = _dtype_typecode(dtype)
    swap = _need_byteswap(endianness=endianness)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for cid in chunk_ids:
            row = array.array(typecode, [0.0]) * int(dims)
            for i, v in vectors_by_id.get(cid, []) or []:
                if 0 <= int(i) < int(dims):
                    row[int(i)] = float(v)
            if swap:
                row.byteswap()
            f.write(row.tobytes())


def write_vectors_npy(
    path: Path,
    *,
    chunk_ids: list[str],
    vectors_by_id: dict[str, SparseVector],
    dims: int,
    dtype: str,
    endianness: str,
) -> None:
    """Write dense row-major vectors to a NumPy .npy file (v1.0 header)."""
    if int(dims) <= 0:
        raise ValueError(f"dims must be > 0 (got {dims})")

    n_rows = int(len(chunk_ids))
    d = int(dims)
    descr = _npy_descr(dtype=dtype, endianness=endianness)

    # NumPy v1.0 header is a Python literal dict padded to 16-byte alignment.
    header_dict = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': ({n_rows}, {d}), }}"
    preamble_len = 6 + 2 + 2  # magic + version + header_len(uint16)
    pad_len = (16 - ((preamble_len + len(header_dict) + 1) % 16)) % 16
    header = (header_dict + (" " * pad_len) + "\n").encode("ascii")
    if len(header) >= 65536:
        raise ValueError("npy header too large for v1.0")

    typecode = _dtype_typecode(dtype)
    swap = _need_byteswap(endianness=endianness)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(b"\x93NUMPY")
        f.write(bytes([1, 0]))  # v1.0
        f.write(struct.pack("<H", len(header)))
        f.write(header)

        for cid in chunk_ids:
            row = array.array(typecode, [0.0]) * d
            for i, v in vectors_by_id.get(cid, []) or []:
                if 0 <= int(i) < d:
                    row[int(i)] = float(v)
            if swap:
                row.byteswap()
            f.write(row.tobytes())


def _read_npy_header(path: Path) -> tuple[dict[str, Any], int]:
    with path.open("rb") as f:
        magic = f.read(6)
        if magic != b"\x93NUMPY":
            raise ValueError(f"invalid npy magic at {path}")
        ver = f.read(2)
        if len(ver) != 2:
            raise ValueError(f"truncated npy header at {path}")
        major, minor = ver[0], ver[1]
        if (major, minor) == (1, 0):
            header_len_bytes = f.read(2)
            if len(header_len_bytes) != 2:
                raise ValueError(f"truncated npy header_len at {path}")
            header_len = struct.unpack("<H", header_len_bytes)[0]
        elif major in (2, 3):
            header_len_bytes = f.read(4)
            if len(header_len_bytes) != 4:
                raise ValueError(f"truncated npy header_len at {path}")
            header_len = struct.unpack("<I", header_len_bytes)[0]
        else:
            raise ValueError(f"unsupported npy version {major}.{minor} at {path}")

        header_raw = f.read(int(header_len))
        if len(header_raw) != int(header_len):
            raise ValueError(f"truncated npy header at {path}")
        try:
            header_text = header_raw.decode("latin1")
            header = ast.literal_eval(header_text)
        except Exception as e:
            raise ValueError(f"failed to parse npy header at {path}: {e}") from e
        if not isinstance(header, dict):
            raise ValueError(f"invalid npy header type at {path}: {type(header)}")
        data_offset = f.tell()
        return header, int(data_offset)


def _dtype_endianness_from_npy_descr(descr: str) -> tuple[str, str]:
    s = str(descr or "")
    if len(s) < 3:
        raise ValueError(f"invalid npy descr: {descr!r}")
    endian_ch = s[0]
    type_ch = s[1]
    size_s = s[2:]
    if type_ch != "f":
        raise ValueError(f"unsupported npy descr type: {descr!r}")
    try:
        size = int(size_s)
    except Exception as e:
        raise ValueError(f"invalid npy descr size: {descr!r}") from e
    dtype = "float32" if size == 4 else "float64" if size == 8 else None
    if dtype is None:
        raise ValueError(f"unsupported npy float size: {size} ({descr!r})")
    if endian_ch == "<":
        endianness = "little"
    elif endian_ch == ">":
        endianness = "big"
    elif endian_ch == "|":
        # Not applicable; treat as native.
        endianness = "little" if sys.byteorder == "little" else "big"
    else:
        raise ValueError(f"unsupported npy endianness: {descr!r}")
    return dtype, endianness


def read_vectors_dense_payload_as_sparse(
    path: Path,
    *,
    chunk_ids: list[str],
    dims: int,
    dtype: str,
    endianness: str,
    normalize: bool = False,
) -> dict[str, SparseVector]:
    """Read dense .bin/.npy vectors and convert them to sparse pairs.

    Intended for incremental update paths; for retrieval, prefer direct scoring over the dense payload.
    """
    if int(dims) <= 0:
        raise ValueError(f"dims must be > 0 (got {dims})")

    d = int(dims)
    want_dtype = _norm_dtype(dtype)
    want_end = _norm_endianness(endianness)

    suffix = path.suffix.lower()
    data_offset = 0
    if suffix == ".npy":
        header, data_offset = _read_npy_header(path)
        if bool(header.get("fortran_order")):
            raise ValueError(f"npy fortran_order must be false at {path}")
        shape = header.get("shape")
        if not (isinstance(shape, tuple) and len(shape) == 2):
            raise ValueError(f"npy shape must be a 2-tuple at {path} (got {shape!r})")
        n_rows, n_cols = int(shape[0]), int(shape[1])
        if n_cols != d:
            raise ValueError(f"npy dims mismatch at {path}: shape[1]={n_cols} != dims={d}")
        file_dtype, file_end = _dtype_endianness_from_npy_descr(str(header.get("descr") or ""))
        if file_dtype != want_dtype or file_end != want_end:
            raise ValueError(
                f"npy dtype/endianness mismatch at {path}: file={file_dtype}/{file_end} cfg={want_dtype}/{want_end}"
            )
        if n_rows != len(chunk_ids):
            raise ValueError(f"npy row count mismatch at {path}: shape[0]={n_rows} != chunks={len(chunk_ids)}")
    elif suffix == ".bin":
        itemsize = _dtype_itemsize(want_dtype)
        expected = int(len(chunk_ids)) * d * int(itemsize)
        try:
            size = int(os.path.getsize(path))
        except Exception:
            size = -1
        if size >= 0 and size != expected:
            raise ValueError(f"bin size mismatch at {path}: {size} != expected {expected}")
    else:
        raise ValueError(f"unsupported dense vector payload: {path}")

    typecode = _dtype_typecode(want_dtype)
    swap = _need_byteswap(endianness=want_end)

    out: dict[str, SparseVector] = {}
    with path.open("rb") as f:
        if data_offset:
            f.seek(int(data_offset))
        buf = array.array(typecode)
        try:
            buf.fromfile(f, int(len(chunk_ids)) * d)
        except EOFError as e:
            raise ValueError(f"truncated vector payload at {path}") from e

    if swap:
        buf.byteswap()

    for row_idx, cid in enumerate(chunk_ids):
        base = int(row_idx) * d
        pairs: SparseVector = []
        for i in range(d):
            v = float(buf[base + i])
            if v != 0.0:
                pairs.append((i, v))
        out[cid] = l2_normalize_sparse(pairs) if normalize else pairs
    return out


class DenseVectorReader:
    """Memory-mapped dense vector payload reader for fast dot products with sparse queries."""

    def __init__(
        self,
        path: Path,
        *,
        dims: int,
        dtype: str,
        endianness: str,
        data_offset: int = 0,
        rows: int | None = None,
    ) -> None:
        if int(dims) <= 0:
            raise ValueError(f"dims must be > 0 (got {dims})")
        self.path = path
        self.dims = int(dims)
        self.dtype = _norm_dtype(dtype)
        self.endianness = _norm_endianness(endianness)
        self.data_offset = int(max(0, data_offset))
        self.itemsize = _dtype_itemsize(self.dtype)
        prefix = "<" if self.endianness == "little" else ">"
        fmt = "f" if self.dtype == "float32" else "d"
        self._unpack = struct.Struct(prefix + fmt)
        self._rows_hint = int(rows) if rows is not None else None
        self._f = None
        self._mm = None

    def __enter__(self) -> "DenseVectorReader":
        self._f = self.path.open("rb")
        self._mm = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_READ)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        try:
            if self._mm is not None:
                self._mm.close()
        finally:
            self._mm = None
            if self._f is not None:
                self._f.close()
            self._f = None

    @property
    def rows(self) -> int:
        if self._rows_hint is not None:
            return self._rows_hint
        if self._mm is None:
            raise RuntimeError("DenseVectorReader not opened")
        nbytes = max(0, len(self._mm) - self.data_offset)
        denom = self.dims * self.itemsize
        return int(nbytes // denom) if denom > 0 else 0

    def dot_sparse(self, row: int, qvec: SparseVector) -> float:
        if self._mm is None:
            raise RuntimeError("DenseVectorReader not opened")
        r = int(row)
        if r < 0:
            return 0.0
        base = self.data_offset + (r * self.dims * self.itemsize)
        if base < self.data_offset:
            return 0.0
        out = 0.0
        for i, qv in qvec:
            ii = int(i)
            if ii < 0 or ii >= self.dims:
                continue
            off = base + (ii * self.itemsize)
            try:
                dv = self._unpack.unpack_from(self._mm, off)[0]
            except Exception:
                return out
            out += float(dv) * float(qv)
        return float(out)


def open_dense_vector_reader_from_file(
    path: Path,
    *,
    dims: int,
    dtype: str,
    endianness: str,
) -> DenseVectorReader:
    """Create a DenseVectorReader for either .bin or .npy dense payloads."""
    suffix = path.suffix.lower()
    if suffix == ".bin":
        return DenseVectorReader(path, dims=dims, dtype=dtype, endianness=endianness, data_offset=0, rows=None)
    if suffix == ".npy":
        header, data_offset = _read_npy_header(path)
        if bool(header.get("fortran_order")):
            raise ValueError(f"npy fortran_order must be false at {path}")
        shape = header.get("shape")
        if not (isinstance(shape, tuple) and len(shape) == 2):
            raise ValueError(f"npy shape must be a 2-tuple at {path} (got {shape!r})")
        n_rows, n_cols = int(shape[0]), int(shape[1])
        if int(n_cols) != int(dims):
            raise ValueError(f"npy dims mismatch at {path}: shape[1]={n_cols} != dims={dims}")
        file_dtype, file_end = _dtype_endianness_from_npy_descr(str(header.get("descr") or ""))
        want_dtype = _norm_dtype(dtype)
        want_end = _norm_endianness(endianness)
        if file_dtype != want_dtype or file_end != want_end:
            raise ValueError(
                f"npy dtype/endianness mismatch at {path}: file={file_dtype}/{file_end} cfg={want_dtype}/{want_end}"
            )
        return DenseVectorReader(
            path,
            dims=dims,
            dtype=want_dtype,
            endianness=want_end,
            data_offset=data_offset,
            rows=n_rows,
        )
    raise ValueError(f"unsupported dense vector payload: {path}")
