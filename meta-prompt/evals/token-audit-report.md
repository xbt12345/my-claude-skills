# Meta-Prompt Token Audit

## Measured

- SKILL.md entry: 2002 tokens
- All references + schemas if fully loaded: 15066 tokens
- Compiled prompt mean: 410.1 tokens
- Range: 256–519 tokens
- Budget pass rate: 100.0%
- Previous mean: 558.3 tokens; reduction: 26.5%

## By Mode

| Mode | Count | Mean | Max | Budget | Pass |
|---|---:|---:|---:|---:|---:|
| Guided | 11 | 294.5 | 319 | 350 | 100.0% |
| Harness | 22 | 467.9 | 519 | 700 | 100.0% |

## Evidence Boundary

- Token counts cover static files and deterministic compiled prompts.
- Historical Claude/Codex session usage cannot isolate the net cost caused by this Skill.
- API-equivalent USD values are comparison estimates, not subscription charges.
- Real optimization requires actual input/output/cached token fields recorded per run.
