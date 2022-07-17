import pkg_resources
import fileinput
import os
import logging
from enum import Enum
from typing import List

from .mutable_text import MutableText
from .tags import decompress_tags

import marisa_trie


log = logging.getLogger(__name__)


class StressSymbol:
    AcuteAccent = "´"
    CombiningAcuteAccent = "\u0301"


class Stressify:

    def __init__(self, dict_path=None, stress_symbol=StressSymbol.AcuteAccent):
        if dict_path is None:
            dict_path = pkg_resources.resource_filename('ukrainian_word_stress', 'data/stress.v2.trie')
        import stanza
        self.dict = marisa_trie.BytesTrie()
        self.dict.load(dict_path)
        self.nlp = stanza.Pipeline(
            'uk',
            processors='tokenize,pos,mwt',
            download_method=stanza.pipeline.core.DownloadMethod.REUSE_RESOURCES,
            logging_level=logging.getLevelName(log.getEffectiveLevel())
        )
        self.stress_symbol = stress_symbol

    def __call__(self, text):
        parsed = self.nlp(text)
        result = MutableText(text)
        log.debug("Parsed text: %s", parsed)
        for token in parsed.iter_tokens():
            accents = find_accent_positions(self.dict, token.to_dict()[0])
            accented_token = self.apply_accent_positions(token.text, accents)
            if accented_token != token:
                result.replace(token.start_char, token.end_char, accented_token)

        return result.get_edited_text()

    def apply_accent_positions(self, s, positions):
        for position in sorted(positions, reverse=True):
            s = s[:position] + self.stress_symbol + s[position:]
        return s


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
    for word in (base, base.lower(), base.title()):
        if word in trie:
            values = trie[word]
            break
    else:
        # non-dictionary word
        log.debug("%s is not in the dictionary", base)
        return []

    assert len(values) == 1
    accents_by_tags = _parse_dictionary_value(values[0])

    if len(accents_by_tags) == 0:
        # dictionary word with missing accents (dictionary has to be fixed)
        log.warning("The word `%s` is in dictionary, but lacks accents", base)
        return []

    if len(accents_by_tags) == 1:
        # this word has no other stress options, so no need 
        # to look at POS and tags
        log.debug("`%s` has single accent, looks no further", base)
        return accents_by_tags[0][1]

    # Match parsed word info with dictionary entries.
    # Dictionary entries have tags compressed to single byte codes.
    # Parse tags is a superset of dictionary tags. They include more
    # irrelevant info. They also and lack `upos` which we add separately
    log.debug("Trying to resolve ambigous entry %s", base)
    feats = parse.get('feats', '').split('|') + [f'upos={parse["upos"]}']
    for tags, accents in accents_by_tags:
        if all(tag in feats for tag in tags):
            return accents

    # If we reach here:
    # - the word have multiple stress options
    # - none of them matched the dictionary
    # At this point, the best we can do is to disregard parse
    # and return a randomly chosen accent option.
    # Ways to improve that in the future:
    # - Return best partially matched option
    # - Sort hyperonyms by frequency and return the most frequent one
    log.debug("Failed to resolve ambiguity, using a random option")
    return accents_by_tags[0][1]


def _parse_dictionary_value(value):
    accents_by_tags = []
    
    if b'$' not in value:
        # single item, all record is accent positions
        accents = [int(b) for b in value]
        tags = []
        accents_by_tags.append((tags, accents))

    else:
        # words whose accent position depends on POS and other tags
        items = value.split(b'$')
        for item in items:
            accents, _, tags = item.partition(b'^')
            accents = [int(b) for b in accents]
            tags = decompress_tags(tags)
            accents_by_tags.append((tags, accents))

    return accents_by_tags
