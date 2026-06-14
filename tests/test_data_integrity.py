"""
Validate the source-of-truth JSON files that build_app.py consumes.
A broken or schema-violating data file should fail loudly here, before a build.
"""

import json

import pytest

from conftest import DATA_DIR, ADJ_JSON, FLASHCARDS_DIR


VOCAB_FILES = [
    "vocab_pronouns_demonstratives.json",
    "vocab_countries.json",
    "vocab_family.json",
    "vocab_occupations.json",
    "vocab_time.json",
    "vocab_location.json",
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_data_files_parse():
    for p in DATA_DIR.glob("*.json"):
        try:
            _load(p)
        except json.JSONDecodeError as e:
            pytest.fail(f"{p.name} is not valid JSON: {e}")


def test_adjectives_file_exists_and_parses():
    assert ADJ_JSON.exists(), f"missing {ADJ_JSON}"
    _load(ADJ_JSON)


@pytest.mark.parametrize("fname", VOCAB_FILES)
def test_vocab_file_schema(fname):
    data = _load(DATA_DIR / fname)
    for key in ("id", "name", "icon", "groups"):
        assert key in data, f"{fname} missing top-level '{key}'"
    assert data["groups"], f"{fname} has no groups"
    for grp in data["groups"]:
        assert "cards" in grp, f"{fname} group missing 'cards'"
        for card in grp["cards"]:
            assert card.get("id"), f"{fname} card missing id"
            assert card.get("front"), f"{fname} card {card.get('id')} missing front"
            assert card.get("back"), f"{fname} card {card.get('id')} missing back"


def test_adjectives_schema():
    data = _load(ADJ_JSON)
    assert "categories" in data
    types = {cat["type"] for cat in data["categories"]}
    assert {"i", "na"} <= types, f"expected i and na categories, got {types}"
    for cat in data["categories"]:
        assert cat.get("words"), f"adjective category {cat['type']} has no words"
        for w in cat["words"]:
            for key in ("hiragana", "kanji", "romaji", "english"):
                assert key in w, f"{cat['type']} word missing '{key}': {w}"
            assert w["hiragana"].strip(), f"empty hiragana in {cat['type']}"


def test_i_adjectives_end_in_i():
    """Every i-adjective primary form should end in い (sanity for the stemmer)."""
    data = _load(ADJ_JSON)
    i_cat = next(c for c in data["categories"] if c["type"] == "i")
    offenders = []
    for w in i_cat["words"]:
        primary = w["hiragana"].split("/")[0].strip()
        if not primary.endswith("い"):
            offenders.append(primary)
    assert not offenders, f"i-adjectives not ending in い: {offenders}"


def test_verbs_schema():
    data = _load(DATA_DIR / "verbs.json")
    assert data.get("verbs"), "verbs.json has no verbs"
    valid_types = {"ru", "u", "suru", "irreg"}
    seen_ids = set()
    for v in data["verbs"]:
        assert v.get("id"), "verb missing id"
        assert v["id"] not in seen_ids, f"duplicate verb id {v['id']}"
        seen_ids.add(v["id"])
        assert v.get("dict"), f"verb {v['id']} missing dict form"
        assert v.get("type") in valid_types, f"verb {v['id']} bad type {v.get('type')}"
        forms = v.get("forms", {})
        for fk in ("masu", "masen", "te", "ta"):
            assert forms.get(fk), f"verb {v['id']} missing '{fk}' form"


def test_weekly_recaps_have_metadata():
    recaps = list(DATA_DIR.glob("weekly_recap_*.json"))
    assert recaps, "no weekly_recap_*.json files found"
    for p in recaps:
        data = _load(p)
        for key in ("id", "name", "icon", "date", "groups"):
            assert key in data, f"{p.name} missing '{key}'"


def test_no_duplicate_ids_within_each_data_file():
    for fname in VOCAB_FILES:
        data = _load(DATA_DIR / fname)
        ids = [c["id"] for grp in data["groups"] for c in grp["cards"]]
        dupes = {i for i in ids if ids.count(i) > 1}
        assert not dupes, f"{fname} has duplicate card ids: {dupes}"
