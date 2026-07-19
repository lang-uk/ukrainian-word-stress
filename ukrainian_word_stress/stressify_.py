from __future__ import annotations

from importlib import resources as pkg_resources
import importlib.util
import logging
import re

from ukrainian_word_stress.mutable_text import MutableText
from ukrainian_word_stress.tags import TAGS, decompress_tags

import marisa_trie


log = logging.getLogger(__name__)

_STANZA_INIT_HELP = """\
Failed to initialize the Stanza NLP pipeline for Ukrainian \
(see the original error above).

On the first run, ukrainian-word-stress downloads Stanza models for \
Ukrainian (about 500 MB) into ~/stanza_resources. If the error above is a \
network error (proxy, firewall, or offline machine), download the models \
on a machine with internet access:

    python -c "import stanza; stanza.download('uk')"

and copy the resulting ~/stanza_resources directory to the same location \
on the target machine. A custom location can be set with the \
STANZA_RESOURCES_DIR environment variable on both machines.

Alternatively, use the dictionary-only mode, which needs no Stanza at all:

    Stressifier(disambiguation=Disambiguation.Dictionary)
"""

_STANZA_MISSING_HELP = """\
The 'stanza' disambiguation backend requires the stanza package, which is \
not installed. Install it with:

    pip install ukrainian-word-stress[stanza]

or use the dictionary-only mode, which needs no extra dependencies:

    Stressifier(disambiguation=Disambiguation.Dictionary)
"""

# Matches words: letter runs optionally joined by apostrophes or hyphens
# (м'яч, буль-буль).  Digits and underscores are not part of dictionary
# entries, so they are excluded.
_WORD_RE = re.compile(r"[^\W\d_]+(?:['’ʼ`-][^\W\d_]+)*")

# The dictionary stores apostrophes as U+0027; real-world texts often use
# typographic variants instead.
_APOSTROPHES = str.maketrans("’ʼ`", "'''")


class StressSymbol:
    AcuteAccent = "´"
    CombiningAcuteAccent = "\u0301"


class OnAmbiguity:
    Skip = "skip"
    First = "first"
    All = "all"


class Disambiguation:
    Auto = "auto"
    Stanza = "stanza"
    Dictionary = "dictionary"


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

        `disambiguation`: How to resolve heteronyms (words that share
            spelling but differ in stress, like за´мок/замо´к).
            - `Disambiguation.Auto` (default): use Stanza if it is
                installed, otherwise fall back to dictionary-only mode.
            - `Disambiguation.Stanza`: parse the text with the Stanza NLP
                pipeline and use POS/morphology to pick the right stress.
                Requires `pip install ukrainian-word-stress[stanza]` and
                downloads ~500 MB of models on the first run.
            - `Disambiguation.Dictionary` (or `None`): dictionary lookup
                only. No extra dependencies and no model downloads.
                About 98.7% of dictionary entries have a single stress
                variant and are handled identically to the Stanza mode;
                the rest follow the `on_ambiguity` strategy.

    Example:
        >>> stressify = Stressifier()
        >>> stressify("Привіт, як справи?")
        'Приві´т, як спра´ви?'
    """



    def __init__(self,
                 stress_symbol: str = StressSymbol.AcuteAccent,
                 on_ambiguity: str = OnAmbiguity.Skip,
                 disambiguation: str | None = Disambiguation.Auto) -> None:

        dict_path = pkg_resources.files('ukrainian_word_stress').joinpath('data/stress.trie')

        self.dict = marisa_trie.BytesTrie()
        self.dict.load(str(dict_path))

        if disambiguation is None:
            disambiguation = Disambiguation.Dictionary
        if disambiguation == Disambiguation.Auto:
            if importlib.util.find_spec('stanza') is not None:
                disambiguation = Disambiguation.Stanza
            else:
                disambiguation = Disambiguation.Dictionary
            log.info("Auto-selected '%s' disambiguation", disambiguation)

        if disambiguation == Disambiguation.Stanza:
            self.nlp = _create_stanza_pipeline()
        elif disambiguation == Disambiguation.Dictionary:
            self.nlp = None
        else:
            raise ValueError(f"Unknown disambiguation value: {disambiguation}")

        self.disambiguation = disambiguation
        self.stress_symbol = stress_symbol
        self.on_ambiguity = on_ambiguity

    def __call__(self, text: str) -> str:
        if self.nlp is None:
            return self._stressify_dictionary_only(text)

        parsed = self.nlp(text)
        result = MutableText(text)
        log.debug("Parsed text: %s", parsed)
        for token in parsed.iter_tokens():
            accents = find_accent_positions(self.dict, token.to_dict()[0], self.on_ambiguity)
            accented_token = self._apply_accent_positions(token.text, accents)
            if accented_token != token.text:
                result.replace(token.start_char, token.end_char, accented_token)

        return result.get_edited_text()

    def _stressify_dictionary_only(self, text: str) -> str:
        result = MutableText(text)
        for match in _WORD_RE.finditer(text):
            word = match.group()
            accents = find_accent_positions(self.dict, {'text': word}, self.on_ambiguity)
            if accents:
                result.replace(match.start(), match.end(),
                               self._apply_accent_positions(word, accents))
            elif '-' in word and not self._in_dictionary(word):
                # Ad-hoc compound (Київ-Львів) that is not a dictionary
                # entry as a whole: stress its parts individually
                offset = match.start()
                for part in word.split('-'):
                    accents = find_accent_positions(self.dict, {'text': part}, self.on_ambiguity)
                    if accents:
                        result.replace(offset, offset + len(part),
                                       self._apply_accent_positions(part, accents))
                    offset += len(part) + 1

        return result.get_edited_text()

    def _in_dictionary(self, word: str) -> bool:
        return bool(find_accent_positions(self.dict, {'text': word}, OnAmbiguity.First))

    def _apply_accent_positions(self, s: str, positions: list[int]) -> str:
        for position in sorted(positions, reverse=True):
            s = s[:position] + self.stress_symbol + s[position:]
        return s


def _create_stanza_pipeline():
    try:
        import stanza
    except ImportError as exc:
        raise RuntimeError(_STANZA_MISSING_HELP) from exc

    try:
        return stanza.Pipeline(
            'uk',
            processors='tokenize,pos,mwt',
            download_method=stanza.pipeline.core.DownloadMethod.REUSE_RESOURCES,
            logging_level=logging.getLevelName(log.getEffectiveLevel())
        )
    except Exception as exc:
        raise RuntimeError(_STANZA_INIT_HELP) from exc


def find_accent_positions(trie: marisa_trie.BytesTrie,
                          parse: dict,
                          on_ambiguity: str = OnAmbiguity.Skip) -> list[int]:
    """Return best accent guess for the given token parsed tags.

    Returns:
        A list of accent positions. The size of the list can be:
        0 for tokens that are not in the dictionary.
        1 for most of in-dictionary words.
        2 and more - for compound words and for words that have
          multiple valid accents.
    """

    base = parse['text']
    normalized = base.translate(_APOSTROPHES)
    candidates = dict.fromkeys([
        base, base.lower(), base.title(),
        normalized, normalized.lower(), normalized.title(),
    ])
    for word in candidates:
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
        unique_accents = len({repr(accents) for _, accents in matches})
        if unique_accents == 1:
            # All dictionary readings agree on the accents, so the word
            # is not really ambiguous for our purposes
            log.debug("All readings of `%s` share the same accents", base)
            return matches[0][1]

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


def _parse_dictionary_value(value: bytes) -> list[tuple[list[str], list[int]]]:
    POS_SEP = TAGS['POS-separator']
    REC_SEP = TAGS['Record-separator']
    accents_by_tags = []

    if REC_SEP not in value:
        # single item, all record is accent positions
        accents = [int(b) for b in value]
        tags = []
        accents_by_tags.append((tags, accents))

    else:
        # words whose accent position depends on POS and other tags
        items = value.split(REC_SEP)
        for item in items:
            if item:
                accents, _, tags = item.partition(POS_SEP)
                accents = [int(b) for b in accents]
                tags = decompress_tags(tags)
                accents_by_tags.append((tags, accents))

    return accents_by_tags
