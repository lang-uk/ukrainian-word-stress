from ukrainian_stress import stressify, find_accent_positions, ACCENT
import marisa_trie
import pytest



def test_single_syllable():
    assert stressify("а") == "а"
    assert stressify("кіт") == "кіт"


def test_single_choice():
    assert stressify("Україна") == f"Украї´на"


def test_depends_on_tags():
    assert stressify("жодного яйця") == f"жо´дного яйця´"
    assert stressify("сталеві яйця") == f"стале´ві я´йця"


def test_ignore_case():
    assert stressify("мама") == f"ма´ма"
    assert stressify("Мама") == f"Ма´ма"
    assert stressify("МАМА") == f"МА´МА"


def test_preserve_whitespace_and_punctuation():
    assert stressify(" Привіт ,  як справи ?") == " Приві´т ,  як спра´ви ?"



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
    result.load("./stress.v2.trie")
    return result
