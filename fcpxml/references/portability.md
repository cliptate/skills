# Portable FCPXML bundle workflow

Build a self-contained `.fcpxmld` when the user needs an FCPXML artifact to
survive a different mount point, username, volume layout, or computer.

## Preconditions

1. Require FCPXML 1.10 or newer; Apple introduced bundle support in DTD 1.10.
2. Require every `media-rep/@src` to resolve to a readable local regular file.
   Report remote URLs as not packageable rather than claiming self-containment.
3. Select an output path in an ignored output directory. Require a new
   `.fcpxmld` path; preserve the Source FCPXML, media, and bundle sidecars.
4. Supply `--dtd` when the target installation's exactly matching DTD is not
   installed locally.

## Build and verify

```text
scripts/package-fcpxmld <source.fcpxml|source.fcpxmld> \
  --output <ignored-output-dir>/<name>-portable.fcpxmld \
  [--dtd <matching.dtd>]
```

The command produces this shape:

```text
name-portable.fcpxmld/
├── Info.fcpxml
└── Media/
    ├── narration.wav
    └── clip.mov
```

It rewrites each packaged representation structurally, for example:

```xml
<media-rep kind="original-media" src="./Media/narration.wav"/>
```

Apple defines a relative `media-rep/@src` against the location of the FCPXML
document. Because bundle `Info.fcpxml` is at the root, `./Media/...` resolves
inside the bundle. The command percent-encodes URL path segments, reuses one
copy for repeated references to the same file, disambiguates filename
collisions, and retains existing bundle sidecars.

Accept the result only when all of these are true:

- `status` is `created`.
- `sourceValidation.valid` and `outputValidation.valid` are both `true`.
- Every media record reports `byteIdentical: true` and a SHA-256 digest.
- The reported `outputArtifact` exists as the complete `.fcpxmld` directory.

Report the output path, media-source and bundled-file counts, media bytes,
bundle bytes, and the validation result. Treat hashes as creation-time
integrity evidence, not protection against later modification.

## Handoff boundaries

Copy, mount, or archive the whole `.fcpxmld` directory while preserving its
internal structure. Copying only `Info.fcpxml` makes its relative URLs point at
missing files. Packaging proves local media presence, byte equality, and the
implemented validation gates; it does not prove that Final Cut Pro completed
an import or that installed effects are available.

Import only when the user separately requests it. If the user explicitly asks
Final Cut Pro to copy packaged media into the target Library, pass
`--copy-assets` to `scripts/import-fcpxml`; treat `dispatch_accepted` as handoff
evidence only.

Authoritative references:

- [Apple `media-rep`](https://developer.apple.com/documentation/professional-video-applications/media-rep)
- [Apple FCPXML Bundle Reference](https://developer.apple.com/documentation/professional-video-applications/fcpxml-bundle-reference)
