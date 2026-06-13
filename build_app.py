#!/usr/bin/env python3
"""
build_app.py — Japanese SRS Study App builder
==============================================
Run this script to regenerate index.html from the source JSON files.

  python3 build_app.py

Directory layout (relative to this script):
  study-app/
    build_app.py              <- this script
    index.html                <- generated output (open in any browser)
    data/
      vocab_pronouns_demonstratives.json
      vocab_countries.json
      vocab_family.json
      vocab_occupations.json
      vocab_time.json
      vocab_location.json
      verbs.json              <- includes all conjugated forms
      weekly_recap_*.json     <- one file per class session
    ../flashcards/
      adjectives_vocab.json   <- shared with flashcard printouts

To add new vocabulary: edit the relevant JSON file, then re-run this script.
To add a new weekly recap: create data/weekly_recap_YYYY_MM_DD.json, then re-run.
To add new verb conjugation forms: edit the CONJ_FORMS list in this script.

NOTE: Avoid apostrophes (') inside single-quoted JS strings in this template.
Use double-quotes ("...") for any JS string that may contain an apostrophe.
"""

import json, os, glob

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, 'data')
OUT_PATH = os.path.join(HERE, 'index.html')
ADJ_PATH = os.path.join(HERE, '..', 'flashcards', 'adjectives_vocab.json')

# ── Load all data files ───────────────────────────────────────────
def load(name):
    with open(os.path.join(DATA_DIR, name), encoding='utf-8') as f:
        return json.load(f)

pronouns  = load('vocab_pronouns_demonstratives.json')
countries = load('vocab_countries.json')
family    = load('vocab_family.json')
occs      = load('vocab_occupations.json')
time_v    = load('vocab_time.json')
location  = load('vocab_location.json')
verbs_d   = load('verbs.json')

with open(ADJ_PATH, encoding='utf-8') as f:
    adj_data = json.load(f)

# Load all weekly recaps (sorted by date)
recap_files = sorted(glob.glob(os.path.join(DATA_DIR, 'weekly_recap_*.json')))
recaps = [json.load(open(fp, encoding='utf-8')) for fp in recap_files]

# ── Helper: flatten groups into card list ─────────────────────────
def flatten(deck_data):
    cards = []
    for grp in deck_data.get('groups', []):
        for c in grp.get('cards', []):
            cards.append({
                'id':         c['id'],
                'front':      c['front'],
                'frontSub':   c.get('frontSub', ''),
                'frontLabel': c.get('frontLabel', ''),
                'back':       c['back'],
                'backSub':    c.get('backSub', ''),
                'notes':      c.get('notes', '')
            })
    return cards

# ── Build DECKS array ─────────────────────────────────────────────
decks = []

# 1. Vocab decks
for d in [pronouns, countries, family, occs, time_v, location]:
    decks.append({
        'id':    d['id'],
        'name':  d['name'],
        'icon':  d['icon'],
        'type':  'vocab',
        'cards': flatten(d)
    })

# 2. Adjective vocab decks
def adj_cards(cat):
    cards = []
    for w in cat['words']:
        cards.append({
            'id':         f"adj_{w['hiragana'].replace(' ','_').replace('/','_')}",
            'front':      w['hiragana'],
            'frontSub':   w['kanji'] if w['kanji'] != w['hiragana'] else '',
            'frontLabel': '',
            'back':       w['english'],
            'backSub':    w['romaji'],
            'notes':      w.get('notes', '')
        })
    return cards

for cat in adj_data['categories']:
    label = 'い' if cat['type'] == 'i' else 'な'
    decks.append({
        'id':    f"adj_{cat['type']}",
        'name':  f"{label}-Adjectives",
        'icon':  '🔤',
        'type':  'vocab',
        'cards': adj_cards(cat)
    })

# 3. Verb vocab deck
verb_type_labels = {'ru':'Ru-regular','u':'U-regular','suru':'する compound','irreg':'Irregular'}
verb_vocab_cards = []
for v in verbs_d['verbs']:
    verb_vocab_cards.append({
        'id':         f"vvoc_{v['id']}",
        'front':      v['dict'],
        'frontSub':   v['kanji'] if v['kanji'] != v['dict'] else '',
        'frontLabel': '',
        'back':       v['english'],
        'backSub':    '',
        'notes':      verb_type_labels[v['type']] + ((' — ' + v['notes']) if v.get('notes') else '')
    })
decks.append({'id':'verb_vocab','name':'Verbs (vocabulary)','icon':'🗣️','type':'vocab','cards':verb_vocab_cards})

# 4. Verb conjugation decks
CONJ_FORMS = [
    ('masu',  '→ polite present?',  'ます form',  'Polite, non-past'),
    ('masen', '→ polite negative?', 'ません form', 'Polite negative'),
    ('te',    '→ て form?',         'て form',    'Connects actions; requests (~てください); progressive (~ています)'),
    ('ta',    '→ past casual?',     'た form',    'Casual past tense; also used before から for past reason'),
]

rule_hints = {
    'ru':   {'masu':'stem + ます','masen':'stem + ません','te':'stem + て','ta':'stem + た'},
    'u':    {'masu':'i-row + ます','masen':'i-row + ません','te':'varies by ending','ta':'varies by ending'},
    'suru': {'masu':'~します','masen':'~しません','te':'~して','ta':'~した'},
    'irreg':{'masu':'irregular','masen':'irregular','te':'irregular','ta':'irregular'},
}

for form_key, question, form_name, form_desc in CONJ_FORMS:
    conj_cards = []
    for v in verbs_d['verbs']:
        hint  = rule_hints[v['type']][form_key]
        extra = v.get('notes','')
        conj_cards.append({
            'id':         f"vconj_{v['id']}_{form_key}",
            'front':      v['dict'],
            'frontSub':   v['english'],
            'frontLabel': question,
            'back':       v['forms'][form_key],
            'backSub':    '',
            'notes':      f"{verb_type_labels[v['type']]}: {hint}" + (f" — {extra}" if extra else '')
        })
    decks.append({
        'id':       f'verb_conj_{form_key}',
        'name':     f'Verb Conjugation — {form_name}',
        'icon':     '⚡',
        'type':     'conjugation',
        'formDesc': form_desc,
        'cards':    conj_cards
    })

# 5. Adjective conjugation decks

# ── i-adjective conjugation helper ────────────────────────────────
# The adjective いい / よい ("good") is irregular: its casual forms come from
# the stem よ (よくない / よかった / よくなかった), NOT いく-. Critically, any
# compound whose final element is this いい inherits the irregularity:
#   あたまがいい → あたまがよくない    なかがいい → なかがよくない
#   かっこいい  → かっこよくない
# These were previously rendered as あたまがくない / なかがくない / かっこくない,
# which is what Atsuko-sensei flagged.
#
# One trap: かわいい ("cute") also ends in いい but is a normal i-adjective and
# conjugates regularly (かわいくない, never かわよくない). It is listed as an
# explicit exception below. Add any future 〜いい words that are NOT "good".
#
# Second bug fixed here: the old code used hira.rstrip("い"), which strips ALL
# trailing い. For any word ending in double-い that over-stripped a kana
# (かわいい → かわ → かわくない). We now drop exactly ONE final い.
REGULAR_II_ADJECTIVES = {'かわいい'}  # end in いい but are NOT the irregular "good"

def i_adj_info(hira):
    """Return (forms_dict, is_irregular_good) for a casual i-adjective.

    Slash-separated entries (e.g. "しょっぱい / しおからい") conjugate from the
    first/primary form only.
    """
    primary = hira.split('/')[0].strip()
    is_good = (
        primary in ('いい', 'よい')
        or (primary.endswith(('いい', 'よい')) and primary not in REGULAR_II_ADJECTIVES)
    )
    if is_good:
        stem = (primary[:-2] if len(primary) >= 2 else '') + 'よ'
    else:
        stem = primary[:-1] if primary.endswith('い') else primary
    forms = {
        'neg_cas':     stem + 'くない',
        'past_cas':    stem + 'かった',
        'negpast_cas': stem + 'くなかった',
    }
    return forms, is_good

def make_adj_conj_cards(adj_type, form_key, question, rule_i, rule_na):
    cards = []
    for cat in adj_data['categories']:
        if cat['type'] != adj_type:
            continue
        for w in cat['words']:
            hira = w['hiragana']
            eng  = w['english']
            if adj_type == 'i':
                forms, is_good = i_adj_info(hira)
                answer = forms.get(form_key, '?')
                rule   = rule_i
                if is_good:
                    rule = 'Irregular: いい/よい (good) uses stem よ — よくない / よかった / よくなかった'
            else:
                primary = hira.split('/')[0].strip()
                answer = {'neg_pol': primary+'ではありません','past_pol': primary+'でした'}.get(form_key,'?')
                rule   = rule_na
            safe_id = hira.replace(' ','_').replace('/','_')
            cards.append({
                'id':         f"adjconj_{adj_type}_{safe_id}_{form_key}",
                'front':      hira,
                'frontSub':   eng,
                'frontLabel': question,
                'back':       answer,
                'backSub':    '',
                'notes':      rule
            })
    return cards

adj_conj_specs = [
    ('i',  'neg_cas',     '→ negative (casual)?',   'い → くない',         ''),
    ('i',  'past_cas',    '→ past tense (casual)?',  'い → かった',         ''),
    ('i',  'negpast_cas', '→ negative past?',        'い → くなかった',     ''),
    ('na', 'neg_pol',     '→ negative (polite)?',    '', 'adj + ではありません'),
    ('na', 'past_pol',    '→ past (polite)?',        '', 'adj + でした'),
]
for adj_type, form_key, question, rule_i, rule_na in adj_conj_specs:
    label = 'い' if adj_type == 'i' else 'な'
    form_readable = question.replace('→ ','').replace('?','').strip()
    decks.append({
        'id':    f'adj_conj_{adj_type}_{form_key}',
        'name':  f'{label}-Adj Conjugation — {form_readable}',
        'icon':  '🔄',
        'type':  'conjugation',
        'cards': make_adj_conj_cards(adj_type, form_key, question, rule_i, rule_na)
    })

# 6. Weekly recap decks
recap_deck_ids = []
for recap in recaps:
    deck = {
        'id':       recap['id'],
        'name':     recap['name'],
        'icon':     recap['icon'],
        'type':     'recap',
        'date':     recap['date'],
        'homework': recap.get('homework',''),
        'topics':   recap.get('topics_covered',[]),
        'cards':    flatten(recap)
    }
    decks.append(deck)
    recap_deck_ids.append(recap['id'])

# ── Stats ─────────────────────────────────────────────────────────
total = sum(len(d['cards']) for d in decks)
print(f"Total decks: {len(decks)}, Total cards: {total}")
for d in decks:
    print(f"  [{d['icon']}] {d['name']}: {len(d['cards'])} cards")

# ── Embed data ────────────────────────────────────────────────────
decks_json       = json.dumps(decks,          ensure_ascii=False)
recap_ids_json   = json.dumps(recap_deck_ids, ensure_ascii=False)

# ── HTML App ──────────────────────────────────────────────────────
# IMPORTANT: Do NOT use apostrophes inside single-quoted JS strings below.
# Use double-quoted JS strings ("...") for any text that might contain an apostrophe.

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>日本語 SRS — Atsuko-san's Class</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ── Reset ────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:       #f4f5f7;
  --surface:  #ffffff;
  --navy:     #1a1a2e;
  --red:      #e63946;
  --blue:     #457b9d;
  --green:    #2a9d8f;
  --yellow:   #e9c46a;
  --gray:     #8d99ae;
  --border:   #e0e4ea;
  --shadow:   0 2px 12px rgba(0,0,0,0.08);
  --shadow-lg:0 8px 32px rgba(0,0,0,0.12);
  --radius:   14px;
  --jp:       'Noto Sans JP', sans-serif;
  --ui:       'Inter', sans-serif;
}
body { font-family: var(--ui); background: var(--bg); color: var(--navy); min-height: 100vh; }

/* ── Layout ───────────────────────────────────────────────────── */
#app { max-width: 680px; margin: 0 auto; padding: 20px 16px 60px; }
.screen { display: none; }
.screen.active { display: block; }

/* ── Header ───────────────────────────────────────────────────── */
.header { display:flex; align-items:center; justify-content:space-between; padding:16px 0 24px; }
.header h1 { font-family:var(--jp); font-size:1.4rem; font-weight:700; }
.header h1 span { color: var(--red); }
.btn-back { background:none; border:none; cursor:pointer; font-size:0.9rem; color:var(--gray);
  font-family:var(--ui); padding:6px 0; display:flex; align-items:center; gap:4px; }
.btn-back:hover { color: var(--navy); }

/* ── Intro screen ─────────────────────────────────────────────── */
#screen-intro { background: var(--navy); min-height: 100vh; }
#screen-intro #app { padding-top: 48px; }
.intro-jp  { font-family:var(--jp); font-size:3rem; font-weight:700; color:#fff;
  text-align:center; margin-bottom:4px; }
.intro-jp span { color: var(--red); }
.intro-sub { text-align:center; color:rgba(255,255,255,0.6); font-size:0.85rem;
  margin-bottom:36px; line-height:1.5; }
.intro-card { background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
  border-radius:var(--radius); padding:22px; margin-bottom:14px; }
.intro-card h3 { color:#fff; font-size:0.9rem; margin-bottom:8px; }
.intro-card p  { color:rgba(255,255,255,0.65); font-size:0.82rem; line-height:1.6; }
.intro-how { display:flex; flex-direction:column; gap:10px; margin-bottom:28px; }
.intro-step { display:flex; align-items:flex-start; gap:14px; }
.intro-step-num { width:28px; height:28px; border-radius:50%; background:var(--red);
  color:#fff; font-size:0.78rem; font-weight:700; display:flex; align-items:center;
  justify-content:center; flex-shrink:0; margin-top:1px; }
.intro-step-text { color:rgba(255,255,255,0.75); font-size:0.83rem; line-height:1.5; }
.intro-step-text strong { color:#fff; }
.btn-start { width:100%; padding:18px; background:var(--red); color:#fff; border:none;
  border-radius:12px; font-family:var(--ui); font-size:1rem; font-weight:700; cursor:pointer;
  margin-top:8px; transition: filter 0.1s; }
.btn-start:hover { filter: brightness(1.1); }
.intro-credit { text-align:center; color:rgba(255,255,255,0.35); font-size:0.72rem;
  margin-top:20px; line-height:1.6; }

/* ── Stat bar ─────────────────────────────────────────────────── */
.stat-bar { display:flex; gap:12px; margin-bottom:28px; }
.stat { flex:1; background:var(--surface); border-radius:var(--radius);
  padding:14px 16px; box-shadow:var(--shadow); text-align:center; }
.stat-num { font-size:1.8rem; font-weight:700; color:var(--navy); }
.stat-num.red   { color: var(--red); }
.stat-num.blue  { color: var(--blue); }
.stat-num.green { color: var(--green); }
.stat-label { font-size:0.72rem; color:var(--gray); margin-top:2px;
  text-transform:uppercase; letter-spacing:0.04em; }

/* ── Search ───────────────────────────────────────────────────── */
.search-wrap { position:relative; margin-bottom:24px; }
.search-icon { position:absolute; left:14px; top:50%; transform:translateY(-50%);
  font-size:0.95rem; opacity:0.55; pointer-events:none; }
.search-input { width:100%; padding:13px 42px 13px 40px; border:1.5px solid var(--border);
  border-radius:12px; font-family:var(--ui); font-size:0.9rem; color:var(--navy);
  background:var(--surface); box-shadow:var(--shadow); outline:none; transition:border-color 0.12s; }
.search-input::placeholder { color:var(--gray); }
.search-input:focus { border-color:var(--blue); }
.search-clear { position:absolute; right:8px; top:50%; transform:translateY(-50%);
  background:none; border:none; cursor:pointer; font-size:0.85rem; color:var(--gray);
  padding:6px 9px; border-radius:8px; line-height:1; }
.search-clear:hover { background:var(--bg); color:var(--navy); }
.search-results { display:none; flex-direction:column; gap:8px; margin-bottom:28px; }
.search-results.active { display:flex; }
.search-count { font-size:0.74rem; color:var(--gray); margin-bottom:2px; }
.sr-card { background:var(--surface); border-radius:var(--radius); padding:12px 14px;
  box-shadow:var(--shadow); border:1.5px solid transparent; cursor:pointer;
  transition:transform 0.1s, border-color 0.1s; }
.sr-card:hover { transform:translateY(-1px); border-color:var(--border); }
.sr-top { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:5px; }
.sr-deck { font-size:0.68rem; color:var(--gray); text-transform:uppercase; letter-spacing:0.04em; }
.sr-label { font-size:0.66rem; color:var(--blue); font-weight:600; white-space:nowrap; }
.sr-front { font-family:var(--jp); font-size:1.15rem; font-weight:700; color:var(--navy); }
.sr-front .sr-fsub { font-size:0.8rem; color:var(--gray); font-weight:400; margin-left:8px; }
.sr-back { font-family:var(--jp); font-size:0.95rem; color:var(--green); margin-top:3px; }
.sr-back .sr-bsub { color:var(--gray); font-size:0.8rem; margin-left:8px; }
.sr-empty { text-align:center; color:var(--gray); font-size:0.88rem; padding:28px 16px;
  background:var(--surface); border-radius:var(--radius); box-shadow:var(--shadow); }

/* ── Study-all banner ─────────────────────────────────────────── */
.study-all-banner { background:var(--navy); color:#fff; border-radius:var(--radius);
  padding:18px 22px; display:flex; align-items:center; justify-content:space-between;
  margin-bottom:28px; box-shadow:var(--shadow-lg); cursor:pointer; transition:transform 0.1s; }
.study-all-banner:hover { transform: translateY(-1px); }
.study-all-banner .label { font-size:0.8rem; opacity:0.7; margin-bottom:2px; }
.study-all-banner .count { font-size:1.5rem; font-weight:700; }
.study-all-banner .arrow { font-size:1.4rem; opacity:0.8; }

/* ── Recap banner ─────────────────────────────────────────────── */
.recap-section { margin-bottom:28px; }
.recap-banner { background:linear-gradient(135deg,#2d6a4f,#1a1a2e);
  border-radius:var(--radius); padding:18px 20px; color:#fff;
  box-shadow:var(--shadow-lg); cursor:pointer; transition:transform 0.1s; }
.recap-banner:hover { transform: translateY(-1px); }
.recap-banner .rb-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
.recap-banner .rb-tag { font-size:0.7rem; font-weight:700; text-transform:uppercase;
  letter-spacing:0.08em; background:rgba(255,255,255,0.15); padding:3px 9px; border-radius:20px; }
.recap-banner .rb-date { font-size:0.75rem; opacity:0.6; }
.recap-banner h3 { font-size:1rem; font-weight:700; margin-bottom:6px; }
.recap-banner .rb-topics { display:flex; flex-wrap:wrap; gap:6px; }
.recap-banner .rb-topic { background:rgba(255,255,255,0.12); border-radius:20px;
  font-size:0.72rem; padding:3px 10px; }
.recap-banner .rb-hw { margin-top:10px; font-size:0.72rem; opacity:0.6;
  border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; }

/* ── Section title ────────────────────────────────────────────── */
.section-title { font-size:0.75rem; font-weight:600; color:var(--gray);
  text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px; }

/* ── Deck list ────────────────────────────────────────────────── */
.deck-grid { display:flex; flex-direction:column; gap:8px; margin-bottom:32px; }
.deck-card { background:var(--surface); border-radius:var(--radius);
  padding:14px 16px; display:flex; align-items:center; gap:14px;
  box-shadow:var(--shadow); cursor:pointer; transition:transform 0.1s, box-shadow 0.1s;
  border:1.5px solid transparent; }
.deck-card:hover { transform:translateY(-1px); box-shadow:var(--shadow-lg); border-color:var(--border); }
.deck-icon { font-size:1.4rem; width:36px; text-align:center; flex-shrink:0; }
.deck-info { flex:1; min-width:0; }
.deck-name { font-weight:600; font-size:0.92rem; margin-bottom:4px; }
.deck-meta { font-size:0.76rem; color:var(--gray); }
.deck-due { font-size:0.78rem; font-weight:700; padding:3px 10px; border-radius:20px; flex-shrink:0; }
.deck-due.has-due { background:#fee2e2; color:var(--red); }
.deck-due.no-due  { background:#f1f5f9; color:var(--gray); }
.progress-bar { height:4px; background:var(--border); border-radius:2px; margin-top:6px; }
.progress-fill { height:100%; border-radius:2px; background:var(--green); transition:width 0.4s; }

/* ── Progress tools ───────────────────────────────────────────── */
.progress-tools { background:var(--surface); border-radius:var(--radius);
  padding:16px 18px; box-shadow:var(--shadow); margin-bottom:12px; }
.progress-btn-row { display:flex; gap:10px; margin-bottom:10px; }
.btn-progress { flex:1; padding:10px 14px; border-radius:10px; border:1.5px solid var(--border);
  background:var(--surface); color:var(--navy); cursor:pointer; font-family:var(--ui);
  font-size:0.82rem; font-weight:600; transition:background 0.1s; text-align:center; }
.btn-progress:hover { background: var(--bg); }
.progress-note { font-size:0.73rem; color:var(--gray); line-height:1.5; }

/* ── Study screen ─────────────────────────────────────────────── */
.session-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.session-progress { font-size:0.82rem; color:var(--gray); font-weight:500; }
.session-counts { display:flex; gap:10px; font-size:0.78rem; }
.sc-again { color:var(--red);   font-weight:600; }
.sc-good  { color:var(--green); font-weight:600; }

/* ── Card ─────────────────────────────────────────────────────── */
.card-area { perspective:1200px; margin-bottom:24px; cursor:pointer; }
.card-inner { position:relative; width:100%; min-height:280px;
  transform-style:preserve-3d;
  transition:transform 0.45s cubic-bezier(0.4, 0, 0.2, 1); }
.card-inner.flipped { transform: rotateY(180deg); }
.card-face { position:absolute; width:100%; min-height:280px; background:var(--surface);
  border-radius:20px; box-shadow:var(--shadow-lg); display:flex; flex-direction:column;
  align-items:center; justify-content:center; padding:32px 28px;
  backface-visibility:hidden; -webkit-backface-visibility:hidden; }
.card-face.back { transform: rotateY(180deg); }
.card-tag { position:absolute; top:14px; left:16px; font-size:0.65rem; font-weight:700;
  color:var(--gray); text-transform:uppercase; letter-spacing:0.08em; }
.card-front-label { font-size:0.78rem; color:var(--gray); margin-bottom:14px; font-weight:500; }
.card-main { font-family:var(--jp); font-size:2.4rem; font-weight:700; color:var(--navy);
  text-align:center; line-height:1.3; word-break:break-all; }
.card-sub  { font-family:var(--jp); font-size:0.9rem; color:var(--gray); margin-top:10px;
  text-align:center; border-top:1px solid var(--border); padding-top:8px; width:100%; }
.card-notes { font-size:0.68rem; color:#a0aec0; margin-top:12px; text-align:center;
  font-style:italic; line-height:1.4; max-width:280px; }
.card-hint { position:absolute; bottom:14px; font-size:0.7rem; color:var(--gray); opacity:0.6; }

/* ── Rating buttons ───────────────────────────────────────────── */
.rating-row { display:flex; gap:10px; margin-bottom:16px; }
.rating-row.hidden { display: none; }
.btn-rate { flex:1; padding:14px 8px; border-radius:12px; border:none; cursor:pointer;
  font-family:var(--ui); font-weight:600; font-size:0.82rem; transition:transform 0.1s, filter 0.1s; }
.btn-rate:active { transform: scale(0.96); }
.btn-again { background:#fee2e2; color:#c0392b; }
.btn-hard  { background:#fef3c7; color:#d97706; }
.btn-good  { background:#d1fae5; color:#059669; }
.btn-easy  { background:#dbeafe; color:#1d4ed8; }
.btn-rate:hover { filter: brightness(0.95); }
.btn-flip { width:100%; padding:16px; border-radius:12px; background:var(--navy);
  color:#fff; border:none; cursor:pointer; font-family:var(--ui); font-size:0.95rem;
  font-weight:600; box-shadow:var(--shadow); transition:background 0.1s; }
.btn-flip:hover { background: #2d2d4e; }

/* ── Interval hints ───────────────────────────────────────────── */
.interval-hints { display:flex; gap:10px; margin-bottom:20px; }
.interval-hints.hidden { display: none; }
.int-hint { flex:1; text-align:center; font-size:0.68rem; color:var(--gray); }

/* ── Complete screen ──────────────────────────────────────────── */
.complete-card { background:var(--surface); border-radius:20px; padding:40px 28px;
  text-align:center; box-shadow:var(--shadow-lg); margin-bottom:24px; }
.complete-emoji { font-size:3rem; margin-bottom:16px; }
.complete-title { font-size:1.4rem; font-weight:700; margin-bottom:8px; }
.complete-sub   { color:var(--gray); font-size:0.9rem; margin-bottom:28px; }
.result-row { display:flex; gap:16px; justify-content:center; margin-bottom:8px; }
.result-item { text-align:center; }
.result-num  { font-size:1.8rem; font-weight:700; }
.result-lbl  { font-size:0.72rem; color:var(--gray); text-transform:uppercase; letter-spacing:0.04em; }
.btn-primary { display:inline-flex; align-items:center; justify-content:center;
  padding:12px 22px; border-radius:10px; border:none; cursor:pointer;
  font-family:var(--ui); font-size:0.9rem; font-weight:600; }
.btn-full { width:100%; margin-bottom:10px; }
.btn-primary { background:var(--navy); color:#fff; box-shadow:var(--shadow); }
.btn-primary:hover { background: #2d2d4e; }

@media (max-width: 400px) {
  .card-main { font-size: 1.9rem; }
  .stat-num  { font-size: 1.4rem; }
}
</style>
</head>
<body>
<div id="app">

  <!-- ── INTRO ─────────────────────────────────────────────────── -->
  <div id="screen-intro" class="screen">
    <div class="intro-jp">日本語 <span>SRS</span></div>
    <p class="intro-sub">
      Spaced repetition study app for<br>
      <strong style="color:rgba(255,255,255,0.85)">Atsuko-san's Japanese Class</strong><br>
      Upstate International · Greenville, SC
    </p>

    <div class="intro-card">
      <h3>What is spaced repetition?</h3>
      <p>SRS shows you cards just before you would forget them. Cards you know well come back weeks later; cards you struggle with come back the next day. It is the most efficient way to build vocabulary and grammar over time.</p>
    </div>

    <div class="intro-how">
      <div class="intro-step">
        <div class="intro-step-num">1</div>
        <div class="intro-step-text"><strong>See the front of a card</strong> — hiragana, a verb, or a grammar question.</div>
      </div>
      <div class="intro-step">
        <div class="intro-step-num">2</div>
        <div class="intro-step-text"><strong>Try to recall the answer</strong>, then tap the card to flip it.</div>
      </div>
      <div class="intro-step">
        <div class="intro-step-num">3</div>
        <div class="intro-step-text"><strong>Rate yourself honestly:</strong> Again · Hard · Good · Easy. The app schedules your next review automatically.</div>
      </div>
      <div class="intro-step">
        <div class="intro-step-num">4</div>
        <div class="intro-step-text"><strong>Come back daily.</strong> Even 10 minutes a day compounds into fluency over time.</div>
      </div>
    </div>

    <button class="btn-start" onclick="startApp()">始めましょう — Let's Begin!</button>
    <p class="intro-credit">
      Content sourced from Atsuko-sensei's A0/A1 course materials.<br>
      Progress is saved locally in your browser.
    </p>
  </div>

  <!-- ── HOME ──────────────────────────────────────────────────── -->
  <div id="screen-home" class="screen">
    <div class="header">
      <h1>日本語 <span>SRS</span></h1>
      <button class="btn-back" onclick="showIntro()" style="font-size:0.75rem">About ℹ</button>
    </div>

    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input id="search-input" class="search-input" type="text" autocomplete="off"
        placeholder="Search cards — Japanese, romaji, or English…" oninput="runSearch(this.value)">
      <button id="search-clear" class="search-clear" onclick="clearSearch()" style="display:none" aria-label="Clear search">✕</button>
    </div>
    <div id="search-results" class="search-results"></div>

    <div id="home-body">
    <div class="stat-bar">
      <div class="stat"><div class="stat-num red"   id="home-due">—</div><div class="stat-label">Due Now</div></div>
      <div class="stat"><div class="stat-num blue"  id="home-learning">—</div><div class="stat-label">Learning</div></div>
      <div class="stat"><div class="stat-num green" id="home-mastered">—</div><div class="stat-label">Mastered</div></div>
    </div>

    <div class="study-all-banner" onclick="startSession('__all__')">
      <div>
        <div class="label">Study all due cards</div>
        <div class="count" id="home-due-banner">Loading…</div>
      </div>
      <div class="arrow">→</div>
    </div>

    <div class="recap-section" id="recap-section"></div>

    <div class="section-title">Vocabulary</div>
    <div class="deck-grid" id="deck-list-vocab"></div>

    <div class="section-title">Verb Conjugation</div>
    <div class="deck-grid" id="deck-list-vconj"></div>

    <div class="section-title">Adjective Conjugation</div>
    <div class="deck-grid" id="deck-list-adjconj"></div>

    <div class="section-title">Progress</div>
    <div class="progress-tools">
      <div class="progress-btn-row">
        <button class="btn-progress" onclick="exportProgress()">⬇ Export Progress</button>
        <label class="btn-progress" style="cursor:pointer;">
          ⬆ Import Progress
          <input type="file" accept=".json" onchange="importProgress(event)" style="display:none">
        </label>
      </div>
      <p class="progress-note">Your progress is automatically saved in this browser. Export / Import is only needed to back up your data or move to a different browser or device.</p>
    </div>
    </div><!-- /#home-body -->
  </div>

  <!-- ── STUDY ─────────────────────────────────────────────────── -->
  <div id="screen-study" class="screen">
    <div class="header">
      <button class="btn-back" onclick="goHome()">← Home</button>
      <div class="session-counts">
        <span class="sc-again" id="sess-again">0 again</span>
        <span class="sc-good"  id="sess-good">0 good</span>
      </div>
    </div>
    <div class="session-header">
      <div class="session-progress" id="sess-progress">Card 1 of 1</div>
      <div style="font-size:0.78rem;color:var(--gray)" id="sess-deck-name"></div>
    </div>
    <div class="card-area" onclick="flipCard()">
      <div class="card-inner" id="card-inner">
        <div class="card-face front">
          <div class="card-tag" id="cf-tag"></div>
          <div class="card-front-label" id="cf-label"></div>
          <div class="card-main" id="cf-main"></div>
          <div class="card-sub"  id="cf-sub"></div>
          <div class="card-hint">tap to flip</div>
        </div>
        <div class="card-face back">
          <div class="card-tag" id="cb-tag"></div>
          <div class="card-main" id="cb-main"></div>
          <div class="card-sub"  id="cb-sub"></div>
          <div class="card-notes" id="cb-notes"></div>
          <div class="card-hint">tap to flip back</div>
        </div>
      </div>
    </div>
    <div class="rating-row hidden" id="rating-row">
      <button class="btn-rate btn-again" onclick="rateCard(0)">Again</button>
      <button class="btn-rate btn-hard"  onclick="rateCard(1)">Hard</button>
      <button class="btn-rate btn-good"  onclick="rateCard(2)">Good</button>
      <button class="btn-rate btn-easy"  onclick="rateCard(3)">Easy</button>
    </div>
    <div class="interval-hints hidden" id="interval-hints">
      <div class="int-hint" id="ih-again"></div>
      <div class="int-hint" id="ih-hard"></div>
      <div class="int-hint" id="ih-good"></div>
      <div class="int-hint" id="ih-easy"></div>
    </div>
    <button class="btn-flip" id="btn-flip" onclick="flipCard()">Flip Card ↓</button>
  </div>

  <!-- ── COMPLETE ───────────────────────────────────────────────── -->
  <div id="screen-complete" class="screen">
    <div class="header">
      <button class="btn-back" onclick="goHome()">← Home</button>
    </div>
    <div class="complete-card">
      <div class="complete-emoji">🎉</div>
      <div class="complete-title">Session Complete!</div>
      <div class="complete-sub" id="complete-sub">All cards reviewed.</div>
      <div class="result-row">
        <div class="result-item"><div class="result-num" id="res-again" style="color:var(--red)">0</div><div class="result-lbl">Again</div></div>
        <div class="result-item"><div class="result-num" id="res-hard" style="color:var(--yellow)">0</div><div class="result-lbl">Hard</div></div>
        <div class="result-item"><div class="result-num" id="res-good" style="color:var(--green)">0</div><div class="result-lbl">Good</div></div>
        <div class="result-item"><div class="result-num" id="res-easy" style="color:var(--blue)">0</div><div class="result-lbl">Easy</div></div>
      </div>
    </div>
    <button class="btn btn-primary btn-full" onclick="goHome()">Back to Decks</button>
  </div>

</div>
<script>
// ================================================================
// DATA
// ================================================================
const DECKS = """ + decks_json + """;
const RECAP_IDS = """ + recap_ids_json + """;

// ================================================================
// SRS ENGINE (SM-2 variant)
// ================================================================
const DAY       = 86400000;
const STORE_KEY = 'jp_srs_v2';
const SEEN_INTRO_KEY = 'jp_srs_intro_seen';

function loadProgress() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; }
  catch(e) { return {}; }
}
function saveProgress(p) { localStorage.setItem(STORE_KEY, JSON.stringify(p)); }
function getCard(progress, id) {
  return progress[id] || { interval:0, ef:2.5, reps:0, due:0 };
}
function sm2Update(card, rating) {
  const q = [1, 2, 4, 5][rating];
  let { interval, ef, reps } = card;
  if (q < 3) { reps = 0; interval = 1; }
  else {
    if (reps === 0)      interval = 1;
    else if (reps === 1) interval = 4;
    else                 interval = Math.round(interval * ef);
    reps += 1;
    ef = Math.max(1.3, ef + 0.1 - (5-q) * (0.08 + (5-q) * 0.02));
  }
  return { interval, ef, reps, due: Date.now() + interval * DAY };
}
function nextIntervals(card) {
  return [0,1,2,3].map(r => {
    const u = sm2Update(card, r);
    if (u.interval <= 1) return 'soon';
    if (u.interval < 7)  return u.interval + 'd';
    if (u.interval < 30) return Math.round(u.interval/7) + 'w';
    return Math.round(u.interval/30) + 'mo';
  });
}
function isDue(card) { return card.due <= Date.now(); }

// ================================================================
// STATE
// ================================================================
let progress = loadProgress();
let session  = { deckIds:[], queue:[], idx:0, flipped:false, stats:{0:0,1:0,2:0,3:0} };

// ================================================================
// DECK HELPERS
// ================================================================
function allCards() { return DECKS.flatMap(d => d.cards); }
function cardsForDecks(deckIds) {
  if (deckIds[0] === '__all__') return allCards();
  return DECKS.filter(d => deckIds.includes(d.id)).flatMap(d => d.cards);
}
function dueCards(deckIds) {
  return cardsForDecks(deckIds).filter(c => isDue(getCard(progress, c.id)));
}
function deckStats(deckId) {
  const cards = deckId === '__all__' ? allCards()
    : (DECKS.find(d => d.id === deckId) || {cards:[]}).cards;
  let due=0, learning=0, mastered=0;
  for (const c of cards) {
    const p = getCard(progress, c.id);
    if (p.reps === 0)         { if (isDue(p)) due++; }
    else if (p.interval < 21) { learning++; if (isDue(p)) due++; }
    else                      { mastered++; }
  }
  return { due, learning, mastered, total: cards.length };
}

// ================================================================
// NAVIGATION
// ================================================================
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-' + id).classList.add('active');
  window.scrollTo(0, 0);
}
function showIntro() { showScreen('intro'); }
function startApp() {
  localStorage.setItem(SEEN_INTRO_KEY, '1');
  renderHome();
  showScreen('home');
}
function goHome() {
  progress = loadProgress();
  renderHome();
  showScreen('home');
}

// ================================================================
// HOME RENDER
// ================================================================
function renderHome() {
  resetSearch();
  const all = deckStats('__all__');
  document.getElementById('home-due').textContent      = all.due;
  document.getElementById('home-learning').textContent = all.learning;
  document.getElementById('home-mastered').textContent = all.mastered;
  document.getElementById('home-due-banner').textContent =
    all.due > 0 ? all.due + ' cards due' : 'All caught up! 🌸';

  // Recap banners
  const recapEl = document.getElementById('recap-section');
  recapEl.innerHTML = '';
  if (RECAP_IDS.length > 0) {
    const titleEl = document.createElement('div');
    titleEl.className = 'section-title';
    titleEl.textContent = 'Class Review';
    recapEl.appendChild(titleEl);
    for (const rid of RECAP_IDS) {
      const deck = DECKS.find(d => d.id === rid);
      if (!deck) continue;
      const s = deckStats(rid);
      const topics = (deck.topics || []).map(t =>
        '<span class="rb-topic">' + t + '</span>'
      ).join('');
      const hwHtml = deck.homework
        ? '<div class="rb-hw">📚 Homework: ' + deck.homework + '</div>' : '';
      const div = document.createElement('div');
      div.className = 'recap-banner';
      div.onclick = () => startSession(rid);
      div.innerHTML =
        '<div class="rb-top">' +
          '<span class="rb-tag">Class Recap</span>' +
          '<span class="rb-date">' + deck.date + '</span>' +
        '</div>' +
        '<h3>' + deck.name + ' · ' + deck.cards.length + ' cards' +
          (s.due > 0 ? ' · <span style="color:#a7f3d0">' + s.due + ' due</span>' : '') +
        '</h3>' +
        '<div class="rb-topics">' + topics + '</div>' +
        hwHtml;
      recapEl.appendChild(div);
    }
  }

  const vocabIds   = DECKS.filter(d => d.type==='vocab').map(d => d.id);
  const vconjIds   = DECKS.filter(d => d.id.startsWith('verb_conj')).map(d => d.id);
  const adjconjIds = DECKS.filter(d => d.id.startsWith('adj_conj')).map(d => d.id);
  renderDeckList('deck-list-vocab',   vocabIds);
  renderDeckList('deck-list-vconj',   vconjIds);
  renderDeckList('deck-list-adjconj', adjconjIds);
}

function renderDeckList(containerId, deckIds) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  for (const id of deckIds) {
    const deck = DECKS.find(d => d.id === id);
    if (!deck) continue;
    const s   = deckStats(id);
    const pct = deck.cards.length ? Math.round(s.mastered / deck.cards.length * 100) : 0;
    const dueClass = s.due > 0 ? 'has-due' : 'no-due';
    const dueLabel = s.due > 0 ? s.due + ' due' : 'up to date';
    const div = document.createElement('div');
    div.className = 'deck-card';
    div.onclick = () => startSession(id);
    div.innerHTML =
      '<div class="deck-icon">' + deck.icon + '</div>' +
      '<div class="deck-info">' +
        '<div class="deck-name">' + deck.name + '</div>' +
        '<div class="deck-meta">' + deck.cards.length + ' cards · ' + s.mastered + ' mastered</div>' +
        '<div class="progress-bar"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
      '</div>' +
      '<div class="deck-due ' + dueClass + '">' + dueLabel + '</div>';
    el.appendChild(div);
  }
}

// ================================================================
// SEARCH
// ================================================================
// Flat, lowercase-indexed view of every card across every deck.
const SEARCH_INDEX = DECKS.flatMap(function(d) {
  return d.cards.map(function(c) {
    const parts = [c.front, c.frontSub, c.frontLabel, c.back, c.backSub, c.notes, d.name];
    return {
      deckId:    d.id,
      deckName:  d.name,
      deckIcon:  d.icon,
      front:     c.front,
      frontSub:  c.frontSub,
      frontLabel:c.frontLabel,
      back:      c.back,
      backSub:   c.backSub,
      hay:       parts.join(" ").toLowerCase()
    };
  });
});

function escHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function runSearch(raw) {
  const q         = (raw || '').trim().toLowerCase();
  const clearBtn  = document.getElementById('search-clear');
  const resultsEl = document.getElementById('search-results');
  const bodyEl    = document.getElementById('home-body');
  clearBtn.style.display = q ? '' : 'none';

  if (!q) {
    resultsEl.classList.remove('active');
    resultsEl.innerHTML = '';
    bodyEl.style.display = '';
    return;
  }

  bodyEl.style.display = 'none';
  resultsEl.classList.add('active');

  const matches = SEARCH_INDEX.filter(function(r) { return r.hay.indexOf(q) !== -1; });
  const CAP   = 60;
  const shown = matches.slice(0, CAP);

  let html = '<div class="search-count">' + matches.length + ' result' +
    (matches.length === 1 ? '' : 's') +
    (matches.length > CAP ? ' (showing first ' + CAP + ')' : '') + '</div>';

  if (shown.length === 0) {
    html += '<div class="sr-empty">No cards match “' + escHtml(raw.trim()) + '”</div>';
  } else {
    shown.forEach(function(r) {
      const label = r.frontLabel ? '<span class="sr-label">' + escHtml(r.frontLabel) + '</span>' : '';
      const fsub  = r.frontSub  ? '<span class="sr-fsub">'  + escHtml(r.frontSub)  + '</span>' : '';
      const bsub  = r.backSub   ? '<span class="sr-bsub">'  + escHtml(r.backSub)   + '</span>' : '';
      html +=
        '<div class="sr-card" data-deck="' + escHtml(r.deckId) + '">' +
          '<div class="sr-top">' +
            '<span class="sr-deck">' + r.deckIcon + ' ' + escHtml(r.deckName) + '</span>' +
            label +
          '</div>' +
          '<div class="sr-front">' + escHtml(r.front) + fsub + '</div>' +
          '<div class="sr-back">' + escHtml(r.back) + bsub + '</div>' +
        '</div>';
    });
  }
  resultsEl.innerHTML = html;
}

// Delegated click: tapping a result jumps into that card's deck.
function initSearchClicks() {
  const resultsEl = document.getElementById('search-results');
  if (!resultsEl) return;
  resultsEl.addEventListener('click', function(e) {
    const card = e.target.closest('.sr-card');
    if (card && card.dataset.deck) startSession(card.dataset.deck);
  });
}

function clearSearch() {
  const input = document.getElementById('search-input');
  input.value = '';
  runSearch('');
  input.focus();
}

function resetSearch() {
  const input = document.getElementById("search-input");
  if (input) input.value = "";
  const clearBtn = document.getElementById("search-clear");
  if (clearBtn) clearBtn.style.display = "none";
  const resultsEl = document.getElementById("search-results");
  if (resultsEl) { resultsEl.classList.remove("active"); resultsEl.innerHTML = ""; }
  const bodyEl = document.getElementById("home-body");
  if (bodyEl) bodyEl.style.display = "";
}

// ================================================================
// SESSION
// ================================================================
function startSession(deckIdOrAll) {
  const deckIds = deckIdOrAll === '__all__' ? ['__all__'] : [deckIdOrAll];
  let queue = dueCards(deckIds);
  if (queue.length === 0) {
    const unseen = cardsForDecks(deckIds).filter(c => getCard(progress, c.id).reps === 0);
    const batch  = unseen.slice(0, 20);
    if (batch.length === 0) {
      alert("All caught up for this deck! Come back later.");
      return;
    }
    queue = shuffle([...batch]);
  } else {
    queue = shuffle([...queue]);
  }
  const deckName = deckIdOrAll === '__all__' ? 'All Decks'
    : (DECKS.find(d => d.id === deckIdOrAll) || {name:''}).name;
  session = { deckIds, queue, idx:0, flipped:false, revealed:false, stats:{0:0,1:0,2:0,3:0} };
  document.getElementById('sess-deck-name').textContent = deckName;
  showScreen('study');
  renderCard();
}

// ================================================================
// CARD RENDER
// ================================================================
function renderCard() {
  // Instantly snap back to front (no animation) so the new card front
  // is never shown on the back face mid-transition.
  const inner = document.getElementById('card-inner');
  inner.style.transition = 'none';
  inner.classList.remove('flipped');
  inner.getBoundingClientRect();  // force reflow
  inner.style.transition = '';

  const card  = session.queue[session.idx];
  const total = session.queue.length;

  document.getElementById('sess-progress').textContent = 'Card ' + (session.idx+1) + ' of ' + total;
  document.getElementById('sess-again').textContent = session.stats[0] + ' again';
  document.getElementById('sess-good').textContent  = (session.stats[2]+session.stats[3]) + ' good';

  document.getElementById('cf-tag').textContent   = card.frontLabel ? 'Grammar' : 'Vocabulary';
  document.getElementById('cf-label').textContent = card.frontLabel || '';
  document.getElementById('cf-main').textContent  = card.front;

  const cfSub = document.getElementById('cf-sub');
  if (card.frontSub) { cfSub.textContent = card.frontSub; cfSub.style.display=''; }
  else cfSub.style.display = 'none';

  document.getElementById('cb-tag').textContent   = 'Answer';
  document.getElementById('cb-main').textContent  = card.back;
  const cbSub = document.getElementById('cb-sub');
  if (card.backSub) { cbSub.textContent = card.backSub; cbSub.style.display=''; }
  else cbSub.style.display = 'none';
  document.getElementById('cb-notes').textContent = card.notes || '';

  session.flipped   = false;
  session.revealed  = false;
  document.getElementById('rating-row').classList.add('hidden');
  document.getElementById('interval-hints').classList.add('hidden');
  document.getElementById('btn-flip').style.display = '';
}

function flipCard() {
  session.flipped = !session.flipped;
  const inner = document.getElementById('card-inner');
  if (session.flipped) {
    inner.classList.add('flipped');
  } else {
    inner.classList.remove('flipped');
  }
  // First time reaching the back: reveal ratings and lock in intervals
  if (session.flipped && !session.revealed) {
    session.revealed = true;
    document.getElementById('btn-flip').style.display = 'none';
    document.getElementById('rating-row').classList.remove('hidden');
    document.getElementById('interval-hints').classList.remove('hidden');
    const p = getCard(progress, session.queue[session.idx].id);
    const intervals = nextIntervals(p);
    ['ih-again','ih-hard','ih-good','ih-easy'].forEach((id, i) => {
      document.getElementById(id).textContent = intervals[i];
    });
  }
}

function rateCard(rating) {
  const card    = session.queue[session.idx];
  const updated = sm2Update(getCard(progress, card.id), rating);
  progress[card.id] = updated;
  saveProgress(progress);
  session.stats[rating]++;
  if (rating === 0) session.queue.push(card);
  session.idx++;
  if (session.idx >= session.queue.length) showComplete();
  else renderCard();
}

function showComplete() {
  document.getElementById('res-again').textContent = session.stats[0];
  document.getElementById('res-hard').textContent  = session.stats[1];
  document.getElementById('res-good').textContent  = session.stats[2];
  document.getElementById('res-easy').textContent  = session.stats[3];
  const total = session.stats[0]+session.stats[1]+session.stats[2]+session.stats[3];
  document.getElementById('complete-sub').textContent = 'Reviewed ' + total + ' cards — well done!';
  showScreen('complete');
}

// ================================================================
// IMPORT / EXPORT
// ================================================================
function exportProgress() {
  const data = JSON.stringify(loadProgress(), null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url;
  a.download = 'japanese_srs_progress.json';
  a.click();
  URL.revokeObjectURL(url);
}
function importProgress(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result);
      if (typeof data !== 'object' || Array.isArray(data)) throw new Error();
      localStorage.setItem(STORE_KEY, JSON.stringify(data));
      progress = data;
      renderHome();
      alert("Progress imported successfully!");
    } catch(err) {
      alert("Could not read that file. Make sure it is a progress export from this app.");
    }
  };
  reader.readAsText(file);
  event.target.value = '';
}

// ================================================================
// UTILS
// ================================================================
function shuffle(arr) {
  for (let i = arr.length-1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i+1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// ================================================================
// INIT
// ================================================================
initSearchClicks();
if (localStorage.getItem(SEEN_INTRO_KEY)) {
  renderHome();
  showScreen('home');
} else {
  showScreen('intro');
}
</script>
</body>
</html>"""

with open(OUT_PATH, 'w') as f:
    f.write(HTML)
print("App written to", OUT_PATH)
