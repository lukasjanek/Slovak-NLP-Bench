import json, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from supabase import create_client

def _sort_key(task):
    def _key(r):
        if task == "qa":
            v = r.get("bertscore_f1") if r.get("qa_subtask") == "generative" else r.get("token_f1")
            return v or 0
        if task == "classification": return r.get("f1_weighted") or 0
        if task == "fill_mask":      return r.get("top1_accuracy") or 0
        if task == "generation":     return -(r.get("perplexity") or 999999)
        return 0
    return _key

class app(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            task = urlparse(self.path).path.rstrip("/").split("/")[-1]
            sb   = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
            rows = sb.table("latest_results").select("*").eq("task", task).execute().data or []
            rows.sort(key=_sort_key(task), reverse=True)
            body = json.dumps(rows).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)