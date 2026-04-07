from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json, os
from supabase import create_client

def get_sb():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_ANON_KEY"]
    )

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Extract model_id from path: /api/model/author/modelname
            path     = urlparse(self.path).path
            # Everything after /api/model/
            model_id = path.split("/api/model/", 1)[-1].strip("/")

            if not model_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"model_id required"}')
                return

            sb   = get_sb()
            meta = sb.table("models").select("*").eq("model_id", model_id).execute()

            if not meta.data:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Model not found: {model_id}"}).encode())
                return

            res  = sb.table("latest_results").select("*").eq("model_id", model_id).execute()
            code = sb.table("model_code").select("*").eq("model_id", model_id).execute()

            payload = {
                "model":   meta.data[0],
                "results": res.data or [],
                "code":    code.data or [],
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
