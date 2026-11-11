"""Shared page chrome: icon sprite, header, contents sidebar, dialogs. Used by build.py for every page."""
from __future__ import annotations

import html

NBSP = "\u00a0"


def b(en: str, fr: str) -> str:
    fr = fr.replace(" :", NBSP + ":").replace(" ?", "\u202f?")
    return f'<span class="l-en" lang="en">{en}</span><span class="l-fr" lang="fr">{fr}</span>'


def attr(en: str, fr: str, name: str = "aria-label") -> str:
    return f'{name}="{html.escape(en)}" data-label-en="{html.escape(en)}" data-label-fr="{html.escape(fr)}"'


# One icon set: 24px grid, stroke only, currentColor; vector-effect keeps the stroke width constant when scaled.
_ICONS = {
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "home": '<path d="M4 11 12 4l8 7M6 10v10h12V10"/>',
    "route": '<rect x="3" y="3" width="6" height="6" rx="1.5"/><rect x="15" y="15" width="6" height="6" rx="1.5"/><path d="M6 9v4a2 2 0 0 0 2 2h7"/>',
    "workflow": '<rect x="3" y="4" width="7" height="6" rx="1.5"/><rect x="14" y="14" width="7" height="6" rx="1.5"/><path d="M10 7h4a3 3 0 0 1 3 3v4"/>',
    "bot": '<rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 4v4M9 13v1M15 13v1"/>',
    "package": '<path d="m12 3 8 4v10l-8 4-8-4V7zM4 7l8 4 8-4M12 11v10"/>',
    "wrench": '<path d="M14.5 6.5a4 4 0 0 0 5 5L10 21a2.1 2.1 0 0 1-3-3z"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 3 3 5-6"/>',
    "ring": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "triangle": '<path d="M12 4 21 20H3z"/><path d="M12 10v4M12 17v.5"/>',
    "x-circle": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>',
    "x": '<path d="m6 6 12 12M18 6 6 18"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7"/>',
    "arrow-up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "arrow-down": '<path d="M12 5v14M6 13l6 6 6-6"/>',
    "sort": '<path d="M8 5v14M4 9l4-4 4 4M16 19V5M12 15l4 4 4-4"/>',
    "chevron-right": '<path d="m9 5 7 7-7 7"/>',
    "keyboard": '<rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 10h.5M10 10h.5M14 10h.5M18 10h.5M7 14h10"/>',
    "grid": '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
    "file": '<path d="M6 3h8l4 4v14H6zM14 3v4h4"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "loader": '<path d="M12 3a9 9 0 1 0 9 9"/>',
    "alert": '<circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/>',
    "palette": '<path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 1.5-2s0-2 1.5-2h2a3 3 0 0 0 3-3c0-6-4-11-8-11z"/><path d="M7.5 11h.5M10 7.5h.5M14.5 8h.5"/>',
    "sun-moon": '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11M4 6h.5M4 12h.5M4 18h.5"/>',
}


def sprite() -> str:
    ve = ' vector-effect="non-scaling-stroke"'
    parts = []
    for name, body in _ICONS.items():
        for tag in ("<path", "<circle", "<rect"):
            body = body.replace(tag, tag + ve)
        parts.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{body}</symbol>')
    symbols = "".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="sprite" width="0" height="0" aria-hidden="true" '
            f'focusable="false" data-no-translate>{symbols}</svg>')


def icon(name: str, size: str = "") -> str:
    cls = f"icon {size}".strip()
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


NAV_ICONS = {"home": "home", "pipeline": "route", "workflows": "workflow", "agents": "bot", "release": "package", "setup": "wrench"}
# Primary items stay in the bottom bar on small screens; the rest move into the contents drawer.
SHORT = {"home": ("Home", "Accueil"), "pipeline": ("Pipeline", "Pipeline"), "workflows": ("Workflows", "Workflows"),
         "agents": ("Agents", "Agents")}


def header(root: str, nav: list[tuple[str, str, str, str]], key: str) -> str:
    items = []
    for nav_key, href, en, fr in nav:
        cur = ' aria-current="page"' if nav_key == key else ""
        extra = "" if nav_key in SHORT else ' class="nav-extra"'
        s_en, s_fr = SHORT.get(nav_key, (en, fr))
        label = f'<span class="l-en" lang="en">{s_en}</span><span class="l-fr" lang="fr">{s_fr}</span>'
        items.append(f'<a href="{root}{href}"{cur}{extra}>{icon(NAV_ICONS[nav_key])}{label}</a>')
    more = (f'<button type="button" class="nav-more js-only" data-open-contents aria-controls="site-contents">{icon("menu")}'
            f'{b("More", "Plus")}</button>')
    return f"""<header class="app-header" data-no-translate>
    <button type="button" class="icon-btn js-only" id="nav-toggle" aria-controls="site-contents" aria-expanded="false" {attr("Contents", "Sommaire")}>{icon("menu")}</button>
    <a class="brand" href="{root}" aria-label="agentic-pipelines">{icon("route")}<span class="brand-name">agentic-pipelines</span></a>
    <nav class="site-nav" {attr("Site", "Site")}>{"".join(items)}{more}</nav>
    <div class="header-actions">
      <button type="button" class="btn js-only" id="open-search" aria-haspopup="dialog" {attr("Search pages and actions", "Rechercher des pages et des actions")}>{icon("search")}<span class="hide-narrow">{b("Search", "Rechercher")}</span><kbd class="hide-narrow">Ctrl K</kbd></button>
      <button type="button" class="btn js-only" id="open-prefs" aria-haspopup="dialog" aria-expanded="false" aria-controls="prefs-dialog" {attr("Display settings", "Paramètres d’affichage")}>{icon("settings")}<span class="hide-narrow">{b("Display", "Affichage")}</span></button>
      <button class="btn language-switch js-only" type="button" role="switch" aria-checked="false" data-language-switch {attr("Use French", "Utiliser l’anglais")}>{icon("globe")}<span lang="en" class="l-en">EN</span><span lang="fr" class="l-fr">FR</span></button>
    </div>
  </header>"""


def sidenav(root: str, current: str, tree: list[tuple[tuple[str, str], list[tuple[str, str, str]]]]) -> str:
    groups = []
    for (g_en, g_fr), entries in tree:
        lis = []
        for url, t_en, t_fr in entries:
            cur = ' aria-current="page"' if url == current else ""
            lis.append(f'<li><a href="{root}{url}"{cur}>{b(html.escape(t_en), html.escape(t_fr))}</a></li>')
        groups.append(f'<li class="nav-group"><div class="nav-heading">{b(g_en, g_fr)}</div><ul>{"".join(lis)}</ul></li>')
    return f"""<nav class="sidenav" id="site-contents" data-no-translate {attr("Contents", "Sommaire")}>
      <div class="sidenav-filter js-only"><label class="nav-heading" for="nav-filter">{b("Filter pages", "Filtrer les pages")}</label>
      <input id="nav-filter" type="search" autocomplete="off" {attr("Filter pages", "Filtrer les pages")}></div>
      <div class="sidenav-scroll"><ul>{"".join(groups)}</ul><p class="nav-empty hint" hidden>{b("No pages match.", "Aucune page ne correspond.")}</p></div>
    </nav>"""


def _seg(name: str, legend: tuple[str, str], opts: list[tuple[str, str, str]]) -> str:
    inputs = "".join(
        f'<label><input type="radio" name="{name}" value="{v}"><span>{b(en, fr)}</span></label>' for v, en, fr in opts)
    return f'<fieldset><legend>{b(*legend)}</legend><div class="seg">{inputs}</div></fieldset>'


def _toggle(name: str, en: str, fr: str, d_en: str, d_fr: str) -> str:
    return (f'<label class="toggle-row"><input type="checkbox" name="{name}"><span><span class="toggle-label">{b(en, fr)}</span>'
            f'<small>{b("Default: " + d_en, "Par défaut : " + d_fr)}</small></span></label>')


ACCENTS = ["blue", "purple", "slate", "teal", "green", "orange", "pink", "indigo"]
ACCENT_FR = {"blue": "Bleu", "purple": "Violet", "slate": "Ardoise", "teal": "Sarcelle", "green": "Vert", "orange": "Orange", "pink": "Rose", "indigo": "Indigo"}


def _close(target: str) -> str:
    return (f'<button type="button" class="close-button" data-close {attr("Close", "Fermer")}>{icon("x")}</button>')


def dialogs() -> str:
    swatches = "".join(
        f'<label><input type="radio" name="accent" value="{a}" {attr(a.capitalize(), ACCENT_FR[a])}><span><i class="sw-{a}"></i></span></label>'
        for a in ACCENTS)
    prefs = f"""<div class="prefs-layer" id="prefs-layer" hidden data-no-translate>
  <div class="dialog prefs-dialog" id="prefs-dialog" role="dialog" aria-modal="true" aria-labelledby="prefs-title">
    <div class="dialog-head"><h2 id="prefs-title">{b("Display settings", "Paramètres d’affichage")}</h2>{_close("prefs")}</div>
    <div class="dialog-body" data-prefs-body>
      {_seg("colorMode", ("Color theme", "Thème de couleurs"), [("system", "System", "Système"), ("light", "Light", "Clair"), ("dark", "Dark", "Sombre")])}
      {_seg("contrastMode", ("Contrast", "Contraste"), [("system", "System", "Système"), ("standard", "Standard", "Standard"), ("high", "High", "Élevé")])}
      <fieldset><legend>{b("Accent color", "Couleur d’accent")}</legend><div class="swatches">{swatches}</div>
      <p class="hint-small">{b("Accent never changes focus rings or status colors, and is ignored in high contrast.", "L’accent ne change ni les anneaux de focus ni les couleurs d’état, et il est ignoré en contraste élevé.")}</p></fieldset>
      {_seg("density", ("Density", "Densité"), [("compact", "Compact", "Compact"), ("comfortable", "Comfortable", "Confortable"), ("spacious", "Spacious", "Aéré")])}
      {_seg("motion", ("Motion", "Animations"), [("system", "System", "Système"), ("reduce", "Reduce", "Réduire"), ("full", "Full", "Complètes")])}
      {_toggle("readableText", "Readable text", "Texte plus lisible", "off", "désactivé")}
      {_toggle("largerTargets", "Larger click targets", "Cibles plus grandes", "off (44px on touch)", "désactivé (44 px au tactile)")}
      {_toggle("strongFocus", "Stronger focus ring", "Anneau de focus renforcé", "off", "désactivé")}
      {_toggle("shortcuts", "Single-key shortcuts", "Raccourcis à une touche", "on", "activé")}
    </div>
    <div class="dialog-foot"><button type="button" class="btn" data-prefs-reset>{b("Reset to defaults", "Rétablir les valeurs par défaut")}</button>
      <p class="hint" data-prefs-status role="status"></p></div>
  </div>
</div>"""
    palette = f"""<div class="modal-layer" id="palette-layer" hidden data-no-translate>
  <div class="dialog palette" role="dialog" aria-modal="true" aria-labelledby="palette-title">
    <h2 class="sr-only" id="palette-title">{b("Search pages and actions", "Rechercher des pages et des actions")}</h2>
    <div class="palette-input">{icon("search")}
      <input id="palette-input" type="text" role="combobox" aria-expanded="true" aria-controls="palette-list" aria-autocomplete="list" aria-activedescendant="" autocomplete="off" spellcheck="false" {attr("Search pages, workflows and actions", "Rechercher des pages, workflows et actions")} placeholder="Search pages, workflows and actions" data-placeholder-en="Search pages, workflows and actions" data-placeholder-fr="Rechercher des pages, workflows et actions">
      <button type="button" class="close-button" data-close {attr("Close", "Fermer")}>{icon("x")}</button></div>
    <ul id="palette-list" class="palette-list" role="listbox" {attr("Results", "Résultats")}></ul>
    <div class="palette-empty" id="palette-empty" hidden>{icon("search", "icon-24")}<div>{b("No results. Try fewer letters.", "Aucun résultat. Essayez moins de lettres.")}</div></div>
    <div class="palette-foot"><span><kbd>↑</kbd> <kbd>↓</kbd> {b("move", "naviguer")}</span><span><kbd>Enter</kbd> {b("open", "ouvrir")}</span><span><kbd>Esc</kbd> {b("close", "fermer")}</span><span>{b("Prefix", "Préfixe")} <kbd>&gt;</kbd> {b("actions", "actions")}</span></div>
    <p class="sr-only" id="palette-count" role="status" aria-live="polite"></p>
  </div>
</div>"""
    rows = [
        (["Ctrl", "K"], "or /", "ou /", "Search pages, workflows and actions", "Rechercher des pages, workflows et actions"),
        (["?"], "", "", "Show this help", "Afficher cette aide"),
        (["G"], "", "", "Open the page overview grid", "Ouvrir la grille des pages"),
        (["C"], "", "", "Show or hide the contents sidebar", "Afficher ou masquer le sommaire"),
        (["T"], "", "", "Cycle color theme", "Changer de thème de couleurs"),
        ([","], "", "", "Open display settings", "Ouvrir les paramètres d’affichage"),
        (["Esc"], "", "", "Close the open panel", "Fermer le panneau ouvert"),
        (["Tab"], "", "", "Move between controls", "Passer d’un contrôle à l’autre"),
        (["←", "→"], "", "", "Move between tabs and nav items", "Passer d’un onglet à l’autre"),
    ]
    dl = "".join(
        f'<dt>{" ".join(f"<kbd>{k}</kbd>" for k in keys)}{(" " + b(o_en, o_fr)) if o_en else ""}</dt><dd>{b(d_en, d_fr)}</dd>'
        for keys, o_en, o_fr, d_en, d_fr in rows)
    help_ = f"""<div class="modal-layer centered" id="help-layer" hidden data-no-translate>
  <div class="dialog help-dialog" role="dialog" aria-modal="true" aria-labelledby="help-title">
    <div class="dialog-head"><h2 id="help-title">{b("Keyboard shortcuts", "Raccourcis clavier")}</h2>{_close("help")}</div>
    <div class="dialog-body"><dl class="help-list">{dl}</dl>
    <p class="hint-small">{b("Single-key shortcuts only work outside text fields and can be turned off in display settings.", "Les raccourcis à une touche fonctionnent hors des champs de texte et se désactivent dans les paramètres d’affichage.")}</p></div>
  </div>
</div>"""
    overview = f"""<div class="modal-layer centered" id="overview-layer" hidden data-no-translate>
  <div class="dialog overview-dialog" role="dialog" aria-modal="true" aria-labelledby="overview-title">
    <div class="dialog-head"><h2 id="overview-title">{b("All pages", "Toutes les pages")}</h2>{_close("overview")}</div>
    <div class="dialog-body" id="overview-body"></div>
  </div>
</div>"""
    stats = f"""<div class="modal-layer centered" id="stat-layer" hidden data-no-translate>
  <div class="dialog stat-dialog" role="dialog" aria-modal="true" aria-labelledby="stat-title">
    <div class="dialog-head"><h2 id="stat-title"></h2>{_close("stat")}</div>
    <div class="dialog-body" id="stat-body" tabindex="0"></div>
  </div>
</div>"""
    return (f'{prefs}\n{palette}\n{help_}\n{overview}\n{stats}\n<div class="nav-scrim" id="nav-scrim" hidden></div>\n'
            '<div class="sr-only" id="live" role="status" aria-live="polite" aria-atomic="true"></div>')
