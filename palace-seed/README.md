# Curated Valdris seed review

`source-manifest.json` pins the authored Git tree at commit
`137ea1981223fedf4c36902a98d8d66a73d701b4` and records the SHA-256 of
every tracked Markdown note. It reconciles those notes with the local iCloud
Obsidian vault by digest. The extra iCloud-only Markdown file is counted, not
published by path or content. Every note is held; there are no approved seed
items and this repository contains no Palace write tool.

The note `audience` values are review hints, not permission grants. `player`
means `Welcome.md` or `Player Resources/`; `gm` means `Adventures/` or
`DM Resources/`; other notes are `undetermined`. A reviewer must inspect the
specific excerpt and claim before assigning its final audience and status.
The public vault includes material intended for game masters, so publication
of the source repository alone does not authorize a player response.

## Recheck the pinned source

Run this with the iCloud vault available on the operator's Mac:

```bash
python3 tools/valdris_seed.py validate \
  --vault "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Valdris" \
  --manifest palace-seed/source-manifest.json
python3 tools/valdris_seed.py preview \
  --vault "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Valdris" \
  --manifest palace-seed/source-manifest.json
```

The preview reports counts only and makes no Palace request. Any pinned-source
digest, vault snapshot, destination, or schema mismatch blocks it. To freeze a
new source revision, use `freeze --revision <reviewed-commit> --manifest
<new-private-path>`; it refuses to overwrite an existing manifest.

## Review and admission

Copy the manifest to an operator-controlled `.private/` path before adding
claim text or decisions. The private copy may add `items`, each with a stable
lowercase hyphenated `id`, `source_path`, `source_revision`, `source_sha256`, an
exact `source_excerpt`, a short atomic `claim`, `audience`, `status`, `operation`,
`native_identity`, and `approval`. Held items use `status: held` and null
`native_identity` and `approval`. An approved drawer requires an explicit
`approval` object with `decision: approved`, nonempty `reviewer`, UTC
`reviewed_at`, and `native_identity: valdris-seed-<id>`. The current validator
accepts only `drawer`; KG operations need a separate audience-safe triple and
timeline contract.

Structural validation cannot authenticate the reviewer's identity or establish
that a paraphrase is true. Independent operator review must approve the exact
private manifest digest before a later importer can write. That importer needs
its own fixed-wing credential, exact target readback, write receipt, and
zero-write replay proof. The Lorekeeper's player retrieval boundary also needs
negative tests before any approved GM item can coexist with player traffic.

The first review candidates are `Welcome.md`, `Timeline.md`, and
`Player Resources/Common Knowledge.md`. The current manifest admits none of
their claims. Valdris Hindsight records remain a separate held source and
cannot enter a bulk import cohort through this manifest.
