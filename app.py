"""
app.py — Slovak Benchmark Flask Backend
Run: python app.py  →  http://localhost:5000
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Always resolve static folder relative to THIS file, not the working directory
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_ANON_KEY']
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route('/api/tasks')
def tasks():
    return jsonify([
        {'id':'qa',            'label':'Question Answering','icon':'❓',
         'description':'Extractive & generative QA on SKQuAD',
         'dataset':'lukasjanek/skquad','metric':'Token F1'},
        {'id':'classification','label':'Sentiment','icon':'💬',
         'description':'3-class sentiment on SentiSK',
         'dataset':'lukasjanek/senti-sk','metric':'F1 Weighted'},
        {'id':'fill_mask',     'label':'Fill Mask','icon':'🔤',
         'description':'Masked token prediction on SlovakSum',
         'dataset':'lukasjanek/slovaksum (validation)','metric':'Top-1 Accuracy'},
        {'id':'generation',    'label':'Text Generation','icon':'✍️',
         'description':'Perplexity & BPC on SlovakSum',
         'dataset':'lukasjanek/slovaksum (test)','metric':'Perplexity ↓'},
    ])


@app.route('/api/leaderboard/<task>')
def leaderboard(task):
    resp = sb.table('latest_results').select('*').eq('task', task).execute()
    rows = resp.data or []
    def sort_key(r):
        if task == 'qa':
            v = r.get('bertscore_f1') if r.get('qa_subtask') == 'generative' else r.get('token_f1')
            return v or 0
        if task == 'classification': return r.get('f1_weighted') or 0
        if task == 'fill_mask':      return r.get('top1_accuracy') or 0
        if task == 'generation':     return -(r.get('perplexity') or 999999)
        return 0
    rows.sort(key=sort_key, reverse=True)
    return jsonify(rows)


@app.route('/api/model/<path:model_id>')
def model_detail(model_id):
    meta = sb.table('models').select('*').eq('model_id', model_id).execute()
    if not meta.data:
        return jsonify({'error': 'Model not found'}), 404
    res  = sb.table('latest_results').select('*').eq('model_id', model_id).execute()
    code = sb.table('model_code').select('*').eq('model_id', model_id).execute()
    return jsonify({'model': meta.data[0], 'results': res.data or [], 'code': code.data or []})


# ── Static files — all served explicitly from absolute STATIC_DIR ─────────────

@app.route('/')
def home():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/leaderboard.html')
def leaderboard_page():
    return send_from_directory(STATIC_DIR, 'leaderboard.html')

@app.route('/model.html')
def model_page():
    return send_from_directory(STATIC_DIR, 'model.html')

@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory(os.path.join(STATIC_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory(os.path.join(STATIC_DIR, 'js'), filename)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
