# ECP Reference Implementation (v1.0)

This repository provides a **minimal, publishable reference implementation** for the **Expert Context Pack (ECP) v1.0** specification.

See the spec: `spec/ECP-SPEC.md`.

## Docs

- `docs/PILOT-PLAYBOOK.md` - step-by-step guide to create, validate, run, and publish packs.
- `examples/README.md` - index of included example packs and demo scripts.
- `CONTRIBUTING.md` - contribution guidelines.

It is intended to demonstrate:

- **Persistent expert context** stored inside a Skill directory (backward-compatible with Agent Skills).
- **Incremental refresh** of context artifacts (git-diff where available; filesystem diff fallback).
- **Grounded answers** with **portable citations** (file path + revision + line ranges).
- **Eval-gated maintenance**: refresh runs eval suites and can rollback on failure.

## What this is (and is not)

**This is:**
- A pragmatic baseline runtime and CLI (`ecpctl`) to build, refresh, and query an ECP-enabled skill.
- A keyword + portable vector indexer/retriever suitable for a PoC (vector supports local hashing embeddings and optional caller-provided query vectors).
- A harness to run ECP eval suites.
- An optional MCP-compatible stdio server exposing `expert.*` tools (`ecpctl mcp`).

**This is not:**
- A full agent runtime or IDE integration.
- A production embedding model or vector DB integration (the PoC supports a portable `vector-index-v1` artifact, plus optional caller-provided query vectors for real embeddings).

ECP is aimed at portable, offline, and auditable expert context. It complements hosted file-search tools and centralized eval platforms by packaging evidence, provenance, and maintenance controls directly with the skill so packs can be validated and moved across runtimes without vendor lock-in.

## Repository layout

- `spec/` - the ECP spec (v1.0) and JSON Schemas (source of truth for this repo)
- `src/ecp_reference/` - the reference implementation
- `examples/` - example ECP-enabled skills and demo corpora (see `examples/README.md`)

## Installation

Python 3.10+ is recommended.

```bash
python -m pip install -e .
ecpctl --help
```

Or without editable mode:

```bash
python -m pip install .
```

## Quickstart (runs out-of-the-box)

1) Build the example skill index against the included demo repo (`examples/realworld_repo`):

```bash
# From repository root:
ecpctl validate --skill examples/codebase-expert
ecpctl build --skill examples/codebase-expert
ecpctl status --skill examples/codebase-expert
```

2) Query it:

```bash
ecpctl query --skill examples/codebase-expert --source-id repo "Which modules handle authentication?"
```

3) Refresh it (incremental if possible):

```bash
ecpctl refresh --dry-run --skill examples/codebase-expert
ecpctl refresh --skill examples/codebase-expert
```

4) Run evals explicitly:

```bash
ecpctl run-evals --skill examples/codebase-expert
```

To run stricter, offline conformance checks (response shape + citation integrity):

```bash
ecpctl run-evals --skill examples/codebase-expert --suite-id conformance
```

For a scripted end-to-end run (including packaging and retention), see `examples/demo-codebase-expert.ps1` or `examples/demo-codebase-expert.sh`.

## Offline conformance pack (self-contained)

`examples/ecp-conformance-pack` bundles its source corpus under the skill root, so it can be packaged and verified by others without cloning anything:

```bash
ecpctl validate --with-artifacts --skill examples/ecp-conformance-pack
ecpctl query --skill examples/ecp-conformance-pack "Which modules handle authentication?"
ecpctl run-evals --skill examples/ecp-conformance-pack --suite-id conformance
```

`examples/ecp-vector-payloads-pack` is another offline pack that demonstrates `vector-index-v1` portability (JSONL vs NPY/BIN payloads):

```bash
ecpctl validate --with-artifacts --skill examples/ecp-vector-payloads-pack
ecpctl query --skill examples/ecp-vector-payloads-pack "Which modules handle authentication?"
ecpctl run-evals --skill examples/ecp-vector-payloads-pack --suite-id conformance
```

For a full "package -> unzip -> query -> evals" run, see `examples/demo-ecp-conformance-pack.ps1` or `examples/demo-ecp-conformance-pack.sh`.

## CLI overview

All commands support `--json` for machine-readable output (useful for tool calls).

Common commands:
- `ecpctl validate --skill <skill_dir>`: schema-validate `SKILL.md`, `expert/EXPERT.yaml`, `expert/maintenance/policy.json`, and eval suites.
- `ecpctl validate --strict --skill <skill_dir>`: additionally enforce portability/provenance constraints and (when `profile` is recognized) strict profile requirements intended for CI gating.
- `ecpctl validate --with-artifacts --skill <skill_dir>`: also schema-validate referenced index artifacts (`index.json`, `index_data.json`, `chunks.jsonl`) when present (use `--max-chunks` to limit `chunks.jsonl` validation; `0` = all).
- `ecpctl status --skill <skill_dir>`: show configured sources, artifacts, and eval suites.
- `ecpctl set-source --skill <skill_dir> --uri file:///abs/path/to/repo`: point a source at a local repo (PoC convenience; use `--source-id` if needed).
- `ecpctl build --skill <skill_dir>`: build context artifacts (use `--rebuild` to force a full rebuild; `--dry-run` to preview; runs evals unless `--no-evals`).
- `ecpctl refresh --skill <skill_dir>`: refresh artifacts (incremental if possible; use `--rebuild` to force rebuild; `--dry-run` to preview; runs evals unless `--no-evals`).
- `ecpctl query --skill <skill_dir> "<question>"`: retrieve + synthesize an answer with citations (common filters: `--source-id`, `--path-prefix`; tuning: `--top-k`, `--mode`; optional `--query-vector-file` for vector indexes; optional `--llm openrouter` with `--llm-model` / `--llm-timeout-seconds`).
- `ecpctl run-evals --skill <skill_dir>`: run eval suites (defaults to `policy.validation.eval_suites`).
- `ecpctl mcp --skill <skill_dir>`: run an MCP-compatible stdio server exposing `expert.*` tools.
- `ecpctl pack --skill <skill_dir> --out <zip>`: create a distributable ZIP package (defaults: excludes `expert/logs/**` and `**/.backup/**`; use `--include-logs` / `--include-backups` to include; deterministic by default)
- `ecpctl verify-pack --package <zip>`: verify file hashes and schema-validate a packaged skill (`--no-validate` skips schema validation after extraction)
- `ecpctl prune --skill <skill_dir>`: apply retention rules to backups/logs (best-effort)

Packaging note: for `profile: codebase` skills with `sources[].type: git`, `ecpctl pack` enforces commit pinning and refuses to package when `sources[].revision.commit` is missing or set to `HEAD` (run `ecpctl refresh` to record a concrete commit hash).

Generated artifacts live inside the skill directory under `expert/context/` (indexes, summaries) and `expert/logs/` (optional). `build`/`refresh` also update `sources[].revision` in `expert/EXPERT.yaml` so `as_of` is reproducible.

## Using this on a real repository

1) Copy `examples/codebase-expert` into your skill collection location.   

2) Point the expert source at your repository:

```bash
ecpctl set-source --skill /path/to/codebase-expert --uri file:///abs/path/to/your/repo
```

On Windows, file URIs typically look like `file:///C:/path/to/repo` (forward slashes).

3) Build and query:

```bash
ecpctl build --skill /path/to/codebase-expert
ecpctl query --skill /path/to/codebase-expert "Where is auth implemented?"
```

## Real-world demo: VeraCrypt + OpenRouter

This repository includes VeraCrypt skill templates:
- `examples/veracrypt-expert` (keyword index backend)
- `examples/veracrypt-expert-sqlite` (SQLite FTS backend)
- `examples/veracrypt-expert-hybrid-vector` (hybrid retrieval: vector + SQLite FTS; recommended)

For a scripted run, see `examples/demo-veracrypt-expert.ps1` or `examples/demo-veracrypt-expert.sh` (auto-selects hybrid vector+FTS when available).
The VeraCrypt repository is not bundled; clone it locally before running the demo.

1) Clone VeraCrypt (recommended sibling layout):

```bash
git clone https://github.com/veracrypt/VeraCrypt examples/VeraCrypt
```

If you cloned VeraCrypt elsewhere, point the skill at your checkout:

```bash
SKILL=examples/veracrypt-expert-hybrid-vector
ecpctl set-source --skill "$SKILL" --source-id repo --uri file:///abs/path/to/VeraCrypt
```

2) Build the expert context:

```bash
SKILL=examples/veracrypt-expert-hybrid-vector
ecpctl validate --skill "$SKILL"
ecpctl build --skill "$SKILL"
```

To force a full rebuild (even if an index already exists):

```bash
SKILL=examples/veracrypt-expert-hybrid-vector
ecpctl build --rebuild --skill "$SKILL"
```

3) Query it (local synthesizer, always offline):

```bash
SKILL=examples/veracrypt-expert-hybrid-vector
ecpctl query --skill "$SKILL" "Where is the main source code located?"
```

4) Query it with LLM synthesis via OpenRouter (citations still come from local context artifacts):

```bash
# Either export env vars (or put them in a `.env` file in the current directory):
export OPENROUTER_API_KEY="..."
export OPENROUTER_MODEL="xiaomi/mimo-v2-flash:free"
SKILL=examples/veracrypt-expert-hybrid-vector
ecpctl query --llm openrouter --skill "$SKILL" "Summarize the main components involved in mounting a volume."
```

PowerShell equivalent:

```powershell
$env:OPENROUTER_API_KEY="..."
$env:OPENROUTER_MODEL="xiaomi/mimo-v2-flash:free"
$skill="examples/veracrypt-expert-hybrid-vector"
ecpctl query --llm openrouter --skill $skill "Summarize the main components involved in mounting a volume."
```

`.env` example (auto-loaded from the current directory):

```dotenv
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=xiaomi/mimo-v2-flash:free
```

Notes:
- `ecpctl` auto-loads `.env` from the current directory (without overriding existing env vars).
- Avoid committing `.env` (this repo ignores it via `.gitignore`).
- `OPENROUTER_API_KEY` must be set for `--llm openrouter`.
- Remote LLM synthesis is blocked when `security.contains_secrets: true`, and is disabled by default unless `security.allow_remote_llm: true` is set in `expert/EXPERT.yaml`.
- The OpenRouter call sends the retrieved evidence snippets to OpenRouter. Do not enable it for sensitive repositories.
- `--llm openrouter` requires outbound HTTPS access to `openrouter.ai`.
- `ecpctl pack` refuses to package skills with `security.contains_secrets: true` unless `--allow-secrets` is explicitly set.

5) Refresh after updating the repo:

```bash
# Detect what would happen (incremental vs rebuild), without modifying artifacts:
SKILL=examples/veracrypt-expert-hybrid-vector
ecpctl refresh --dry-run --skill "$SKILL"

# Apply the refresh (runs evals and may rollback on failure per policy.json):
ecpctl refresh --skill "$SKILL"

# Force a full rebuild:
ecpctl refresh --rebuild --skill "$SKILL"
```

## Implementation notes

- **Index type:** chunked keyword index (`keyword-index-v2`) or SQLite FTS-backed keyword index (`sqlite-fts-index-v1`, set `backend: sqlite-fts` on the index entry).
- **Multiple indexes:** declare multiple `context.artifacts.indexes[]`; the runtime retrieves from each and fuses results via Reciprocal Rank Fusion (RRF). `ecpctl build/refresh` builds all configured indexes (see `examples/codebase-expert-hybrid`).
- **Chunking:** `line-window` with configurable `max_chars`/`overlap_chars` via `context.artifacts.indexes[].chunking` in `expert/EXPERT.yaml`.
- **Multiple sources:** all `sources[]` are indexed into one combined index; use `ecpctl query --source-id <id>` and/or `ecpctl query --path-prefix <prefix>` to restrict retrieval.
- **Incremental refresh detection (per source):**
  - For `git` sources in a git worktree, uses `git diff --name-status <old_commit>..HEAD` when possible.
  - Otherwise, uses a stored `file_manifest.json` and diffs sha256 hashes.

- **Rollback behavior:** controlled by `expert/maintenance/policy.json`.
- **Summary citations:** in `--mode summarized`, citations may use `source_id: ecp_artifacts` to indicate evidence came from `expert/context/summaries/*` (derived artifacts under the skill root).

- **Query logging:** when enabled, stores `question_sha256` by default; set `logs.store_question: true` in `expert/EXPERT.yaml` to also store the raw question (suppressed if `security.contains_secrets: true`). In `mode: persistent`, the runtime also stores `question` and `answer` (unless suppressed).

## How to integrate with an LLM agent (typical PoC pattern)

Most host agents can invoke a local CLI tool. Treat `ecpctl query --json` as the tool call, e.g.:

```bash
ecpctl query --json --skill /path/to/codebase-expert "What modules handle authentication?"
```

To have `ecpctl` synthesize the `answer` field with OpenRouter (instead of the local summarizer), add:

```bash
ecpctl query --llm openrouter --json --skill /path/to/codebase-expert "What modules handle authentication?"
```

If your host supports MCP, you can also run the stdio server:

```bash
ecpctl mcp --skill /path/to/codebase-expert
```

This exposes `expert.query`, `expert.refresh`, `expert.run_evals`, and `expert.status`.

The output contains:
- `answer`
- `as_of`
- `citations[]`
- `chunks[]` (snippets with scores)

This lets your host agent:
- display the answer,
- cite the evidence,
- ask follow-ups or open files in an IDE.

## License

Apache-2.0 (see `LICENSE`).
