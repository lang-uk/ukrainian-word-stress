from ukrainian_word_stress.compile_dict import parse_tags, accent_pos


def test_parse_tags():
    defn = "однина місцевий"
    assert parse_tags(defn) == ['Number=Sing', 'Case=Loc']


def test_accent_pos():
    assert accent_pos("по́ми́лка") == b'\x02\x04'
