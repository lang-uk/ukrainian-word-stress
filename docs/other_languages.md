# Adapting this approach to other languages

This package is sometimes mistaken for a neural network. It is not one —
and that is good news if you want to build the same thing for another
language.

## How it actually works

1. **Dictionary lookup.** A [marisa-trie](https://github.com/pytries/marisa-trie)
   maps ~2.9M Ukrainian word forms to stress positions. The dictionary is
   derived from ULIF's "Dictionaries of Ukraine". For ~98.7% of the word
   forms there is exactly one valid stress pattern, and the lookup alone
   gives the correct answer.

2. **Morphological disambiguation (optional).** The remaining ~1.3% are
   heteronyms — forms whose stress depends on the reading (`за́мок` "castle"
   vs `замо́к` "lock", `голови́` singular genitive vs `го́лови` plural
   nominative). For those, the dictionary stores several records, each
   tagged with the morphological features (case, number, gender, POS) of
   the corresponding reading. At runtime, [Stanza](https://stanfordnlp.github.io/stanza/)
   parses the sentence and the parse features select the matching record.
   Without Stanza, the package falls back to a configurable strategy
   (`skip`/`first`/`all`).

There is no training step anywhere: accuracy comes from dictionary
coverage plus the quality of the morphological parser.

## The recipe for your language

You need two ingredients:

1. **A stress dictionary of inflected forms** — not just lemmas. For Slavic
   languages, stress moves within paradigms, so per-form data is essential.
   Possible sources: Wiktionary dumps, national language institute
   dictionaries, morphological databases (e.g. Zaliznyak-derived data for
   Russian, SGJP for Polish accent-adjacent tasks). Watch the license.

2. **A morphological tagger** for the ~1-2% of forms that are heteronyms —
   any UD-compatible tagger works (Stanza covers 70+ languages), because
   the disambiguation is just matching tagger output against the features
   attached to each dictionary record. If no tagger is available, you can
   still ship the dictionary-only mode; it simply skips heteronyms.

The pipeline then is exactly `compile_dict.py` in this repository:
group per-form records by surface form; store the accent positions
directly when all records agree; store `(features, accent-positions)`
records otherwise. See [dictionary_format.md](./dictionary_format.md) for
the byte-level format.

## Practical notes

- Measure before optimizing the hard part: in Ukrainian, only ~1.3% of
  forms are ambiguous. If your dictionary shows a similar profile, a
  dictionary-only mode already gets you close to the ceiling, and the
  tagger only earns its keep on the tail.
- The trie keeps the whole thing fast and small (~30 MB for 2.9M forms).
- Accuracy on out-of-dictionary words is zero by design — this approach
  does not generalize to unseen words. If your dictionary is small, a
  character-level model may serve you better than a trie.
