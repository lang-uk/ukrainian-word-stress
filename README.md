Ukrainian word stress
=====================

[![Tests](https://github.com/lang-uk/ukrainian-word-stress/actions/workflows/tests.yml/badge.svg)](https://github.com/lang-uk/ukrainian-word-stress/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/ukrainian-word-stress.svg)](https://pypi.org/project/ukrainian-word-stress/)
[![Python versions](https://img.shields.io/pypi/pyversions/ukrainian-word-stress.svg)](https://pypi.org/project/ukrainian-word-stress/)

Word stress is an emphasis we place on a particular syllable of a word as
we pronounce it: ма́ма

This package takes text in Ukrainian and adds the stress mark after an accented
vowel. This is useful in speech synthesis applications and for preparing text
for language learners.


## Example


### From Python

```python
>>> from ukrainian_word_stress import Stressifier
>>> text = """Потяг зупинився, ми зійшли на платформу. Було тихо, широкі навскісні промені золотили повітря, заважаючи бачити речі такими, якими вони були. Третя по обіді. Жодноі живоі душі. Найкращий час для урочистих відвідин померлих. Взяли в привокзальному торбу вина, рушили вздовж колій, піщаною стежкою."""
>>> stressify = Stressifier()
>>> stressify(text)

'Потяг зупини´вся, ми зійшли´ на платфо´рму. Було´ ти´хо, широ´кі навскі´сні
про´мені золоти´ли пові´тря, заважа´ючи ба´чити ре´чі таки´ми, яки´ми вони´
були´. Тре´тя по обі´ді. Жодноі живоі душі´. Найкра´щий час для урочи´стих
відві´дин поме´рлих. Взя´ли в привокза´льному то´рбу вина, ру´шили вздовж
ко´лій, піща´ною сте´жкою.'

```

The `ukrainian_word_stress.Stressifier` class has optional arguments for
fine-graded configuration (see sections below). For example:

```python
>>> from ukrainian_word_stress import Stressifier, StressSymbol
>>> stressify = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
>>> stressify(text)

'Потяг зупини́вся, ми зійшли́ на платфо́рму. Було́ ти́хо, широ́кі навскі́сні про́мені
золоти́ли пові́тря, заважа́ючи ба́чити ре́чі таки́ми, яки́ми вони́ були́. Тре́тя по
обі́ді. Жодноі живоі душі́. Найкра́щий час для урочи́стих відві́дин поме́рлих. Взя́ли
в привокза́льному то́рбу вина, ру́шили вздовж ко́лій, піща́ною сте́жкою.'
```


### From command-line

```bash
$ echo 'Золоті яйця, але нема ні яйця' | ukrainian-word-stress
Золоті´ я´йця, але´ нема´ ні яйця´
```

Note: this example resolves the two different readings of `яйця` from
context, which requires the Stanza backend (installed by default). The
lightweight dictionary-only mode skips such ambiguous words instead of
guessing — see [Disambiguation modes](#disambiguation-modes).


## Setup

Requires Python 3.9+.

```bash
$ pip install ukrainian-word-stress
```

This installs the full version, including the Stanza NLP backend used to
resolve heteronyms from context. On the first call it downloads around
500M of Stanza resources; the default location for this is
`~/stanza_resources`


#### Lightweight installation (no Stanza, no PyTorch)

For TTS pipelines and other size-constrained environments, the package
also works in a dictionary-only mode that needs nothing beyond
`marisa-trie` (megabytes instead of gigabytes, no model downloads).
pip cannot exclude a dependency with a flag, so the lightweight install
uses `--no-deps`:

```bash
$ pip install --no-deps ukrainian-word-stress
$ pip install marisa-trie
```

(pip may later warn that `stanza is not installed` for this environment —
that is expected with `--no-deps` and harmless.)

Without stanza installed, `Stressifier()` automatically runs in the
dictionary-only mode: it covers the ~98.7% of dictionary word forms that
have a single valid stress pattern and skips heteronyms (see
[Disambiguation modes](#disambiguation-modes) below).

> **Note:** 2.0.0 briefly made the lightweight version the default
> install; since 2.1.0 the default installs Stanza again, matching 1.x.
> Since 2.0.0, some words that 1.x left unstressed (typographic
> apostrophes, words whose readings agree on stress) receive a stress
> mark in both modes.


### Disambiguation modes

Most Ukrainian word forms (98.7% of the 2.9M dictionary entries) have
exactly one valid stress pattern — a dictionary lookup answers them
without any NLP. The rest are heteronyms (за́мок/замо́к) that need context.
The `disambiguation` parameter controls how they are handled:

* `auto` (default): use Stanza if it is installed, otherwise
  dictionary-only.

* `stanza`: parse the text with Stanza's POS/morphology pipeline and pick
  the reading that matches. Best accuracy. Requires the stanza package
  (installed by default; PyTorch, ~500MB of models).

* `dictionary`: lookup only, no dependencies beyond the bundled trie.
  Unambiguous words are handled identically to the Stanza mode; heteronyms
  follow the `on_ambiguity` strategy (`skip` by default, i.e. no stress
  mark rather than a wrong one).

```python
>>> from ukrainian_word_stress import Stressifier, Disambiguation
>>> stressify = Stressifier(disambiguation=Disambiguation.Dictionary)
>>> stressify("Привіт, як справи?")
'Приві´т, як спра´ви?'
```

Or from the command line:

```bash
$ echo 'Привіт, як справи?' | ukrainian-word-stress --disambiguation=dictionary
```


### Offline installation

The dictionary-only mode works fully offline out of the box.

For the Stanza mode on a machine with no internet access (or behind a
firewall), the models can be downloaded elsewhere and copied over:

1. On a machine with internet access, run:

   ```bash
   python -c "import stanza; stanza.download('uk')"
   ```

2. Copy the resulting `~/stanza_resources` directory to the same location
   on the target machine.

A custom location can be set with the `STANZA_RESOURCES_DIR` environment
variable on both machines.


## Handling ambiguity

Some words have different pronunciation and meaning but share the same spelling.
These are so called [heteronyms][1].

In most cases, this happens when a word used in its form (singular/plural, case).
For example:

* блохи́ - родовий відмінок в однині ("немає ані блохи́")
* бло́хи - множина називного відмінку ("повсюди були бло́хи")

We handle this more or less correctly by doing morphological and POS text parse
with Stanza (in the `stanza` disambiguation mode; the `dictionary` mode
falls back to the strategies below for all heteronyms).

A much smaller category of heteronyms is where words have completely different meanings:

* а́тлас - збірник карт
* атла́с - тканина

Resolving this is much harder and sometimes impossible.

There's no ideal solution to heteronyms ambiguity. We let you decide what to
do for such cases. Possible strategies are:

* `skip`: do not place stress at all (this is the default).

* `all`: return all possible options at once.  This will look as multiple
  stress symbols in one word (за´мо´к).

* `first`: place a stress of the first match with a high chance of being
  incorrect. Essentially, means a random guess on the heteronyms meaning.

The strategy can be configured via `--on-ambiguity` parameter of the
command-line utility. In Python, use `on_ambiguity` parameter of the 
`ukrainian_word_stress.Stressifier` class.


## Stress mark symbols

By default, the Unicode Acute Acent symbol is used: “´” (U+00B4).

On print, Combining Acute Acent is more common and visually less intrusive.
This can be turned on by passing "--symbol=combining" to the CLI utility,
or `stress_symbol=StressSymbol.CombiningAcuteAccent` in the `Stressifier` class.

Note, that some platforms (Windows, for example) render it incorrectly.

You can also pass custom characters in place of these two:

```bash
$ echo 'олені небриті і не голені.' | ukrainian-word-stress --symbol +
о+лені небри+ті і не го+лені.

$ echo 'олені небриті і не голені.' | ukrainian-word-stress --symbol combining
о́лені небри́ті і не го́лені.
```


## Variative stress

Some words allow for multiple stress positions. For example,
по́милка and поми́лка are both acceptable. For such words we return
double stress:

```
$ echo помилка | ukrainian-word-stress
по´ми´лка
```




## Debugging and reporting issues

Use the `--verbose` switch to get info useful for debugging.

If you believe that you found a bug, please open a [Github issue](https://github.com/lang-uk/ukrainian-word-stress/issues)

But first, make sure that the bug is not related to heteronyms disambiguation.
For example, if you see that some word lacks accent, add the `--on-ambiguity=all`
switch to see if this was a heteronym. If the word of question has
multiple accents, that's a heteronym, not a bug:

```bash
$ echo замок | ukrainian-word-stress --on-ambiguity=all
за´мо´к
```


## More docs

* [Dictionary format](./docs/dictionary_format.md)
* [Adapting this approach to other languages](./docs/other_languages.md)
* [Contributing (missing stresses, dev setup)](./CONTRIBUTING.md)


[1]: https://en.wikipedia.org/wiki/Heteronym_(linguistics)
