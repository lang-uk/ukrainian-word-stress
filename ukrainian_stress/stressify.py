from typing import List
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
            accents = find_accent_positions(self.dict, token.to_dict()[0])
            result.append(apply_accent_positions(token.text, accents))
        return " ".join(result)  # restore original whitespace



def stressify(text: str) -> str:
    if not hasattr(stressify, "f"):
        stressify.f = Stressify()
    return stressify.f(text)


def find_accent_positions(trie, parse) -> List[int]:
    """Return best accent guess for the given token parsed tags.

    Returns:
        A list of accent positions. The size of the list can be:
        0 for tokens that are not in the dictionary.
        1 for most of in-dictionary words.
        2 and more - for compound words and for words that have
          multiple valid accents.
    """

    base = parse['text']
    if base not in trie:
        # non-dictionary words
        return []

    values = trie[base]
    assert len(values) == 1

    accents_by_tags = _parse_value(values[0])

    if len(accents_by_tags) == 1:
        # this word has no other stress options, so no need 
        # to look at POS and tags
        return accents_by_tags[0][1]

    # Match parsed word info with dictionary entries.
    # Dictionary entries have tags like this:
    #   Number=Plur|Case=Nom|upos=NOUN
    # Parsed tags has the same format but have more irrelevant info
    # and lack `upos` which we add separately
    feats = parse['feats'].split('|') + [f'upos={parse["upos"]}']
    for tags, accents in accents_by_tags:
        if all(tag in feats for tag in tags.split('|')):
            return accents

    # If we reach here:
    # - the word have multiple stress options
    # - none of them matched the dictionary
    # At this point, the best we can do is to disregard parse
    # and return a randomly chosen accent option.
    # Ways to improve that in the future:
    # - Return best partially matched option
    # - Sort hyperonyms by frequency and return the most frequent one
    return accents[0]


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
            accents, _, tags = item.partition(b'^')
            accents = [int(b) for b in accents]
            tags = tags.decode()
            accents_by_tags.append((tags, accents))

    return accents_by_tags


def apply_accent_positions(s, positions):
    for position in sorted(positions, reverse=True):
        s = s[:position] + ACCENT + s[position:]
    return s

