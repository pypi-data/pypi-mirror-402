from __future__ import annotations

import dataclasses
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_CAMEL_PART_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")

# Small, pragmatic stopword set for code/text; keep conservative.
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by",
    "for", "from", "has", "have", "in", "into", "is", "it",
    "of", "on", "or", "s", "such", "t", "that", "the", "their",
    "then", "there", "these", "they", "this", "to", "was", "will",
    "with", "without", "we", "you", "your", "our",
    # Question-ish / instruction words
    "where", "what", "which", "who", "whom", "whose", "when", "why", "how",
    "does", "do", "did", "can", "could", "would", "should", "may", "might", "must",
    "please", "explain", "describe", "summarize",
    "implemented", "implement", "implementation",
    "reference", "references", "referenced",
    "located", "location",
    # Code-ish
    "true", "false", "none", "null", "nil", "var", "let", "const",
    "function", "class", "def", "return", "import", "export",
    "public", "private", "protected", "static", "final", "void",
}

def load_dotenv(path: Path, *, override: bool = False) -> dict[str, str]:
    """Load environment variables from a .env file.

    - Does not override existing env vars unless override=True.
    - Supports `KEY=VALUE` and `export KEY=VALUE`.
    - Ignores blank lines and lines starting with `#`.
    """
    try:
        if not path.exists():
            return {}
    except Exception:
        return {}

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    loaded: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        quote = value[0] if value else ""
        if len(value) >= 2 and quote in ("'", '"') and value.endswith(quote):
            value = value[1:-1]

        if not override and key in os.environ:
            continue
        os.environ[key] = value
        loaded[key] = value
    return loaded

def rfc3339_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, obj: Any, *, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")

def write_jsonl(path: Path, records: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def write_yaml(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))

def normalize_newlines(text: str) -> str:
    # Canonicalize CRLF/CR to LF for portability and stable hashing across OSes.
    return text.replace("\r\n", "\n").replace("\r", "\n")

def read_text_file(path: Path) -> str:
    return normalize_newlines(path.read_text(encoding="utf-8", errors="replace"))

def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def looks_like_text(path: Path, *, max_probe_bytes: int = 8192) -> bool:
    """Heuristic: treat as text if it decodes as UTF-8 and contains no NUL bytes in probe."""
    try:
        data = path.read_bytes()[:max_probe_bytes]
    except Exception:
        return False
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True

def iter_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            yield Path(dirpath) / fn

def normalize_posix(path: Path) -> str:
    return path.as_posix()

def resolve_under_root(root: Path, rel_path: str) -> Path:
    """Resolve a manifest-relative path safely under a root directory."""
    root = root.resolve()
    candidate = Path(rel_path)
    if candidate.is_absolute():
        raise ValueError(f"expected a relative path under {root}, got absolute: {rel_path}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"path escapes root {root}: {rel_path}")
    return resolved

def _pattern_variants(pat: str) -> list[str]:
    """Generate pragmatic pattern variants to approximate gitignore-like '**/' behavior.

    In gitignore semantics, '**/*' matches files in the repository root *and* nested directories.
    Python's fnmatch treats '**/*' as requiring a '/' in the candidate string.
    We therefore also test a variant with a leading '**/' stripped.
    """
    variants = [pat]
    if pat.startswith("./"):
        variants.append(pat[2:])
    if pat.startswith("**/"):
        variants.append(pat[3:])
    if pat.startswith("/"):
        variants.append(pat[1:])
    # de-dup while preserving order
    out: list[str] = []
    for v in variants:
        if v not in out and v:
            out.append(v)
    return out

def match_any(path_posix: str, patterns: Sequence[str]) -> bool:
    for pat in patterns:
        for v in _pattern_variants(pat):
            if fnmatch.fnmatch(path_posix, v):
                return True
    return False

def within_scope(path_posix: str, include: Sequence[str] | None, exclude: Sequence[str] | None) -> bool:
    include = list(include or [])
    exclude = list(exclude or [])
    if include and not match_any(path_posix, include):
        return False
    if exclude and match_any(path_posix, exclude):
        return False
    return True

def tokenize(text: str) -> list[str]:
    # Keep the baseline regex tokenization (spec v1.0 Section 6.1.1.2) but add a small
    # amount of identifier-aware splitting for codebases (camelCase, snake_case,
    # and letter/digit boundaries). Always keep the original whole-token form so
    # older indexes remain queryable.
    raw_tokens = _TOKEN_RE.findall(text)

    out: list[str] = []
    seen: set[str] = set()

    def _add(t: str) -> None:
        s = t.strip().lower()
        if not s or len(s) < 2 or s in _STOPWORDS:
            return
        if s in seen:
            return
        seen.add(s)
        out.append(s)

    for raw in raw_tokens:
        _add(raw)

        if "_" in raw:
            for part in raw.split("_"):
                _add(part)

        # CamelCase / digit splitting (preserve acronyms reasonably).
        parts = _CAMEL_PART_RE.findall(raw)
        if len(parts) > 1:
            for part in parts:
                _add(part)

    return out

def chunk_lines_around_match(lines: list[str], match_line_idx: int, *, window: int = 3) -> tuple[int, int, str]:
    start = max(0, match_line_idx - window)
    end = min(len(lines), match_line_idx + window + 1)
    snippet = "".join(lines[start:end])
    return start + 1, end, snippet  # line numbers 1-based

@dataclasses.dataclass(frozen=True)
class Citation:
    """Citation object per ECP spec Section 6.3."""
    source_id: str  # Required by spec
    source_type: str
    uri: str
    revision: dict
    artifact_path: str | None = None
    chunk_id: str | None = None
    retrieved_at: str | None = None
    loc: dict[str, Any] | None = None
    line_start: int | None = None
    line_end: int | None = None
    chunk_hash: str | None = None
    classification: str | None = None
    license: str | None = None

def citation_to_dict(c: Citation) -> dict:
    d = dataclasses.asdict(c)
    # Remove nulls for compactness.
    return {k: v for k, v in d.items() if v is not None}
