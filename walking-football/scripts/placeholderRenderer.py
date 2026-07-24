"""Targeted placeholder replacement for OpenDocument content XML."""

import re
from dataclasses import dataclass
from typing import Literal

from lxml import etree

from scripts.builderErrors import SessionTemplateError

TEXT_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_CONTAINER_XPATH = "//text:p | //text:h"
_PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Za-z][A-Za-z0-9]*)\}\}")


@dataclass(frozen=True)
class _TextSlot:
    owner: etree._Element
    attribute: Literal["text", "tail"]

    def valueGet(self) -> str:
        """Return the current text held by this XML slot."""
        return getattr(self.owner, self.attribute) or ""

    def valueSet(self, value: str) -> None:
        """Replace the current text held by this XML slot."""
        setattr(self.owner, self.attribute, value)


@dataclass(frozen=True)
class _Character:
    slot: _TextSlot
    offset: int


## rendering


def placeholdersFind(contentXml: bytes) -> set[str]:
    """Return all syntactically valid placeholder names in content XML."""
    tree = _xmlParse(contentXml)
    return {
        match.group(1)
        for container in _containersGet(tree)
        for match in _PLACEHOLDER_PATTERN.finditer(_containerTextGet(container))
    }


def placeholdersRender(contentXml: bytes, values: dict[str, str]) -> bytes:
    """Replace placeholders without rebuilding surrounding ODF structures."""
    tree = _xmlParse(contentXml)
    found: set[str] = set()

    for container in _containersGet(tree):
        found.update(_containerRender(container, values))

    unresolved = placeholdersFind(_xmlSerialise(tree))
    if unresolved:
        raise SessionTemplateError(
            f"unresolved template placeholders: {', '.join(sorted(unresolved))}"
        )
    if not found:
        raise SessionTemplateError("template contains no placeholders")
    return _xmlSerialise(tree)


## containers


def _containerRender(container: etree._Element, values: dict[str, str]) -> set[str]:
    text, characters = _containerMapBuild(container)
    matches = list(_PLACEHOLDER_PATTERN.finditer(text))
    found = {match.group(1) for match in matches}
    unknown = sorted(found - set(values))
    if unknown:
        raise SessionTemplateError(f"unknown template placeholders: {', '.join(unknown)}")

    for match in reversed(matches):
        _matchReplace(characters, match.start(), match.end(), values[match.group(1)])
    return found


def _containersGet(tree: etree._ElementTree) -> list[etree._Element]:
    return tree.xpath(_CONTAINER_XPATH, namespaces={"text": TEXT_NAMESPACE})


def _containerMapBuild(container: etree._Element) -> tuple[str, list[_Character]]:
    characters: list[_Character] = []
    textParts: list[str] = []
    for slot in _slotsGet(container):
        value = slot.valueGet()
        textParts.append(value)
        characters.extend(_Character(slot, offset) for offset in range(len(value)))
    return "".join(textParts), characters


def _containerTextGet(container: etree._Element) -> str:
    return "".join(slot.valueGet() for slot in _slotsGet(container))


def _slotsGet(container: etree._Element) -> list[_TextSlot]:
    slots: list[_TextSlot] = []
    for element in container.iter():
        if element.text:
            slots.append(_TextSlot(element, "text"))
        if element is not container and element.tail:
            slots.append(_TextSlot(element, "tail"))
    return slots


## replacement


def _matchReplace(
    characters: list[_Character], start: int, end: int, replacement: str
) -> None:
    affected = characters[start:end]
    if not affected:
        return
    first = affected[0]
    bySlot: dict[_TextSlot, list[int]] = {}
    for character in affected:
        bySlot.setdefault(character.slot, []).append(character.offset)

    for slot, offsets in bySlot.items():
        value = slot.valueGet()
        before = value[: min(offsets)]
        after = value[max(offsets) + 1 :]
        slot.valueSet(before + (replacement if slot == first.slot else "") + after)

    _lineBreaksMaterialise(first.slot)


def _lineBreaksMaterialise(slot: _TextSlot) -> None:
    value = slot.valueGet()
    if "\n" not in value:
        return
    parts = value.split("\n")
    slot.valueSet(parts[0])
    if slot.attribute == "text":
        _lineBreaksInsertAsChildren(slot.owner, parts[1:])
    else:
        _lineBreaksInsertAsSiblings(slot.owner, parts[1:])


def _lineBreaksInsertAsChildren(owner: etree._Element, parts: list[str]) -> None:
    for index, part in reversed(list(enumerate(parts))):
        lineBreak = etree.Element(f"{{{TEXT_NAMESPACE}}}line-break")
        lineBreak.tail = part
        owner.insert(0, lineBreak)


def _lineBreaksInsertAsSiblings(owner: etree._Element, parts: list[str]) -> None:
    parent = owner.getparent()
    if parent is None:
        raise SessionTemplateError("cannot insert a line break at the XML root")
    insertionIndex = parent.index(owner) + 1
    for part in parts:
        lineBreak = etree.Element(f"{{{TEXT_NAMESPACE}}}line-break")
        lineBreak.tail = part
        parent.insert(insertionIndex, lineBreak)
        insertionIndex += 1


## XML


def _xmlParse(contentXml: bytes) -> etree._ElementTree:
    parser = etree.XMLParser(
        no_network=True,
        recover=False,
        remove_blank_text=False,
        resolve_entities=False,
        strip_cdata=False,
    )
    try:
        root = etree.fromstring(contentXml, parser=parser)
    except etree.XMLSyntaxError as error:
        raise SessionTemplateError(f"content.xml is invalid: {error}") from error
    return root.getroottree()


def _xmlSerialise(tree: etree._ElementTree) -> bytes:
    return etree.tostring(tree, encoding="UTF-8", xml_declaration=True, pretty_print=False)
