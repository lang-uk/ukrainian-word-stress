from importlib import resources as pkg_resources
import logging
from enum import Enum
from typing import List

from ukrainian_word_stress.mutable_text import MutableText
from ukrainian_word_stress.tags import decompress_tags, TAGS

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
            - `OnAmbiguity.Skip` (default): do not place stress on the word.
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

        dict_path = pkg_resources.files('ukrainian_word_stress').joinpath('data/stress.trie')
        
        self.dict = marisa_trie.BytesTrie()
        self.dict.load(dict_path)
        self.nlp = stanza.Pipeline(
            "uk",
            processors="tokenize,pos,mwt",
            download_method=stanza.pipeline.core.DownloadMethod.REUSE_RESOURCES,
            logging_level=logging.getLevelName(log.getEffectiveLevel()),
        )
        self.stress_symbol = stress_symbol
        self.on_ambiguity = on_ambiguity

    def __call__(self, text):
        parsed = self.nlp(text)
        result = MutableText(text)
        log.debug("Parsed text: %s", parsed)
        for token in parsed.iter_tokens():
            accents = find_accent_positions(
                self.dict, token.to_dict()[0], self.on_ambiguity
            )
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

    base = parse["text"]
    values = []
    for word in (base, base.lower(), base.title()):
        if word in trie:
            values += trie[word]
            # for the first word in the sentence, try lowercased.
            # for the rest, exit early.
            if parse["id"] == 1 and base[0].isupper():
                continue
            break

    if not values:
        # non-dictionary word
        log.debug("%s is not in the dictionary", base)
        return []

    accents_by_tags = []
    for vs in values:
        accents_by_tags += _parse_dictionary_value(vs)

    if len(accents_by_tags) == 0:
        # dictionary word with missing accents (dictionary has to be fixed)
        log.debug("The word `%s` is in dictionary, but lacks accents", base)
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
    feats = _get_tags_from_parse(parse)
    matches = _match_parse_to_dictionary(feats, accents_by_tags)
    unique_accents = len({repr(accents) for _, accents in matches})

    if unique_accents == 1:
        log.debug("Ambiguity resolved to a single option: %s", matches)
        accents = matches[0][1]
        return accents

    if unique_accents == 0:
        log.debug("Nothing matched the parse, consider all dictionary options.")
        log.debug("Tags from parse: %s", feats)
        log.debug("Tags from dictionary: \n * %s",
                "\n * ".join(repr(tags) for tags, _ in accents_by_tags))
        matches = accents_by_tags

    # If we reach here:
    # - the word have multiple stress options and none of them matched the parse
    # - OR the word is hyperonym (го'род/горо'д)
    # There's no ideal action, so follow a configured strategy
    # Ways to improve that in the future:
    # - [x] Return best partially matched option
    # - [ ] Sort hyperonyms by frequency and return the most frequent one
    # - [ ] Integrate a proper word sense disambiguation model
    log.debug("Using %s strategy for %s", on_ambiguity, base)

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

    elif callable(on_ambiguity):
        return on_ambiguity(matches, parse)

    else:
        raise ValueError(f"Unknown on_ambiguity value: {on_ambiguity}")


def _parse_dictionary_value(value):
    accents_by_tags = []

    if b"\n" not in value:
        # single item, all record is accent positions
        accents = [int(b) for b in value]
        tags = []
        accents_by_tags.append((tags, accents))

    else:
        # words whose accent position depends on POS and other tags
        items = value.split(b"\n")
        for item in items:
            if item:
                accents, _, tags = item.partition(b"\t")
                accents = [int(b) for b in accents]
                tags = decompress_tags(tags)
                accents_by_tags.append((tags, accents))

    return accents_by_tags


def _get_tags_from_parse(parse):
    """Take a Stanza parse and return a list of tags to match."""

    upos = parse.get("upos")
    if upos == "PROPN":
        # Dictionary makes no distinction between proper and common nouns
        upos = "NOUN"

    feats = parse.get("feats", "").split("|")
    feats.append(f"upos={upos}")

    return feats


def _match_parse_to_dictionary(feats, accents_by_tags, penalty_tolerance=1):
    """Return a list of matching dictionary entries, allowing for some penalty.
    Penalty is the number of tags that does not match.

    Returns:
        A list of (tags, accents) tuples: the best matches.

    """

    # Count how many tags match for each dictionary entry.
    # Each tag that does not match is penalized by 1.
    match_penalty = []  # (penalty, match)
    for tags, accents in accents_by_tags:
        tags_to_match = [f for f in tags if f in TAGS and f]
        penalty = len([f for f in tags_to_match if f not in feats])
        match_penalty.append((penalty, (tags, accents)))
        log.debug("   penalty: %s, match: %s", penalty, (tags, accents))

    # Take the best matches withing the penalty tolerance.
    match_penalty.sort()
    best_penalty = match_penalty[0][0]
    log.debug("Best penalty: %s", best_penalty)
    if best_penalty > penalty_tolerance:
        matches = []
    else:
        matches = [m for penalty, m in match_penalty if penalty == best_penalty]

    return matches
