// api.js — pure JS, no JSX
// Shared constants, helpers and translations for all pages

//const API    = 'http://localhost:5000/api';
const API = '/api';
const GITHUB = 'https://github.com/lukasjanek/Slovak-Mini-Benchmark';

function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

const fmt = (v, d = 2) => v == null ? '—' : Number(v).toFixed(d);

function pillClass(val, task) {
  if (val == null) return '';
  if (task === 'generation') return val < 20 ? 'high' : val < 100 ? 'mid' : 'low';
  return val >= 65 ? 'high' : val >= 35 ? 'mid' : 'low';
}

function primaryMetric(row, task) {
  if (task === 'qa')             return { val: row.qa_subtask === 'generative' ? row.bertscore_f1 : row.token_f1 };
  if (task === 'classification') return { val: row.f1_weighted   };
  if (task === 'fill_mask')      return { val: row.top1_accuracy  };
  if (task === 'generation')     return { val: row.perplexity     };
  return { val: null };
}

// ── Language persistence ──────────────────────────────────────────────────────
function getSavedLang() {
  try { return localStorage.getItem('skbench_lang') || 'en'; } catch { return 'en'; }
}
function saveLang(lang) {
  try { localStorage.setItem('skbench_lang', lang); } catch {}
}

// ── Translations ──────────────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    tasksLabel:'TASKS', home:'Home', sourceCode:'source code & docs',
    benchmarkDatasets:'Benchmark Datasets', langToggle:'SK',
    splashTag:'SLOVAK NLP BENCHMARK', splashH1a:'Find the right model',
    splashH1b:'for', splashH1em:'Slovak language',
    splashP:'Open benchmark evaluating language models on Slovak NLP tasks. All evaluations are reproducible — source code and methodology available on GitHub. Select a task from the sidebar to explore results.',
    modelsCount:'models', datasetLabel:'Dataset', primaryMetricLbl:'Primary metric',
    methodologyLink:'methodology ↗', colModel:'MODEL', colPrimary:'PRIMARY',
    colType:'TYPE', colRating:'RATING', colParams:'PARAMS', unknownTask:'Unknown task',
    backBtn:'← Back to leaderboard', modelInfo:'MODEL INFO',
    mName:'Name', mArchitecture:'Architecture', mType:'Type',
    mParameters:'Parameters', mLanguage:'Language', scoresLabel:'SCORES',
    mQaType:'QA Type', mModelClasses:'Model Classes', mDatasetClasses:'Dataset Classes',
    mSamples:'Samples evaluated', mEvalMode:'Eval Mode',
    viewOnHF:'View Files on HuggingFace', openColab:'Open in Google Colab',
    interactiveNb:'interactive notebook', ghMethodology:'methodology & source code',
    aboutLabel:'ABOUT', noSnippet:'no snippet',
    noCode:'# No code snippet available yet.\n# Check the HuggingFace repo for usage examples.',
    unreliableWarn:'⚠️ Scores may be unreliable — model was pre-trained without EOS signal.',
    loading:'Loading...', noData:'No data.',
    taskLabels:{ qa:'Question Answering', classification:'Sentiment', fill_mask:'Fill Mask', generation:'Text Generation' },
    taskDescs:{ qa:'Extractive & generative QA on SKQuAD', classification:'3-class sentiment on SentiSK', fill_mask:'Masked token prediction on SlovakSum', generation:'Perplexity & BPC on SlovakSum' },
    taskMetrics:{ qa:'Token F1', classification:'F1 Weighted', fill_mask:'Top-1 Accuracy', generation:'Perplexity ↓' },
  },
  sk: {
    tasksLabel:'ÚLOHY', home:'Domov', sourceCode:'zdrojový kód & dokumentácia',
    benchmarkDatasets:'Datasety benchmarku', langToggle:'EN',
    splashTag:'SLOVENSKÝ NLP BENCHMARK', splashH1a:'Nájdite správny model',
    splashH1b:'pre', splashH1em:'slovenský jazyk',
    splashP:'Otvorený benchmark na porovnávanie jazykových modelov pre slovenčinu. Všetky vyhodnotenia sú reprodukovateľné — zdrojový kód a metodika sú dostupné na GitHub. Vyberte úlohu zo sidebaru a preskúmajte výsledky.',
    modelsCount:'modelov', datasetLabel:'Dataset', primaryMetricLbl:'Primárna metrika',
    methodologyLink:'metodika ↗', colModel:'MODEL', colPrimary:'PRIMÁRNE',
    colType:'TYP', colRating:'HODNOTENIE', colParams:'PARAMETRE', unknownTask:'Neznáma úloha',
    backBtn:'← Späť na rebríček', modelInfo:'INFO O MODELI',
    mName:'Názov', mArchitecture:'Architektúra', mType:'Typ',
    mParameters:'Parametre', mLanguage:'Jazyk', scoresLabel:'SKÓRE',
    mQaType:'Typ QA', mModelClasses:'Triedy modelu', mDatasetClasses:'Triedy datasetu',
    mSamples:'Vyhodnotených vzoriek', mEvalMode:'Mód hodnotenia',
    viewOnHF:'Zobraziť súbory na HuggingFace', openColab:'Otvoriť v Google Colab',
    interactiveNb:'interaktívny notebook', ghMethodology:'metodika & zdrojový kód',
    aboutLabel:'O MODELI', noSnippet:'bez kódu',
    noCode:'# Kód zatiaľ nie je k dispozícii.\n# Pozrite si repozitár modelu na HuggingFace.',
    unreliableWarn:'⚠️ Skóre môže byť nespoľahlivé — model bol predtrénovaný bez EOS signálu.',
    loading:'Načítavanie...', noData:'Žiadne dáta.',
    taskLabels:{ qa:'Otázky a odpovede', classification:'Sentimentová analýza', fill_mask:'Dopĺňanie slov', generation:'Generovanie textu' },
    taskDescs:{ qa:'Extraktívne & generatívne QA na SKQuAD', classification:'3-triedna sentimentová analýza na SentiSK', fill_mask:'Predikcia maskovaného tokenu na SlovakSum', generation:'Perplexita & BPC na SlovakSum' },
    taskMetrics:{ qa:'Token F1', classification:'F1 Weighted', fill_mask:'Top-1 Presnosť', generation:'Perplexita ↓' },
  },
};

function t(lang, key) {
  return (TRANSLATIONS[lang] || TRANSLATIONS.en)[key] ?? key;
}

function translateTask(task, lang) {
  const tr = TRANSLATIONS[lang] || TRANSLATIONS.en;
  return {
    ...task,
    label:       tr.taskLabels[task.id]  || task.label,
    description: tr.taskDescs[task.id]  || task.description,
    metric:      tr.taskMetrics[task.id] || task.metric,
  };
}
