from ukrainian_stress import stressify, get_accent_positions, ACCENT
import marisa_trie
import pytest



def test_single_syllable():
    assert stressify("а") == "а"
    assert stressify("кіт") == "кіт"


def test_single_choice():
    assert stressify("Україна") == f"Украї{ACCENT}на"


def test_get_accent_positions(trie):
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
    assert get_accent_positions(trie, parse) == expected


@pytest.fixture(scope='module')
def trie():
    result = marisa_trie.BytesTrie()
    result.load("./stress.v1.trie")
    return result
