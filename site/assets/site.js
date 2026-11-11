/* Site behaviour: overlays, display preferences UI, command palette, shortcuts, contents navigation,
   language switch, copy buttons and sortable tables. Preference state lives in boot.js (window.SiteDisplay). */
(function () {
  "use strict";
  var root = document.documentElement;
  var display = window.SiteDisplay;
  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  var RECENT_KEY = "site.recent.v1";
  var NAV_KEY = "site.nav.v1";

  function $(selector, scope) { return (scope || document).querySelector(selector); }
  function $$(selector, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }
  function lang() { return root.lang === "fr" ? "fr" : "en"; }
  function pick(pair) { return pair[lang() === "fr" ? 1 : 0]; }
  function store(key) { try { return window.localStorage.getItem(key); } catch (error) { return null; } }
  function save(key, value) { try { window.localStorage.setItem(key, value); } catch (error) { /* storage blocked */ } }
  function visible(element) { return !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length); }
  function icon(name) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "icon");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", "#i-" + name);
    svg.appendChild(use);
    return svg;
  }
  function bilingual(en, fr) {
    var wrap = document.createDocumentFragment();
    [["en", en], ["fr", fr]].forEach(function (pair) {
      var span = document.createElement("span");
      span.className = "l-" + pair[0];
      span.lang = pair[0];
      span.textContent = pair[1];
      wrap.appendChild(span);
    });
    return wrap;
  }

  /* ------------------------------------------------------------ live region */
  var live = null;
  var liveTimer = 0;
  function announce(message) {
    if (!live) return;
    live.textContent = "";
    window.clearTimeout(liveTimer);
    liveTimer = window.setTimeout(function () { live.textContent = message; }, 40);
  }

  /* ------------------------------------------------------------ language */
  function applyLabels() {
    $$("[data-label-en]").forEach(function (element) {
      if (element.hasAttribute("data-language-switch") && window.pipelineI18n) return;
      var text = element.getAttribute("data-label-" + lang());
      element.setAttribute("aria-label", text);
      if (element.hasAttribute("data-title")) element.title = text;
    });
    $$("[data-placeholder-en]").forEach(function (element) {
      element.placeholder = element.getAttribute("data-placeholder-" + lang());
    });
    var title = $("title");
    if (title && !window.pipelineI18n) {
      if (!title.dataset.en) title.dataset.en = title.textContent;
      title.textContent = lang() === "fr" && title.dataset.fr ? title.dataset.fr : title.dataset.en;
    }
    $$("[data-language-switch]").forEach(function (button) {
      if (!window.pipelineI18n) button.setAttribute("aria-checked", String(lang() === "fr"));
    });
  }
  function setLanguage(next) {
    root.lang = next;
    if (display) save(display.languageKey, next);
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("lang", next);
      window.history.replaceState(null, "", url.pathname + url.search + url.hash);
    } catch (error) { /* history unavailable */ }
    applyLabels();
    announce(next === "fr" ? "Langue : français" : "Language: English");
  }
  function bindLanguage() {
    $$("[data-language-switch]").forEach(function (button) {
      button.hidden = false;
      if (window.pipelineI18n) return;
      button.addEventListener("click", function () { setLanguage(lang() === "fr" ? "en" : "fr"); });
    });
    applyLabels();
    new MutationObserver(function () { applyLabels(); renderPalette(); }).observe(root, { attributes: true, attributeFilter: ["lang"] });
  }

  /* ------------------------------------------------------------ overlays */
  var openLayer = null;
  var returnFocus = null;
  var inertTargets = [];

  function setInert(on) {
    if (on) {
      inertTargets = $$(".skip, .app-header, .app-shell, .site-footer");
      inertTargets.forEach(function (node) { node.inert = true; });
    } else {
      inertTargets.forEach(function (node) { node.inert = false; });
      inertTargets = [];
    }
  }
  function closeLayer(restore) {
    if (!openLayer) return;
    var layer = openLayer;
    openLayer = null;
    layer.hidden = true;
    setInert(false);
    var opener = $("#open-prefs");
    if (opener) opener.setAttribute("aria-expanded", "false");
    if (restore !== false && returnFocus && returnFocus.isConnected && visible(returnFocus)) returnFocus.focus();
    returnFocus = null;
  }
  function showLayer(layer, focusTarget) {
    if (!layer) return;
    if (openLayer) closeLayer(false);
    if (root.classList.contains("nav-open")) setNav(false, false);
    returnFocus = document.activeElement;
    openLayer = layer;
    layer.hidden = false;
    setInert(true);
    var target = focusTarget || $(FOCUSABLE, $(".dialog", layer) || layer);
    if (target) target.focus();
  }
  function trap(event) {
    if (!openLayer || event.key !== "Tab") return;
    var items = $$(FOCUSABLE, openLayer).filter(visible);
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || !openLayer.contains(document.activeElement))) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  function bindStats() {
    $$("[data-stat-list]").forEach(function (card) {
      card.addEventListener("click", function () {
        var tpl = document.getElementById(card.dataset.statList);
        if (!tpl) return;
        var fr = lang() === "fr";
        $("#stat-title").textContent = (fr ? card.dataset.titleFr : card.dataset.titleEn) + " (" + card.dataset.count + ")";
        var body = $("#stat-body");
        body.textContent = "";
        body.appendChild(tpl.content.cloneNode(true));
        body.scrollTop = 0;
        showLayer($("#stat-layer"), $("a", body) || body);
      });
    });
  }
  function bindLayers() {
    $$(".prefs-layer, .modal-layer").forEach(function (layer) {
      layer.addEventListener("mousedown", function (event) { if (event.target === layer) closeLayer(); });
      $$("[data-close]", layer).forEach(function (button) { button.addEventListener("click", function () { closeLayer(); }); });
    });
  }

  /* ------------------------------------------------------------ preferences panel */
  var CYCLE = ["system", "light", "dark"];
  function syncPrefs() {
    if (!display) return;
    var prefs = display.get();
    $$("[data-prefs-body] input[type=radio]").forEach(function (input) { input.checked = prefs[input.name] === input.value; });
    $$("[data-prefs-body] input[type=checkbox]").forEach(function (input) { input.checked = prefs[input.name] === true; });
    var status = $("[data-prefs-status]");
    var state = display.status();
    if (status && !status.dataset.busy) {
      status.textContent = state.invalid ? (lang() === "fr" ? "Préférences enregistrées invalides : valeurs par défaut utilisées." : "Saved preferences were invalid; defaults are in use.")
        : state.blocked ? (lang() === "fr" ? "Stockage bloqué : les choix ne durent que pour cette page." : "Storage is blocked; choices last for this page only.") : "";
    }
  }
  function bindPrefs() {
    var body = $("[data-prefs-body]");
    if (!body || !display) return;
    syncPrefs();
    display.onChange(syncPrefs);
    body.addEventListener("change", function (event) {
      var input = event.target;
      var change = {};
      change[input.name] = input.type === "checkbox" ? input.checked : input.value;
      if (display.set(change)) {
        var status = $("[data-prefs-status]");
        var name = input.closest("label") ? input.closest("label").textContent.trim() : input.name;
        var message = (lang() === "fr" ? "Enregistré : " : "Saved: ") + name;
        if (status) { status.dataset.busy = "1"; status.textContent = message; window.setTimeout(function () { delete status.dataset.busy; }, 1500); }
      }
    });
    $("[data-prefs-reset]").addEventListener("click", function () {
      display.reset();
      announce(lang() === "fr" ? "Préférences rétablies" : "Preferences reset to defaults");
    });
    var opener = $("#open-prefs");
    if (opener) opener.addEventListener("click", function () { openPrefs(); });
  }
  function openPrefs() {
    syncPrefs();
    showLayer($("#prefs-layer"), $("[data-prefs-body] input:checked") || null);
    var opener = $("#open-prefs");
    if (opener) opener.setAttribute("aria-expanded", "true");
  }
  function cycleTheme() {
    if (!display) return;
    var next = CYCLE[(CYCLE.indexOf(display.get().colorMode) + 1) % CYCLE.length];
    display.set({ colorMode: next });
    var names = { en: { system: "system", light: "light", dark: "dark" }, fr: { system: "système", light: "clair", dark: "sombre" } };
    announce((lang() === "fr" ? "Thème : " : "Theme: ") + names[lang()][next]);
  }

  /* ------------------------------------------------------------ contents navigation */
  function wide() { return window.matchMedia("(min-width: 1440px)").matches; }
  function navShown() { return wide() ? root.dataset.nav !== "collapsed" : root.classList.contains("nav-open"); }
  function syncNavButton() {
    var button = $("#nav-toggle");
    if (button) button.setAttribute("aria-expanded", String(navShown()));
    var scrim = $("#nav-scrim");
    if (scrim) scrim.hidden = wide() || !root.classList.contains("nav-open");
  }
  function setNav(open, focus) {
    if (wide()) {
      if (open) delete root.dataset.nav; else root.dataset.nav = "collapsed";
      save(NAV_KEY, open ? "open" : "collapsed");
    } else {
      root.classList.toggle("nav-open", open);
      if (open && focus !== false) { var field = $("#nav-filter"); if (field && visible(field)) field.focus(); }
      if (!open && focus !== false) { var button = $("#nav-toggle"); if (button && visible(button)) button.focus(); }
    }
    syncNavButton();
  }
  function bindNav() {
    if (store(NAV_KEY) === "collapsed") root.dataset.nav = "collapsed";
    var toggle = $("#nav-toggle");
    if (toggle) toggle.addEventListener("click", function () { setNav(!navShown()); });
    $$("[data-open-contents]").forEach(function (button) { button.addEventListener("click", function () { setNav(true); }); });
    var scrim = $("#nav-scrim");
    if (scrim) scrim.addEventListener("click", function () { setNav(false); });
    $$("#site-contents a").forEach(function (anchor) {
      anchor.addEventListener("click", function () { if (!wide()) root.classList.remove("nav-open"); syncNavButton(); });
    });
    window.matchMedia("(min-width: 1440px)").addEventListener("change", function () { root.classList.remove("nav-open"); syncNavButton(); });
    syncNavButton();
    var current = $("#site-contents [aria-current='page']");
    var scroller = $(".sidenav-scroll");
    if (current && scroller) scroller.scrollTop = Math.max(0, current.offsetTop - scroller.clientHeight / 2);

    var filter = $("#nav-filter");
    if (filter) {
      filter.addEventListener("input", function () {
        var query = filter.value.trim();
        var shown = 0;
        $$("#site-contents .nav-group").forEach(function (group) {
          var any = false;
          $$("li", group).forEach(function (item) {
            var hit = !query || !!fuzzy(query, item.textContent.replace(/\s+/g, " "));
            item.hidden = !hit;
            if (hit) { any = true; shown += 1; }
          });
          group.hidden = !any;
        });
        var empty = $(".nav-empty");
        if (empty) empty.hidden = shown > 0;
        announce(shown + (lang() === "fr" ? " pages" : " pages"));
      });
    }
  }

  /* Roving tabindex: one tab stop per group, arrow keys move within it. */
  function rove(container, selector, keys) {
    if (!container) return;
    function items() { return $$(selector, container).filter(function (node) { return !node.closest("[hidden]") && visible(node); }); }
    function setStop(target) {
      $$(selector, container).forEach(function (node) { node.tabIndex = node === target ? 0 : -1; });
    }
    function init() {
      var list = items();
      if (!list.length) return;
      setStop(list.filter(function (node) { return node.getAttribute("aria-current") === "page"; })[0] || list[0]);
    }
    container.addEventListener("focusin", function (event) {
      if (event.target.matches && event.target.matches(selector)) setStop(event.target);
    });
    container.addEventListener("keydown", function (event) {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      var list = items();
      var index = list.indexOf(document.activeElement);
      if (index < 0 || keys.indexOf(event.key) < 0 && event.key !== "Home" && event.key !== "End") return;
      var forward = event.key === keys[1];
      var next = event.key === "Home" ? 0 : event.key === "End" ? list.length - 1 : (index + (forward ? 1 : -1) + list.length) % list.length;
      event.preventDefault();
      list[next].focus();
    });
    window.addEventListener("resize", init);
    init();
  }

  /* ------------------------------------------------------------ fuzzy search + command palette */
  function fold(text) {
    var out = "";
    for (var i = 0; i < text.length; i += 1) out += text.charAt(i).normalize("NFD").charAt(0).toLowerCase();
    return out;
  }
  // Returns {score, idx} for a substring or in-order subsequence match, else null.
  function fuzzy(query, text) {
    var q = fold(query).replace(/\s+/g, "");
    var t = fold(text);
    if (!q) return { score: 0, idx: [] };
    var at = t.indexOf(fold(query.trim()));
    var idx = [];
    var i;
    if (at >= 0) {
      for (i = 0; i < query.trim().length; i += 1) idx.push(at + i);
      return { score: 200 - at - t.length / 10 + (at === 0 || /\W/.test(t.charAt(at - 1)) ? 40 : 0), idx: idx };
    }
    var pos = 0;
    var score = 0;
    var last = -2;
    for (i = 0; i < q.length; i += 1) {
      var found = t.indexOf(q.charAt(i), pos);
      if (found < 0) return null;
      score += found === last + 1 ? 12 : 2;
      if (found === 0 || /\W/.test(t.charAt(found - 1))) score += 8;
      idx.push(found);
      last = found;
      pos = found + 1;
    }
    return { score: score - t.length / 20, idx: idx };
  }

  var palette = { selected: 0, results: [], query: "" };
  var recents = [];
  function loadRecents() {
    try {
      var list = JSON.parse(store(RECENT_KEY));
      recents = Array.isArray(list) ? list.filter(function (item) { return typeof item === "string"; }).slice(0, 8) : [];
    } catch (error) { recents = []; }
  }
  function remember(id) {
    recents = [id].concat(recents.filter(function (item) { return item !== id; })).slice(0, 8);
    save(RECENT_KEY, JSON.stringify(recents));
  }
  function actions() {
    return [
      { id: "a:theme", t: ["Cycle color theme", "Changer de thème de couleurs"], icon: "sun-moon", run: cycleTheme },
      { id: "a:prefs", t: ["Open display settings", "Ouvrir les paramètres d’affichage"], icon: "settings", run: openPrefs },
      { id: "a:lang", t: ["Switch language (English / French)", "Changer de langue (anglais / français)"], icon: "globe", run: function () {
        var button = $("[data-language-switch]");
        if (window.pipelineI18n && button) button.click(); else setLanguage(lang() === "fr" ? "en" : "fr");
      } },
      { id: "a:help", t: ["Show keyboard shortcuts", "Afficher les raccourcis clavier"], icon: "keyboard", run: function () { showLayer($("#help-layer")); } },
      { id: "a:grid", t: ["Open page overview grid", "Ouvrir la grille des pages"], icon: "grid", run: openOverview },
      { id: "a:nav", t: ["Show or hide contents sidebar", "Afficher ou masquer le sommaire"], icon: "list", run: function () { setNav(!navShown()); } },
      { id: "a:reset", t: ["Reset display settings", "Rétablir les paramètres d’affichage"], icon: "x-circle", run: function () { if (display) display.reset(); announce(lang() === "fr" ? "Préférences rétablies" : "Preferences reset to defaults"); } },
      { id: "a:top", t: ["Scroll to top", "Remonter en haut de la page"], icon: "arrow-up", run: function () { window.scrollTo(0, 0); } }
    ];
  }
  function corpus() {
    var base = $("body").dataset.root || "";
    var pages = (window.SITE_INDEX || []).map(function (entry) {
      return { id: "p:" + entry.u, t: entry.t, g: entry.g, icon: entry.u.indexOf("#") > 0 ? "route" : entry.u.indexOf("workflows/") === 0 && entry.u !== "workflows/" ? "workflow" : "file", href: base + entry.u };
    });
    var acts = actions().map(function (item) { item.g = ["Action", "Action"]; item.action = true; return item; });
    return pages.concat(acts);
  }
  function computeResults(raw) {
    var items = corpus();
    var query = raw.replace(/^\s+/, "");
    var onlyActions = query.charAt(0) === ">";
    var onlyPages = /^go\s/i.test(query);
    if (onlyActions) query = query.slice(1);
    if (onlyPages) query = query.slice(3);
    query = query.trim();
    if (onlyActions) items = items.filter(function (item) { return item.action; });
    if (onlyPages) items = items.filter(function (item) { return !item.action; });
    if (!query) {
      var byId = {};
      items.forEach(function (item) { byId[item.id] = item; });
      var recent = recents.map(function (id) { return byId[id]; }).filter(Boolean);
      var rest = items.filter(function (item) { return recent.indexOf(item) < 0 && (onlyActions || !item.action || false); });
      var list = recent.map(function (item) { return { item: item, idx: [], group: ["Recent", "Récents"] }; });
      rest.slice(0, onlyActions ? 20 : 8).forEach(function (item) { list.push({ item: item, idx: [], group: onlyActions ? ["Actions", "Actions"] : ["Suggested", "Suggestions"] }); });
      return list;
    }
    var out = [];
    items.forEach(function (item) {
      var shown = fuzzy(query, pick(item.t));
      var other = fuzzy(query, item.t[lang() === "fr" ? 0 : 1]);
      var sub = fuzzy(query, pick(item.g));
      var best = shown || (other && { score: other.score - 20, idx: [] }) || (sub && { score: sub.score - 60, idx: [] });
      if (best) out.push({ item: item, idx: shown ? shown.idx : [], score: best.score + (recents.indexOf(item.id) >= 0 ? 15 : 0) });
    });
    out.sort(function (a, b) { return b.score - a.score; });
    return out.slice(0, 40);
  }
  function highlight(target, text, idx) {
    var marks = {};
    idx.forEach(function (position) { marks[position] = true; });
    var buffer = "";
    var inMark = false;
    function flush() {
      if (!buffer) return;
      if (inMark) { var mark = document.createElement("mark"); mark.textContent = buffer; target.appendChild(mark); }
      else target.appendChild(document.createTextNode(buffer));
      buffer = "";
    }
    for (var i = 0; i < text.length; i += 1) {
      var on = !!marks[i];
      if (on !== inMark) { flush(); inMark = on; }
      buffer += text.charAt(i);
    }
    flush();
  }
  function renderPalette() {
    var layer = $("#palette-layer");
    if (!layer || layer.hidden) return;
    var input = $("#palette-input");
    var list = $("#palette-list");
    palette.results = computeResults(input.value);
    palette.selected = Math.min(palette.selected, Math.max(0, palette.results.length - 1));
    list.textContent = "";
    var lastGroup = "";
    var failed = !window.SITE_INDEX;
    palette.results.forEach(function (result, index) {
      var group = result.group ? pick(result.group) : "";
      if (group && group !== lastGroup) {
        var heading = document.createElement("li");
        heading.className = "nav-heading palette-group";
        heading.setAttribute("role", "presentation");
        heading.textContent = group;
        list.appendChild(heading);
        lastGroup = group;
      }
      var option = document.createElement("li");
      option.id = "palette-opt-" + index;
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", String(index === palette.selected));
      option.appendChild(icon(result.item.icon || "file"));
      var title = document.createElement("span");
      title.className = "palette-title";
      highlight(title, pick(result.item.t), result.idx);
      option.appendChild(title);
      var kind = document.createElement("span");
      kind.className = "palette-sub";
      kind.textContent = pick(result.item.g);
      option.appendChild(kind);
      option.addEventListener("click", function () { choose(index); });
      list.appendChild(option);
    });
    var empty = $("#palette-empty");
    empty.hidden = palette.results.length > 0;
    list.hidden = palette.results.length === 0;
    input.setAttribute("aria-activedescendant", palette.results.length ? "palette-opt-" + palette.selected : "");
    input.setAttribute("aria-expanded", String(palette.results.length > 0));
    var count = $("#palette-count");
    if (failed) { count.textContent = lang() === "fr" ? "L’index de recherche n’a pas pu être chargé." : "The search index could not be loaded."; }
    else count.textContent = palette.results.length + (lang() === "fr" ? " résultats" : " results");
    var selected = $("#palette-opt-" + palette.selected);
    if (selected && selected.scrollIntoView) selected.scrollIntoView({ block: "nearest" });
  }
  function openPalette(prefill) {
    var input = $("#palette-input");
    if (!input) return;
    loadRecents();
    palette.selected = 0;
    input.value = prefill || "";
    showLayer($("#palette-layer"), input);
    renderPalette();
  }
  function choose(index) {
    var result = palette.results[index];
    if (!result) return;
    var item = result.item;
    remember(item.id);
    closeLayer(!item.action);
    if (item.action) { window.setTimeout(item.run, 0); return; }
    var target = new URL(item.href, window.location.href);
    var here = new URL(window.location.href);
    var same = target.pathname === here.pathname;
    window.location.href = target.href;
    if (same && target.hash) window.setTimeout(function () { window.dispatchEvent(new HashChangeEvent("hashchange")); }, 0);
  }
  function bindPalette() {
    var input = $("#palette-input");
    var button = $("#open-search");
    if (button) button.addEventListener("click", function () { openPalette(); });
    if (!input) return;
    input.addEventListener("input", function () { palette.selected = 0; renderPalette(); });
    input.addEventListener("keydown", function (event) {
      var last = palette.results.length - 1;
      if (event.key === "ArrowDown") { event.preventDefault(); palette.selected = palette.selected >= last ? 0 : palette.selected + 1; renderPalette(); }
      else if (event.key === "ArrowUp") { event.preventDefault(); palette.selected = palette.selected <= 0 ? last : palette.selected - 1; renderPalette(); }
      else if (event.key === "Home" && !input.value) { event.preventDefault(); palette.selected = 0; renderPalette(); }
      else if (event.key === "End" && !input.value) { event.preventDefault(); palette.selected = Math.max(0, last); renderPalette(); }
      else if (event.key === "Enter") { event.preventDefault(); choose(palette.selected); }
    });
  }

  /* ------------------------------------------------------------ overview grid */
  function openOverview() {
    var body = $("#overview-body");
    if (!body) return;
    body.textContent = "";
    var here = window.location.pathname;
    var groups = {};
    var order = [];
    (window.SITE_INDEX || []).forEach(function (entry) {
      if (entry.u.indexOf("#") > 0) return;
      var key = entry.g[0];
      if (!groups[key]) { groups[key] = { title: entry.g, items: [] }; order.push(key); }
      groups[key].items.push(entry);
    });
    if (!order.length) {
      var failure = document.createElement("div");
      failure.className = "state state-error";
      failure.appendChild(icon("alert"));
      failure.appendChild(document.createTextNode(lang() === "fr" ? "La liste des pages n’a pas pu être chargée." : "The page list could not be loaded."));
      body.appendChild(failure);
    }
    var base = $("body").dataset.root || "";
    order.forEach(function (key) {
      var section = document.createElement("section");
      section.className = "overview-group";
      var heading = document.createElement("h3");
      heading.textContent = pick(groups[key].title);
      var grid = document.createElement("ul");
      grid.className = "overview-grid";
      groups[key].items.forEach(function (entry) {
        var item = document.createElement("li");
        var anchor = document.createElement("a");
        anchor.className = "overview-card";
        var target = new URL(base + entry.u, window.location.href);
        anchor.href = target.href;
        if (target.pathname === here) anchor.setAttribute("aria-current", "page");
        var title = document.createElement("span");
        title.className = "overview-title";
        title.textContent = pick(entry.t);
        anchor.appendChild(icon(entry.u.indexOf("workflows/") === 0 ? "workflow" : "file"));
        anchor.appendChild(title);
        if (target.pathname === here) {
          var now = document.createElement("span");
          now.className = "overview-now";
          now.textContent = lang() === "fr" ? "Page actuelle" : "Current page";
          anchor.appendChild(now);
        }
        item.appendChild(anchor);
        grid.appendChild(item);
      });
      section.appendChild(heading);
      section.appendChild(grid);
      body.appendChild(section);
    });
    showLayer($("#overview-layer"), $(".overview-card[aria-current]", body) || $(".overview-card", body));
  }

  /* ------------------------------------------------------------ shortcuts */
  function typing(target) {
    return !!(target && target.closest && target.closest("input, textarea, select, [contenteditable=''], [contenteditable='true']"));
  }
  function bindKeys() {
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        if (openLayer) { event.preventDefault(); closeLayer(); return; }
        if (root.classList.contains("nav-open")) { event.preventDefault(); setNav(false); return; }
      }
      trap(event);
      if (event.defaultPrevented) return;
      var mod = event.ctrlKey || event.metaKey;
      if (mod && !event.altKey && event.key.toLowerCase() === "k") {
        if (document.querySelector("dialog[open]")) return;
        event.preventDefault();
        if (openLayer && openLayer.id === "palette-layer") return;
        openPalette();
        return;
      }
      if (mod || event.altKey || openLayer || typing(event.target) || document.querySelector("dialog[open]")) return;
      if (root.dataset.shortcuts === "false") return;
      var key = event.key;
      if (key === "/") { event.preventDefault(); openPalette(); }
      else if (key === "?") { event.preventDefault(); showLayer($("#help-layer")); }
      else if (key === "g" || key === "G") { event.preventDefault(); openOverview(); }
      else if (key === "c" || key === "C") { event.preventDefault(); setNav(!navShown()); }
      else if (key === "t" || key === "T") { event.preventDefault(); cycleTheme(); }
      else if (key === ",") { event.preventDefault(); openPrefs(); }
    });
  }

  /* ------------------------------------------------------------ content enhancements */
  function copyButtons() {
    $$("main pre, .markdown-body pre").forEach(function (pre) {
      if (pre.parentNode.classList.contains("code-block")) return;
      var wrap = document.createElement("div");
      wrap.className = "code-block";
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);
      var button = document.createElement("button");
      button.type = "button";
      button.className = "btn copy-btn";
      function label(done) {
        button.textContent = "";
        button.appendChild(icon(done ? "check" : "copy"));
        button.appendChild(done ? bilingual("Copied", "Copié") : bilingual("Copy", "Copier"));
        button.setAttribute("aria-label", done ? pick(["Copied", "Copié"]) : pick(["Copy code", "Copier le code"]));
      }
      label(false);
      button.addEventListener("click", function () {
        var text = pre.innerText;
        function done() { label(true); announce(lang() === "fr" ? "Code copié" : "Code copied"); window.setTimeout(function () { label(false); }, 1800); }
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { announce(lang() === "fr" ? "Copie impossible" : "Copy failed"); });
        else {
          var area = document.createElement("textarea");
          area.value = text;
          area.setAttribute("readonly", "");
          area.className = "sr-only";
          document.body.appendChild(area);
          area.select();
          try { document.execCommand("copy"); done(); } catch (error) { announce(lang() === "fr" ? "Copie impossible" : "Copy failed"); }
          area.remove();
        }
      });
      wrap.appendChild(button);
    });
  }
  function cellValue(cell) {
    var text = cell.innerText.trim();
    var number = parseFloat(text.replace(/[^0-9.\-]/g, ""));
    return /^[\d\s.,\-+%]+$/.test(text) && !isNaN(number) ? number : text.toLowerCase();
  }
  function sortableTables() {
    $$("table.ref-table").forEach(function (table) {
      var head = $$("thead th", table);
      var body = table.tBodies[0];
      if (!head.length || !body || body.rows.length < 3) return;
      var uniform = $$("tr", body).every(function (row) { return row.cells.length === head.length; });
      if (!uniform) return;
      head.forEach(function (th, column) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "th-sort";
        while (th.firstChild) button.appendChild(th.firstChild);
        button.appendChild(icon("sort"));
        th.appendChild(button);
        button.addEventListener("click", function () {
          var ascending = th.getAttribute("aria-sort") !== "ascending";
          head.forEach(function (other) { other.removeAttribute("aria-sort"); var mark = $("use", other); if (mark) mark.setAttribute("href", "#i-sort"); });
          th.setAttribute("aria-sort", ascending ? "ascending" : "descending");
          $("use", button).setAttribute("href", ascending ? "#i-arrow-up" : "#i-arrow-down");
          var rows = $$("tr", body);
          rows.map(function (row, index) { return { row: row, index: index, value: cellValue(row.cells[column]) }; })
            .sort(function (a, b) {
              var order = typeof a.value === "number" && typeof b.value === "number" ? a.value - b.value : String(a.value).localeCompare(String(b.value), lang());
              return (ascending ? order : -order) || a.index - b.index;
            }).forEach(function (entry) { body.appendChild(entry.row); });
          announce((lang() === "fr" ? "Trié par " : "Sorted by ") + button.innerText.trim() + ", " + (ascending ? (lang() === "fr" ? "croissant" : "ascending") : (lang() === "fr" ? "décroissant" : "descending")));
        });
      });
    });
  }
  function revealTabs() {
    var current = $(".tabs [aria-selected='true']");
    if (current && current.scrollIntoView) current.scrollIntoView({ block: "nearest", inline: "center" });
  }

  document.addEventListener("DOMContentLoaded", function () {
    live = $("#live");
    bindLanguage();
    bindLayers();
    bindStats();
    bindPrefs();
    bindNav();
    bindPalette();
    bindKeys();
    rove($("#site-contents .sidenav-scroll"), "a", ["ArrowUp", "ArrowDown"]);
    rove($(".site-nav"), "a, button", ["ArrowLeft", "ArrowRight"]);
    copyButtons();
    sortableTables();
    revealTabs();
  });
}());
