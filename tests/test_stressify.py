from ukrainian_stress import stressify


def test_single_syllable():
    assert stressify("а") == "а"
    assert stressify("кіт") == "кіт"


def test_single_choice():
    assert stressify("Україна") == "Украї'на"
