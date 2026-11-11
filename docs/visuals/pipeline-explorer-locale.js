(() => {
  "use strict";

  const storageKey = "pipeline-guide-language";
  const textSources = new WeakMap();
  const attributeSources = new WeakMap();
  const graphSources = new WeakMap();
  const missing = new Set();
  const errors = new Set();
  const storageError = "Language settings could not be saved. This choice applies to this page only.";
  const missingError = "Some French text is missing. English text is shown for those items.";
  const invalidError = "The saved language setting is invalid and has been ignored.";
  const urlError = "The language URL could not be updated.";
  const unsupportedError = "The requested language is not supported. Select English or French.";
  const excluded = "script, style, code, noscript, [data-no-translate]";
  let language = "en";
  let initialized = false;
  let refreshing = false;

  function report(message, error) {
    if (!errors.has(message)) console.error(message, error);
    errors.add(message);
  }

  function isTechnical(text) {
    return /^(?:https?:\/\/|(?:\.{0,2}\/)|[A-Za-z]:\\)\S+$/u.test(text) ||
      /^[\w./\\-]+\.(?:md|ya?ml|json|xml|java|py|svg|js|css|html|jar)$/iu.test(text) ||
      /^[a-f\d]{7,}$/iu.test(text) ||
      /^v?\d+(?:\.\d+)+(?:[-+][\w.-]+)?$/u.test(text) ||
      /^[A-Za-z]\w*_\w+$/u.test(text);
  }

  function translate(text) {
    if (language === "en" || !text.trim() || !/\p{L}/u.test(text)) return text;
    const source = text.trim();
    const dictionary = window.pipelineFrench;
    const result = dictionary?.translate(source);
    if (typeof result === "string" && result.length) {
      return text.slice(0, text.indexOf(source)) + result +
        text.slice(text.indexOf(source) + source.length);
    }
    if (isTechnical(source)) return text;
    if (!missing.has(source)) console.error("Missing French translation:", source);
    missing.add(source);
    return text;
  }

  function localize(current, previous) {
    // Explorer writes English into reused nodes; only our last output is reversible.
    const source = previous && current === previous.current ? previous.source : current;
    return { source, current: translate(source) };
  }

  function updateDiagnostics() {
    const status = document.getElementById("route-status");
    if (!status) return;
    const messages = [...errors].map(translate);
    if (language === "fr" && missing.size) messages.push(translate(missingError));
    let diagnostic = status.querySelector("[data-pipeline-locale-status]");
    if (!messages.length) {
      diagnostic?.remove();
      return;
    }
    if (!diagnostic) {
      diagnostic = document.createElement("span");
      diagnostic.setAttribute("data-pipeline-locale-status", "");
      status.append(diagnostic);
    }
    const value = ` ${messages.join(" ")}`;
    if (diagnostic.textContent !== value) diagnostic.textContent = value;
  }

  function updateGraph() {
    for (const element of document.querySelectorAll("img[src], a[href]")) {
      const attribute = element.tagName === "IMG" ? "src" : "href";
      const current = element.getAttribute(attribute);
      let original = graphSources.get(element);
      if (!original && /(?:^|\/)(?:pipeline-overview|agentic-vs-legacy|agentic-run-guardrails)\.svg(?:[?#].*)?$/u.test(current)) {
        original = current;
        graphSources.set(element, original);
      }
      if (original) {
        const value = language === "fr" ? original.replace(/\.svg(?=[?#]|$)/u, "-fr.svg") : original;
        if (current !== value) element.setAttribute(attribute, value);
      }
    }
  }

  function refresh() {
    if (refreshing || !initialized) return;
    refreshing = true;
    try {
      document.documentElement.lang = language;
      const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (node.parentElement.closest(`${excluded}, [data-language-switch], [data-pipeline-locale-status]`)) continue;
        const record = localize(node.nodeValue, textSources.get(node));
        textSources.set(node, record);
        if (node.nodeValue !== record.current) node.nodeValue = record.current;
      }
      for (const element of document.querySelectorAll("[aria-label], [alt], [title]")) {
        if (element.closest(`${excluded}, [data-pipeline-locale-status]`)) continue;
        let sources = attributeSources.get(element);
        if (!sources) {
          sources = new Map();
          attributeSources.set(element, sources);
        }
        for (const attribute of ["aria-label", "alt", "title"]) {
          if (!element.hasAttribute(attribute)) {
            sources.delete(attribute);
            continue;
          }
          const current = element.getAttribute(attribute);
          const record = localize(current, sources.get(attribute));
          sources.set(attribute, record);
          if (current !== record.current) element.setAttribute(attribute, record.current);
        }
      }
      for (const button of document.querySelectorAll("[data-language-switch]")) {
        button.setAttribute("aria-checked", String(language === "fr"));
      }
      updateGraph();
      updateDiagnostics();
    } finally {
      refreshing = false;
    }
  }

  function save() {
    try {
      window.localStorage.setItem(storageKey, language);
    } catch (error) {
      report(storageError, error);
    }
  }

  function initialize() {
    if (initialized) return;
    let saved = null;
    try {
      saved = window.localStorage.getItem(storageKey);
    } catch (error) {
      report(storageError, error);
    }
    if (saved !== null && saved !== "en" && saved !== "fr") {
      report(invalidError);
      saved = null;
    }
    const requested = new URL(window.location.href).searchParams.get("lang");
    if (requested !== null && requested !== "en" && requested !== "fr") report(unsupportedError);
    language = requested === "en" || requested === "fr" ? requested : saved || "en";
    initialized = true;
    save();
    document.addEventListener("click", event => {
      if (!(event.target instanceof Element)) return;
      const button = event.target.closest("[data-language-switch]");
      if (!button || event.defaultPrevented || button.disabled) return;
      language = language === "en" ? "fr" : "en";
      const url = new URL(window.location.href);
      url.searchParams.set("lang", language);
      try {
        window.history.replaceState(window.history.state, "", url);
      } catch (error) {
        report(urlError, error);
      }
      save();
      refresh();
    });
    refresh();
  }

  window.pipelineI18n = {
    refresh,
    t(text) {
      const translated = translate(text);
      if (!refreshing) updateDiagnostics();
      return translated;
    },
    get language() { return language; },
    get missing() { return new Set(missing); }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
