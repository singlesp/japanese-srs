"""
Conjugation correctness — the heart of the suite.

Covers the bug Atsuko-sensei flagged: いい/よい (good) is irregular and uses the
よ-stem, including in compounds (あたまがいい → あたまがよくない), while かわいい is a
*regular* i-adjective that merely ends in いい (かわいい → かわいくない).
"""

import pytest

from conftest import reference_i_adj


# ── Linguistic ground truth (hand-verified), forms: neg / past / negpast ──
GROUND_TRUTH = {
    # regular i-adjectives
    "たかい":   ("たかくない",   "たかかった",   "たかくなかった"),
    "おいしい": ("おいしくない", "おいしかった", "おいしくなかった"),
    "すごい":   ("すごくない",   "すごかった",   "すごくなかった"),
    "おおきい": ("おおきくない", "おおきかった", "おおきくなかった"),
    "たのしい": ("たのしくない", "たのしかった", "たのしくなかった"),
    "きいろい": ("きいろくない", "きいろかった", "きいろくなかった"),
    # compound that is NOT いい-good -> stays regular
    "せがたかい": ("せがたかくない", "せがたかかった", "せがたかくなかった"),
    # the irregular いい/よい (good) and its compounds -> よ-stem
    "いい":       ("よくない",       "よかった",       "よくなかった"),
    "よい":       ("よくない",       "よかった",       "よくなかった"),
    "あたまがいい": ("あたまがよくない", "あたまがよかった", "あたまがよくなかった"),
    "なかがいい":   ("なかがよくない",   "なかがよかった",   "なかがよくなかった"),
    "かっこいい":   ("かっこよくない",   "かっこよかった",   "かっこよくなかった"),
    # the false-friend: ends in いい but conjugates regularly
    "かわいい":     ("かわいくない",     "かわいかった",     "かわいくなかった"),
}


@pytest.mark.parametrize("hira,expected", GROUND_TRUTH.items())
def test_i_adj_info_matches_ground_truth(i_adj_info, hira, expected):
    forms, _ = i_adj_info(hira)
    got = (forms["neg_cas"], forms["past_cas"], forms["negpast_cas"])
    assert got == expected, f"{hira}: got {got}, expected {expected}"


def test_kawaii_is_not_treated_as_good(i_adj_info):
    """The critical distinction: かわいい must NOT use the よ-stem."""
    forms, is_good = i_adj_info("かわいい")
    assert is_good is False
    assert forms["neg_cas"] == "かわいくない"
    assert "よ" not in forms["neg_cas"]


@pytest.mark.parametrize("hira", ["いい", "よい", "あたまがいい", "なかがいい", "かっこいい"])
def test_good_words_flagged_irregular(i_adj_info, hira):
    _, is_good = i_adj_info(hira)
    assert is_good is True


@pytest.mark.parametrize("hira", ["たかい", "かわいい", "せがたかい", "おいしい"])
def test_regular_words_not_flagged(i_adj_info, hira):
    _, is_good = i_adj_info(hira)
    assert is_good is False


def test_slash_form_uses_primary(i_adj_info):
    """しょっぱい / しおからい must conjugate from the first form only."""
    forms, _ = i_adj_info("しょっぱい / しおからい")
    assert forms["neg_cas"] == "しょっぱくない"
    assert forms["past_cas"] == "しょっぱかった"
    assert "/" not in forms["neg_cas"]


@pytest.mark.parametrize(
    "hira,expected_neg",
    [
        ("ぐあいがいい", "ぐあいがよくない"),  # synthetic 〜がいい compound (good)
        ("つごうがいい", "つごうがよくない"),  # synthetic 〜がいい compound (good)
        ("あかい",       "あかくない"),        # plain
    ],
)
def test_i_adj_info_generalizes(i_adj_info, hira, expected_neg):
    forms, _ = i_adj_info(hira)
    assert forms["neg_cas"] == expected_neg


def test_single_trailing_i_only_stripped(i_adj_info):
    """rstrip('い') over-stripped double-い words; we drop exactly one い."""
    forms, _ = i_adj_info("かわいい")
    # If both い were stripped we'd get かわくない (the old bug).
    assert forms["neg_cas"] != "かわくない"


# ── Integration: audit the actually-generated conjugation cards ───
CONJ_DECK_FORM = {
    "adj_conj_i_neg_cas": "neg_cas",
    "adj_conj_i_past_cas": "past_cas",
    "adj_conj_i_negpast_cas": "negpast_cas",
}


def _i_adj_conj_cards(decks):
    for d in decks:
        form = CONJ_DECK_FORM.get(d["id"])
        if form:
            for c in d["cards"]:
                yield c, form


def test_generated_i_adj_conjugations_match_reference(decks):
    """Every generated い-adj conjugation matches the independent reference."""
    mismatches = []
    count = 0
    for card, form in _i_adj_conj_cards(decks):
        count += 1
        expected = reference_i_adj(card["front"])[form]
        if card["back"] != expected:
            mismatches.append(f"{card['front']} [{form}]: {card['back']} != {expected}")
    assert count > 0, "no い-adjective conjugation cards were generated"
    assert not mismatches, "Conjugation mismatches:\n" + "\n".join(mismatches)


def test_previously_broken_words_now_correct(decks):
    """The six words corrupted by the original bug, asserted in real output."""
    expected = {
        "いい / よい":             ("よくない", "よかった", "よくなかった"),
        "あたまがいい":           ("あたまがよくない", "あたまがよかった", "あたまがよくなかった"),
        "かっこいい":             ("かっこよくない", "かっこよかった", "かっこよくなかった"),
        "なかがいい":             ("なかがよくない", "なかがよかった", "なかがよくなかった"),
        "かわいい":               ("かわいくない", "かわいかった", "かわいくなかった"),
        "しょっぱい / しおからい": ("しょっぱくない", "しょっぱかった", "しょっぱくなかった"),
    }
    by_front = {}
    for card, form in _i_adj_conj_cards(decks):
        by_front.setdefault(card["front"], {})[form] = card["back"]

    for front, (neg, past, negpast) in expected.items():
        assert front in by_front, f"missing conjugation cards for {front}"
        got = (by_front[front]["neg_cas"], by_front[front]["past_cas"], by_front[front]["negpast_cas"])
        assert got == (neg, past, negpast), f"{front}: got {got}"


# NB: do not include 'いくない' here — it is a legitimate substring of かわい-くない.
@pytest.mark.parametrize(
    "artifact",
    [
        "あたまがくない",
        "なかがくない",
        "かっこくない",
        "かわくない",
        "あたまがくなかった",
        "なかがかった",
        "かっこかった",
    ],
)
def test_no_buggy_conjugation_artifacts(built, artifact):
    """None of the old wrong forms may appear anywhere in the built app."""
    assert artifact not in built.html, f"buggy form {artifact!r} present in output"


def test_no_unresolved_conjugation_placeholders(decks):
    """Conjugation answers should never be the '?' fallback or empty."""
    for d in decks:
        if d.get("type") == "conjugation":
            for c in d["cards"]:
                assert c["back"] not in ("", "?"), f"{d['id']} / {c['front']} has bad answer"


# ── na-adjective polite forms (slash handling) ────────────────────
def test_na_adj_slash_uses_primary(decks):
    neg = {c["front"]: c["back"] for d in decks if d["id"] == "adj_conj_na_neg_pol" for c in d["cards"]}
    past = {c["front"]: c["back"] for d in decks if d["id"] == "adj_conj_na_past_pol" for c in d["cards"]}
    assert neg["たいせつ / だいじ"] == "たいせつではありません"
    assert past["たいせつ / だいじ"] == "たいせつでした"


def test_na_adj_basic_forms(decks):
    neg = {c["front"]: c["back"] for d in decks if d["id"] == "adj_conj_na_neg_pol" for c in d["cards"]}
    assert neg["きれい"] == "きれいではありません"
    assert neg["げんき"] == "げんきではありません"
