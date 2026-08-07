"""ODT package rendering with byte preservation for untouched members."""

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZIP_STORED, ZipFile, ZipInfo

from scripts.builderErrors import SessionTemplateError
from scripts.placeholderRenderer import placeholdersRender
from scripts.sessionModels import Session

_MIMETYPE = b"application/vnd.oasis.opendocument.text"


@dataclass(frozen=True)
class BuildResult:
    """Description of one successfully rendered output."""

    destination: Path
    preservedMembers: int


## build


def sessionBuild(template: Path, session: Session, destination: Path) -> BuildResult:
    """Render one session into a new ODT using an existing template package."""
    _pathsValidate(template, destination)
    try:
        with ZipFile(template, "r") as source:
            _templateValidate(source)
            contentXml = placeholdersRender(
                source.read("content.xml"), session.placeholdersBuild()
            )
            members = source.infolist()
            payloads = {member.filename: source.read(member.filename) for member in members}
    except BadZipFile as error:
        message = f"template is not a valid ODT ZIP package: {template}"
        raise SessionTemplateError(message) from error

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporaryPathCreate(destination)
    try:
        _packageWrite(temporary, members, payloads, contentXml)
        _outputValidate(temporary, payloads)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return BuildResult(destination=destination, preservedMembers=len(members) - 1)


## package


def _outputValidate(path: Path, sourcePayloads: dict[str, bytes]) -> None:
    try:
        with ZipFile(path, "r") as output:
            if output.testzip() is not None:
                raise SessionTemplateError("generated ODT contains a corrupt archive member")
            for name, payload in sourcePayloads.items():
                if name == "content.xml":
                    continue
                if _digest(output.read(name)) != _digest(payload):
                    raise SessionTemplateError(f"generated ODT changed preserved member: {name}")
    except BadZipFile as error:
        raise SessionTemplateError("generated document is not a valid ZIP package") from error


def _packageWrite(
    path: Path,
    members: list[ZipInfo],
    payloads: dict[str, bytes],
    contentXml: bytes,
) -> None:
    with ZipFile(path, "w") as output:
        for member in members:
            payload = contentXml if member.filename == "content.xml" else payloads[member.filename]
            output.writestr(member, payload)


def _templateValidate(source: ZipFile) -> None:
    names = source.namelist()
    if not names or names[0] != "mimetype":
        raise SessionTemplateError("template mimetype must be the first archive member")
    mimetypeInfo = source.getinfo("mimetype")
    if mimetypeInfo.compress_type != ZIP_STORED or source.read("mimetype") != _MIMETYPE:
        raise SessionTemplateError("template has an invalid or compressed ODT mimetype")
    if "content.xml" not in names:
        raise SessionTemplateError("template does not contain content.xml")


## paths


def _pathsValidate(template: Path, destination: Path) -> None:
    if not template.is_file() or template.suffix.lower() != ".odt":
        raise SessionTemplateError(f"template must be an existing .odt file: {template}")
    if destination.suffix.lower() != ".odt":
        raise SessionTemplateError(f"destination must use the .odt extension: {destination}")
    if template.resolve() == destination.resolve():
        raise SessionTemplateError("template and destination must be different files")


def _temporaryPathCreate(destination: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{destination.stem}-", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    return Path(name)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
