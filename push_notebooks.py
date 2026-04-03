"""
push_notebooks.py
==================
Reads your model use-notebooks (.ipynb files), extracts the code cell
that contains the actual model usage (cell index 1 — the second cell),
strips boilerplate (Drive mount, cache clear), and pushes to Supabase.
"""

import os, json, glob, argparse, re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

SKIP_PATTERNS = [
    r"^from google\.colab import drive",
    r"^drive\.mount",
    r"^!rm -rf.*cache",
    r"^print\(['\"]Hugging Face cache",
    r"^# Mount",
    r"^# Clear",
]

TASK_KEYWORDS = {
    "fill_mask":      "fill_mask",
    "fillmask":       "fill_mask",
    "masked":         "fill_mask",
    "classification": "classification",
    "sentiment":      "classification",
    "qa":             "qa",
    "question":       "qa",
    "generation":     "generation",
    "causal":         "generation",
    "gpt":            "generation",
}


# ── DB model ID resolver ──────────────────────────────────────────────────────

_db_model_ids = None   # cached after first fetch

def _normalise_id(s: str) -> str:
    """Lowercase and treat hyphens/underscores as the same for matching."""
    return s.lower().replace("-", "_")


def resolve_model_id(raw: str) -> str | None:
    """
    Given a model ID parsed from a filename (may have wrong case or
    hyphen/underscore mix), find the exact model_id from the DB.

    e.g. 'dgurgurov/xlm_r_slovak_sentiment' → 'DGurgurov/xlm-r_slovak_sentiment'
    """
    global _db_model_ids

    if _db_model_ids is None:
        try:
            from supabase import create_client
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            resp = sb.table("models").select("model_id").execute()
            _db_model_ids = [r["model_id"] for r in (resp.data or [])]
            print(f"  📋 Loaded {len(_db_model_ids)} model IDs from DB")
        except Exception as e:
            print(f"  ⚠️  Could not fetch model IDs from DB: {e}")
            _db_model_ids = []

    raw_norm = _normalise_id(raw)
    for db_id in _db_model_ids:
        if _normalise_id(db_id) == raw_norm:
            return db_id   # exact normalised match

    return None   # no match found


# ── Code cell extraction ──────────────────────────────────────────────────────

def extract_code_cell(nb_path: str, cell_index: int = 1) -> str | None:
    try:
        nb = json.load(open(nb_path, encoding="utf-8"))
    except Exception as e:
        print(f"  ❌ Could not read {nb_path}: {e}")
        return None

    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]

    if cell_index >= len(code_cells):
        print(f"  ⚠️  Only {len(code_cells)} code cells found, requested index {cell_index}")
        return None

    source = code_cells[cell_index].get("source", [])
    if isinstance(source, list):
        source = "".join(source)

    lines = source.splitlines()
    clean = []
    for line in lines:
        if not any(re.match(p, line.strip()) for p in SKIP_PATTERNS):
            clean.append(line)

    while clean and not clean[0].strip():
        clean.pop(0)
    while clean and not clean[-1].strip():
        clean.pop()

    return "\n".join(clean) if clean else None


# ── Filename parser ───────────────────────────────────────────────────────────

def parse_filename(fname: str) -> tuple[str | None, str | None]:
    """
    Parse author__modelname__task.ipynb.
    Returns (raw_model_id, task) — raw_model_id may need resolve_model_id() call.
    """
    stem       = Path(fname).stem
    stem_lower = stem.lower()
    parts      = stem.split("__")

    # Detect task keyword (case-insensitive)
    task = None
    for keyword, task_id in TASK_KEYWORDS.items():
        if keyword in stem_lower:
            task = task_id
            break

    if len(parts) >= 2:
        # Preserve original case, keep underscores — DB lookup will resolve exact ID
        raw_model_id = f"{parts[0]}/{parts[1]}"
        return raw_model_id, task

    return None, task


# ── Push to Supabase ──────────────────────────────────────────────────────────

def push_snippet(model_id: str, task: str, code: str,
                 colab_url: str = None, dry_run: bool = False) -> bool:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    row = {"model_id": model_id, "task": task, "code": code}
    if colab_url:
        row["colab_url"] = colab_url

    if dry_run:
        print(f"  [DRY RUN] Would upsert: {model_id} / {task}")
        print(f"  Code preview ({len(code)} chars):")
        print("  " + "\n  ".join(code.splitlines()[:5]) + "\n  ...")
        return True

    try:
        sb.table("model_code").upsert(row, on_conflict="model_id,task").execute()
        print(f"  ✅ Pushed: {model_id} / {task}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to push {model_id}/{task}: {e}")
        return False


# ── Process directory ─────────────────────────────────────────────────────────

def process_directory(notebooks_dir: str, cell_index: int = 1,
                      dry_run: bool = False):
    files = glob.glob(os.path.join(notebooks_dir, "*.ipynb"))
    if not files:
        print(f"⚠️  No .ipynb files found in {notebooks_dir}")
        return

    print(f"Found {len(files)} notebooks.\n")
    ok = skipped = 0

    for fpath in sorted(files):
        fname = Path(fpath).name
        print(f"📓 {fname}")

        raw_model_id, task = parse_filename(fname)

        if not raw_model_id:
            print(f"  ⚠️  Could not parse model_id — rename to author__modelname__task.ipynb")
            skipped += 1
            continue
        if not task:
            print(f"  ⚠️  Could not detect task — add keyword: fill_mask, qa, classification, generation")
            skipped += 1
            continue

        # Resolve exact model_id from DB
        model_id = resolve_model_id(raw_model_id)
        if not model_id:
            print(f"  ⚠️  No DB match for '{raw_model_id}' — model may not have been benchmarked yet.")
            print(f"      Run push_to_supabase.py first, or use --model flag to specify the exact ID.")
            skipped += 1
            continue

        print(f"  model={model_id}  task={task}")

        code = extract_code_cell(fpath, cell_index)
        if not code:
            print(f"  ⚠️  No usable code in cell {cell_index} — skipping.")
            skipped += 1
            continue

        if push_snippet(model_id, task, code, dry_run=dry_run):
            ok += 1
        else:
            skipped += 1

    print(f"\n✅ Done. {ok} pushed, {skipped} skipped.")


def process_single(fpath: str, model_id: str, task: str,
                   colab_url: str = None, cell_index: int = 1,
                   dry_run: bool = False):
    print(f"📓 {Path(fpath).name}  →  {model_id} / {task}")
    code = extract_code_cell(fpath, cell_index)
    if not code:
        print("  ❌ No usable code found.")
        return
    push_snippet(model_id, task, code, colab_url=colab_url, dry_run=dry_run)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebooks", help="Directory containing .ipynb files")
    parser.add_argument("--file",      help="Single .ipynb file")
    parser.add_argument("--model",     help="Exact model ID (e.g. DGurgurov/xlm-r_slovak_sentiment)")
    parser.add_argument("--task",      help="Task: qa | classification | fill_mask | generation")
    parser.add_argument("--colab",     help="Google Colab URL")
    parser.add_argument("--cell",      type=int, default=1,
                        help="Code cell index to extract (default=1)")
    parser.add_argument("--dry-run",   action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if args.file:
        if not args.model or not args.task:
            print("❌ --file requires --model and --task")
        else:
            process_single(args.file, args.model, args.task,
                           colab_url=args.colab,
                           cell_index=args.cell,
                           dry_run=args.dry_run)
    elif args.notebooks:
        process_directory(args.notebooks, cell_index=args.cell, dry_run=args.dry_run)
    else:
        parser.print_help()