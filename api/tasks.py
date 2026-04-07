from flask import Flask, jsonify

app = Flask(__name__)

TASKS = [
    {"id":"qa",            "label":"Question Answering","icon":"❓",
     "description":"Extractive & generative QA on SKQuAD",
     "dataset":"lukasjanek/skquad","metric":"Token F1"},
    {"id":"classification","label":"Sentiment","icon":"💬",
     "description":"3-class sentiment on SentiSK",
     "dataset":"lukasjanek/senti-sk","metric":"F1 Weighted"},
    {"id":"fill_mask",     "label":"Fill Mask","icon":"🔤",
     "description":"Masked token prediction on SlovakSum",
     "dataset":"lukasjanek/slovaksum (validation)","metric":"Top-1 Accuracy"},
    {"id":"generation",    "label":"Text Generation","icon":"✍️",
     "description":"Perplexity & BPC on SlovakSum",
     "dataset":"lukasjanek/slovaksum (test)","metric":"Perplexity ↓"},
]

@app.route("/api/tasks")
@app.route("/api/tasks/")
def tasks():
    resp = jsonify(TASKS)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp