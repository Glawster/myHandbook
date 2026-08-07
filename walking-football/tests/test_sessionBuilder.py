"""Integration tests for ODT package rendering."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from scripts.sessionBuilder import sessionBuild
from scripts.sessionModels import Session

_MIMETYPE = b"application/vnd.oasis.opendocument.text"
_CONTENT = b"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
 <office:body><office:text>
  <text:p text:style-name="Title">{{sessionTitle}}</text:p>
  <text:p>{{equipment}}</text:p>
 </office:text></office:body>
</office:document-content>"""


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _session() -> Session:
    return Session(
        sessionNumber=1,
        sessionTitle="Passing",
        theme="Simple Passing",
        keyPhrase="Pass. Move.",
        duration="60 minutes",
        players="8-16",
        equipment=("Balls", "Bibs"),
        objectives=("Pass accurately",),
    )


def _templateCreate(path: Path) -> None:
    with ZipFile(path, "w") as package:
        package.writestr("mimetype", _MIMETYPE, compress_type=ZIP_STORED)
        package.writestr("content.xml", _CONTENT, compress_type=ZIP_DEFLATED)
        package.writestr("styles.xml", b"<styles>unchanged</styles>")
        package.writestr("Pictures/diagram.svg", b"<svg>unchanged</svg>")


def test_sessionBuildPreservesEveryUntouchedMember(tmp_path: Path) -> None:
    template = tmp_path / "template.odt"
    destination = tmp_path / "generated" / "01-passing.odt"
    _templateCreate(template)
    with ZipFile(template) as package:
        expected = {
            name: _digest(package.read(name))
            for name in package.namelist()
            if name != "content.xml"
        }

    result = sessionBuild(template, _session(), destination)

    assert result.destination == destination
    with ZipFile(destination) as package:
        actual = {
            name: _digest(package.read(name))
            for name in package.namelist()
            if name != "content.xml"
        }
        assert package.namelist()[0] == "mimetype"
        assert package.getinfo("mimetype").compress_type == ZIP_STORED
        assert b"Passing" in package.read("content.xml")
    assert actual == expected
