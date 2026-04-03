# 🔓 SK·BENCH web portal
---
Flask backend + React frontend, which loads results from the Supabase cloud database and displays them in the form of rankings and detailed model cards

```
slovak-benchmark-site/
├── app.py                  
├── push_to_supabase.py     
├── push_notebooks.py        
├── requirements.txt
├── notebooks/              — použitie modelov ako Colab notebooky (.ipynb)
└── static/
    ├── index.html          — domovská stránka (splash + výber úlohy)
    ├── leaderboard.html    — rebríček pre vybranú úlohu (?task=qa)
    ├── model.html          — detail modelu (?model=gerulata/slovakbert&task=fill_mask)
    ├── css/
    │   └── main.css        — všetky zdieľané štýly (CSS premenné, layout, komponenty)
    └── js/
        └── api.js          — zdieľané JS pomocné funkcie (API konštanty, formátovanie)
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

##  🚀 Spustenie webového portálu
---
Change to main directory folder with cd ...
```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```
