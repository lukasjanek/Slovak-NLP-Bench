import os
from flask import Flask, jsonify
from supabase import create_client

app = Flask(__name__)

def get_sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

@app.route("/api/model/<path:model_id>")
def model(model_id):
    try:
        sb   = get_sb()
        meta = sb.table("models").select("*").eq("model_id", model_id).execute()
        if not meta.data:
            return jsonify({"error": f"Not found: {model_id}"}), 404
        res  = sb.table("latest_results").select("*").eq("model_id", model_id).execute()
        code = sb.table("model_code").select("*").eq("model_id", model_id).execute()
        resp = jsonify({"model": meta.data[0], "results": res.data or [], "code": code.data or []})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500