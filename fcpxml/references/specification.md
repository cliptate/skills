# FCPXML specification guide

Use this guide to explain FCPXML concepts and to decide which normative source
to inspect. Query the matching DTD for exact grammar; do not treat this guide as
a replacement for that DTD.

## Contents

- [Source precedence](#source-precedence)
- [Version and representation](#version-and-representation)
- [Document model](#document-model)
- [Resources and references](#resources-and-references)
- [Story and timing model](#story-and-timing-model)
- [Media URLs and formats](#media-urls-and-formats)
- [Safe authoring rules](#safe-authoring-rules)
- [Official reference map](#official-reference-map)

## Source precedence

Use sources in this order:

1. The artifact's `fcpxml/@version` and the exactly matching DTD installed with
   the target Final Cut Pro release or explicitly supplied by the user.
2. Apple's FCPXML reference for element semantics, workflow behavior, and
   examples.
3. A verified export from the target Final Cut Pro release when serializing
   undocumented effect, title, metadata, or application-managed values.
4. Third-party examples, including MadAppGang's Final Cut Pro Skill, only as
   non-normative orientation.

Apple's online DTD article may describe an older version than the target
application. Do not validate a newer document with that older page's DTD. This
Skill uses the installation's matching DTD when available; an example using
1.14 does not make 1.14 correct for every external workflow.

## Version and representation

- A flat interchange document uses the `.fcpxml` extension.
- An FCPXML bundle uses the `.fcpxmld` extension. Resolve its XML document as
  `Info.fcpxml` at the bundle root and preserve all sidecar files.
- Bundle support starts with DTD 1.10. Final Cut Pro normally exports 1.10 and
  later interchange data as bundles, but a tool may still produce a flat
  `.fcpxml` document.
- A `.fcpbundle` is a Final Cut Pro Library. Never inspect or change its
  internal database as though it were FCPXML.
- Use the root `version` value, not the extension or application version, to
  select the DTD. For version `1.14`, the installed filename is commonly
  `FCPXMLv1_14.dtd`.
- Do not downgrade a source document merely for broad compatibility. Features
  and child structures can be version-specific and conversion is semantic,
  not a string replacement.

## Document model

The common project shape is:

```text
fcpxml
├── import-options (optional; ordering is version-defined)
├── resources
└── library, event, project, or other event/story items
    └── project
        └── sequence
            └── spine
                └── story elements
```

Use the matching DTD for the exact allowed top-level alternatives, ordering,
and cardinality. At a conceptual level:

- `resources` defines shared assets, formats, media, effects, and related
  objects used by events and projects.
- `library` groups events; `event` groups clips, projects, and collections.
- `project/sequence/spine` describes the primary project storyline.
- Story elements in positive or negative `lane` values are anchored above or
  below a base story element. Contained items have an implied lane of zero.
- Higher video lanes composite above lower lanes. Audio lane ordering does not
  imply visual compositing.

## Resources and references

- Give every resource a document-local `id` that begins with a letter and is
  unique within the document.
- Resolve every `ref` to a compatible resource in the same document. Existence
  alone is insufficient: a sequence format, clip asset, title effect, and
  transition effect have different semantic roles.
- Preserve the transitive resource closure when copying a story element. This
  includes formats, assets, media, effects, text styles, and referenced nested
  objects.
- Treat `uid` differently from local `id`. Final Cut Pro manages most unique
  identifiers. Do not invent or copy stale application-managed `uid` values
  into newly created events or projects. Asset identifiers have documented
  third-party workflows; follow Apple's asset rules for those cases.
- Follow DTD child order exactly. XML child order is part of the grammar even
  when two elements appear semantically independent.

## Story and timing model

FCPXML expresses time as a rational number of seconds with a 64-bit numerator
and 32-bit denominator. Whole seconds may be reduced, such as `5s`.

```text
24 fps       1/24s
23.976 fps   1001/24000s
25 fps       1/25s
29.97 fps    1001/30000s
50 fps       1/50s
59.94 fps    1001/60000s
```

- `offset` locates an element in parent time, or locates an anchored item in
  the base element's time.
- `start` establishes the element's local timeline or selects its source
  in-point.
- `duration` is the element's extent in parent time.
- Interpret all three through the containing structure, resource timing, and
  `format/@frameDuration`. There is no single global-clock interpretation that
  works for nested storylines, synchronized clips, multicam, retimes, or
  connected clips.
- Align edit boundaries to the applicable frame duration. Apple warns that
  non-frame-aligned timing can cause Final Cut Pro to insert a gap during
  import.
- Use integer rational arithmetic. Do not generate floating-point time strings.

## Media URLs and formats

- Define file-based media with `asset` and one or more `media-rep` elements as
  allowed by the selected DTD version.
- Use valid URL syntax and percent-encode file URLs when serializing. Decode a
  URL only for local existence checks.
- Resolve relative `media-rep/@src` URLs from the directory containing the
  FCPXML document. For a bundle-root `Info.fcpxml`, `./Media/clip.mov` points
  inside that `.fcpxmld`; keep the whole bundle together during handoff.
- Final Cut Pro needs read access to referenced media for an online import.
  Remote authenticated workflows and deliberate offline/proxy workflows are
  exceptions with their own asset semantics.
- Specify the recommended implied asset attributes when media can be offline,
  including video/audio presence and relevant audio-source details.
- Resolve `sequence/@format` to a compatible `format`. Check positive frame
  duration and dimensions for video projects and preserve color-space policy.
- Do not infer format correctness solely from a human-readable format name;
  explicit format attributes can override or qualify it depending on version.

## Safe authoring rules

- Encode the XML as Unicode and emit a root `fcpxml` element with an explicit
  supported version.
- Omit `standalone="yes"`; it can prevent external DTD validation.
- Preserve source artifacts byte-for-byte and write generated or repaired XML
  to a distinct path.
- Parse and serialize structurally. Never edit XML text with regular
  expressions.
- Preserve roles, source time, metadata, audio configuration, and resource
  relationships unless the requested edit deliberately changes them.
- Copy values for installed effects, titles, and published parameters from a
  verified export of the target Final Cut Pro/Motion environment. DTD validity
  cannot prove that a template or effect exists locally.

## Official reference map

- [FCPXML Reference](https://developer.apple.com/documentation/professional-video-applications/fcpxml-reference)
- [Creating FCPXML Documents](https://developer.apple.com/documentation/professional-video-applications/creating-fcpxml-documents)
- [Document Type Definition](https://developer.apple.com/documentation/professional-video-applications/document-type-definition)
- [FCPXML Bundle Reference](https://developer.apple.com/documentation/professional-video-applications/fcpxml-bundle-reference)
- [Story Elements](https://developer.apple.com/documentation/professional-video-applications/story-elements)
- [Timing Attributes](https://developer.apple.com/documentation/professional-video-applications/timing-attributes)
- [Asset](https://developer.apple.com/documentation/professional-video-applications/asset)
- [`media-rep`](https://developer.apple.com/documentation/professional-video-applications/media-rep)
- [Format](https://developer.apple.com/documentation/professional-video-applications/format)
- [Final Cut Pro XML transfer guide](https://support.apple.com/guide/final-cut-pro/use-xml-to-transfer-projects-verdbd66ae/mac)
- [MadAppGang Final Cut Pro Skill](https://github.com/MadAppGang/claude-code/blob/main/plugins/video-editing/skills/final-cut-pro/SKILL.md) — examples only
