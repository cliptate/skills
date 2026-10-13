# FCPXML construction patterns

Use these worked patterns to understand or draft common Final Cut Pro XML
structures. They adapt the topic coverage of MadAppGang's Final Cut Pro Skill,
but use original examples and correct the patterns for version-aware use. Query
the matching DTD before applying any fragment to a real document.

## Contents

- [Version policy](#version-policy)
- [Minimal project skeleton](#minimal-project-skeleton)
- [Formats and assets](#formats-and-assets)
- [Place clips on a timeline](#place-clips-on-a-timeline)
- [Insert gaps and transitions](#insert-gaps-and-transitions)
- [Add connected clips](#add-connected-clips)
- [Add titles and text](#add-titles-and-text)
- [Add markers](#add-markers)
- [Calculate rational time](#calculate-rational-time)
- [Run pre-import checks](#run-pre-import-checks)
- [Import into Final Cut Pro](#import-into-final-cut-pro)
- [Coverage from the source Skill](#coverage-from-the-source-skill)

## Version policy

The source Skill illustrates FCPXML 1.8 through 1.11 and recommends 1.9 for
broad compatibility. Keep that only as historical orientation. Do not select a
version from that table for a current workflow.

Instead:

1. Preserve `fcpxml/@version` when inspecting or editing an export.
2. Select the version supported by the target Final Cut Pro release when
   creating a new document.
3. Query the exactly matching DTD for every version-sensitive structure.
4. Convert versions only through an explicit, tested semantic conversion.

The examples below use FCPXML 1.14 for illustration.
Replace the version and structures together when targeting another release.

## Minimal project skeleton

Use a document-local format and asset resource, then reference them from a
project sequence. Replace the illustrative media URL before validation:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.14">
  <resources>
    <format id="r1" name="FFVideoFormat1080p25"
            frameDuration="1/25s" width="1920" height="1080"
            colorSpace="1-1-1 (Rec. 709)"/>
    <asset id="r2" name="Scene A" start="0s" duration="250/25s"
           hasVideo="1" hasAudio="1" format="r1"
           audioSources="1" audioChannels="2" audioRate="48000">
      <media-rep kind="original-media"
                 src="file:///Users/example/Media/Scene-A.mov"/>
    </asset>
  </resources>
  <event name="Example Event">
    <project name="Example Project">
      <sequence format="r1" duration="250/25s"
                tcStart="0s" tcFormat="NDF"
                audioLayout="stereo" audioRate="48k">
        <spine>
          <asset-clip name="Scene A" ref="r2" format="r1"
                      offset="0s" start="0s" duration="250/25s"/>
        </spine>
      </sequence>
    </project>
  </event>
</fcpxml>
```

Do not add invented `uid` or stale `modDate` attributes to a new Event or
Project. Final Cut Pro manages those values. A user-supplied Library location
is optional and must never be used as permission to edit a `.fcpbundle`.

## Formats and assets

Define the actual frame duration rather than relying on a display name:

```xml
<!-- True 24 fps -->
<format id="r1" frameDuration="1/24s"
        width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>

<!-- NTSC-compatible 29.97 fps -->
<format id="r2" frameDuration="1001/30000s"
        width="3840" height="2160" colorSpace="1-1-1 (Rec. 709)"/>

<!-- True 30 fps; this is not 29.97 fps -->
<format id="r3" frameDuration="1/30s"
        width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>
```

For current FCPXML versions, place the original-media URL in `media-rep`:

```xml
<asset id="r10" name="Interview" start="0s" duration="1500/25s"
       hasVideo="1" hasAudio="1" format="r1"
       audioSources="1" audioChannels="2" audioRate="48000">
  <media-rep kind="original-media"
             src="file:///Volumes/Editorial/Interview.mov"/>
</asset>
```

Do not copy an old example's direct `asset/@src` into a newer document. Apple
documents that form for FCPXML 1.8 and earlier; use the matching DTD to select
the representation for the target version. Percent-encode file URLs and check
decoded local paths for readability.

## Place clips on a timeline

Use `offset` for placement in parent time, `start` for the source/local in-point,
and `duration` for the scheduled extent:

```xml
<spine>
  <asset-clip name="Opening" ref="r10"
              offset="0s" start="50/25s" duration="125/25s"/>
  <asset-clip name="Cutaway" ref="r11"
              offset="125/25s" start="0s" duration="100/25s"/>
  <asset-clip name="Return" ref="r10"
              offset="225/25s" start="300/25s" duration="75/25s"/>
</spine>
```

The example produces a 12-second primary storyline: 5 seconds, then 4 seconds,
then 3 seconds. Ensure the containing `sequence/@duration` covers the resulting
storyline. Recalculate nested, retimed, synchronized, or multicam timing in its
actual parent/local contexts rather than applying this flat example blindly.

## Insert gaps and transitions

Represent explicit empty primary-storyline time with `gap`:

```xml
<spine>
  <asset-clip ref="r10" offset="0s" start="0s" duration="4s"/>
  <gap name="Pause" offset="4s" duration="2s"/>
  <asset-clip ref="r11" offset="6s" start="0s" duration="4s"/>
</spine>
```

Represent an effect-backed video transition with a resource reference:

Place the `effect` in the document's existing `resources` container and the
`transition` in the applicable `spine`; the two blocks below are fragments, not
a standalone document:

```xml
<resources>
  <!-- Keep other resources here. -->
  <effect id="r20" name="Cross Dissolve"
          uid="REPLACE_WITH_UID_FROM_TARGET_EXPORT"/>
</resources>

<spine>
  <asset-clip ref="r10" offset="0s" start="0s" duration="5s"/>
  <transition name="Cross Dissolve" offset="4s" duration="2s">
    <filter-video ref="r20" name="Cross Dissolve"/>
  </transition>
  <asset-clip ref="r11" offset="4s" start="0s" duration="5s"/>
</spine>
```

Copy the effect UID from a verified export made on the target Final Cut Pro
installation. Validate transition handles and overlap semantically; DTD
validity alone does not prove that the adjacent clips contain enough media.

## Add connected clips

Nest an anchored story element under its base item and use a nonzero lane:

```xml
<asset-clip name="Primary" ref="r10"
            offset="0s" start="0s" duration="10s">
  <asset-clip name="Picture in Picture" ref="r11"
              lane="1" offset="2s" start="0s" duration="3s">
    <adjust-transform position="0 0" scale="0.35 0.35"/>
  </asset-clip>
</asset-clip>
```

Interpret the nested `offset` in the base element's timing context. Positive
video lanes composite above the base. Keep intrinsic adjustments, anchored
items, markers, filters, and metadata in the exact child order declared for
the selected version.

## Add titles and text

Reference a verified title effect, define text, then define the referenced text
style after the `text` element as required by current title child order:

Place the `effect` in `resources` and place the `gap`/`title` fragment in the
applicable `spine`:

```xml
<effect id="r30" name="Basic Title"
        uid="REPLACE_WITH_UID_FROM_TARGET_EXPORT"/>

<gap name="Title Bed" offset="0s" duration="3s">
  <title name="Opening Title" ref="r30"
         lane="1" offset="0s" start="0s" duration="3s">
    <text>
      <text-style ref="tsOpening">Field Notes</text-style>
    </text>
    <text-style-def id="tsOpening">
      <text-style font="Helvetica" fontSize="48"
                  fontColor="1 1 1 1" alignment="center"/>
    </text-style-def>
  </title>
</gap>
```

Keep every text-style ID document-unique. Installed Motion templates can have
published parameters and UIDs that the DTD cannot verify, so copy those values
from a target-environment export instead of inventing them.

## Add markers

Place markers in the annotated element's local time:

```xml
<asset-clip ref="r10" offset="0s" start="0s" duration="10s">
  <marker start="2s" duration="1/25s"
          value="Review framing" note="Editor pass"/>
  <chapter-marker start="6s" duration="1/25s"
                  value="Demonstration" posterOffset="0s"/>
</asset-clip>
```

Use `marker`, `chapter-marker`, rating, keyword, and metadata elements only in
parents and positions allowed by the matching DTD. A one-frame marker duration
must use the applicable frame duration, not a hard-coded `1/24s`.

## Calculate rational time

Calculate time as an exact frame count multiplied by `frameDuration`:

```text
25 fps, 125 frames:
125 × 1/25s = 125/25s = 5s

29.97 fps, 300 frames:
300 × 1001/30000s = 300300/30000s = 1001/100s
```

Reduce fractions with integer arithmetic when convenient. Do not branch on a
floating-point comparison such as `fps == 29.97`; carry the rational frame
duration or an explicit rate identifier.

## Run pre-import checks

Replace a syntax-only and regular-expression checklist with the Skill's
version-aware workflow:

1. Query every uncertain element with `scripts/query-fcpxml-dtd`.
2. Run `scripts/validate-fcpxml <artifact>`.
3. Require semantic and embedded matching-DTD validity.
4. Require the matching target-installation DTD when available.
5. Resolve every resource reference structurally.
6. Decode and check original-media URLs without rewriting them.
7. Confirm sequence format, duration, frame alignment, transition handles,
   lane timing, and target-installed effects or titles.

Do not extract or mutate XML with `grep` or another regular expression. It can
mis-handle bundles, XML escaping, URL encoding, namespaces, and multiline
attributes.

## Import into Final Cut Pro

For a manual handoff, use Final Cut Pro's **File > Import > XML** command and
select the validated `.fcpxml` or `.fcpxmld` artifact. Final Cut Pro creates the
libraries, events, projects, and clips described by the document's top-level
structure.

For an automated handoff, require explicit user intent and run:

```text
scripts/import-fcpxml <artifact.fcpxml|artifact.fcpxmld>
```

The command validates the unchanged artifact first, then sends the flat file
or complete bundle to Final Cut Pro through the documented Open Document Apple
event using `osascript`. Treat `dispatch_accepted` as a handoff, not proof that
Final Cut Pro completed the import or rendered all effects correctly.

## Coverage from the source Skill

| MadAppGang topic | Added here | Safety/version adjustment |
|---|---|---|
| Compatibility table and 1.9 recommendation | Version policy | Select from the artifact and target release; never default globally to 1.9. |
| Basic project and complete template | Minimal project skeleton | Omit invented managed UIDs and require a matching DTD. |
| Format and asset definitions | Formats and assets | Distinguish true 30 from 29.97 and use version-correct `media-rep`. |
| Clip placement, gaps, and transitions | Timeline construction sections | Preserve timing contexts, exact rationals, handles, and verified effect UIDs. |
| Video layers | Connected clips | Explain lane and anchored-time semantics. |
| Titles and text | Titles and text | Add the referenced style definition in DTD child order. |
| Markers | Markers | Use the active format's frame duration. |
| Timing helper | Rational-time calculation | Avoid floating-point rate comparisons. |
| Syntax/path checks and manual import | Pre-import and import sections | Use structural, semantic, matching-DTD validation and explicit import intent. |

Source: [MadAppGang Final Cut Pro Skill](https://github.com/MadAppGang/claude-code/blob/main/plugins/video-editing/skills/final-cut-pro/SKILL.md).
