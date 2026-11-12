# Simplified Technical French for the pipeline guide

This is the project's controlled-French writing standard for the
[pipeline explorer](fuzzing-pipeline-explorer.html), its accessible text, and
its French diagram. It is not a certified language standard or a translation
of ASD-STE100. It does not claim review by a human native French speaker.

The target is clear, idiomatic French for French-speaking software developers.
Use neutral professional language and French typographic conventions.
Do not reproduce awkward literal translations merely because a vendor uses
them. Historical source reports keep their original language.

## Writing rules

1. Use one term for one concept. Use the approved terms below in interface
   labels, descriptions, diagrams, accessible names, and diagnostics.
2. Prefer short sentences and the active voice. Name the tool or component
   that performs an operation. Use the imperative with **vous** in instructions.
3. Give one action per instruction. Split a long explanation at a natural
   boundary. Do not remove technical conditions to make a sentence shorter.
4. Distinguish an input, a result, a reported anomaly, and a confirmed defect.
   Do not turn a scanner finding into a proven vulnerability.
5. Preserve current, planned, measured, required, and advisory status.
   Never translate a proposed check as an active release requirement.
6. Preserve negation, limits, units, comparison boundaries, dates, and numeric
   facts. A configured time budget or example limit is not a measured total.
7. Explain a technical borrowing in the glossary. Keep product names,
   identifiers, filenames, URLs, commands, versions, and GitHub event names
   unchanged. A product name is not a live-status indicator.
8. Use sentence case. Keep accents on capital letters. Use French apostrophes
   and quotation marks in prose, not in code or identifiers.
9. Use a nonbreaking space before a colon or percent sign and inside French
   quotation marks. Use a narrow nonbreaking space before a semicolon,
   question mark, or exclamation mark. Use a decimal comma and nonbreaking
   thousands separators. Do not localize version numbers or code literals.
10. Read complete rendered sentences, including text split by links or code
    elements. A correct fragment can become incorrect when joined to another.
11. Keep accessible names and diagram labels consistent with the visible
    controls. Short diagram labels may omit an article, but not a distinction
    needed to understand a result or decision.

## Approved terminology

Terms are lowercase here unless they are proper names or acronyms. Capitalize
the first word when it starts a label or sentence.

| English concept | Approved French | Meaning or restriction |
| --- | --- | --- |
| pipeline | pipeline | The complete sequence and its parallel branches. |
| graph / diagram | schéma | The visual connection map. |
| graph card | fiche | A selectable item in the diagram. |
| side panel | panneau latéral | The details opened from a fiche or product. |
| pipeline stage | étape du pipeline | A conceptual grouping, not necessarily a GitHub Actions step. |
| workflow | workflow | A GitHub Actions automation; do not alternate with *flux de travail*. |
| job | tâche | A group of GitHub Actions steps executed on one runner. |
| runner | exécuteur | The machine or environment that executes a task. |
| commit | commit | An identified saved state in Git, not an approval. |
| pull request | pull request | A request to review and merge branch changes. |
| tag | tag | A Git reference; not the published release itself. |
| release process | publication | The process, not necessarily deployment to production. |
| published release | version publiée | The published GitHub release object. Preserve product identifiers. |
| build | compilation | Short pipeline label; explain assembly and packaging when relevant. |
| package | paquet | A published software package; retain registry identifiers. |
| input | entrée | Data supplied to a test or application. |
| test results | résultats de test | Outputs and observations, not the supplied test data. |
| test record | dossier de résultats | Result files and metadata associated with a test run. |
| data record | enregistrement | One structured data entry; not a synonym for all result files. |
| artifact | artefact | A saved output file from a build or test task. |
| manifest | manifeste | The index that identifies results, tools, inputs, and executions. |
| fuzzing | fuzzing | Automated testing with generated or modified inputs, not only random data. |
| corpus | corpus | Saved test inputs. |
| seed corpus | corpus initial | Starting inputs; not the pseudo-random seed. |
| random seed | graine aléatoire | Initialization value for reproducible pseudo-random generation. |
| replay | rejeu | A test repeated with the same input. |
| rerun | nouvelle exécution | Does not by itself guarantee the same inputs. |
| shrinking / input reduction | réduction d’une entrée | Make a failing input smaller while preserving the failure. |
| property-based test | test fondé sur les propriétés | Check a general rule with generated inputs. |
| regression test | test de non-régression | Check that an earlier defect does not return. |
| mutation test | test par mutation | Modify application code to assess the tests. |
| input mutation | mutation d’une entrée | Modify test data; not a code-mutation score. |
| code coverage | couverture du code | Code executed during tests, not proof of correctness. |
| finding | anomalie | A reported observation that still requires review. |
| defect | défaut | A fault in software; not every reported anomaly is a confirmed defect. |
| severity | gravité | How serious a reported anomaly is. |
| gate | contrôle bloquant | A check that controls whether the pipeline may continue. |
| quality / release gate | contrôle de qualité / de publication | Contextual short labels for a gate. Explain its blocking effect. |
| pass / hold | autoriser / bloquer | Illustrative decisions, not a claim about a live execution. |
| allowlist | liste d’exceptions | Accepted exceptions; acceptance does not fix the reported problem. |
| hash | empreinte de hachage | Identifies a commit or helps verify file contents. |
| time budget | durée maximale | An allowed duration, not elapsed time. |
| UTF-16 code unit | unité de code UTF-16 | .NET string length unit (UTF-16); not necessarily one visible character. |
| CI/CD | CI/CD | Intégration continue et livraison continue in this guide. |

The compact diagram form **contrôle qualité** is allowed for quality and
release gates. The pipeline row supplies the context; the side panel explains
the full rule and its blocking effect. After the glossary explains
**empreinte de hachage**, **empreinte** is allowed in context. An empreinte is
not a digital signature.

## Review and validation

- Review every message value and every dynamic translation pattern against
  the English meaning and the component that displays it.
- Review every French SVG text node, title, and description. Keep diagram
  geometry, connection meaning, and the current/planned distinction intact.
- Check all glossary definitions, control labels, status messages, and
  accessible names. Keep explanations consistent across the interface.
- Exercise all tabs, stage panels, and product panels in both languages.
  Check joined text, missing translations, switching languages in an open
  panel, and number formatting.
- Check long French text at narrow widths and enlarged text sizes. Check SVG
  text bounds. Do not solve overflow by removing meaning or reducing legibility.
- Record automated and AI-assisted review separately from human linguistic
  review. Do not claim formal certification or human review that did not occur.

## Reference basis

These references inform terminology and technical meaning. They do not
certify this project's complete glossary:

- [DITP: La mallette du langage clair](https://www.modernisation.gouv.fr/campus-de-la-transformation-publique/catalogue-de-ressources/outil/la-mallette-du-langage-clair)
  provides a reader-centered approach to clear writing. This guide adapts that
  goal to technical instructions without removing technical conditions.
- [MDN: Fuzzing (test à données aléatoires)](https://developer.mozilla.org/fr/docs/Glossary/Fuzzing)
  explains the established borrowing and invalid or unexpected inputs.
- [GitHub: Workflows](https://docs.github.com/fr/actions/concepts/workflows-and-actions/workflows)
  distinguishes workflows, jobs, steps, and runners. This guide deliberately
  uses the consistent project terms *workflow*, *tâche*, and *exécuteur*.
- [GitHub: About releases](https://docs.github.com/fr/repositories/releasing-projects-on-github/about-releases)
  distinguishes published versions from Git tags. This guide retains *tag*
  rather than alternating between several French translations.
