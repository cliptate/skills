---
name: fcpxml
description: Draft, inspect, validate, package, and import Final Cut Pro .fcpxml documents and .fcpxmld bundles. Use for FCPXML structure and rational timing, portable media handoff, import diagnosis, or transcript-guided rough cuts using Cliptate transcription.
---

# FCPXML specification, portable packaging, rough cut, validation, and import

Treat the document's declared version and its exactly matching DTD as the
structural contract. Use Apple's documentation for semantics and verified
Final Cut Pro exports for environment-managed values. Use this Skill's Python
scripts for deterministic local operations; no Swift tool is required.

Run the bundled scripts with Python 3.9+; validation also requires `xmllint`
and the exact matching DTD. Final Cut Pro is required for import and automatic
DTD discovery; a supplied DTD supports validation without the application.
Resolve `scripts/...` relative to this Skill's folder, not the user's project.
For new transcription, install `cliptate/` beside `fcpxml/` and read
[the Cliptate Skill](../cliptate/SKILL.md). Other routes and reuse of an aligned
transcript do not require Cliptate.

## Route the request

| Request | Read and run |
|---|---|
| Explain an element, attribute, hierarchy, reference, or time value | Read [specification.md](references/specification.md). For an exact declaration, run `scripts/query-fcpxml-dtd`. |
| Draft or review common structures | Read [construction-patterns.md](references/construction-patterns.md) and [specification.md](references/specification.md), then query version-sensitive elements. |
| Validate `.fcpxml` or `.fcpxmld` | Read [validation.md](references/validation.md), then run `scripts/validate-fcpxml`. |
| Make media portable across computers, avoid path-dependent offline clips, or build a self-contained bundle | Read [portability.md](references/portability.md), then run `scripts/package-fcpxmld`. |
| Stamp one generated standalone Project with the local time | Run `scripts/stamp-fcpxml-project`; use its reported output artifact for later operations. |
| Rough-cut an existing Project from a story-aligned transcript | Read [rough-cut.md](references/rough-cut.md); use `$cliptate` for transcription when needed, then select ranges, construct the edit, stamp, and validate the new document. Import when requested. |
| Diagnose an import rejection | Read [specification.md](references/specification.md), [construction-patterns.md](references/construction-patterns.md), and [validation.md](references/validation.md); validate the unchanged artifact and map each finding to its validation layer. |
| Import into Final Cut Pro | Read [validation.md](references/validation.md), require explicit user intent, then run `scripts/import-fcpxml`. |

Read every selected reference completely before answering or acting.

## Resolve the version before reasoning

1. Accept only a flat `.fcpxml` file or a `.fcpxmld` directory containing
   root `Info.fcpxml`.
2. Read `fcpxml/@version`; never infer it from the extension or application
   marketing version.
3. Preserve the version unless the user explicitly requests a tested
   conversion.
4. Use a DTD whose fixed `fcpxml/@version` exactly matches the document.
5. Never read or modify a `.fcpbundle`; it is a Library, not FCPXML.

## Query the normative declaration

```text
scripts/query-fcpxml-dtd --input <artifact.fcpxml|artifact.fcpxmld> \
  --element <element-name>
```

Without an artifact, pass `--version <major.minor>`. Pass `--dtd <path>` only
for an authoritative user-supplied DTD. The script rejects version mismatch.

## Validate without mutation

```text
scripts/validate-fcpxml <artifact.fcpxml|artifact.fcpxmld>
```

The Python validator checks artifact shape, XML/root/version invariants,
rejects `standalone="yes"`, checks the required resources container and every
`ref`, reports negative time warnings, verifies local original media, and runs
the matching DTD with `xmllint`.
Supply `--dtd <path>` when the target Final Cut Pro DTD is not installed.

Accept only `status: valid` with `valid: true`. Exit 0 is valid, 65 is invalid,
and 2 is incomplete. Preserve the source byte-for-byte.

## Package local media for portable handoff

```text
scripts/package-fcpxmld <source.fcpxml|source.fcpxmld> \
  --output <ignored-output-dir>/<name>-portable.fcpxmld
```

The command validates the Source, copies every local `media-rep/@src` into
`Media/`, rewrites those URLs relative to root `Info.fcpxml`, verifies SHA-256
byte identity, preserves input-bundle sidecars, and validates the staged output
before publishing it. Accept only `status: created` with
`outputValidation.valid: true`. Move and deliver the complete `.fcpxmld`
bundle. A packaging request does not authorize import.

## Import according to route intent

```text
scripts/import-fcpxml <artifact.fcpxml|artifact.fcpxmld>
scripts/import-fcpxml <artifact> --library-location <Library.fcpbundle>
```

Import when the user's request includes Final Cut Pro import. Inspection,
construction, packaging, validation, and rough-cut generation alone produce
artifacts without dispatch. Existing import authorization carries through
successful validation; no second confirmation is needed.

The command validates the Source artifact, resolves a deterministic Target
Library, creates and validates an Import-ready artifact, then uses `osascript`
to send Apple's documented Open Document Apple event. It copies an existing
exported `.fcpbundle` location into `import-options`; otherwise require
`--library-location`. Final Cut Pro ignores `library/@location` during import.
Do not ask for a second confirmation immediately before dispatch.

The Source artifact remains unchanged. Flat documents produce a new `.fcpxml`;
bundles produce a complete `.fcpxmld` copy including sidecars. Use
`--import-copy` for a stable output path or accept the reported unique temporary
path. Media placement follows Final Cut Pro's preference unless exactly one of
`--copy-assets` or `--leave-assets-in-place` is supplied. Non-fatal warnings are
suppressed by default for zero-click import; pass `--show-warnings` to expose
them. Use `--dry-run` to prepare and validate without dispatch, and use
`--bundle-id` only to select a known Final Cut Pro distribution explicitly.

Treat `dispatch_accepted` as evidence of handoff only. It does not prove Final
Cut Pro finished importing, resolved media, or rendered installed effects.

## Keep claims precise

- DTD validity is necessary but insufficient; it cannot prove media semantics,
  effect availability, or successful import.
- Prefer the target installation's matching DTD and Apple's reference.
  MadAppGang's Skill is a non-normative pattern source.
- Do not recommend one universal FCPXML version.
- Interpret `offset`, `start`, and `duration` in their parent/local contexts.
- Parse or edit XML structurally; never mutate FCPXML with regular expressions.
- Do not repair, rewrite, or import merely because validation was requested.
