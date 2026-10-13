# FCPXML validation and import workflow

Validate without changing the artifact. A passing lower layer never hides an
unverified higher layer.

## Validation layers

1. **Artifact** — accept a flat `.fcpxml` or a `.fcpxmld` bundle whose root
   contains `Info.fcpxml`; reject `.fcpbundle`.
2. **Syntax and document** — require well-formed XML, `fcpxml` root, numeric
   `major.minor` version, and no `standalone="yes"` declaration.
3. **Semantic** — require `resources`, resolve every nonempty `ref` to an `id`,
   report negative `duration`, `offset`, and `start`, and require every local
   `original-media` URL to exist. Resolve relative URLs from the directory
   containing the flat document or bundle-root `Info.fcpxml`.
4. **Matching DTD** — select the DTD fixed to the exact declared version and
   validate with `xmllint`.
5. **Workflow** — separately check project intent, frame alignment, effect or
   title availability, transition handles, and target-version behavior when
   relevant.
6. **Import** — dispatch after successful validation when the user requests
   import. Validation is preflight, not proof of completed import.

Apple notes that DTD-conforming documents can still contain data Final Cut Pro
cannot import. A DTD failure is nevertheless a hard structural failure.

## Run the Python validator

```text
scripts/validate-fcpxml <artifact.fcpxml|artifact.fcpxmld>
scripts/validate-fcpxml <artifact> --dtd <matching.dtd>
```

The command emits one JSON object and never writes the artifact, its bundle,
or media.

- `status: valid`, exit 0 — semantic and matching-DTD gates passed.
- `status: invalid`, exit 65 — at least one executed gate rejected the input.
- `status: incomplete`, exit 2 — the exact DTD or `xmllint` was unavailable.

Top-level `semanticValid` and `dtdValid` expose each validation gate. Issues
use `gate`, `type`, `message`, and `context`; `checks` records the tool and DTD
actually used.

## Find a matching DTD

For `X.Y`, automatic discovery checks:

```text
/Applications/Final Cut Pro Creator Studio.app/Contents/Frameworks/
  Interchange.framework/Versions/A/Resources/FCPXMLvX_Y.dtd
/Applications/Final Cut Pro.app/Contents/Frameworks/
  Interchange.framework/Versions/A/Resources/FCPXMLvX_Y.dtd
```

An explicit DTD must declare the same fixed version. Never approximate with an
older or newer DTD.

## Diagnose failures

| Gate | Typical finding | Direction |
|---|---|---|
| Artifact | Missing `Info.fcpxml`, wrong extension, `.fcpbundle` | Select an interchange artifact. |
| Document | Malformed XML, wrong root/version, `standalone="yes"` | Fix serialization into a new output. |
| DTD | Illegal child, order, attribute, value, duplicate ID | Query the exact declaration and correct structure. |
| Semantic | Missing `resources` or unresolved `ref` | Rebuild the document-local reference graph. |
| Media | Missing decoded absolute or document-relative original-media path | Correct URL encoding/path or define an intentional offline workflow. |
| Target | Missing effect/title or unsupported feature | Compare a verified export from the target installation. |
| Import | Final Cut Pro rejects valid preflight | Preserve the artifact and capture the application diagnostic. |

## Automated import handoff

```text
scripts/import-fcpxml <artifact>
scripts/import-fcpxml <artifact> --dry-run
scripts/import-fcpxml <artifact> --dtd <matching.dtd>
scripts/import-fcpxml <artifact> --library-location <Library.fcpbundle>
scripts/import-fcpxml <artifact> --copy-assets
scripts/import-fcpxml <artifact> --leave-assets-in-place
```

The import command validates the Source artifact, resolves a deterministic
Target Library, creates an immutable Import-ready copy, injects
`import-options` as the first `fcpxml` child, and validates the copy before
dispatch. It reuses an existing exported `.fcpbundle` location when possible;
otherwise it requires `--library-location` and fails before Final Cut Pro can
show its modal Library picker. A path without the `.fcpbundle` suffix is
normalised to that suffix. The parent directory must already exist.

The Import-ready options always include `library location` and `suppress
warnings`; warning suppression defaults to enabled. The `copy assets` option is
omitted by default so Final Cut Pro retains its current preference. Pass exactly
one of `--copy-assets` or `--leave-assets-in-place` to override it. Use
`--show-warnings` to disable warning suppression. `--dry-run` still creates and
validates the Import-ready artifact but skips the Apple event.

Dispatch invokes `osascript` with a static AppleScript handler that targets the
supported Final Cut Pro bundle identifier, activates the application, and opens
the Import-ready flat file or copied bundle as a POSIX file. The path is passed
through `argv`, not interpolated into AppleScript source. macOS may ask the
invoking terminal or Codex for Automation permission.

A zero result with `status: dispatch_accepted` and
`dispatchMethod: open-document-apple-event` means only that the Open Document
event returned without an immediate error. Confirm completion separately in
Final Cut Pro.

For transcript-guided rough cuts and other workflows, dispatch after successful
validation when the user's request includes import.

Authoritative workflow reference: [Sending Data Programmatically to Final Cut
Pro](https://developer.apple.com/documentation/professional-video-applications/sending-data-programmatically-to-final-cut-pro).

For validation-only requests, stop after reporting; never dispatch implicitly.
