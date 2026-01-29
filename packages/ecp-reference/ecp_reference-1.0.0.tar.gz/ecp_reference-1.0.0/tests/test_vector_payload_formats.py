from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ecp_reference.errors import QueryError
from ecp_reference.indexer import SourceSpec, build_vector_index_multi, load_vector_index
from ecp_reference.retriever import retrieve_vector
from ecp_reference.vectors import open_dense_vector_reader_from_file


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


class TestVectorPayloadFormats(unittest.TestCase):
    def test_vector_retrieval_matches_across_jsonl_bin_npy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td)
            repo = root / "repo"
            _write(repo / "auth.py", "def login(user, pw):\n    return user == 'ok'\n")
            _write(repo / "db.py", "def connect():\n    return 'db'\n")
            _write(repo / "README.md", "This repo implements login and db access.\n")

            src = SourceSpec(
                source_id="repo",
                source_type="filesystem",
                source_uri="repo",
                source_root=repo,
                include=["**/*"],
                exclude=[],
                revision={"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
            )

            embedding = {
                "model": "hash-embedding-v1",
                "provider": "local",
                "dimensions": 256,
                "params": {"salt": "test-hash-embed-v1"},
            }

            idx_jsonl = root / "vec-jsonl"
            idx_bin = root / "vec-bin"
            idx_npy = root / "vec-npy"

            build_vector_index_multi(
                index_id="vec-jsonl",
                sources=[src],
                out_dir=idx_jsonl,
                embedding=embedding,
                vector={
                    "metric": "cosine",
                    "vectors_path": "vectors.jsonl",
                    "vector_format": "sparse-jsonl-v1",
                },
            )
            build_vector_index_multi(
                index_id="vec-bin",
                sources=[src],
                out_dir=idx_bin,
                embedding=embedding,
                vector={
                    "metric": "cosine",
                    "vectors_path": "vectors.bin",
                    "vector_format": "dense-bin-v1",
                    "dtype": "float32",
                    "endianness": "little",
                    "encoding": "row-major",
                    "chunk_id_order": "chunk_id_lex",
                },
            )
            build_vector_index_multi(
                index_id="vec-npy",
                sources=[src],
                out_dir=idx_npy,
                embedding=embedding,
                vector={
                    "metric": "cosine",
                    "vectors_path": "vectors.npy",
                    "vector_format": "dense-npy-v1",
                    "dtype": "float32",
                    "endianness": "little",
                    "encoding": "row-major",
                    "chunk_id_order": "chunk_id_lex",
                },
            )

            source_roots = {"repo": repo}
            source_meta = {
                "repo": {
                    "source_type": "filesystem",
                    "uri": "repo",
                    "revision": {"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
                    "license": None,
                }
            }

            question = "Where is login implemented?"
            res_jsonl = retrieve_vector(
                index_dir=idx_jsonl,
                index_data=load_vector_index(idx_jsonl),
                source_roots=source_roots,
                source_meta=source_meta,
                classification=None,
                question=question,
                top_k=5,
            )
            res_bin = retrieve_vector(
                index_dir=idx_bin,
                index_data=load_vector_index(idx_bin),
                source_roots=source_roots,
                source_meta=source_meta,
                classification=None,
                question=question,
                top_k=5,
            )
            res_npy = retrieve_vector(
                index_dir=idx_npy,
                index_data=load_vector_index(idx_npy),
                source_roots=source_roots,
                source_meta=source_meta,
                classification=None,
                question=question,
                top_k=5,
            )

            ids_jsonl = [c.citation.chunk_id for c in res_jsonl]
            ids_bin = [c.citation.chunk_id for c in res_bin]
            ids_npy = [c.citation.chunk_id for c in res_npy]

            self.assertTrue(ids_jsonl, "expected at least one vector retrieval result")
            self.assertEqual(ids_jsonl, ids_bin)
            self.assertEqual(ids_jsonl, ids_npy)

            # Optional: sanity-check that scores are close for the top hit.
            top_scores = {
                "jsonl": float(res_jsonl[0].score),
                "bin": float(res_bin[0].score),
                "npy": float(res_npy[0].score),
            }
            self.assertLess(abs(top_scores["jsonl"] - top_scores["bin"]), 1e-4)
            self.assertLess(abs(top_scores["jsonl"] - top_scores["npy"]), 1e-4)

    def test_dense_bin_truncated_payload_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td)
            repo = root / "repo"
            _write(repo / "auth.py", "def login(user, pw):\n    return user == 'ok'\n")
            _write(repo / "README.md", "This repo implements login.\n")

            src = SourceSpec(
                source_id="repo",
                source_type="filesystem",
                source_uri="repo",
                source_root=repo,
                include=["**/*"],
                exclude=[],
                revision={"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
            )

            embedding = {
                "model": "hash-embedding-v1",
                "provider": "local",
                "dimensions": 256,
                "params": {"salt": "test-hash-embed-v1"},
            }

            idx_bin = root / "vec-bin"
            build_vector_index_multi(
                index_id="vec-bin",
                sources=[src],
                out_dir=idx_bin,
                embedding=embedding,
                vector={
                    "metric": "cosine",
                    "vectors_path": "vectors.bin",
                    "vector_format": "dense-bin-v1",
                    "dtype": "float32",
                    "endianness": "little",
                    "encoding": "row-major",
                    "chunk_id_order": "chunk_id_lex",
                },
            )

            # Truncate the payload by 1 byte so the row count no longer matches documents[].
            vpath = idx_bin / "vectors.bin"
            data = vpath.read_bytes()
            self.assertTrue(len(data) > 0)
            vpath.write_bytes(data[:-1])

            with self.assertRaises(QueryError) as ctx:
                retrieve_vector(
                    index_dir=idx_bin,
                    index_data=load_vector_index(idx_bin),
                    source_roots={"repo": repo},
                    source_meta={
                        "repo": {
                            "source_type": "filesystem",
                            "uri": "repo",
                            "revision": {"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
                            "license": None,
                        }
                    },
                    classification=None,
                    question="Where is login implemented?",
                    top_k=5,
                )
            self.assertIn("row count mismatch", str(ctx.exception).lower())

    def test_dense_npy_truncated_header_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td)
            repo = root / "repo"
            _write(repo / "auth.py", "def login(user, pw):\n    return user == 'ok'\n")

            src = SourceSpec(
                source_id="repo",
                source_type="filesystem",
                source_uri="repo",
                source_root=repo,
                include=["**/*"],
                exclude=[],
                revision={"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
            )

            embedding = {
                "model": "hash-embedding-v1",
                "provider": "local",
                "dimensions": 256,
                "params": {"salt": "test-hash-embed-v1"},
            }

            idx_npy = root / "vec-npy"
            build_vector_index_multi(
                index_id="vec-npy",
                sources=[src],
                out_dir=idx_npy,
                embedding=embedding,
                vector={
                    "metric": "cosine",
                    "vectors_path": "vectors.npy",
                    "vector_format": "dense-npy-v1",
                    "dtype": "float32",
                    "endianness": "little",
                    "encoding": "row-major",
                    "chunk_id_order": "chunk_id_lex",
                },
            )

            vpath = idx_npy / "vectors.npy"
            data = vpath.read_bytes()
            self.assertTrue(len(data) > 16)
            vpath.write_bytes(data[:16])

            with self.assertRaises(ValueError) as ctx:
                open_dense_vector_reader_from_file(
                    vpath,
                    dims=256,
                    dtype="float32",
                    endianness="little",
                )
            self.assertIn("truncated npy", str(ctx.exception).lower())

    def test_dense_npy_metadata_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td)
            repo = root / "repo"
            _write(repo / "auth.py", "def login(user, pw):\n    return user == 'ok'\n")

            src = SourceSpec(
                source_id="repo",
                source_type="filesystem",
                source_uri="repo",
                source_root=repo,
                include=["**/*"],
                exclude=[],
                revision={"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
            )

            embedding = {
                "model": "hash-embedding-v1",
                "provider": "local",
                "dimensions": 256,
                "params": {"salt": "test-hash-embed-v1"},
            }

            idx_npy = root / "vec-npy"
            build_vector_index_multi(
                index_id="vec-npy",
                sources=[src],
                out_dir=idx_npy,
                embedding=embedding,
                vector={
                    "metric": "cosine",
                    "vectors_path": "vectors.npy",
                    "vector_format": "dense-npy-v1",
                    "dtype": "float32",
                    "endianness": "little",
                    "encoding": "row-major",
                    "chunk_id_order": "chunk_id_lex",
                },
            )

            vpath = idx_npy / "vectors.npy"

            with self.assertRaises(ValueError) as ctx_dims:
                open_dense_vector_reader_from_file(vpath, dims=128, dtype="float32", endianness="little")
            self.assertIn("dims mismatch", str(ctx_dims.exception).lower())

            with self.assertRaises(ValueError) as ctx_dtype:
                open_dense_vector_reader_from_file(vpath, dims=256, dtype="float64", endianness="little")
            self.assertIn("dtype/endianness mismatch", str(ctx_dtype.exception).lower())
