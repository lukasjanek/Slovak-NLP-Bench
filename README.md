# SK·BENCH web portal
Flask backend + React frontend, which loads results from the Supabase cloud database and displays them in the form of rankings and detailed model cards

```
slovak-benchmark-site/
├── app.py                  — Flask server, REST API endpointy, smerovanie statických stránok
├── push_to_supabase.py     — skript na nahratie výsledkov z JSON súborov do databázy
├── push_notebooks.py       — skript na extrakciu kódu z .ipynb notebookov a nahratie do DB
├── supabase_schema.sql     — SQL schéma pre Supabase (tabuľky, view, indexy)
├── requirements.txt
├── .env.example            — šablóna pre tajné kľúče (nikdy sa necommituje)
├── .gitignore
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

## Spustenie webového portálu
Change to main directory folder with cd ...

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```
