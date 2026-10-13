# Transcript-guided FCPXML rough cut

Use the [Cliptate Skill](../../cliptate/SKILL.md) to obtain transcription.
The current agent selects ranges and constructs a new FCPXML document using
Python XML parsing and rational arithmetic. Cliptate supplies transcription;
its public CLI does not cut video, export FCPXML, translate, or invoke GUI AI Cut.

## Preserve the source and establish its clock

Accept one flat `.fcpxml` or a `.fcpxmld` with root `Info.fcpxml`. Preserve the
export, sidecars, media, and original transcript; record their relevant hashes
and write generated files into a new project output directory outside the
skills repository. A `.fcpbundle` is a Library; obtain an FCPXML export instead
of editing its database.

Identify the intended Project explicitly when the export contains several.
Inspect its sequence format, frame duration, primary story, source in-points,
retiming, transitions, connected clips, multicam, compound clips, roles, and
timed children before constructing the edit. Preserve the declared version,
format, orientation, audio layout, and color policy unless the user requests
a change. Resolve dimensions from the sequence's format resource rather than
assuming landscape.

The transcript clock must follow the Project's rendered story. Reuse an aligned
transcript or transcribe a local audio/video render of that Project. Original
media is suitable only for a proven untrimmed, zero-based single-media story,
or with an explicit verified mapping from media time to story time. A trimmed
or assembled Project generally has a different clock. FCPXML input itself is
not a media file accepted by `cliptate transcribe`.

If an aligned story render or mapping is missing, complete source inspection
and obtain the required render or timing information before generating cuts.

## Obtain and normalize transcription

For a new transcript, read [the Cliptate Skill](../../cliptate/SKILL.md) and
[its transcription reference](../../cliptate/references/transcription.md).
Follow their CLI discovery, model selection, download, and error handling
instructions. Install the `cliptate/` and `fcpxml/` skill folders side by side.

For example, with an existing output directory:

```sh
cliptate transcribe "/path/to/project-story.mov" --format json --output "/path/to/output/transcript.json"
```

Add `--language` or `--model` only as needed and supported by the installed
helper. Use the app's configured model by default. Model arguments are
Cliptate model IDs, not Hugging Face repository names.

Cliptate writes `{ "files": [...] }`. Select the successful entry whose `file`
matches the intended local story render; check process exit status and the
entry's `error` before using `segments`. Each segment supplies `id`, `text`,
`start`, and `end` in seconds, with optional speaker information. Preserve the
raw JSON and original IDs. Already aligned transcripts may be reused after
checking their provenance, timing units, and range against the story duration.

The public JSON provides segment timestamps, not word timestamps. Choose
complete utterances and verify cuts against audio. Finer cuts need listening
and manually verified boundaries; evenly subdividing text does not provide
word alignment.

## Select and record retained ranges

Read the transcript with neighboring context. Apply the user's editorial brief
to remove false starts, repetition, irrelevant passages, or silence while
preserving complete thoughts. With no narrower brief, retain non-empty speech
with enough padding to protect words and describe the result as a conservative
speech assembly. Do not manufacture word-level filler removal from segment
timestamps alone.

Write an edit manifest containing the source Project, transcript source, original
segment IDs, retained story ranges, reasons, and resulting timeline positions.
Keep editorial decisions separate from the immutable original transcript.
Check finite timestamps and `0 <= start < end <= story duration`; merge
overlapping padded ranges and preserve story order unless reordering is requested.
Convert using `Fraction(str(value))` and quantize to the sequence frame grid.
Record actual frame-aligned boundaries and inspect their audio impact.

## Construct the new Project structurally

Read [construction-patterns.md](construction-patterns.md) and
[specification.md](specification.md); query the matching DTD for affected
elements. Use a Python XML parser and `fractions.Fraction`, preserving resource
references and the source's time coordinate conventions.

For a simple, unretimed `asset-clip` in a verified story coordinate system,
intersect each retained range with the clip's visible parent interval. A
fragment's source start is the original clip `start` plus the intersection's
displacement from the original clip `offset`; its duration is the intersection
length. Place fragments contiguously using accumulated retained durations in
the destination parent's coordinate system. Export rational seconds, update
the sequence duration, and retain required resource definitions. Splitting a
range across several source clips yields several fragments, preserving their
source order and in-points.

Do not apply that simple formula to retimed, synchronized, compound, or multicam
structures without resolving their nested clocks. Clip children have local
timing too: trim or remap connected clips, titles, markers, keyframes, and audio
automation with their parent fragments. Rebuild or omit transitions only when
consistent with the user's edit and available handles. Report an unsupported
structure and the missing mapping rather than silently flattening or losing it.

Keep media URLs resolvable from the new document. Moving a flat document with
relative media paths changes their base; resolve those URLs from the source and
serialize valid URLs for the destination. Preserve the complete resource closure,
roles, audio configuration, and metadata for retained content. New Project/Event
identities must follow the target export conventions, avoiding stale identifiers.

When subtitles are requested, the agent prepares original text and any requested
translations. Create editable `<title>` objects using an effect and published
parameters from a verified target export. Distinguish Titles from `<caption>`
objects, map cues through the retained intervals, and check placement in the
actual portrait or landscape frame. If the template is unavailable, deliver
remapped SRT/VTT and report that editable Titles were not generated.

Write a standalone `.fcpxml` to a new path, then stamp its single Project:

```text
scripts/stamp-fcpxml-project <generated.fcpxml>
```

Continue with the reported `outputArtifact`. The stamper creates a sibling file
and a Project name with the local `YYYY-MM-DD HH-MM-SS` suffix; it preserves the
generated input. Use `--timestamp` for reproducible checks or a requested time.

## Verify and deliver

1. Verify source and transcript hashes remain unchanged.
2. Inspect the single output Project, version, orientation, sequence duration,
   fragment order, original source in-points, resource closure, timed children,
   and any requested subtitle text and timing against the edit manifest.
3. Read [validation.md](validation.md) and run `scripts/validate-fcpxml` on the
   stamped file. Require `status: valid` and `valid: true`; generation success
   alone does not establish validity.
4. Listen to and inspect representative edit boundaries, especially the opening,
   ending, and any fragment split across source clips. Report preview limitations
   separately from structural validation.
5. When import is requested, run `scripts/import-fcpxml` after validation using
   the resolved target Library. Existing authorization needs no second confirmation.
   Confirm UI completion separately when available; `dispatch_accepted` proves
   only that the Open Document handoff was accepted.

Deliver the stamped FCPXML, edit manifest, transcript provenance, retained ranges,
and checks performed. For portable handoff, follow [portability.md](portability.md)
and deliver the entire `.fcpxmld` with its media. Preserve failed outputs for
diagnosis and report any missing DTD, media, template, or timing mapping precisely.
