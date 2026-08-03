# Term I Notebook Validation 2026-27 — Audit Report

G.D. Goenka School, Darbhanga. Audit of the Term I notebook validation drive,
29 July – 4 August 2026.

**Live report:** https://abhishekchhetri020.github.io/gdgs-notebook-validation-term1/

Published on the instruction of the Academic Coordinator so that teachers, validators and management all see the
same record. It contains student names and admission numbers and is excluded from search-engine indexing.

## Rebuilding

    python3 build.py

`build.py` generates `index.html` (public) and `confidential.html` (private) from
`data.json`. The class charts join the audit findings to a roster pulled fresh from the school ERP on 3 August 2026
(861 active students, 27 sections).

`data.json` holds the audit findings and `matrix.json` the ERP roster join; `build.py` regenerates both pages from them.
