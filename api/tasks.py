import json
from http.server import BaseHTTPRequestHandler

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

class app(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(TASKS).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)