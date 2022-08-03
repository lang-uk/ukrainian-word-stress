import pkg_resources
import logging
from enum import Enum
from typing import List

from ukrainian_word_stress.mutable_text import MutableText
from ukrainian_word_stress.tags import decompress_tags

import marisa_trie
import stanza


log = logging.getLogger(__name__)


class StressSymbol:
    AcuteAccent = "´"
    CombiningAcuteAccent = "\u0301"


class OnAmbiguity:
    Skip = "skip"
    First = "first"
    All = "all"


class Stressifier:
    """Add word stress to texts in Ukrainian.

    Args:
        `stress_symbol`: Which symbol to use as an accent mark.
            Default is `StressSymbol.AcuteAccent` (я´йця)
            Alternative is `StressSymbol.CombiningAcuteAccent` (я́йця).
                This symbol is commonly used in print. However, not all
                platforms render it correctly (Windows, for one).
            Custom characters are also accepted.

        `on_ambiguity`: What to do if word ambiguity cannot be resolved.
            - `OnAmbiguity.Skip` (default): do not place stress
            - `OnAmbiguity.First`: place a stress of the first match with a
                high chance of being incorrect.
            - `OnAmbiguity.All`: return all possible options at once.
                This will look as multiple stress symbols in one word
                (за´мо´к)

    Example:
        >>> stressify = Stressifier()
        >>> stressify("Привіт, як справи?")
        'Приві´т, як спра´ви?'
    """



    def __init__(self,
                 stress_symbol=StressSymbol.AcuteAccent,
                 on_ambiguity=OnAmbiguity.Skip):

        dict_path = pkg_resources.resource_filename('ukrainian_word_stress', 'data/stress.trie')
        self.dict = marisa_trie.BytesTrie()
        self.dict.load(dict_path)
        self.nlp = stanza.Pipeline(
            'uk',
            processors='tokenize,pos,mwt',
            download_method=stanza.pipeline.core.DownloadMethod.REUSE_RESOURCES,
            logging_level=logging.getLevelName(log.getEffectiveLevel())
        )
        self.stress_symbol = stress_symbol
        self.on_ambiguity = on_ambiguity

    def __call__(self, text):
        parsed = self.nlp(text)
        result = MutableText(text)
        log.debug("Parsed text: %s", parsed)
        for token in parsed.iter_tokens():
            accents = find_accent_positions(self.dict, token.to_dict()[0], self.on_ambiguity)
            accented_token = self._apply_accent_positions(token.text, accents)
            if accented_token != token:
                result.replace(token.start_char, token.end_char, accented_token)

        return result.get_edited_text()

    def _apply_accent_positions(self, s, positions):
        for position in sorted(positions, reverse=True):
            s = s[:position] + self.stress_symbol + s[position:]
        return s


def find_accent_positions(trie, parse, on_ambiguity=OnAmbiguity.Skip) -> List[int]:
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
    log.debug("Resolving ambigous entry %s", base)
    feats = parse.get('feats', '').split('|') + [f'upos={parse.get("upos", "")}']
    matches = []
    for tags, accents in accents_by_tags:
        if all(tag in feats for tag in tags):
            matches.append((tags, accents))
            log.debug("Found match for %s: %s (accent=%s)", base, tags, accents)

    unique_accents = len({repr(accents) for _, accents in matches})

    if unique_accents == 1:
        log.debug("Ambiguity resolved to a single option: %s", matches)
        accents = matches[0][1]
        return accents

    if unique_accents == 0:
        # Nothing matched the parse, consider all dictionary options
        matches = accents_by_tags

    # If we reach here:
    # - the word have multiple stress options and none of them matched the dictionary
    # - OR the word is hyperonym (го'род/горо'д)
    # There's no ideal action, so follow a configured strategy
    # Ways to improve that in the future:
    # - Return best partially matched option
    # - Sort hyperonyms by frequency and return the most frequent one
    # - Integrate a proper word sense disambiguation model
    if on_ambiguity == OnAmbiguity.First:
        # Disregard parse and return the first match (essentially random option)
        log.debug("Failed to resolve ambiguity, using a random option")
        return matches[0][1]

    elif on_ambiguity == OnAmbiguity.Skip:
        # Pretend the word is not dictionary
        return []

    elif on_ambiguity == OnAmbiguity.All:
        # Combine all possible accent positions 
        all_accents = set()
        for tags, accents in matches:
            all_accents |= set(accents)
        return sorted(all_accents)

    else:
        raise ValueError(f"Unknown on_ambiguity value: {on_ambiguity}")


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
            if item:
                accents, _, tags = item.partition(b'^')
                accents = [int(b) for b in accents]
                tags = decompress_tags(tags)
                accents_by_tags.append((tags, accents))

    return accents_by_tags
