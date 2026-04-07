import json, os
from supabase import create_client

def handler(request):
    try:
        # task is the last path segment: /api/leaderboard/qa
        task = request["path"].rstrip("/").split("/")[-1]

        sb   = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        resp = sb.table("latest_results").select("*").eq("task", task).execute()
        rows = resp.data or []

        def sort_key(r):
            if task == "qa":
                v = r.get("bertscore_f1") if r.get("qa_subtask") == "generative" else r.get("token_f1")
                return v or 0
            if task == "classification": return r.get("f1_weighted") or 0
            if task == "fill_mask":      return r.get("top1_accuracy") or 0
            if task == "generation":     return -(r.get("perplexity") or 999999)
            return 0

        rows.sort(key=sort_key, reverse=True)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(rows)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
