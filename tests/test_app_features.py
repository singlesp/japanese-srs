"""
Assert the generated single-file app contains the wiring for each feature, that
its embedded JavaScript is syntactically valid, and that the report address is
exactly what the owner configured.
"""

import shutil
import subprocess

import pytest


# ── JavaScript validity ───────────────────────────────────────────
def test_embedded_js_is_valid(built, tmp_path):
    """node --check the extracted <script> block (skipped if node is absent)."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not available")
    js = tmp_path / "app.js"
    js.write_text(built.script, encoding="utf-8")
    proc = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
    assert proc.returncode == 0, f"JS syntax error:\n{proc.stderr}"


# ── Search ────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "needle",
    [
        'id="search-input"',
        'id="search-results"',
        "const SEARCH_INDEX",
        "function runSearch(",
        "cardId:",                 # search results deep-link to a specific card
        "data-card=",
        "openBrowse(card.dataset.deck, card.dataset.card)",
    ],
)
def test_search_wiring(built, needle):
    assert needle in built.html, f"search wiring missing: {needle}"


# ── Browse + single-card practice ─────────────────────────────────
@pytest.mark.parametrize(
    "needle",
    [
        'id="screen-browse"',
        'id="browse-list"',
        "function renderBrowse(",
        "function openBrowse(",
        "function practiceCard(",
        "function browseDeckView(",
        'class="deck-browse"',
        "initBrowseClicks()",
    ],
)
def test_browse_wiring(built, needle):
    assert needle in built.html, f"browse wiring missing: {needle}"


# ── Favorites ─────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "needle",
    [
        "jp_srs_favs_v1",
        "function toggleFav(",
        "function favCards(",
        "function resolveCards(",
        "'__favs__'",
        'class="fav-banner"',
        'id="study-star"',
        'class="browse-star',
    ],
)
def test_favorites_wiring(built, needle):
    assert needle in built.html, f"favorites wiring missing: {needle}"


def test_favorites_included_in_export(built):
    assert "favorites: [...loadFavs()]" in built.html
    assert "jp_srs_backup_v1" in built.html  # versioned backup format
    # legacy import path preserved
    assert "legacy" in built.html.lower() or "_format" in built.html


# ── Report an issue ───────────────────────────────────────────────
def test_report_wiring(built):
    for needle in [
        'id="report-modal"',
        "function sendReport(",
        "function openReportModal(",
        "reportCurrentCard()",
        "mailto:",
        "encodeURIComponent",
    ]:
        assert needle in built.html, f"report wiring missing: {needle}"


def test_report_email_is_configured_address(built):
    assert "REPORT_EMAIL = 'spsingleton.gwb@gmail.com'" in built.html
    # exactly one place defines the recipient
    assert built.html.count("spsingleton.gwb@gmail.com") == 1


def test_report_body_avoids_raw_newline_escapes(built):
    """The mailto body is built with String.fromCharCode(10), not '\\n' literals
    (a '\\n' inside the single-quoted template would have broken the JS)."""
    assert "String.fromCharCode(10)" in built.script


# ── General hygiene ───────────────────────────────────────────────
def test_no_rstrip_double_strip_bug(built):
    """No actual rstrip() *call* in build_app.py code (comments may mention it).

    rstrip('い') strips ALL trailing い and caused the original double-い bug.
    """
    import ast

    from conftest import BUILD_PATH

    tree = ast.parse(BUILD_PATH.read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "rstrip"
    ]
    assert not calls, "rstrip(...) call reintroduces the double-い stripping bug"


def test_single_script_block(built):
    assert built.html.count("<script>") == 1
    assert built.html.count("</script>") == 1


def test_core_screens_present(built):
    for sid in ["screen-intro", "screen-home", "screen-study", "screen-complete", "screen-browse"]:
        assert f'id="{sid}"' in built.html, f"missing screen {sid}"
