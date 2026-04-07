from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, os
from supabase import create_client

def get_sb():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_ANON_KEY"]
    )

def sort_key(task):
    def _key(r):
        if task == "qa":
            v = r.get("bertscore_f1") if r.get("qa_subtask") == "generative" else r.get("token_f1")
            return v or 0
        if task == "classification": return r.get("f1_weighted") or 0
        if task == "fill_mask":      return r.get("top1_accuracy") or 0
        if task == "generation":     return -(r.get("perplexity") or 999999)
        return 0
    return _key

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # task comes from the URL path: /api/leaderboard/qa
            path = urlparse(self.path).path
            task = path.rstrip("/").split("/")[-1]

            sb   = get_sb()
            resp = sb.table("latest_results").select("*").eq("task", task).execute()
            rows = resp.data or []
            rows.sort(key=sort_key(task), reverse=True)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(rows).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
