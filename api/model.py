import json, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from supabase import create_client

class app(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            path     = urlparse(self.path).path
            model_id = path.split("/api/model/", 1)[-1].strip("/")

            sb   = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
            meta = sb.table("models").select("*").eq("model_id", model_id).execute()

            if not meta.data:
                body = json.dumps({"error": f"Not found: {model_id}"}).encode()
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return

            res  = sb.table("latest_results").select("*").eq("model_id", model_id).execute()
            code = sb.table("model_code").select("*").eq("model_id", model_id).execute()

            body = json.dumps({
                "model":   meta.data[0],
                "results": res.data or [],
                "code":    code.data or [],
            }).encode()
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