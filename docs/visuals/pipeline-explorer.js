(() => {
  const products = {
    actions: { name: "GitHub Actions", logo: "githubactions", use: "Run jobs and save their result files.", source: "../.github/workflows/ci.yml" },
    github: { name: "GitHub", logo: "github", use: "Store code, issues, packages, and releases.", source: "../.github/workflows/release.yml" },
    git: { name: "Git", logo: "git", use: "Identify commits and create version tags.", source: "../.github/workflows/cut-release.yml" },
    adoptium: { name: "Temurin JDK 21", logo: "eclipseadoptium", use: "Compile and run the Java app and tests.", source: "../.github/actions/setup-java/action.yml" },
    maven: { name: "Apache Maven", logo: "apachemaven", use: "Build, test, and publish the Java package.", source: "../pom.xml" },
    junit: { name: "JUnit 5", logo: "junit5", use: "Run Java tests and write XML results.", source: "../src/test/java/io/github/christianpresley/hello/GreetingServiceTest.java" },
    jazzer: { name: "Jazzer 0.30.0", use: "Run saved inputs or search for new failing inputs.", source: "../.github/workflows/fuzz.yml" },
    jqwik: { name: "jqwik 1.10.2", use: "Generate test strings and save random seeds.", source: "../src/test/java/io/github/christianpresley/hello/GreetingServicePropertyTest.java" },
    jacoco: { name: "JaCoCo 0.8.16", use: "Measure lines and branches reached by tests.", source: "../pom.xml" },
    pit: { name: "PIT 1.30.2", use: "Change Java code and check whether tests detect the change.", source: "../pom.xml" },
    spring: { name: "Spring", logo: "spring", use: "Process API requests and validate name inputs.", source: "../src/main/java/io/github/christianpresley/hello/HelloController.java" },
    schemathesis: { name: "Schemathesis 4.33.0", use: "Generate requests from OpenAPI and check responses.", source: "../.github/workflows/dast.yml" },
    zap: { name: "OWASP ZAP", logo: "owasp", use: "Scan the running API for security findings.", source: "../.github/workflows/dast.yml" },
    docker: { name: "Docker", logo: "docker", use: "Build images and run container tests.", source: "../.github/workflows/e2e.yml" },
    python: { name: "Python", logo: "python", use: "Read scanner files and write findings and summaries.", source: "../.github/scripts/security_report.py" },
    actionlint: { name: "actionlint 1.7.12", use: "Check workflow syntax and expressions.", source: "../.github/workflows/lint.yml" },
    zizmor: { name: "zizmor", use: "Check workflow security patterns.", source: "../.github/workflows/lint.yml" },
    ghaw: { name: "gh-aw", use: "Compile agent workflows and control safe outputs.", source: "../.github/workflows/lint.yml" },
    copilot: { name: "GitHub Copilot", logo: "githubcopilot", use: "Write reviews and summaries from checked records.", source: "../.github/workflows/security-triage.md" },
    cosign: { name: "Cosign", use: "Sign published images with short-lived identity.", source: "../.github/workflows/release.yml" },
    sbom: { name: "Syft / CycloneDX", use: "Create software component lists.", source: "../.github/workflows/sca.yml" },
    mermaid: { name: "Mermaid", logo: "mermaid", use: "Show diagrams in the linked Markdown documents.", source: "fuzzing-pipeline-view.md" },
    otel: { name: "OpenTelemetry", logo: "opentelemetry", use: "Export workflow traces if an endpoint is set.", source: "../.github/workflows/observability-otel.yml", other: "Optional Observability workflow. This guide does not export traces." },
    trivy: { name: "Trivy", logo: "trivy", use: "Scan dependencies and container images.", source: "../.github/workflows/container.yml", other: "SCA and Container workflows. Gates read their results; gates do not run Trivy." },
    codeql: { name: "CodeQL", use: "Analyze source code for security defects.", source: "../.github/workflows/sast.yml", other: "SAST workflow. The release gate reads the SAST conclusion." },
    semgrep: { name: "Semgrep", use: "Check source code against security rules.", source: "../.github/workflows/sast.yml", other: "SAST workflow. It runs before release checks." },
    osv: { name: "OSV-Scanner", use: "Check dependencies for known vulnerabilities.", source: "../.github/workflows/sca.yml", other: "SCA workflow. It runs before release checks." },
    gitleaks: { name: "Gitleaks", use: "Check repository history for secrets.", source: "../.github/workflows/secrets-iac.yml", other: "Secrets and IaC workflow. It runs before release checks." },
    hadolint: { name: "Hadolint", use: "Check Dockerfile rules.", source: "../.github/workflows/secrets-iac.yml", other: "Secrets and IaC workflow. It runs before release checks." }
  };
  const stages = {
    source: {
      title: "Source", area: "source-build", phase: "CI", state: "mixed", tools: ["actions", "git"],
      summary: "Select the code and event for the test run.",
      input: ["A pull request, push, schedule, or manual request."],
      actions: ["Identify the tested commit.", "Apply event and branch filters.", "Planned: record trust level and test limits in one result index."],
      output: ["A tested commit and event.", "Planned: a complete run identity."],
      note: "A pull request must not replace approved main-branch inputs.",
      sources: [["../.github/workflows/ci.yml", "CI events"], ["fuzzing-system-design.md#4-scheduling-and-resource-envelope", "Planned run limits"]]
    },
    build: {
      title: "Build", area: "source-build", phase: "CI", state: "mixed", tools: ["actions", "adoptium", "maven"],
      summary: "Compile the app and tests with fixed tool versions.",
      input: ["The selected commit and Maven build settings."],
      actions: ["Set up Temurin JDK 21.", "Build the app with the Maven wrapper.", "Run Maven verification.", "Planned: prepare an isolated workflow test harness."],
      output: ["Java classes, an app jar, and build reports."],
      note: "A cache makes the build faster. It does not prove that tests passed.",
      sources: [["../pom.xml", "Build settings"], ["../.github/actions/setup-java/action.yml", "Java setup"]]
    },
    java: {
      title: "Java tests", area: "java", phase: "CI", state: "mixed", tools: ["adoptium", "junit", "jazzer", "jqwik", "jacoco", "pit"],
      summary: "Test the greeting service without HTTP.",
      input: ["Fixed examples, generated strings, and byte inputs."],
      actions: ["Check greeting format and safe name output.", "Generate strings with jqwik.", "Run saved Jazzer inputs on pull requests and pushes.", "Use Jazzer fuzz mode on scheduled or manual runs.", "Planned: add stronger Unicode and length checks."],
      output: ["JUnit results, coverage, mutation results, and normalized fuzz findings."],
      note: "The sampled push ran saved inputs, not a measured coverage-guided campaign. PIT is not a fuzz input count.",
      sources: [["../src/test/java/io/github/christianpresley/hello/GreetingServiceFuzzTest.java", "Fuzz target"], ["../.github/workflows/fuzz.yml", "Fuzz workflow"], ["../pom.xml", "Versions and checks"]]
    },
    api: {
      title: "API tests", area: "api", phase: "CI", state: "mixed", tools: ["spring", "schemathesis", "zap"],
      summary: "Send requests to the app and check its responses.",
      input: ["The running app and its OpenAPI document."],
      actions: ["Generate requests with Schemathesis.", "Check response codes and JSON against OpenAPI.", "Run separate security scans with ZAP.", "Planned: repeat exact 199/200/201-unit cases."],
      output: ["Schemathesis JUnit files, ZAP reports, and findings-dast."],
      note: "The baseline ST103 finding was an undocumented 400 response. Keep input validation and document the intended response.",
      sources: [["../.github/workflows/dast.yml", "DAST workflow"], ["../src/main/java/io/github/christianpresley/hello/HelloController.java", "Controller"]]
    },
    workflow: {
      title: "Workflow tests", area: "workflows", phase: "CI", state: "mixed", tools: ["actions", "actionlint", "zizmor", "ghaw"],
      summary: "Check workflow settings and test repository-owned decisions.",
      input: ["Workflow source, event records, and scanner reports."],
      actions: ["Run current syntax and security checks.", "Compile agent workflows and check lock-file changes.", "Planned: change test inputs for seven behavior groups.", "Compare actual decisions with expected decisions."],
      output: ["Current lint results.", "Planned: case results, command traces, and repeatable fixtures."],
      note: "Do not execute changed workflows or publish from the harness. It does not model all GitHub behavior.",
      sources: [["../.github/workflows/lint.yml", "Current lint"], ["fuzzing-system-design.md#3-workflow-fuzzing-what-is-actually-exercised", "Seven planned test groups"]]
    },
    collect: {
      title: "Check test records", area: "evidence", phase: "CI", state: "mixed", tools: ["actions", "python"],
      summary: "Read result files and check that required records are complete.",
      input: ["Raw scanner files and job identity."],
      actions: ["Read current XML, JSON, and SARIF reports.", "Planned: verify the commit, event, run, and attempt.", "Check for missing or invalid required files.", "Keep original failed inputs and record repeat runs."],
      output: ["Current normalized findings.", "Planned: a complete result index and repeat-run bundle."],
      note: "A missing report is not a clean result. Strict record checks are planned, not current guarantees.",
      sources: [["../.github/scripts/security_report.py", "Report parser"], ["fuzzing-system-design.md#5-evidence-contract-and-persistence", "Record design"]]
    },
    quality: {
      title: "Quality gate", area: "gates", phase: "CI", state: "planned", tools: ["python", "actions"],
      summary: "Allow the next step only when required records and checks pass.",
      input: ["Checked result records and required test outcomes."],
      actions: ["Require complete records.", "Require clean results for required checks.", "Hold wrong-commit, missing-file, parser-error, and zero-test cases.", "Observe new checks before making them required."],
      output: ["A pass, failure, or incomplete decision with reasons."],
      note: "This complete-record gate is not built yet. Current severity gates use separate rules.",
      sources: [["fuzzing-system-design.md#6-health-defect-and-release-gates", "Gate rules"]]
    },
    pass: {
      title: "Pass: permit the next step", area: "gates", phase: "CI", state: "planned", tools: ["actions"],
      summary: "Mark a change as eligible for merge or release checks.",
      input: ["A complete and clean required result set."],
      actions: ["Record the decision for the tested commit.", "Make the decision available to the next approved step."],
      output: ["Merge or release eligibility, not production approval."],
      note: "This card shows a possible outcome. It is not a live pass indicator.",
      sources: [["fuzzing-system-design.md#6-health-defect-and-release-gates", "Decision rules"]]
    },
    hold: {
      title: "Hold: stop the next step", area: "gates", phase: "CI", state: "planned", tools: ["actions"],
      summary: "Do not continue when required checks fail or records are incomplete.",
      input: ["A defect, missing record, or failed tool start."],
      actions: ["Keep the failure or incomplete state visible.", "Write the reasons and source links.", "Do not replace an unknown result with zero findings."],
      output: ["A blocked decision and follow-up details."],
      note: "This card shows a possible outcome. It is not a live failure indicator.",
      sources: [["fuzzing-system-design.md#6-health-defect-and-release-gates", "Decision rules"]]
    },
    reports: {
      title: "Test records and reports", area: "reports", phase: "CI", state: "mixed", tools: ["python", "github", "mermaid"],
      summary: "Show results and their source links for every outcome.",
      input: ["Findings, build summaries, and checked run records."],
      actions: ["Write current test and security summaries.", "Use Mermaid in the linked diagrams.", "Planned: create summary, technical, and connection reports from one index."],
      output: ["Human-readable reports with counts, dates, and source links."],
      note: "The baseline reports are dated. This page does not load live run status.",
      sources: [["reports/fuzzing-summary-2026-11-10.md", "Summary report"], ["reports/fuzzing-evidence-2026-11-10.md", "Technical report"]]
    },
    tag: {
      title: "Release tag", area: "release", phase: "Release", state: "current", tools: ["git", "github", "actions"],
      summary: "Choose the version and start the release workflow.",
      input: ["Main-branch code and a requested version change."],
      actions: ["Use Cut release to calculate a semantic version.", "Create the version tag.", "Start Release for the tag."],
      output: ["A tag such as v1.2.3 and a Release run."],
      note: "An external tag push is another release entry point. This guide does not create tags.",
      sources: [["../.github/workflows/cut-release.yml", "Cut release"]]
    },
    "validate-tag": {
      title: "Check release tag", area: "release", phase: "Release", state: "current", tools: ["git", "github"],
      summary: "Check that the tag is valid and points to approved history.",
      input: ["The release tag and commit."],
      actions: ["Check the version format.", "Check that the commit is in main history.", "Reject a tag that already has a GitHub Release."],
      output: ["The checked version, commit, and pre-release flag."],
      note: "Tag checks run before release gates.",
      sources: [["../.github/workflows/release.yml", "Release tag checks"]]
    },
    "release-gate": {
      title: "Release gate", area: "gates", phase: "Release", state: "current", tools: ["github", "actions"],
      summary: "Require scanner passes and no open blocking security findings.",
      input: ["Push-run conclusions for the tag commit and security issue labels."],
      actions: ["Require CI, SAST, SCA, Secrets and IaC, Container, DAST, and Fuzzing passes.", "Block open high and critical security findings."],
      output: ["A release gate pass or failure."],
      note: "The gate reads scanner results. It does not run scanner products. Completion coordination is a separate workflow.",
      sources: [["../.github/workflows/release.yml", "Release gate"], ["../.github/workflows/pipeline.yml", "Pipeline gate"]]
    },
    "verify-release": {
      title: "Test release build", area: "release", phase: "Release", state: "current", tools: ["actions", "adoptium", "maven", "junit", "jacoco", "docker", "sbom"],
      summary: "Build the release and test a container in parallel.",
      input: ["A checked tag and passing release gates."],
      actions: ["Set the release version.", "Run Maven verification.", "Build and test the E2E container.", "Create the jar, SHA512SUMS, and component list."],
      output: ["Release assets, test results, and container E2E results."],
      note: "E2E and publication build images separately. Matching image hashes are not guaranteed.",
      sources: [["../.github/workflows/release.yml", "Release build"], ["../.github/workflows/e2e.yml", "E2E tests"]]
    },
    readiness: {
      title: "Readiness review", area: "release", phase: "Release", state: "current", tools: ["github", "copilot", "ghaw"],
      summary: "Ask an agent to give release advice.",
      input: ["The release tag, check results, changes, and open issues."],
      actions: ["Start the release-readiness agent.", "Ask it to write a GO or NO-GO issue.", "Send configured notifications."],
      output: ["A readiness issue for the human reviewer."],
      note: "The issue is advice. Publication does not wait for a machine-enforced GO verdict.",
      sources: [["../.github/workflows/release-readiness.md", "Readiness agent"]]
    },
    approval: {
      title: "Production approval", area: "release", phase: "Release", state: "current", tools: ["github", "actions"],
      summary: "Apply the production environment rules before publication.",
      input: ["Completed build, E2E, and readiness-dispatch jobs."],
      actions: ["Wait for configured environment protection.", "Continue only when GitHub permits the publish job."],
      output: ["Permission to start publication, or a held job."],
      note: "Reviewer settings live outside the YAML. The baseline did not inspect those settings.",
      sources: [["../.github/workflows/release.yml", "Production environment"]]
    },
    publish: {
      title: "Publish packages", area: "release", phase: "Release", state: "current", tools: ["github", "actions", "docker", "maven", "cosign"],
      summary: "Publish packages and attach signatures and build records.",
      input: ["The release version, build assets, and environment permission."],
      actions: ["Build and push the image with Buildx.", "Publish the Maven package to GitHub Packages.", "Sign the image with Cosign.", "Attach build and SBOM attestations."],
      output: ["GHCR image, Maven package, signatures, and attestations."],
      note: "This is package delivery. The repository has no app deployment stage here.",
      sources: [["../.github/workflows/release.yml", "Publish job"]]
    },
    release: {
      title: "GitHub Release", area: "release", phase: "Release", state: "current", tools: ["github", "copilot", "ghaw"],
      summary: "Create the release page and ask an agent to improve the notes.",
      input: ["Published packages and release assets."],
      actions: ["Create the GitHub Release with generated notes.", "Attach the jar, checksums, and SBOM.", "Start the release-notes agent."],
      output: ["A GitHub Release and updated notes."],
      note: "The notes agent runs after an explicit dispatch. It does not approve the release.",
      sources: [["../.github/workflows/release.yml", "Release job"], ["../.github/workflows/release-notes.md", "Notes agent"]]
    },
    deep: {
      title: "Extended tests", area: "feedback", phase: "Review and reuse", state: "mixed", tools: ["actions", "jazzer", "schemathesis"],
      summary: "Run longer tests at set times or by manual request.",
      input: ["Trusted code, approved inputs, and a fixed time limit."],
      actions: ["Use current Jazzer schedule and manual entry points.", "Planned: run deeper Java, API, and workflow test groups.", "Stop at the set time or case limit."],
      output: ["New candidate inputs and measured run records."],
      note: "The three-group extended design is planned. These runs must not start a release.",
      sources: [["../.github/workflows/fuzz.yml", "Current fuzz schedule"], ["fuzzing-system-design.md#4-scheduling-and-resource-envelope", "Planned limits"]]
    },
    finding: {
      title: "Check a finding", area: "evidence", phase: "Review and reuse", state: "planned", tools: ["python", "jazzer", "schemathesis"],
      summary: "Keep enough data to repeat and understand a failure.",
      input: ["A candidate failure and its original input."],
      actions: ["Keep the original failed input.", "Reduce the input without changing the failure.", "Repeat it three times in fresh isolation.", "Record stable and intermittent results separately."],
      output: ["A checked finding, input hash, and repeat-run records."],
      note: "A failure to reduce or repeat an input stays visible. It does not become a clean test.",
      sources: [["fuzzing-system-design.md#5-evidence-contract-and-persistence", "Repeat-run design"]]
    },
    review: {
      title: "Human review", area: "feedback", phase: "Review and reuse", state: "mixed", tools: ["github", "copilot", "ghaw"],
      summary: "Review the finding and choose a follow-up action.",
      input: ["A checked finding, report, and proposed fix or acceptance."],
      actions: ["Use current issues and agent summaries for follow-up.", "Planned: approve a fix or record owned, time-limited acceptance.", "Approve input reuse as a separate decision."],
      output: ["A reviewed fix, acceptance, or approved test input."],
      note: "Agents can summarize. They cannot waive gates or approve production.",
      sources: [["../.github/workflows/security-triage.md", "Current finding review"], ["fuzzing-system-design.md#5-evidence-contract-and-persistence", "Planned input review"]]
    },
    corpus: {
      title: "Approved test inputs", area: "feedback", phase: "Review and reuse", state: "planned", tools: ["git", "github"],
      summary: "Store only reviewed inputs for future tests.",
      input: ["A small failing input approved for reuse."],
      actions: ["Record the input hash and source finding.", "Keep trusted and pull-request input stores separate.", "Treat cache storage as optional."],
      output: ["A reviewed corpus with a known version and integrity hash."],
      note: "Accepting a finding does not automatically approve its input. Pull requests cannot replace trusted corpus state.",
      sources: [["fuzzing-system-design.md#5-evidence-contract-and-persistence", "Corpus rules"]]
    },
    regression: {
      title: "Next test run", area: "feedback", phase: "Review and reuse", state: "mixed", tools: ["actions", "junit", "jazzer", "jqwik"],
      summary: "Repeat approved inputs to detect returning defects.",
      input: ["The next code change and reviewed test inputs."],
      actions: ["Run current fixed and generated tests.", "Planned: include each approved failure input.", "Check the same contract with the new code."],
      output: ["A new result set for the quality gate."],
      note: "Current regression tests exist. The full reviewed corpus promotion process is planned.",
      sources: [["../.github/workflows/ci.yml", "Current tests"], ["../.github/workflows/fuzz.yml", "Current fuzz regression"]]
    }
  };

  const tabs = [...document.querySelectorAll("[data-tab]")];
  const panels = [...document.querySelectorAll("[data-panel]")];
  const byId = new Map(panels.map(panel => [panel.id, panel]));
  const status = document.getElementById("route-status");
  const navigation = document.querySelector(".tabs");
  const drawer = document.getElementById("stage-drawer");
  const content = document.getElementById("stage-content");
  const order = Object.keys(stages);
  const stateNames = { current: "Current", planned: "Planned", mixed: "Current tools; planned changes" };
  const stateClasses = { current: "existing", planned: "proposed", mixed: "mixed" };
  let activeArea = "overview";
  let returnFocus = null;
  let currentStage = null;
  let settingsMessage = "";
  const preferenceKey = "fuzzing-pipeline-guide.display.v1";
  const defaultPreferences = {
    version: 2, colorMode: "system", contrastMode: "system", accent: "blue", density: "comfortable", motion: "system",
    readableText: false, largerTargets: false, strongFocus: false, shortcuts: true
  };
  const choices = {
    colorMode: ["system", "light", "dark"], contrastMode: ["system", "standard", "high"],
    accent: ["blue", "purple", "slate", "teal", "green", "orange", "pink", "indigo"],
    density: ["compact", "comfortable", "spacious"], motion: ["system", "reduce", "full"]
  };
  const flagNames = ["readableText", "largerTargets", "strongFocus", "shortcuts"];
  // On the Pages site, site/assets/boot.js owns the same stored object, so this page only reads it.
  const siteOwnsPreferences = Boolean(window.SiteDisplay);
  let preferences = { ...defaultPreferences };
  const media = {
    dark: window.matchMedia("(prefers-color-scheme: dark)"),
    contrast: window.matchMedia("(prefers-contrast: more)"),
    forced: window.matchMedia("(forced-colors: active)"),
    motion: window.matchMedia("(prefers-reduced-motion: reduce)"),
    narrow: window.matchMedia("(max-width: 760px)")
  };
  const controls = {
    colorMode: document.getElementById("color-mode"),
    contrastMode: document.getElementById("contrast-mode"),
    readableText: document.getElementById("readable-text"),
    reduceMotion: document.getElementById("reduce-motion")
  };
  const stageList = document.getElementById("stage-list");
  const graph = document.getElementById("pipeline-graph");
  const listToggle = document.getElementById("stage-list-toggle");
  let listChoice = null;

  function refreshLocale() {
    window.pipelineI18n?.refresh();
  }
  function setStatus(message) {
    status.textContent = message;
    refreshLocale();
  }
  function invalidPreferences(error) {
    console.error("Invalid saved pipeline display settings.", error);
    settingsMessage = "Saved display settings are invalid. System settings are shown.";
  }
  // Accepts schema 1 (migrated) and schema 2; unknown keys or invalid values reject the whole object.
  function validPreferences(value) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) return null;
    const known = new Set([...Object.keys(defaultPreferences), "reduceMotion"]);
    if (value.version !== 1 && value.version !== 2) return null;
    if (Object.keys(value).some(key => !known.has(key))) return null;
    const next = { ...defaultPreferences };
    for (const [key, allowed] of Object.entries(choices)) {
      if (value[key] === undefined) continue;
      if (!allowed.includes(value[key])) return null;
      next[key] = value[key];
    }
    for (const key of flagNames) {
      if (value[key] === undefined) continue;
      if (typeof value[key] !== "boolean") return null;
      next[key] = value[key];
    }
    if (value.version === 1) {
      if (typeof value.reduceMotion !== "boolean") return null;
      next.motion = value.reduceMotion ? "reduce" : "system";
    }
    return next;
  }
  function loadPreferences() {
    let saved;
    try {
      saved = window.localStorage.getItem(preferenceKey);
    } catch (error) {
      console.error("Pipeline display settings could not be read.", error);
      settingsMessage = "Display settings could not be saved. This choice applies to this page only.";
      return;
    }
    if (saved === null) return;
    let value;
    try {
      value = JSON.parse(saved);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      invalidPreferences(error);
      return;
    }
    const checked = validPreferences(value);
    if (!checked) {
      invalidPreferences(new Error("Unsupported display settings values or schema."));
      return;
    }
    preferences = checked;
  }
  function applyPreferences() {
    if (siteOwnsPreferences) return;
    const root = document.documentElement;
    const reduce = preferences.motion === "system" ? media.motion.matches : preferences.motion === "reduce";
    root.dataset.colorMode = preferences.colorMode === "system" ? (media.dark.matches ? "dark" : "light") : preferences.colorMode;
    root.dataset.contrastMode = preferences.contrastMode === "system" ?
      (media.contrast.matches || media.forced.matches ? "high" : "standard") : preferences.contrastMode;
    root.dataset.readableText = String(preferences.readableText);
    root.dataset.reduceMotion = String(reduce);
    root.style.colorScheme = root.dataset.colorMode;
    for (const [key, control] of Object.entries(controls)) {
      if (!control) continue;
      if (key === "reduceMotion") control.checked = preferences.motion === "reduce";
      else if (control.type === "checkbox") control.checked = preferences[key];
      else control.value = preferences[key];
    }
  }
  function savePreferences() {
    try {
      window.localStorage.setItem(preferenceKey, JSON.stringify(preferences));
      settingsMessage = "";
    } catch (error) {
      console.error("Pipeline display settings could not be saved.", error);
      settingsMessage = "Display settings could not be saved. This choice applies to this page only.";
    }
    setStatus(settingsMessage);
  }
  function updateStageView() {
    if (!stageList || !graph || !listToggle) return;
    const showList = listChoice ?? (media.narrow.matches || media.forced.matches);
    const losingFocus = (showList ? graph : stageList).contains(document.activeElement);
    stageList.hidden = !showList;
    graph.hidden = showList;
    listToggle.setAttribute("aria-pressed", String(showList));
    if (losingFocus) listToggle.focus({ preventScroll: true });
  }
  function buildStageList() {
    if (!stageList) return;
    stageList.append(element("h3", "Pipeline stages"),
      element("p", "Use the diagram for connections. Use the list for stage details.", "hint"));
    const groups = new Map();
    for (const [id, stage] of Object.entries(stages)) {
      if (!groups.has(stage.phase)) {
        const group = element("section", "", "stage-list-group");
        const heading = element("h4", stage.phase);
        heading.id = `stage-list-phase-${groups.size}`;
        group.setAttribute("aria-labelledby", heading.id);
        const list = element("ul", "", "stage-list-items");
        group.append(heading, list);
        stageList.append(group);
        groups.set(stage.phase, list);
      }
      const item = element("li");
      const button = element("button", "", "secondary-button stage-link");
      button.type = "button";
      button.dataset.openStage = id;
      button.setAttribute("aria-haspopup", "dialog");
      button.setAttribute("aria-controls", "stage-drawer");
      button.append(element("span", stage.title), badge(stage.state));
      item.append(button);
      groups.get(stage.phase).append(item);
    }
  }

  function element(tag, text, className) {
    const item = document.createElement(tag);
    if (text) item.textContent = text;
    if (className) item.className = className;
    return item;
  }
  function badge(state) {
    const chip = element("span", "", `badge ${stateClasses[state]}`);
    // The Pages build supplies an icon sprite; the standalone page shows the word and pattern only.
    if (document.getElementById("i-check-circle")) {
      const glyph = { current: "check-circle", planned: "ring", mixed: "triangle" }[state];
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "icon icon-16");
      svg.setAttribute("aria-hidden", "true");
      svg.setAttribute("focusable", "false");
      const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      use.setAttribute("href", `#i-${glyph}`);
      svg.append(use);
      chip.append(svg);
    }
    chip.append(element("span", stateNames[state]));
    return chip;
  }
  function productButton(id) {
    const product = products[id];
    if (!product) throw new Error(`Unknown product: ${id}`);
    const button = element("button", "", "product");
    button.type = "button";
    button.dataset.tool = id;
    button.setAttribute("aria-label", `${product.name}: show where it is used`);
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-controls", "stage-drawer");
    if (product.logo) {
      const image = element("img");
      image.src = `visuals/product-logos/${product.logo}.svg`;
      image.alt = "";
      image.width = image.height = 22;
      image.addEventListener("error", () => {
        setStatus(`The ${product.name} logo did not load. Its name is still shown.`);
        console.error(`Logo did not load: ${product.logo}`);
      });
      button.append(image);
    }
    button.append(element("span", product.name));
    return button;
  }
  function section(title, values) {
    content.append(element("h3", title));
    const list = element("ul");
    for (const value of values) list.append(element("li", value));
    content.append(list);
  }
  function showDrawer() {
    if (!drawer.open) {
      returnFocus = document.activeElement;
      drawer.showModal();
    }
    refreshLocale();
    document.getElementById("drawer-body").scrollTop = 0;
    drawer.scrollTop = 0;
    const heading = document.getElementById("stage-title");
    const bounds = heading.getBoundingClientRect();
    const focusTarget = bounds.top >= 0 && bounds.bottom <= window.innerHeight ? heading : document.getElementById("close-drawer");
    focusTarget.focus({ preventScroll: true });
  }
  function closeDrawer(restoreFocus = true) {
    if (!drawer.open) return;
    const target = returnFocus;
    returnFocus = null;
    if (location.hash.startsWith("#stage/") || location.hash.startsWith("#tool/")) {
      history.replaceState(null, "", `#${activeArea}`);
    }
    drawer.close();
    if (restoreFocus) {
      const fallback = tabs.find(tab => tab.dataset.tab === activeArea);
      const visibleTarget = target?.isConnected && !target.closest("[hidden]") ? target : fallback;
      visibleTarget?.focus({ preventScroll: true });
    }
  }
  function setHeading(title, summary, location, state) {
    const heading = document.getElementById("stage-title");
    heading.textContent = title;
    heading.tabIndex = -1;
    document.getElementById("stage-summary").textContent = summary;
    document.getElementById("stage-location").textContent = location;
    const stateLabel = document.getElementById("stage-status");
    stateLabel.hidden = !state;
    stateLabel.textContent = state ? stateNames[state] : "";
    stateLabel.className = state ? `badge ${stateClasses[state]}` : "badge";
    content.replaceChildren();
  }
  function renderStage(id) {
    const stage = stages[id];
    currentStage = id;
    setHeading(stage.title, stage.summary, `${stage.phase} / Graph card ${order.indexOf(id) + 1} of ${order.length}`, stage.state);
    content.append(element("h3", "Tools used here"));
    const tools = element("div", "", "product-list");
    for (const tool of stage.tools) tools.append(productButton(tool));
    content.append(tools);
    section("Input", stage.input);
    section("Work", stage.actions);
    section("Result", stage.output);
    content.append(element("p", stage.note, "callout"));
    content.append(element("h3", "Source files"));
    const sources = element("ul");
    for (const [href, label] of stage.sources) {
      const item = element("li");
      const link = element("a", label);
      link.href = href;
      item.append(link);
      sources.append(item);
    }
    content.append(sources);
    const area = element("a", "Open the full area", "secondary-button");
    area.href = `#${stage.area}`;
    content.append(area);
    document.getElementById("stage-navigation").hidden = false;
    document.getElementById("previous-stage").textContent = "Previous card";
    document.getElementById("next-stage").textContent = "Next card";
    showDrawer();
  }
  function renderTool(id) {
    const product = products[id];
    setHeading(product.name, product.use, "Product use");
    if (product.logo) {
      const image = element("img");
      image.src = `visuals/product-logos/${product.logo}.svg`;
      image.alt = `${product.name} mark`;
      image.width = image.height = 48;
      content.append(image);
    }
    content.append(element("h3", "Graph stages"));
    const links = element("div", "", "stage-links");
    for (const [key, stage] of Object.entries(stages)) {
      if (!stage.tools.includes(id)) continue;
      const button = element("button", "", "secondary-button stage-link");
      button.type = "button";
      button.dataset.openStage = key;
      button.append(element("span", stage.title), badge(stage.state));
      links.append(button);
    }
    content.append(links);
    if (!links.children.length) content.append(element("p", "This tool runs outside the graph stages."));
    if (product.other) {
      content.append(element("h3", "Other use"));
      content.append(element("p", product.other));
    }
    content.append(element("p", "Planned stages are not active yet. A product mark does not show run status.", "callout"));
    const source = element("a", "Open the source file", "secondary-button");
    source.href = product.source;
    content.append(element("h3", "Source"), source);
    document.getElementById("stage-navigation").hidden = true;
    showDrawer();
  }
  function activate(id, focus = "") {
    activeArea = id;
    for (const tab of tabs) {
      const active = tab.dataset.tab === id;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
    }
    for (const panel of panels) panel.hidden = panel.id !== id;
    closeDrawer(false);
    closeStatPane(false);
    if (focus === "tab") {
      const tab = tabs.find(item => item.dataset.tab === id);
      tab.focus({ preventScroll: true });
      if (getComputedStyle(navigation.parentElement).position !== "sticky") {
        tab.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
    } else if (focus === "panel") {
      byId.get(id).focus({ preventScroll: true });
      byId.get(id).scrollIntoView({ block: "start" });
    }
  }
  function route() {
    const hash = location.hash.slice(1) || "overview";
    setStatus(settingsMessage);
    if (hash.startsWith("stage/") && Object.hasOwn(stages, hash.slice(6))) renderStage(hash.slice(6));
    else if (hash.startsWith("tool/") && Object.hasOwn(products, hash.slice(5))) renderTool(hash.slice(5));
    else if (byId.has(hash)) activate(hash);
    else {
      activate("overview");
      setStatus("This link does not identify a known area or graph card. The overview is shown.");
    }
  }
  function go(hash, replace = false) {
    if (location.hash !== `#${hash}`) history[replace ? "replaceState" : "pushState"](null, "", `#${hash}`);
    route();
  }

  // Summary cards open a pane that lists everything behind the card. Counts come from the data above.
  const statPane = document.getElementById("stat-pane");
  const statList = document.getElementById("stat-pane-list");
  const siteRoot = document.body.dataset.root;
  // On the Pages site each workflow has its own page; standalone, the link goes to the workflow source file.
  const workflowHref = (stem, extension = "yml") =>
    siteRoot ? `${siteRoot}workflows/${stem}.html` : `../.github/workflows/${stem}.${extension}`;
  const stageLink = id => ({ label: "Stage details", href: `#stage/${id}`, stage: id });
  const workflowLink = (stem, name, extension) => ({ label: name, href: workflowHref(stem, extension), name: true });
  const groupItem = (id, stem, name) => ({
    title: stages[id].title, note: stages[id].summary, href: `#${stages[id].area}`,
    also: [stageLink(id), workflowLink(stem, name)]
  });
  const checkItem = (stem, name, note) => ({ title: name, name: true, note, href: workflowHref(stem) });
  const agentItem = (stem, name, note) => ({ title: name, name: true, note, href: workflowHref(stem, "md") });
  const statPanes = {
    groups: {
      title: "3 test groups",
      intro: "Select a group to open its area. Each group also links to its stage details and its workflow.",
      items: [groupItem("java", "fuzz", "Fuzzing"), groupItem("api", "dast", "DAST"), groupItem("workflow", "lint", "Workflow lint")]
    },
    checks: {
      title: "7 release checks",
      intro: "The Release gate requires these seven workflows to pass for the tag commit. Select one to open its workflow page.",
      items: [
        checkItem("ci", "CI", "Build the app and run unit, property and integration tests with coverage."),
        checkItem("sast", "SAST", "CodeQL and Semgrep check source code for security defects."),
        checkItem("sca", "SCA", "OSV-Scanner and Trivy check dependencies for known vulnerabilities."),
        checkItem("secrets-iac", "Secrets and IaC", "Gitleaks checks repository history for secrets. Hadolint checks Dockerfile rules."),
        checkItem("container", "Container", "Trivy scans container images."),
        checkItem("dast", "DAST", "Schemathesis and OWASP ZAP test the running API."),
        checkItem("fuzz", "Fuzzing", "Jazzer runs saved inputs or searches for new failing inputs.")
      ]
    },
    agents: {
      title: "7 agents",
      intro: "Each agent is a GitHub Agentic Workflow with declared limits. Select one to open its workflow page.",
      items: [
        agentItem("security-triage", "Security Finding Triage", "Opens one deduplicated issue for each new scanner rule or CVE."),
        agentItem("pr-security-reviewer", "Pull Request Security Reviewer", "Posts one security review comment on each pull request."),
        agentItem("daily-security-report", "Daily Security Report", "Publishes a daily Discussion and chat notifications."),
        agentItem("pipeline-failure-analyst", "Pipeline Failure Analyst", "Diagnoses failed CI, E2E, Container and Release runs and opens one issue."),
        agentItem("release-readiness", "Release Readiness Review", "Posts a go or no-go readiness issue before the production approval."),
        agentItem("release-notes", "Release Notes Writer", "Writes a highlights section for the GitHub Release notes."),
        agentItem("security-remediation", "Security Remediation", "Fixes one open security-finding issue and opens a pull request.")
      ]
    },
    guide: {
      title: "Read-only guide",
      intro: "What this page can and cannot do. Select a fact to open the page that backs it up.",
      items: [
        { kind: "Can", title: "Show the pipeline graph and the details of each stage.", href: "#overview" },
        { kind: "Can", title: "Link to source files, reports and diagrams.", href: "#reports" },
        { kind: "Can", title: "Label each step as current or planned.", href: "#gates" },
        { kind: "Cannot", title: "Run jobs or start a workflow.", note: "GitHub Actions runs the jobs.", href: workflowHref("pipeline") },
        { kind: "Cannot", title: "Approve a release.", note: "People approve the production environment.", href: "#stage/approval", stage: "approval" },
        { kind: "Cannot", title: "Show live pass or fail results.", note: "Pass and Hold are example decisions.", href: "#stage/pass", stage: "pass" }
      ]
    }
  };
  let statCard = null;
  function statLinkItem(item) {
    const entry = element("li", "", "stat-pane-item");
    const link = element("a", "", "stat-pane-link");
    link.href = item.href;
    if (item.stage) link.dataset.stage = item.stage;
    if (item.kind) link.append(element("span", item.kind, `stat-pane-kind${item.kind === "Cannot" ? " stat-pane-kind-no" : ""}`));
    const title = element("span", item.title, "stat-pane-title");
    if (item.name) title.setAttribute("data-no-translate", "");
    link.append(title);
    if (item.note) link.append(element("span", item.note, "stat-pane-note"));
    entry.append(link);
    if (item.also) {
      const row = element("p", "", "stat-pane-also");
      for (const extra of item.also) {
        const anchor = element("a", extra.label);
        anchor.href = extra.href;
        if (extra.stage) anchor.dataset.stage = extra.stage;
        if (extra.name) anchor.setAttribute("data-no-translate", "");
        row.append(anchor);
      }
      entry.append(row);
    }
    return entry;
  }
  function openStatPane(card) {
    const pane = statPanes[card.dataset.stat];
    if (!pane || statPane.open) return;
    statCard = card;
    document.getElementById("stat-pane-title").textContent = pane.title;
    document.getElementById("stat-pane-intro").textContent = pane.intro;
    statList.replaceChildren(...pane.items.map(statLinkItem));
    card.setAttribute("aria-expanded", "true");
    statPane.showModal();
    refreshLocale();
    document.getElementById("stat-pane-body").scrollTop = 0;
    document.getElementById("stat-pane-title").focus({ preventScroll: true });
  }
  function closeStatPane(restoreFocus = true) {
    if (!statPane.open) return;
    const card = statCard;
    statCard = null;
    statPane.close();
    card?.setAttribute("aria-expanded", "false");
    if (restoreFocus && card?.isConnected && !card.closest("[hidden]")) card.focus({ preventScroll: true });
  }
  for (const card of document.querySelectorAll("[data-stat]")) {
    const pane = statPanes[card.dataset.stat];
    const count = Number.parseInt(card.querySelector("strong").textContent, 10);
    if (!pane || (Number.isInteger(count) && count !== pane.items.length)) console.error(`Summary card "${card.dataset.stat}" does not match its list.`);
    card.addEventListener("click", () => openStatPane(card));
  }

  navigation.setAttribute("role", "tablist");
  const navigationSize = new ResizeObserver(entries => {
    document.documentElement.style.setProperty("--navigation-height", `${entries[0].target.getBoundingClientRect().height}px`);
  });
  navigationSize.observe(navigation.parentElement);
  for (const tab of tabs) {
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-controls", tab.dataset.tab);
  }
  for (const panel of panels) {
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", `tab-${panel.id}`);
    panel.tabIndex = 0;
  }
  for (const link of document.querySelectorAll("[data-box]")) {
    const [x, y, width, height] = link.dataset.box.split(" ").map(Number);
    link.style.left = `${100 * x / 1600}%`;
    link.style.top = `${100 * y / 2268}%`;
    link.style.width = `${100 * width / 1600}%`;
    link.style.height = `${100 * height / 2268}%`;
    link.setAttribute("aria-haspopup", "dialog");
    link.setAttribute("aria-controls", "stage-drawer");
  }
  for (const list of document.querySelectorAll("[data-products]")) {
    for (const id of list.dataset.products.split(" ")) list.append(productButton(id));
  }
  const directory = document.getElementById("tool-directory");
  for (const [id, product] of Object.entries(products)) {
    const card = element("article", "", "card tool-card");
    card.append(productButton(id), element("p", product.use));
    const used = Object.values(stages).filter(stage => stage.tools.includes(id));
    card.append(element("p", used.length ? `Graph cards: ${used.map(stage => stage.title).join(", ")}.` : product.other));
    directory.append(card);
  }
  buildStageList();
  refreshLocale();
  if (!siteOwnsPreferences) loadPreferences();
  applyPreferences();
  updateStageView();
  for (const [key, control] of Object.entries(controls)) {
    control?.addEventListener("change", () => {
      if (key === "reduceMotion") preferences.motion = control.checked ? "reduce" : "system";
      else preferences[key] = control.type === "checkbox" ? control.checked : control.value;
      applyPreferences();
      savePreferences();
    });
  }
  for (const query of Object.values(media)) {
    query.addEventListener("change", () => {
      applyPreferences();
      updateStageView();
    });
  }
  listToggle?.addEventListener("click", () => {
    listChoice = listToggle.getAttribute("aria-pressed") !== "true";
    updateStageView();
  });
  document.documentElement.classList.add("enhanced");
  activate("overview");
  route();
  window.addEventListener("popstate", route);
  window.addEventListener("hashchange", route);
  document.getElementById("close-drawer").addEventListener("click", () => closeDrawer());
  drawer.addEventListener("cancel", event => {
    event.preventDefault();
    closeDrawer();
  });
  drawer.addEventListener("keydown", event => trapTab(drawer, event));
  statPane.addEventListener("keydown", event => trapTab(statPane, event));
  function trapTab(dialog, event) {
    if (event.key !== "Tab" || event.ctrlKey || event.altKey || event.metaKey) return;
    const controls = [...dialog.querySelectorAll("button, a[href], input, select, textarea, [tabindex]")]
      .filter(control => control.tabIndex >= 0 && !control.matches(":disabled") && control.getClientRects().length);
    const first = controls[0];
    const last = controls.at(-1);
    if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    } else if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    }
  }
  function outsideDrawer(event) {
    const bounds = drawer.getBoundingClientRect();
    return event.target === drawer &&
      (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom);
  }
  let backdropPress = false;
  drawer.addEventListener("pointerdown", event => {
    backdropPress = event.button === 0 && outsideDrawer(event);
  });
  drawer.addEventListener("pointercancel", () => { backdropPress = false; });
  drawer.addEventListener("click", event => {
    const close = backdropPress && outsideDrawer(event);
    backdropPress = false;
    if (close) closeDrawer();
  });
  document.getElementById("close-stat-pane").addEventListener("click", () => closeStatPane());
  statPane.addEventListener("cancel", event => {
    event.preventDefault();
    closeStatPane();
  });
  statPane.addEventListener("click", event => {
    if (event.target === statPane) {
      const bounds = statPane.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) closeStatPane();
      return;
    }
    const link = event.target.closest('a[href^="#"]');
    if (link && event.button === 0 && !(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)) closeStatPane();
  });
  for (const [button, step] of [["previous-stage", -1], ["next-stage", 1]]) {
    document.getElementById(button).addEventListener("click", () => {
      const next = (order.indexOf(currentStage) + step + order.length) % order.length;
      go(`stage/${order[next]}`, true);
    });
  }
  document.addEventListener("click", event => {
    const stageButton = event.target.closest("[data-open-stage]");
    const product = event.target.closest("[data-tool]");
    if (stageButton) { go(`stage/${stageButton.dataset.openStage}`); return; }
    if (product) { go(`tool/${product.dataset.tool}`); return; }
    const link = event.target.closest('a[href^="#"]');
    if (!link || event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (link.dataset.stage) {
      event.preventDefault();
      go(`stage/${link.dataset.stage}`);
      return;
    }
    const id = link.getAttribute("href").slice(1);
    if (id === "content") {
      event.preventDefault();
      const main = document.getElementById("content");
      main.focus({ preventScroll: true });
      main.scrollIntoView({ block: "start" });
      return;
    }
    if (!byId.has(id)) return;
    event.preventDefault();
    go(id);
    activate(id, link.hasAttribute("data-tab") ? "tab" : "panel");
  });
  navigation.addEventListener("keydown", event => {
    const index = tabs.indexOf(event.target);
    if (index < 0 || event.altKey || event.ctrlKey || event.metaKey ||
        !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 :
      (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    go(tabs[next].dataset.tab, true);
    activate(tabs[next].dataset.tab, "tab");
  });
})();
