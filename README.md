Ukrainian word stress
=====================

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


## Setup

```bash
$ pip install ukrainian-word-stress
```

Note, that on the first call this will download around 500M of Stanza resources.
The default location for this is `~/stanza_resources`


## Handling ambiguity

Some words have different pronunciation and meaning but share the same spelling.
These are so called [heteronyms][1].

In most cases, this happens when a word used in its form (singular/plural, case).
For example:

* блохи́ - родовий відмінок в однині ("немає ані блохи́")
* бло́хи - множина називного відмінку ("повсюди були бло́хи")

We handle this more or less correctly by doing morphological and POS text parse
with Stanza.

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


[1]: https://en.wikipedia.org/wiki/Heteronym_(linguistics)
