# Tests for the dictionary-only mode (no Stanza).
#
# These run without stanza installed and without any model downloads,
# so they can execute in fully offline environments.

import importlib.util
import subprocess
import sys

import pytest

from ukrainian_word_stress import Disambiguation, OnAmbiguity, Stressifier


@pytest.fixture(scope='module')
def stressify():
    return Stressifier(disambiguation=Disambiguation.Dictionary)


def test_single_syllable(stressify):
    assert stressify("а") == "а"
    assert stressify("кіт") == "кіт"


def test_single_choice(stressify):
    assert stressify("Україна") == "Украї´на"


def test_ignore_case(stressify):
    assert stressify("мама") == "ма´ма"
    assert stressify("Мама") == "Ма´ма"
    assert stressify("МАМА") == "МА´МА"


def test_preserve_whitespace_and_punctuation(stressify):
    assert stressify(" Привіт ,  як справи ?") == " Приві´т ,  як спра´ви ?"


def test_apostrophe(stressify):
    assert stressify("п'ятниця") == "п'я´тниця"
    assert stressify("п’ятниця") == "п’я´тниця"


def test_hyphenated(stressify):
    assert stressify("будь-який") == "будь-яки´й"


def test_hyphenated_compound_not_in_dictionary(stressify):
    # The compound is not a dictionary entry, but its parts are
    assert stressify("потяг Київ-Львів") == "потяг Ки´їв-Львів"


def test_auto_falls_back_to_dictionary_without_stanza():
    # This is the default path for lightweight (--no-deps) installs
    # without stanza.  It only runs in an environment where stanza is
    # absent (e.g. the test-lite CI job).  The fallback must be visible
    # to the end user as a UserWarning.
    if importlib.util.find_spec('stanza') is not None:
        pytest.skip("stanza is installed; auto would select the stanza backend")
    with pytest.warns(UserWarning, match="Stanza is not installed"):
        stressify = Stressifier()
    assert stressify.disambiguation == Disambiguation.Dictionary
    assert stressify("Україна") == "Украї´на"


@pytest.mark.filterwarnings("error")
def test_explicit_dictionary_mode_does_not_warn():
    # Explicitly choosing dictionary mode is not a downgrade and must
    # stay silent (filterwarnings turns any warning into an error here).
    stressify = Stressifier(disambiguation=Disambiguation.Dictionary)
    assert stressify("Україна") == "Украї´на"


def test_none_is_dictionary_mode():
    stressify = Stressifier(disambiguation=None)
    assert stressify.disambiguation == Disambiguation.Dictionary
    assert stressify("Україна") == "Украї´на"


def test_heteronym_on_ambiguity_skip(stressify):
    # За´мок/замо´к cannot be resolved without POS context
    assert stressify("замок") == "замок"


def test_heteronym_on_ambiguity_first():
    stressify = Stressifier(disambiguation=Disambiguation.Dictionary,
                            on_ambiguity=OnAmbiguity.First)
    assert stressify("замок") == "за´мок"


def test_heteronym_on_ambiguity_all():
    stressify = Stressifier(disambiguation=Disambiguation.Dictionary,
                            on_ambiguity=OnAmbiguity.All)
    assert stressify("замок") == "за´мо´к"


def test_multi_record_word_with_agreeing_accents(stressify):
    # This word has multiple dictionary readings (differing in tags), but
    # all of them agree on the stress position.  It must be stressed even
    # without POS disambiguation.
    assert stressify("поперечно-циліндричний") != "поперечно-циліндричний"


def test_invalid_disambiguation_value():
    with pytest.raises(ValueError):
        Stressifier(disambiguation="bogus")


def test_cli_dictionary_mode():
    result = subprocess.run(
        [sys.executable, "-m", "ukrainian_word_stress.cli",
         "--disambiguation=dictionary"],
        input="Привіт, як справи?\n",
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "Приві´т, як спра´ви?\n"
