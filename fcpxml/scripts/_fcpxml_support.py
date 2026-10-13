from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote, urlsplit


VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")
DTD_VERSION_PATTERN = re.compile(
    r"<!ATTLIST\s+fcpxml\b(?P<body>.*?)>",
    re.DOTALL,
)
DTD_FIXED_VERSION_PATTERN = re.compile(
    r"\bversion\s+CDATA\s+#FIXED\s+[\"'](?P<version>[0-9]+\.[0-9]+)[\"']"
)
STANDALONE_YES_PATTERN = re.compile(
    br"<\?xml\b[^?]*\bstandalone\s*=\s*['\"]yes['\"][^?]*\?>",
    re.IGNORECASE,
)
NEGATIVE_TIME_ATTRIBUTES = ("duration", "offset", "start")
SUPPORTED_FINAL_CUT_TARGETS = (
    (
        "com.apple.FinalCutApp",
        Path("/Applications/Final Cut Pro Creator Studio.app"),
    ),
    ("com.apple.FinalCut", Path("/Applications/Final Cut Pro.app")),
)
OPEN_DOCUMENT_TIMEOUT_SECONDS = 120
PORTABLE_BUNDLE_MINIMUM_VERSION = (1, 10)


class FCPXMLSupportError(Exception):
    pass


class ImportDispatchError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PortablePackageError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PortablePackageValidationError(PortablePackageError):
    def __init__(self, report: ValidationReport) -> None:
        super().__init__(
            "portable_bundle_validation_failed",
            "The staged portable FCPXML bundle did not pass validation",
        )
        self.report = report


@dataclass(frozen=True)
class Artifact:
    artifact_path: Path
    xml_path: Path
    version: str
    standalone_yes: bool
    root: ElementTree.Element


@dataclass(frozen=True)
class ValidationIssue:
    gate: str
    type: str
    message: str
    context: dict[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "gate": self.gate,
            "type": self.type,
            "message": self.message,
            "context": self.context,
        }


@dataclass(frozen=True)
class ValidationReport:
    artifact: Artifact | None
    status: str
    valid: bool
    semantic_valid: bool
    dtd_valid: bool
    errors: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...]
    checks: dict[str, object]

    @property
    def exit_status(self) -> int:
        if self.status == "valid":
            return 0
        if self.status == "invalid":
            return 65
        return 2

    def as_dict(self, command: str = "fcpxml.validate") -> dict[str, object]:
        payload: dict[str, object] = {
            "schemaVersion": 1,
            "command": command,
            "status": self.status,
            "valid": self.valid,
            "semanticValid": self.semantic_valid,
            "dtdValid": self.dtd_valid,
            "errors": [value.as_dict() for value in self.errors],
            "warnings": [value.as_dict() for value in self.warnings],
            "checks": self.checks,
        }
        if self.artifact is not None:
            payload.update(
                {
                    "sourceArtifact": str(self.artifact.artifact_path),
                    "sourceXML": str(self.artifact.xml_path),
                    "fcpxmlVersion": self.artifact.version,
                }
            )
        return payload


@dataclass(frozen=True)
class FinalCutTarget:
    bundle_identifier: str
    application_path: Path | None


@dataclass(frozen=True)
class TargetLibrary:
    path: Path
    location: str
    source: str
    existed: bool


@dataclass(frozen=True)
class PreparedImport:
    source: Artifact
    artifact: Artifact
    target_library: TargetLibrary
    suppress_warnings: bool
    copy_assets: bool | None


@dataclass(frozen=True)
class PackagedMedia:
    source_path: Path
    bundled_path: Path
    source_urls: tuple[str, ...]
    bundled_url: str
    size: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "sourcePath": str(self.source_path),
            "bundledPath": str(self.bundled_path),
            "sourceURLs": list(self.source_urls),
            "bundledURL": self.bundled_url,
            "bytes": self.size,
            "sha256": self.sha256,
            "byteIdentical": True,
        }


@dataclass(frozen=True)
class PortablePackage:
    source: Artifact
    artifact: Artifact
    media: tuple[PackagedMedia, ...]
    validation: ValidationReport
    bundle_size: int


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


def validate_version(version: str) -> str:
    if not VERSION_PATTERN.fullmatch(version):
        raise FCPXMLSupportError(
            f"FCPXML version must use major.minor digits, received {version!r}"
        )
    return version


def resolve_artifact(value: str | Path) -> tuple[Path, Path]:
    candidate = Path(value).expanduser()
    try:
        artifact_path = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise FCPXMLSupportError(f"artifact does not exist: {candidate}") from error

    suffix = artifact_path.suffix.lower()
    if suffix == ".fcpxml" and artifact_path.is_file():
        return artifact_path, artifact_path
    if suffix == ".fcpxmld" and artifact_path.is_dir():
        xml_path = artifact_path / "Info.fcpxml"
        if not xml_path.is_file():
            raise FCPXMLSupportError(
                f"FCPXML bundle is missing root Info.fcpxml: {artifact_path}"
            )
        return artifact_path, xml_path.resolve(strict=True)
    if suffix == ".fcpbundle":
        raise FCPXMLSupportError(
            ".fcpbundle is a Final Cut Pro Library, not an FCPXML artifact"
        )
    raise FCPXMLSupportError(
        "input must be a flat .fcpxml file or a .fcpxmld bundle"
    )


def inspect_artifact(value: str | Path) -> Artifact:
    artifact_path, xml_path = resolve_artifact(value)
    try:
        data = xml_path.read_bytes()
    except OSError as error:
        raise FCPXMLSupportError(f"cannot read XML document: {xml_path}") from error

    standalone_yes = STANDALONE_YES_PATTERN.search(data) is not None
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise FCPXMLSupportError(f"XML is not well formed: {error}") from error

    if root.tag != "fcpxml":
        raise FCPXMLSupportError(
            f"root element must be fcpxml, received {root.tag!r}"
        )
    version = root.attrib.get("version")
    if version is None:
        raise FCPXMLSupportError("fcpxml root is missing the version attribute")
    validate_version(version)
    return Artifact(
        artifact_path=artifact_path,
        xml_path=xml_path,
        version=version,
        standalone_yes=standalone_yes,
        root=root,
    )


def resolve_local_media_path(artifact: Artifact, source: str) -> Path | None:
    parsed = urlsplit(source)
    scheme = parsed.scheme.lower()
    if scheme == "file":
        decoded_path = unquote(parsed.path)
        if parsed.netloc and parsed.netloc != "localhost":
            decoded_path = f"//{parsed.netloc}{decoded_path}"
        candidate = Path(decoded_path)
        if not candidate.is_absolute():
            return None
    elif not scheme and not parsed.netloc:
        candidate = Path(unquote(parsed.path))
        if not candidate.is_absolute():
            candidate = artifact.xml_path.parent / candidate
    else:
        return None
    return candidate.resolve(strict=False)


def installed_dtd_candidates(version: str) -> list[Path]:
    validate_version(version)
    filename = f"FCPXMLv{version.replace('.', '_')}.dtd"
    relative = Path(
        "Contents/Frameworks/Interchange.framework/Versions/A/Resources"
    ) / filename
    return [application / relative for _, application in SUPPORTED_FINAL_CUT_TARGETS]


def declared_dtd_version(dtd_path: Path) -> str:
    try:
        text = dtd_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise FCPXMLSupportError(f"cannot read DTD: {dtd_path}") from error
    for declaration in DTD_VERSION_PATTERN.finditer(text):
        match = DTD_FIXED_VERSION_PATTERN.search(declaration.group("body"))
        if match is not None:
            return validate_version(match.group("version"))
    raise FCPXMLSupportError(
        f"cannot determine fixed fcpxml version from DTD: {dtd_path}"
    )


def resolve_matching_dtd(
    version: str,
    explicit_path: str | Path | None = None,
) -> tuple[Path | None, str]:
    validate_version(version)
    if explicit_path is not None:
        candidate = Path(explicit_path).expanduser()
        try:
            dtd_path = candidate.resolve(strict=True)
        except FileNotFoundError as error:
            raise FCPXMLSupportError(f"DTD does not exist: {candidate}") from error
        if not dtd_path.is_file():
            raise FCPXMLSupportError(f"DTD is not a file: {dtd_path}")
        source = "explicit"
    else:
        dtd_path = next(
            (path.resolve() for path in installed_dtd_candidates(version) if path.is_file()),
            None,
        )
        if dtd_path is None:
            return None, "unavailable"
        source = "final-cut-pro-installation"

    dtd_version = declared_dtd_version(dtd_path)
    if dtd_version != version:
        raise FCPXMLSupportError(
            f"DTD version {dtd_version} does not match FCPXML version {version}"
        )
    return dtd_path, source


def _semantic_issues(
    artifact: Artifact,
) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    root = artifact.root

    if artifact.standalone_yes:
        errors.append(
            ValidationIssue(
                gate="document",
                type="standalone_declaration",
                message='XML declaration must not use standalone="yes"',
                context={},
            )
        )

    if not any(child.tag == "resources" for child in root):
        errors.append(
            ValidationIssue(
                gate="semantic",
                type="missing_required_element",
                message="Missing 'resources' element",
                context={},
            )
        )

    identifiers = {
        identifier
        for element in root.iter()
        if (identifier := element.attrib.get("id"))
    }
    for element in root.iter():
        reference = element.attrib.get("ref")
        if reference and reference not in identifiers:
            errors.append(
                ValidationIssue(
                    gate="semantic",
                    type="missing_asset_reference",
                    message=f"Reference '{reference}' does not match any resource id",
                    context={"ref": reference, "element": element.tag},
                )
            )

        for attribute in NEGATIVE_TIME_ATTRIBUTES:
            value = element.attrib.get(attribute)
            if value is not None and value.strip().startswith("-"):
                warnings.append(
                    ValidationIssue(
                        gate="semantic",
                        type="negative_time_attribute",
                        message=(
                            f"Element '{element.tag}' has negative {attribute}: {value}"
                        ),
                        context={"element": element.tag, "attribute": attribute},
                    )
                )

        if element.tag != "media-rep":
            continue
        if element.attrib.get("kind") != "original-media":
            continue
        source = element.attrib.get("src")
        if not source:
            continue
        decoded_path = resolve_local_media_path(artifact, source)
        if decoded_path is None:
            continue
        if not os.path.exists(decoded_path):
            errors.append(
                ValidationIssue(
                    gate="media",
                    type="missing_original_media",
                    message=(
                        "Original media does not exist at the referenced local URL"
                    ),
                    context={"src": source, "path": str(decoded_path)},
                )
            )

    return errors, warnings


def _run_dtd_validation(
    artifact: Artifact,
    dtd_path: Path,
    dtd_source: str,
    xmllint: str,
    runner: ProcessRunner,
) -> tuple[bool, dict[str, object], ValidationIssue | None]:
    result = runner(
        [
            xmllint,
            "--nonet",
            "--noout",
            "--dtdvalid",
            dtd_path.as_uri(),
            str(artifact.xml_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    diagnostics = result.stderr.strip()
    check: dict[str, object] = {
        "status": "passed" if result.returncode == 0 else "failed",
        "tool": xmllint,
        "dtd": str(dtd_path),
        "dtdSource": dtd_source,
        "exitStatus": result.returncode,
        "diagnostics": diagnostics,
    }
    if result.returncode == 0:
        return True, check, None
    return (
        False,
        check,
        ValidationIssue(
            gate="dtd",
            type="dtd_validation",
            message=diagnostics or "xmllint rejected the matching FCPXML DTD",
            context={"dtd": str(dtd_path)},
        ),
    )


def validate_artifact(
    value: str | Path,
    explicit_dtd: str | Path | None = None,
    *,
    xmllint: str | None = None,
    runner: ProcessRunner = subprocess.run,
) -> ValidationReport:
    try:
        artifact = inspect_artifact(value)
    except FCPXMLSupportError as error:
        issue = ValidationIssue(
            gate="artifact",
            type="invalid_artifact",
            message=str(error),
            context={},
        )
        return ValidationReport(
            artifact=None,
            status="invalid",
            valid=False,
            semantic_valid=False,
            dtd_valid=False,
            errors=(issue,),
            warnings=(),
            checks={"artifact": {"status": "failed"}},
        )

    errors, warnings = _semantic_issues(artifact)
    checks: dict[str, object] = {
        "artifact": {"status": "passed"},
        "syntax": {"status": "passed", "tool": "python-elementtree"},
        "semantic": {"status": "passed" if not errors else "failed"},
    }
    semantic_valid = not errors
    dtd_valid = False
    validation_incomplete = False

    try:
        dtd_path, dtd_source = resolve_matching_dtd(
            artifact.version,
            explicit_dtd,
        )
    except FCPXMLSupportError as error:
        validation_incomplete = True
        errors.append(
            ValidationIssue(
                gate="dtd",
                type="dtd_selection_failed",
                message=str(error),
                context={},
            )
        )
        checks["dtd"] = {"status": "unavailable"}
        dtd_path = None
        dtd_source = "unavailable"

    selected_xmllint = xmllint or shutil.which("xmllint")
    if dtd_path is None and "dtd" not in checks:
        validation_incomplete = True
        checks["dtd"] = {
            "status": "unavailable",
            "dtdSource": dtd_source,
        }
        errors.append(
            ValidationIssue(
                gate="dtd",
                type="matching_dtd_unavailable",
                message=(
                    "No matching DTD was found inside Final Cut Pro; pass --dtd."
                ),
                context={"version": artifact.version},
            )
        )
    elif dtd_path is not None and selected_xmllint is None:
        validation_incomplete = True
        checks["dtd"] = {
            "status": "unavailable",
            "dtd": str(dtd_path),
            "dtdSource": dtd_source,
        }
        errors.append(
            ValidationIssue(
                gate="dtd",
                type="xmllint_unavailable",
                message="xmllint is required for matching-DTD validation",
                context={"dtd": str(dtd_path)},
            )
        )
    elif dtd_path is not None and selected_xmllint is not None:
        dtd_valid, dtd_check, dtd_issue = _run_dtd_validation(
            artifact,
            dtd_path,
            dtd_source,
            selected_xmllint,
            runner,
        )
        checks["dtd"] = dtd_check
        if dtd_issue is not None:
            errors.append(dtd_issue)

    has_validation_failure = any(
        value.type
        not in {
            "dtd_selection_failed",
            "matching_dtd_unavailable",
            "xmllint_unavailable",
        }
        for value in errors
    )
    valid = semantic_valid and dtd_valid and not errors
    if valid:
        status = "valid"
    elif has_validation_failure:
        status = "invalid"
    elif validation_incomplete:
        status = "incomplete"
    else:
        status = "invalid"

    return ValidationReport(
        artifact=artifact,
        status=status,
        valid=valid,
        semantic_valid=semantic_valid,
        dtd_valid=dtd_valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        checks=checks,
    )


def _portable_output_path(artifact: Artifact, output_path: str | Path) -> Path:
    candidate = Path(output_path).expanduser().resolve(strict=False)
    if candidate.suffix.lower() != ".fcpxmld":
        raise PortablePackageError(
            "invalid_output_path",
            "Portable output must use the .fcpxmld extension",
        )
    if not candidate.parent.is_dir():
        raise PortablePackageError(
            "invalid_output_path",
            f"Portable output parent directory does not exist: {candidate.parent}",
        )
    if candidate.exists() or candidate.is_symlink():
        raise PortablePackageError(
            "output_exists",
            f"Portable output already exists: {candidate}",
        )
    if artifact.artifact_path == candidate or artifact.artifact_path in candidate.parents:
        raise PortablePackageError(
            "invalid_output_path",
            "Portable output must be separate from and outside the Source artifact",
        )
    return candidate


def _portable_version_supported(version: str) -> bool:
    major, minor = (int(value) for value in validate_version(version).split("."))
    return (major, minor) >= PORTABLE_BUNDLE_MINIMUM_VERSION


def _required_media_source(artifact: Artifact, source: str) -> Path:
    parsed = urlsplit(source)
    if parsed.query or parsed.fragment:
        raise PortablePackageError(
            "unsupported_media_url",
            f"Cannot package a media URL with a query or fragment: {source}",
        )
    path = resolve_local_media_path(artifact, source)
    if path is None:
        raise PortablePackageError(
            "unsupported_media_url",
            f"Cannot make non-local media self-contained: {source}",
        )
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise PortablePackageError(
            "missing_media",
            f"Referenced media does not exist: {path}",
        ) from error
    if not resolved.is_file():
        raise PortablePackageError(
            "invalid_media",
            f"Referenced media is not a regular file: {resolved}",
        )
    if not os.access(resolved, os.R_OK):
        raise PortablePackageError(
            "unreadable_media",
            f"Referenced media is not readable: {resolved}",
        )
    return resolved


def _file_sha256(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise PortablePackageError(
            "media_read_failed",
            f"Could not read media for integrity verification: {path}",
        ) from error
    return digest.hexdigest()


def _media_destination(
    media_directory: Path,
    source: Path,
    source_digest: str,
) -> tuple[Path, bool]:
    suffix = source.suffix
    stem = source.name[: -len(suffix)] if suffix else source.name
    index = 1
    while True:
        name = source.name if index == 1 else f"{stem}-{index}{suffix}"
        candidate = media_directory / name
        if not candidate.exists() and not candidate.is_symlink():
            return candidate, False
        if (
            candidate.is_file()
            and not candidate.is_symlink()
            and _file_sha256(candidate) == source_digest
        ):
            return candidate, True
        index += 1


def _write_portable_xml(
    artifact: Artifact,
    output_xml: Path,
    media_directory: Path,
) -> tuple[PackagedMedia, ...]:
    parser = ElementTree.XMLParser(
        target=ElementTree.TreeBuilder(insert_comments=True, insert_pis=True)
    )
    try:
        root = ElementTree.fromstring(artifact.xml_path.read_bytes(), parser=parser)
    except (OSError, ElementTree.ParseError) as error:
        raise PortablePackageError(
            "source_read_failed",
            f"Could not parse Source artifact for portable packaging: {error}",
        ) from error

    records: dict[Path, dict[str, object]] = {}
    for element in root.iter("media-rep"):
        source_url = element.attrib.get("src")
        if not source_url:
            continue
        source_path = _required_media_source(artifact, source_url)
        existing = records.get(source_path)
        if existing is None:
            digest = _file_sha256(source_path)
            destination, reused = _media_destination(
                media_directory,
                source_path,
                digest,
            )
            if not reused:
                try:
                    shutil.copy2(source_path, destination)
                except OSError as error:
                    raise PortablePackageError(
                        "media_copy_failed",
                        f"Could not copy media into portable bundle: {source_path}",
                    ) from error
            if _file_sha256(destination) != digest:
                raise PortablePackageError(
                    "media_integrity_failed",
                    f"Bundled media differs from its Source file: {source_path}",
                )
            relative_url = f"./Media/{quote(destination.name, safe='-._~')}"
            existing = {
                "source_path": source_path,
                "bundled_path": destination,
                "source_urls": [],
                "bundled_url": relative_url,
                "size": source_path.stat().st_size,
                "sha256": digest,
            }
            records[source_path] = existing
        source_urls = existing["source_urls"]
        assert isinstance(source_urls, list)
        source_urls.append(source_url)
        bundled_url = existing["bundled_url"]
        assert isinstance(bundled_url, str)
        element.set("src", bundled_url)

    ElementTree.indent(root, space="  ")
    body = ElementTree.tostring(root, encoding="utf-8", short_empty_elements=True)
    payload = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b"<!DOCTYPE fcpxml>\n"
        + body
        + b"\n"
    )
    try:
        output_xml.write_bytes(payload)
    except OSError as error:
        raise PortablePackageError(
            "portable_xml_write_failed",
            f"Could not write portable Info.fcpxml: {output_xml}",
        ) from error

    return tuple(
        PackagedMedia(
            source_path=value["source_path"],
            bundled_path=value["bundled_path"],
            source_urls=tuple(value["source_urls"]),
            bundled_url=value["bundled_url"],
            size=value["size"],
            sha256=value["sha256"],
        )
        for value in records.values()
    )


def _bundle_size(path: Path) -> int:
    return sum(
        child.stat().st_size
        for child in path.rglob("*")
        if child.is_file() and not child.is_symlink()
    )


def create_portable_bundle(
    artifact: Artifact,
    output_path: str | Path,
    explicit_dtd: str | Path | None = None,
) -> PortablePackage:
    if not _portable_version_supported(artifact.version):
        raise PortablePackageError(
            "unsupported_bundle_version",
            "Self-contained .fcpxmld packaging requires FCPXML 1.10 or newer",
        )
    destination = _portable_output_path(artifact, output_path)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.stem}-",
            dir=destination.parent,
        )
    )
    staged_bundle = temporary / destination.name
    published = False
    try:
        if artifact.artifact_path.suffix.lower() == ".fcpxmld":
            shutil.copytree(artifact.artifact_path, staged_bundle, symlinks=True)
        else:
            staged_bundle.mkdir()
        staged_xml = staged_bundle / "Info.fcpxml"
        media_directory = staged_bundle / "Media"
        if media_directory.is_symlink():
            raise PortablePackageError(
                "invalid_media_directory",
                "Portable bundle Media directory must not be a symbolic link",
            )
        media_directory.mkdir(exist_ok=True)
        if not media_directory.is_dir():
            raise PortablePackageError(
                "invalid_media_directory",
                f"Portable bundle Media path is not a directory: {media_directory}",
            )

        staged_media = _write_portable_xml(
            artifact,
            staged_xml,
            media_directory,
        )
        staged_validation = validate_artifact(staged_bundle, explicit_dtd)
        if not staged_validation.valid:
            raise PortablePackageValidationError(staged_validation)
        if destination.exists() or destination.is_symlink():
            raise PortablePackageError(
                "output_exists",
                f"Portable output already exists: {destination}",
            )
        staged_bundle.rename(destination)
        published = True

        final_artifact = inspect_artifact(destination)
        final_validation = replace(staged_validation, artifact=final_artifact)
        final_media = tuple(
            replace(
                value,
                bundled_path=destination
                / value.bundled_path.relative_to(staged_bundle),
            )
            for value in staged_media
        )
        for value in final_media:
            if (
                _file_sha256(value.source_path) != value.sha256
                or _file_sha256(value.bundled_path) != value.sha256
            ):
                raise PortablePackageError(
                    "media_integrity_failed",
                    f"Published media differs from its Source file: {value.bundled_path}",
                )
        return PortablePackage(
            source=artifact,
            artifact=final_artifact,
            media=final_media,
            validation=final_validation,
            bundle_size=_bundle_size(destination),
        )
    except PortablePackageError:
        if published and destination.is_dir():
            shutil.rmtree(destination)
        raise
    except (FCPXMLSupportError, OSError) as error:
        if published and destination.is_dir():
            shutil.rmtree(destination)
        raise PortablePackageError(
            "portable_package_failed",
            f"Could not create portable FCPXML bundle: {error}",
        ) from error
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def _local_path_from_library_location(value: str) -> Path:
    parsed = urlsplit(value)
    if parsed.scheme:
        if parsed.scheme.lower() != "file":
            raise ImportDispatchError(
                "invalid_target_library",
                "Target Library location must be a local path or file URL",
            )
        if parsed.netloc not in {"", "localhost"}:
            raise ImportDispatchError(
                "invalid_target_library",
                "Target Library file URL must refer to the local Mac",
            )
        if parsed.query or parsed.fragment:
            raise ImportDispatchError(
                "invalid_target_library",
                "Target Library file URL must not contain a query or fragment",
            )
        return Path(unquote(parsed.path))
    return Path(value).expanduser()


def _resolve_explicit_target_library(value: str) -> TargetLibrary:
    candidate = _local_path_from_library_location(value)
    if candidate.suffix.lower() != ".fcpbundle":
        candidate = candidate.with_suffix(".fcpbundle")
    path = candidate.resolve(strict=False)
    if not path.parent.is_dir():
        raise ImportDispatchError(
            "invalid_target_library",
            f"Target Library parent directory does not exist: {path.parent}",
        )
    if path.exists() and not path.is_dir():
        raise ImportDispatchError(
            "invalid_target_library",
            f"Target Library path exists but is not a directory: {path}",
        )
    return TargetLibrary(
        path=path,
        location=path.as_uri(),
        source="explicit",
        existed=path.exists(),
    )


def _resolve_exported_target_library(artifact: Artifact) -> TargetLibrary:
    library = artifact.root.find("./library")
    exported_location = library.attrib.get("location") if library is not None else None
    if not exported_location:
        raise ImportDispatchError(
            "target_library_required",
            (
                "Zero-click import requires --library-location because the "
                "FCPXML does not contain an exported Library location"
            ),
        )
    path = _local_path_from_library_location(exported_location).resolve(strict=False)
    if path.suffix.lower() != ".fcpbundle" or not path.is_dir():
        raise ImportDispatchError(
            "target_library_required",
            (
                "The exported Library location is not an existing .fcpbundle; "
                "pass --library-location explicitly"
            ),
        )
    return TargetLibrary(
        path=path,
        location=path.as_uri(),
        source="exported-library",
        existed=True,
    )


def resolve_target_library(
    artifact: Artifact,
    explicit_location: str | None = None,
) -> TargetLibrary:
    if explicit_location is not None:
        return _resolve_explicit_target_library(explicit_location)
    return _resolve_exported_target_library(artifact)


def _resolve_import_copy_path(
    artifact: Artifact,
    output_path: str | Path | None,
) -> Path:
    expected_suffix = artifact.artifact_path.suffix.lower()
    if output_path is None:
        temporary = Path(tempfile.mkdtemp(prefix="fcpxml-import-"))
        return temporary / artifact.artifact_path.name

    path = Path(output_path).expanduser().resolve(strict=False)
    if path.suffix.lower() != expected_suffix:
        raise ImportDispatchError(
            "invalid_import_copy_path",
            f"Import-ready artifact must use the {expected_suffix} extension",
        )
    if not path.parent.is_dir():
        raise ImportDispatchError(
            "invalid_import_copy_path",
            f"Import-ready artifact parent directory does not exist: {path.parent}",
        )
    if path.exists():
        raise ImportDispatchError(
            "import_copy_exists",
            f"Import-ready artifact already exists: {path}",
        )
    if path == artifact.artifact_path or artifact.artifact_path in path.parents:
        raise ImportDispatchError(
            "invalid_import_copy_path",
            "Import-ready artifact must be separate from the Source artifact",
        )
    return path


def _write_import_ready_xml(
    source_xml: Path,
    output_xml: Path,
    target_library: TargetLibrary,
    suppress_warnings: bool,
    copy_assets: bool | None,
) -> None:
    parser = ElementTree.XMLParser(
        target=ElementTree.TreeBuilder(insert_comments=True, insert_pis=True)
    )
    try:
        root = ElementTree.fromstring(source_xml.read_bytes(), parser=parser)
    except (OSError, ElementTree.ParseError) as error:
        raise ImportDispatchError(
            "import_copy_failed",
            f"Could not parse Source artifact for import preparation: {error}",
        ) from error

    for element in list(root):
        if element.tag == "import-options":
            root.remove(element)

    options = ElementTree.Element("import-options")
    ElementTree.SubElement(
        options,
        "option",
        key="library location",
        value=target_library.location,
    )
    ElementTree.SubElement(
        options,
        "option",
        key="suppress warnings",
        value="1" if suppress_warnings else "0",
    )
    if copy_assets is not None:
        ElementTree.SubElement(
            options,
            "option",
            key="copy assets",
            value="1" if copy_assets else "0",
        )
    root.insert(0, options)
    ElementTree.indent(root, space="  ")
    body = ElementTree.tostring(root, encoding="utf-8", short_empty_elements=True)
    payload = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b"<!DOCTYPE fcpxml>\n"
        + body
        + b"\n"
    )
    try:
        output_xml.write_bytes(payload)
    except OSError as error:
        raise ImportDispatchError(
            "import_copy_failed",
            f"Could not write Import-ready artifact: {error}",
        ) from error


def prepare_import_artifact(
    artifact: Artifact,
    target_library: TargetLibrary,
    *,
    suppress_warnings: bool = True,
    copy_assets: bool | None = None,
    output_path: str | Path | None = None,
) -> PreparedImport:
    destination = _resolve_import_copy_path(artifact, output_path)
    try:
        if artifact.artifact_path.suffix.lower() == ".fcpxmld":
            shutil.copytree(artifact.artifact_path, destination, symlinks=True)
            output_xml = destination / "Info.fcpxml"
        else:
            destination.parent.mkdir(parents=False, exist_ok=True)
            output_xml = destination
        _write_import_ready_xml(
            artifact.xml_path,
            output_xml,
            target_library,
            suppress_warnings,
            copy_assets,
        )
        prepared_artifact = inspect_artifact(destination)
    except ImportDispatchError:
        raise
    except (OSError, FCPXMLSupportError) as error:
        raise ImportDispatchError(
            "import_copy_failed",
            f"Could not prepare Import-ready artifact: {error}",
        ) from error
    return PreparedImport(
        source=artifact,
        artifact=prepared_artifact,
        target_library=target_library,
        suppress_warnings=suppress_warnings,
        copy_assets=copy_assets,
    )


def resolve_final_cut_target(
    explicit_bundle_identifier: str | None = None,
) -> FinalCutTarget:
    known = dict(SUPPORTED_FINAL_CUT_TARGETS)
    if explicit_bundle_identifier is not None:
        if explicit_bundle_identifier not in known:
            supported = ", ".join(known)
            raise ImportDispatchError(
                "unsupported_final_cut_application",
                f"unsupported Final Cut Pro bundle identifier; use one of: {supported}",
            )
        path = known[explicit_bundle_identifier]
        return FinalCutTarget(
            bundle_identifier=explicit_bundle_identifier,
            application_path=path if path.exists() else None,
        )

    for bundle_identifier, path in SUPPORTED_FINAL_CUT_TARGETS:
        if path.exists():
            return FinalCutTarget(bundle_identifier, path)
    raise ImportDispatchError(
        "final_cut_not_installed",
        "No supported Final Cut Pro application was found in /Applications",
    )


def dispatch_to_final_cut(
    artifact: Artifact,
    target: FinalCutTarget,
    *,
    osascript: str = "/usr/bin/osascript",
    timeout_seconds: int = OPEN_DOCUMENT_TIMEOUT_SECONDS,
    runner: ProcessRunner = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    if not Path(osascript).is_file() or not os.access(osascript, os.X_OK):
        raise ImportDispatchError(
            "osascript_unavailable",
            f"macOS osascript command is unavailable: {osascript}",
        )
    script = "\n".join(
        [
            "on run argv",
            f'    tell application id "{target.bundle_identifier}"',
            "        activate",
            "        open POSIX file (item 1 of argv)",
            "    end tell",
            "end run",
        ]
    )
    try:
        result = runner(
            [
                osascript,
                "-e",
                script,
                "--",
                str(artifact.artifact_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise ImportDispatchError(
            "import_dispatch_timeout",
            (
                "Final Cut Pro did not return from the Open Document Apple event "
                f"within {timeout_seconds} seconds"
            ),
        ) from error
    except OSError as error:
        raise ImportDispatchError(
            "osascript_execution_failed",
            f"could not execute macOS osascript: {error}",
        ) from error
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip()
        normalized_diagnostic = diagnostic.lower()
        if (
            "-1743" in diagnostic
            or "not authorized" in normalized_diagnostic
            or "not allowed" in normalized_diagnostic
        ):
            raise ImportDispatchError(
                "automation_permission_denied",
                (
                    "Automation permission is required to control Final Cut Pro; "
                    "enable the invoking terminal or Codex under System Settings > "
                    "Privacy & Security > Automation"
                ),
            )
        raise ImportDispatchError(
            "import_dispatch_failed",
            diagnostic or "Final Cut Pro rejected the Open Document Apple event",
        )
    return result
