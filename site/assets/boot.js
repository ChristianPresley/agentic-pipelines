/* Blocking head script: validates saved preferences and sets <html> data attributes before first paint.
   Also exposes window.SiteDisplay, the single owner of the display-preferences object
   (localStorage key fuzzing-pipeline-guide.display.v1, schema version 2; version 1 is migrated). */
(function () {
  "use strict";
  var KEY = "fuzzing-pipeline-guide.display.v1";
  var LANGUAGE_KEY = "pipeline-guide-language";
  var CHOICES = {
    colorMode: ["system", "light", "dark"],
    contrastMode: ["system", "standard", "high"],
    accent: ["blue", "purple", "slate", "teal", "green", "orange", "pink", "indigo"],
    density: ["compact", "comfortable", "spacious"],
    motion: ["system", "reduce", "full"]
  };
  var FLAGS = ["readableText", "largerTargets", "strongFocus", "shortcuts"];
  var DEFAULTS = {
    version: 2, colorMode: "system", contrastMode: "system", accent: "blue", density: "comfortable",
    motion: "system", readableText: false, largerTargets: false, strongFocus: false, shortcuts: true
  };
  var root = document.documentElement;
  var memory = null;
  var state = { prefs: copy(DEFAULTS), invalid: false, blocked: false };
  var listeners = [];

  function copy(value) { return JSON.parse(JSON.stringify(value)); }
  function mq(query) {
    try { return window.matchMedia(query); } catch (error) { return { matches: false, addEventListener: function () {} }; }
  }
  var media = {
    dark: mq("(prefers-color-scheme: dark)"), contrast: mq("(prefers-contrast: more)"),
    forced: mq("(forced-colors: active)"), motion: mq("(prefers-reduced-motion: reduce)")
  };

  function read() {
    try { return window.localStorage.getItem(KEY); } catch (error) { state.blocked = true; return memory; }
  }
  function write(text) {
    memory = text;
    try { window.localStorage.setItem(KEY, text); state.blocked = false; } catch (error) { state.blocked = true; }
  }

  // Unknown keys are dropped; any known key with an invalid value rejects the whole object.
  function validate(value) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) return null;
    if (value.version !== 1 && value.version !== 2) return null;
    var prefs = copy(DEFAULTS);
    var key;
    for (key in CHOICES) {
      if (value[key] === undefined) continue;
      if (CHOICES[key].indexOf(value[key]) < 0) return null;
      prefs[key] = value[key];
    }
    for (var i = 0; i < FLAGS.length; i += 1) {
      key = FLAGS[i];
      if (value[key] === undefined) continue;
      if (typeof value[key] !== "boolean") return null;
      prefs[key] = value[key];
    }
    if (value.version === 1) {
      if (value.reduceMotion !== undefined && typeof value.reduceMotion !== "boolean") return null;
      prefs.motion = value.reduceMotion === true ? "reduce" : "system";
    }
    return prefs;
  }

  function load() {
    var text = read();
    state.invalid = false;
    if (text === null || text === undefined) { state.prefs = copy(DEFAULTS); return; }
    var parsed = null;
    try { parsed = JSON.parse(text); } catch (error) { parsed = undefined; }
    var prefs = parsed === undefined ? null : validate(parsed);
    if (!prefs) { state.invalid = true; prefs = copy(DEFAULTS); }
    state.prefs = prefs;
  }

  function resolved(prefs) {
    var more = media.contrast.matches || media.forced.matches;
    return {
      color: prefs.colorMode === "system" ? (media.dark.matches ? "dark" : "light") : prefs.colorMode,
      contrast: prefs.contrastMode === "system" ? (more ? "high" : "standard") : prefs.contrastMode,
      reduceMotion: prefs.motion === "system" ? media.motion.matches : prefs.motion === "reduce"
    };
  }

  function apply() {
    var prefs = state.prefs;
    var now = resolved(prefs);
    root.dataset.colorMode = now.color;
    root.dataset.contrastMode = now.contrast;
    root.dataset.accent = prefs.accent;
    root.dataset.density = prefs.density;
    root.dataset.readableText = String(prefs.readableText);
    root.dataset.targets = prefs.largerTargets ? "large" : "default";
    root.dataset.focus = prefs.strongFocus ? "strong" : "default";
    root.dataset.reduceMotion = String(now.reduceMotion);
    root.dataset.shortcuts = String(prefs.shortcuts);
    root.style.colorScheme = now.color;
    root.classList.add("js");
  }

  function emit() {
    for (var i = 0; i < listeners.length; i += 1) listeners[i](state.prefs);
  }

  function set(change) {
    var next = copy(state.prefs);
    for (var key in change) if (Object.prototype.hasOwnProperty.call(DEFAULTS, key) && key !== "version") next[key] = change[key];
    var checked = validate(next);
    if (!checked) return false;
    state.prefs = checked;
    state.invalid = false;
    write(JSON.stringify(checked));
    apply();
    emit();
    return true;
  }

  function reset() {
    state.prefs = copy(DEFAULTS);
    state.invalid = false;
    write(JSON.stringify(state.prefs));
    apply();
    emit();
  }

  function initialLanguage() {
    var fromUrl = null;
    try { fromUrl = new URLSearchParams(window.location.search).get("lang"); } catch (error) { fromUrl = null; }
    if (fromUrl === "en" || fromUrl === "fr") return fromUrl;
    var saved = null;
    try { saved = window.localStorage.getItem(LANGUAGE_KEY); } catch (error) { saved = null; }
    return saved === "fr" ? "fr" : "en";
  }

  load();
  apply();
  root.lang = initialLanguage();
  for (var name in media) {
    if (media[name].addEventListener) media[name].addEventListener("change", function () { apply(); emit(); });
  }
  window.addEventListener("storage", function (event) {
    if (event.key !== KEY) return;
    memory = event.newValue;
    load();
    apply();
    emit();
  });

  window.SiteDisplay = {
    key: KEY, languageKey: LANGUAGE_KEY, choices: CHOICES, flags: FLAGS, defaults: copy(DEFAULTS),
    get: function () { return copy(state.prefs); },
    status: function () { return { invalid: state.invalid, blocked: state.blocked }; },
    resolved: function () { return resolved(state.prefs); },
    set: set, reset: reset, onChange: function (listener) { listeners.push(listener); }
  };
}());
