import marisa_trie


ACCENT = '\u0301'


class Stressify:

    def __init__(self, dict_path="./stress.v1.trie"):
        import stanza
        self.dict = marisa_trie.BytesTrie()
        self.dict.load(dict_path)
        self.nlp = stanza.Pipeline('uk', 'tokenize,pos')

    def __call__(self, text):
        parsed = self.nlp(text)
        result = []
        for token in parsed.iter_tokens():
            accents = get_accent_positions(self.dict, token.to_dict()[0])
            result.append(apply_accent_positions(token.text, accents))
        return " ".join(result)  # restore original whitespace



def stressify(text: str) -> str:
    if not hasattr(stressify, "f"):
        stressify.f = Stressify()
    return stressify.f(text)


def get_accent_positions(trie, parse):
    base = parse['text']
    if base not in trie:
        return []

    values = trie[base]
    assert len(values) == 1

    accents_by_tags = _parse_value(values[0])

    if len(accents_by_tags) == 1:
        return accents_by_tags[0][1]

    for tags, accents in accents_by_tags.items():
        if f'upos={parse["upos"]}' not in tags:
            continue
        return accents

    return []


def _parse_value(value):
    accents_by_tags = []
    
    if b'$' not in value:
        # single item
        accents = [int(b) for b in value]
        tags = []
        accents_by_tags.append((tags, accents))

    else:
        items = value.split(b'$')
        for item in items:
            accents, _, tags = item.split(b'^')
            accents = [int.from_bytes(b, 'little') for b in accents]
            tags = tags.decode()
            accents_by_tags.append((tags, accents))

    return accents_by_tags


def apply_accent_positions(s, positions):
    for position in sorted(positions, reverse=True):
        s = s[:position] + ACCENT + s[position:]
    return s

