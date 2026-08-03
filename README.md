# Term I Notebook Validation 2026-27 — Audit Report

G.D. Goenka School, Darbhanga. Audit of the Term I notebook validation drive,
29 July – 4 August 2026.

**Live report:** https://abhishekchhetri020.github.io/gdgs-notebook-validation-term1/

This is the shareable summary. It shows coverage by class, validator performance,
teacher accountability and the actions arising. Individual student names and
admission numbers are deliberately withheld — those are held in a separate
confidential version issued to the Director and the Academic Coordinator.

## Rebuilding

    python3 build.py

`build.py` generates `index.html` (public) and `confidential.html` (private) from
`data.json`. The build refuses to write the public page if any student name or
admission number is found in it.

`data.json` is **not** published here — it holds the student-level findings and is
kept inside the school. The public page in this repository is generated output only.
