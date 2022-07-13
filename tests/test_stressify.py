from ukrainian_stress import stressify, find_accent_positions, ACCENT
import marisa_trie
import pytest



@pytest.mark.skip()
def test_single_syllable():
    assert stressify("а") == "а"
    assert stressify("кіт") == "кіт"


@pytest.mark.skip()
def test_single_choice():
    assert stressify("Україна") == f"Украї{ACCENT}на"


def test_depends_on_tags():
    assert stressify("жодного яйця") == f"жодного яйця{ACCENT}"
    assert stressify("золоті яйця") == f"золоті я{ACCENT}йця"


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
    # сталеві яйця
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
    result.load("./stress.v1.trie")
    return result
