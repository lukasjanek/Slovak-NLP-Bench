"""
push_to_supabase.py
====================
"""

import os, json, glob, argparse, math
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()   # reads .env from current directory

# ── Config ────────────────────────────────────────────────────────────────────
# Keys are loaded from .env file — never hardcode them here
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]   # service_role — write access

GITHUB_REPO  = "https://github.com/lukasjanek/Slovak-Mini-Benchmark"


# ── HuggingFace metadata fetcher ──────────────────────────────────────────────

def fetch_hf_metadata(model_id: str) -> dict:
    """
    Fetch model metadata from HuggingFace Hub without downloading weights.
    Returns architecture, param count, language tags etc.
    """
    from huggingface_hub import hf_hub_download, list_repo_files
    import json as _json

    meta = {
        "architecture":    None,
        "param_count":     None,
        "param_count_raw": None,
        "language":        "sk",
    }

    # ── config.json → architecture ────────────────────────────────────────────
    try:
        cfg_path = hf_hub_download(model_id, "config.json")
        cfg      = _json.load(open(cfg_path, encoding="utf-8"))
        archs    = cfg.get("architectures", [])
        if archs:
            meta["architecture"] = archs[0]
        # language
        if cfg.get("language"):
            meta["language"] = cfg["language"] if isinstance(cfg["language"], str) \
                               else ",".join(cfg["language"])
    except Exception as e:
        print(f"    ⚠️  Could not read config.json: {e}")

    # ── Parameter count ───────────────────────────────────────────────────────
    # Try safetensors index first (most accurate)
    try:
        repo_files = set(list_repo_files(model_id))

        if "model.safetensors.index.json" in repo_files:
            idx_path    = hf_hub_download(model_id, "model.safetensors.index.json")
            idx         = _json.load(open(idx_path))
            total_bytes = sum(idx.get("metadata", {}).get("total_size", 0) for _ in [1])
            # Estimate params: assume fp16 = 2 bytes per param, fp32 = 4
            # Read dtype from config
            cfg_torch_dtype = _json.load(open(hf_hub_download(model_id, "config.json"))).get("torch_dtype", "float32")
            bytes_per_param = 2 if "16" in str(cfg_torch_dtype) else 4
            total_size_bytes = idx.get("metadata", {}).get("total_size", 0)
            if total_size_bytes:
                n_params = total_size_bytes // bytes_per_param
                meta["param_count_raw"] = n_params
                meta["param_count"]     = _fmt_params(n_params)

        elif "model.safetensors" in repo_files:
            # Single-file safetensors — parse header to count params
            try:
                import struct
                sf_path = hf_hub_download(model_id, "model.safetensors")
                with open(sf_path, "rb") as f:
                    header_len = struct.unpack("<Q", f.read(8))[0]
                    header     = _json.loads(f.read(header_len))
                n_params = sum(
                    math.prod(v["shape"])
                    for k, v in header.items()
                    if k != "__metadata__" and "shape" in v
                )
                meta["param_count_raw"] = n_params
                meta["param_count"]     = _fmt_params(n_params)
            except Exception as e2:
                print(f"    ⚠️  Could not parse safetensors header: {e2}")

    except Exception as e:
        print(f"    ⚠️  Could not determine param count: {e}")

    return meta


def _fmt_params(n: int) -> str:
    """Format parameter count as human-readable string: 125_000_000 → '125M'"""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{round(n / 1_000_000)}M"
    if n >= 1_000:
        return f"{round(n / 1_000)}K"
    return str(n)


# ── Model type mapping ────────────────────────────────────────────────────────

ARCH_TO_TYPE = {
    "ForQuestionAnswering":      "extractive",
    "ForSequenceClassification": "classification",
    "ForCausalLM":               "generative_causal",
    "ForConditionalGeneration":  "generative_seq2seq",
    "ForMaskedLM":               "masked",
}

def arch_to_type(arch: str | None) -> str | None:
    if not arch:
        return None
    for pattern, mtype in ARCH_TO_TYPE.items():
        if arch.endswith(pattern):
            return mtype
    return None


# ── Push to Supabase ─────────────────────────────────────────────────────────

def push_results(results_dir: str, dry_run: bool = False):
    from supabase import create_client

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✅ Connected to Supabase: {SUPABASE_URL}\n")

    files = sorted(glob.glob(os.path.join(results_dir, "*.json")))
    if not files:
        print(f"⚠️  No JSON files found in {results_dir}")
        return

    seen_models = {}   # model_id → already processed this session

    for fpath in files:
        try:
            data      = json.load(open(fpath, encoding="utf-8"))
            model_id  = data.get("model")
            timestamp = data.get("timestamp", "")
            results   = data.get("results", {})
            tasks_run = data.get("tasks_run", [])

            if not model_id:
                print(f"  ⚠️  Skipping {Path(fpath).name} — no model field")
                continue

            print(f"📦  {model_id}  [{', '.join(tasks_run)}]")

            # ── Upsert model record ──────────────────────────────────────────
            if model_id not in seen_models:
                print(f"    Fetching metadata from HuggingFace...")
                hf_meta  = fetch_hf_metadata(model_id)
                arch     = hf_meta.get("architecture")
                mtype    = arch_to_type(arch)
                hf_url   = f"https://huggingface.co/{model_id}/tree/main"
                display  = model_id.split("/")[-1]

                model_row = {
                    "model_id":        model_id,
                    "display_name":    display,
                    "architecture":    arch,
                    "model_type":      mtype,
                    "param_count":     hf_meta.get("param_count"),
                    "param_count_raw": hf_meta.get("param_count_raw"),
                    "hf_url":          hf_url,
                    "language":        hf_meta.get("language", "sk"),
                    "description":     f"Benchmarked on Slovak NLP Benchmark Mini. See {GITHUB_REPO}",
                    "github_url":      GITHUB_REPO,
                }

                print(f"    arch={arch} | type={mtype} | params={hf_meta.get('param_count')}")

                if not dry_run:
                    sb.table("models").upsert(model_row, on_conflict="model_id").execute()
                    print(f"    ✅ Model upserted.")
                else:
                    print(f"    [DRY RUN] Would upsert model: {model_row}")

                seen_models[model_id] = model_row

            # ── Insert result rows ───────────────────────────────────────────
            for task in tasks_run:
                task_data = results.get(task, {})
                if "error" in task_data:
                    print(f"    ⚠️  Skipping {task} — has error: {task_data['error']}")
                    continue

                result_row = {
                    "model_id":           model_id,
                    "task":               task,
                    "timestamp":          timestamp,
                    "n_samples":          task_data.get("n_samples"),

                    "token_f1":           task_data.get("token_f1"),
                    "exact_match":        task_data.get("exact_match"),
                    "bertscore_f1":       task_data.get("bertscore_f1"),
                    "qa_subtask":         task_data.get("subtask"),

                    "f1_weighted":        task_data.get("f1_weighted"),
                    "accuracy":           task_data.get("accuracy"),
                    "n_classes_model":    task_data.get("n_classes_model"),
                    "n_classes_dataset":  task_data.get("n_classes_dataset"),

                    "top1_accuracy":      task_data.get("top1_accuracy"),
                    "top5_accuracy":      task_data.get("top5_accuracy"),

                    "perplexity":         task_data.get("perplexity"),
                    "perplexity_rating":  task_data.get("perplexity_rating"),
                    "bpc":                task_data.get("bpc"),
                    "bpc_rating":         task_data.get("bpc_rating"),
                    "reliable":           task_data.get("reliable", True),
                    "eval_mode":          task_data.get("eval_mode"),

                    "overall_score":      results.get("overall_score"),
                    "raw_json":           json.dumps(task_data),
                }

                # Remove None values so Supabase doesn't complain about type mismatches
                result_row = {k: v for k, v in result_row.items() if v is not None}

                if not dry_run:
                    sb.table("benchmark_results").insert(result_row).execute()
                    print(f"    ✅ Result inserted: {task}")
                else:
                    primary = {k: result_row.get(k) for k in
                               ["task", "token_f1", "f1_weighted", "top1_accuracy", "perplexity"]}
                    print(f"    [DRY RUN] Would insert result: {primary}")

        except Exception as e:
            print(f"  ❌ Error processing {Path(fpath).name}: {e}")
            import traceback; traceback.print_exc()

    print(f"\n✅ Done. Processed {len(files)} files, {len(seen_models)} unique models.")


# ── Code snippet helper ───────────────────────────────────────────────────────

def push_code_snippet(model_id: str, task: str, code: str,
                      colab_url: str = None, dry_run: bool = False):

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    row = {
        "model_id":  model_id,
        "task":      task,
        "code":      code,
    }
    if colab_url:
        row["colab_url"] = colab_url

    if dry_run:
        print(f"[DRY RUN] Would upsert code for {model_id} / {task}")
        print(code[:200], "...")
        return

    sb.table("model_code").upsert(row, on_conflict="model_id,task").execute()
    print(f"✅ Code snippet saved: {model_id} / {task}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push benchmark results to Supabase")
    parser.add_argument("--results", required=True, help="Path to results directory")
    parser.add_argument("--dry-run", action="store_true",  help="Preview without writing")
    args = parser.parse_args()

    push_results(args.results, dry_run=args.dry_run)
