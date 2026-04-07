import os
from flask import Flask, jsonify, request
from supabase import create_client

app = Flask(__name__)

def get_sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

def sort_key(task, r):
    if task == "qa":
        v = r.get("bertscore_f1") if r.get("qa_subtask") == "generative" else r.get("token_f1")
        return v or 0
    if task == "classification": return r.get("f1_weighted") or 0
    if task == "fill_mask":      return r.get("top1_accuracy") or 0
    if task == "generation":     return -(r.get("perplexity") or 999999)
    return 0

@app.route("/api/leaderboard/<task>")
def leaderboard(task):
    try:
        rows = get_sb().table("latest_results").select("*").eq("task", task).execute().data or []
        rows.sort(key=lambda r: sort_key(task, r), reverse=True)
        resp = jsonify(rows)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500