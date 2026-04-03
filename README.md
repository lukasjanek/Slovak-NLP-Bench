# 🔓 SK·BENCH web portal
---
Flask backend + React frontend, which loads results from the Supabase cloud database and displays them in the form of rankings and detailed model cards

```
slovak-benchmark-site/
├── app.py                  
├── push_to_supabase.py     
├── push_notebooks.py        
├── requirements.txt
├── notebooks/              — models as colab notebooks (.ipynb)
└── static/
    ├── index.html          — landing page (splash + task selection)
    ├── leaderboard.html    — leaderboard for selected task (?task=qa)
    ├── model.html          — model detail (?model=gerulata/slovakbert&task=fill_mask)
    ├── css/
    │   └── main.css        — all styles (CSS variables, layout, components)
    └── js/
        └── api.js          — shared js help functions (API constants, formating)
```

---

---

## ⚙️ Requirements

```
flask>=3.0.0
flask-cors>=4.0.0
supabase>=2.0.0
storage3==0.7.7
huggingface-hub>=0.20.0
python-dotenv>=1.0.0
```

##  🚀 How to run web
---
Change to main directory folder with cd ...
```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```
