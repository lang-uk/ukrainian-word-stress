from typing import List


# Maps known tags to a single byte code
TAGS = {
    "POS-separator": b'\x09',
    "entry-separator": b'\x0a',
    "Number=Sing": b'\x11',
    "Number=Plur": b'\x12',
    "Case=Nom": b'\x20',
    "Case=Gen": b'\x21',
    "Case=Dat": b'\x22',
    "Case=Acc": b'\x23',
    "Case=Ins": b'\x24',
    "Case=Loc": b'\x25',
    "Case=Voc": b'\x26',
    "Gender=Neut": b'\x30',
    "Gender=Masc": b'\x31',
    "Gender=Fem": b'\x32',
    "VerbForm=Inf": b'\x41',
    "VerbForm=Conv": b'\x42',
    "Person=0": b'\x50',
    "upos=NOUN": b'\x61',
    "upos=ADJ": b'\x62',
    "upos=INTJ": b'\x63',
    "upos=CCONJ": b'\x64',
    "upos=PART": b'\x65',
    "upos=PRON": b'\x66',
    "upos=VERB": b'\x67',
    "upos=PROPN": b'\x68',
    "upos=ADV": b'\x69',
    "upos=NOUN": b'\x6a',
    "upos=NUM": b'\x6b',
    "upos=ADP": b'\x6c',

    # Skip these:
    "upos=СПОЛУКА": b'\x00',
    "upos=ПРИСУДКОВЕ СЛОВО": b'\x00',
    "upos=NumType=Card": b'\x00',
    "upos=<None>": b'\x00',
    "": b'\x00',
}


# Maps single byte code to a string tag
TAG_BY_BYTE = {value: key for key, value in TAGS.items()}


def compress_tags(tags: List[str]) -> bytes:
    """Compress a list of string tags into a byte string.

    String tag should have form like "Case=Nom".
    Byte string has one byte per tag according to the `TAGS` mapping.
    """

    result = bytes()
    for tag in tags:
        value = TAGS.get(tag)
        if value is None:
            raise LookupError(f"Unknown tag: {tag}")
        if value != b'\x00':
            result += value
    return result


def decompress_tags(tags_bytes: bytes) -> List[str]:
    """Return list of string tags given bytes representation.
    """

    return [TAG_BY_BYTE[bytes([b])] for b in tags_bytes]
