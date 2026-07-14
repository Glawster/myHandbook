from fmparser.binary import BinaryReader, Endian


def test_binary_reader_numeric_types_and_bookmarks() -> None:
    reader = BinaryReader(bytes.fromhex("01 02 00 78 56 34 12"), endian=Endian.LITTLE)

    assert reader.uint8() == 1
    reader.bookmark("after-first")
    assert reader.uint16() == 2
    assert reader.uint32() == 0x12345678
    assert reader.bookmarks[0].offset == 1


def test_binary_reader_big_endian_override() -> None:
    reader = BinaryReader(bytes.fromhex("12 34 78 56"))

    assert reader.uint16(Endian.BIG) == 0x1234
    assert reader.uint16(Endian.LITTLE) == 0x5678


def test_varints() -> None:
    assert BinaryReader(bytes([0xAC, 0x02])).varuint() == 300
    assert BinaryReader(bytes([0x01])).varint() == -1
