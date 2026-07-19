# Contributing

## Reporting missing or incorrect stresses

The stress dictionary shipped with this package (`ukrainian_word_stress/data/stress.trie`)
covers about 2.9 million word forms derived from the
["Dictionaries of Ukraine"](https://lcorp.ulif.org.ua/dictua/) by ULIF.
A word may still come out without a stress mark. Before reporting it:

1. Check whether it is a heteronym rather than a dictionary gap.
   Words like `замок` have several valid stress patterns, and by default
   the package skips them instead of guessing:

   ```bash
   $ echo замок | ukrainian-word-stress --on-ambiguity=all
   за´мо´к
   ```

   If you see multiple stress marks with `--on-ambiguity=all`, the word is
   in the dictionary; the default `skip` strategy just cannot resolve it
   without context. In Stanza mode, most of these are resolved by the
   POS/morphology parse.

2. Run with `--verbose` to see whether the word was found in the
   dictionary at all.

If the word is genuinely missing or the stress is wrong, please open an
issue in [ukrainian-word-stress-dictionary](https://github.com/lang-uk/ukrainian-word-stress-dictionary)
(the dictionary source) or in this repository. List the word forms with
their stresses using the combining acute accent placed after the stressed
vowel (`ма́ма`), the same format as the dictionary's `stress.txt`.

## How the dictionary becomes a trie

`ukrainian_word_stress/compile_dict.py` compiles a CSV export of the ULIF
dictionary (columns `form`, `tag`, `type`, with tags like case and number
per word form) into a `marisa-trie` where:

- unambiguous words map directly to accent byte positions;
- heteronyms map to multiple records, each carrying compressed
  morphological tags (see [docs/dictionary_format.md](docs/dictionary_format.md))
  used for disambiguation at runtime.

The tagged CSV is derived from ULIF data and is not publicly
redistributable, so regenerating the trie is done by maintainers. Issue
reports with word lists are the practical way to get corrections in.

## Development setup

```bash
pip install -e .[stanza,dev,test]
pytest
```

Tests in `tests/test_dictionary_mode.py` run without Stanza and without
model downloads; the rest of `tests/test_stressify.py` needs the Stanza
Ukrainian models (~500 MB, downloaded automatically on first run).
