from ukrainian_word_stress import find_accent_positions, Stressifier, OnAmbiguity
import marisa_trie
import pytest



def test_single_syllable(stressify):
    assert stressify("а") == "а"
    assert stressify("кіт") == "кіт"


def test_single_choice(stressify):
    assert stressify("Україна") == "Украї´на"


def test_depends_on_tags(stressify):
    assert stressify("жодного яйця") == "жо´дного яйця´"
    assert stressify("сталеві яйця") == "стале´ві я´йця"


def test_ignore_case(stressify):
    assert stressify("мама") == "ма´ма"
    assert stressify("Мама") == "Ма´ма"
    assert stressify("МАМА") == "МА´МА"


def test_preserve_whitespace_and_punctuation(stressify):
    assert stressify(" Привіт ,  як справи ?") == " Приві´т ,  як спра´ви ?"


def test_on_ambiguity_skip():
    stressify = Stressifier(on_ambiguity=OnAmbiguity.Skip)
    assert stressify("замок") == "замок"


def test_on_ambiguity_first_option():
    stressify = Stressifier(on_ambiguity=OnAmbiguity.First)
    assert stressify("замок") == "за´мок"


def test_on_ambiguity_all():
    stressify = Stressifier(on_ambiguity=OnAmbiguity.All)
    assert stressify("замок") == "за´мо´к"


def test_no_ambiguity_multiple_meanings():
    # Word "голови" may have different meanings and tags.
    # However, they all share the same stress positions, so
    # that's not an ambiguity for our purpuses
    stressify = Stressifier(on_ambiguity=OnAmbiguity.Skip)
    assert stressify("рух голови") == "рух голови´"


def test_regression_splitter():
    # This is a regression test.
    stressify = Stressifier(on_ambiguity=OnAmbiguity.All)
    assert stressify("веселим") == "весе´лим"


def test_find_accent_positions_single(trie):
    parse = {
        "id": 1,
        "text": "Україна",
        "lemma": "Україна",
        "upos": "PROPN",
        "xpos": "Npfsnn",
        "feats": "Animacy=Inan|Case=Nom|Gender=Fem|Number=Sing",
        "head": 0,
        "deprel": "root",
        "start_char": 0,
        "end_char": 7,
        "ner": "S-LOC",
        "multi_ner": [
            "S-LOC"
        ]
    }
    expected = [5]
    assert find_accent_positions(trie, parse) == expected


def test_find_accent_positions_mulitple(trie):

    # The word "яйця" that can have multiple stress positions,
    # depending on whether it's used in a singular or plural form.
    #
    # find_accent_positions() should find the correct dictionary
    # entry based on parse features.

    # 1. Plural (as in "сталеві яйця")
    parse = {
        "id": 1,
        "text": "яйця",
        "upos": "NOUN",
        "xpos": "Ncnpnn",
        "feats": "Animacy=Inan|Case=Nom|Gender=Neut|Number=Plur",
        "start_char": 0,
        "end_char": 4
    }
    expected = [1]
    assert find_accent_positions(trie, parse) == expected

    # 2. Singular genetive (as in "жодного яйця")
    parse = {
        "id": 1,
        "text": "яйця",
        "upos": "NOUN",
        "xpos": "Ncnpnn",
        "feats": "Animacy=Inan|Case=Gen|Gender=Neut|Number=Sing",
        "start_char": 0,
        "end_char": 4
    }
    expected = [4]
    assert find_accent_positions(trie, parse) == expected


@pytest.fixture(scope='module')
def trie():
    result = marisa_trie.BytesTrie()
    result.load("./ukrainian_word_stress/data/stress.trie")
    return result


@pytest.fixture(scope='module')
def stressify():
    return Stressifier()
