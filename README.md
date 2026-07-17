# 日本語 SRS — Japanese Spaced Repetition Study App

A browser-based flashcard app using the SM-2 spaced repetition algorithm (the same system used by Anki) to study vocabulary and grammar from **Atsuko-san's Japanese class at Upstate International, Greenville, SC**.

## Using the app

Open `index.html` in any web browser — no installation, no internet connection required (after the initial font load). Progress is saved automatically in your browser's local storage.

The first time you open it, a brief intro explains how spaced repetition works. After that, the home screen shows:

- **Due Now / Learning / Mastered** — your overall progress across all decks
- **Study all due cards** — review everything due in one session
- **Class Review** — decks built from each week's class recap, with topics and homework reminders
- **Hiragana & Katakana** — full kana reading decks (for the A0 class)
- Individual vocabulary and conjugation decks

### Romaji on vocabulary cards

New learners can turn on **Romaji on front** (the switch next to the "Vocabulary" heading on the home screen) to show the romaji reading on the *front* of vocabulary flashcards. It is **off by default**, applies to vocabulary decks only (not kana, conjugation, or recap cards), and your choice is remembered in this browser.

### Rating cards

After flipping a card, rate yourself honestly:

| Rating | Meaning | When to use |
|--------|---------|-------------|
| **Again** | Did not recall | Blank or wrong |
| **Hard** | Recalled with effort | Took a long time or partially wrong |
| **Good** | Recalled correctly | Normal effort |
| **Easy** | Instant recall | Too easy |

The interval hints below the card (e.g. "4d", "2w") show when each rating will schedule the next review.

### Saving your progress

Progress lives in your browser. If you want to transfer it to another browser or device, use the **Export / Import Progress** buttons at the bottom of the home screen.

## What's included

| Deck | Cards |
|------|-------|
| Hiragana ひらがな (full: basic + dakuten + combos) | 104 |
| Katakana カタカナ (full: basic + dakuten + combos) | 104 |
| Pronouns & Demonstratives | 25 |
| Countries & Languages | 27 |
| Family | 28 |
| Occupations | 16 |
| Time & Days | 28 |
| Location Words | 14 |
| い-Adjectives (vocabulary) | 83 |
| な-Adjectives (vocabulary) | 27 |
| Verbs (vocabulary) | 29 |
| Verb Conjugation × 4 forms (ます/ません/て/た) | 116 |
| い-Adjective Conjugation × 3 forms | 249 |
| な-Adjective Conjugation × 2 forms | 54 |
| Class recap decks | grows each week |

## Deploying to GitHub Pages

The app is a single self-contained HTML file — no build step, no dependencies to install.

1. Push the `study-app/` folder to a GitHub repository.
2. Go to **Settings → Pages** in the repo.
3. Under "Branch", select `main` and the `/study-app` folder (or root if that's where `index.html` lives), then click **Save**.
4. GitHub will give you a URL like `https://yourusername.github.io/repo-name/`. Share that link with classmates.

> Note: each person's progress is stored in their own browser, so classmates start fresh with their own data.

## Contributing

### Will rebuilding the app clear my progress?

No. Progress is stored in your browser's `localStorage` under the key `jp_srs_v2`, keyed by each card's unique `id` string. Rebuilding `index.html` does not touch `localStorage`. As long as card IDs stay the same across builds, all scheduling data is preserved.

**The one thing that breaks progress: changing a card's `id` field.** The app treats a renamed ID as a brand-new card with no history. So the golden rule for contributors is:

> **Never rename an existing card ID. Only add new ones.**

### Card ID conventions

IDs are set automatically for most decks during the build — you only need to assign them manually in recap JSON files. Follow these conventions:

| Deck type | ID format | Example |
|-----------|-----------|---------|
| Vocab JSON cards | set in JSON, snake_case | `pron_watashi` |
| Adjectives | `adj_<hiragana>` (auto) | `adj_たかい` |
| Verbs (vocab) | `vvoc_<verb_id>` (auto) | `vvoc_taberu` |
| Verb conjugation | `vconj_<verb_id>_<form>` (auto) | `vconj_taberu_masu` |
| Adj conjugation | `adjconj_<type>_<hiragana>_<form>` (auto) | `adjconj_i_たかい_neg_cas` |
| Recap cards | set in JSON | `recap_0611_no_particle_1` |

### Adding a new class recap

1. Create `data/weekly_recap_YYYY_MM_DD.json` following the same structure as the existing recap file. Use a consistent prefix for card IDs in that file (e.g., `recap_0618_` for the June 18 class).
2. Run `python3 build_app.py`.
3. Commit both the new JSON file and the regenerated `index.html`.

### Adding new vocabulary

Edit the relevant JSON file in `data/`, keeping existing IDs unchanged. Add new entries with new IDs at the end of the list. Then rebuild.

### Changing the app layout or logic

The HTML/CSS/JS all lives in the template string inside `build_app.py`. Edit that template, then run the build script to regenerate `index.html`. A few things to be careful about:

- **No apostrophes in single-quoted JS strings.** The template embeds JSON data inline; a stray `'` will break the script block. Use double-quoted JS strings for any text that might contain an apostrophe (the file has a comment marking this).
- **Test in a private/incognito window** to catch issues without any cached progress interfering.
- **Run `node --check /tmp/check.js`** (or any JS syntax checker) on the script block before shipping — the build script does not validate JS.

### Sharing with classmates

Deploy to GitHub Pages (see below). Each person's progress is isolated to their own browser; there is no shared backend. If a classmate wants to pick up where they left off on a new device, they can use Export / Import Progress.

## Rebuilding after adding new content

The app is generated by `build_app.py`. After editing any JSON source file, regenerate:

```bash
cd japanese/study-app
python3 build_app.py
```

Then refresh `index.html` in your browser (or push the updated file to GitHub Pages).

### Adding a new class recap

1. Create `data/weekly_recap_YYYY_MM_DD.json` following the same structure as the existing recap file.
2. Run `python3 build_app.py`.

The build script automatically discovers all `weekly_recap_*.json` files in the `data/` folder and adds them as "Class Review" decks.

### Adding new vocabulary

Edit the relevant JSON file in `data/`, then rebuild. The JSON structure is self-documenting — each file has `groups` containing `cards` with `front`, `back`, and optional `frontSub`, `backSub`, `notes` fields.

## File layout

```
study-app/
  build_app.py          # run this to regenerate index.html
  index.html            # the app (open this in a browser)
  README.md             # this file
  data/
    vocab_pronouns_demonstratives.json
    vocab_countries.json
    vocab_family.json
    vocab_occupations.json
    vocab_time.json
    vocab_location.json
    verbs.json
    weekly_recap_2026_06_11.json
    weekly_recap_*.json   # add new ones here after each class

../flashcards/
  adjectives_vocab.json   # shared source for adjective decks and printable flashcards
  adjectives_flashcards.html   # printable 3×4 flashcard sheet
```
