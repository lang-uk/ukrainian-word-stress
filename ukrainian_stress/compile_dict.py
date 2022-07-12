import marisa_trie
import csv
import collections
import tqdm


ACCENT = '\u0301'

def compile(csv_path: str) -> marisa_trie.BytesTrie:
    trie = []
    by_basic = _parse_dictionary(csv_path)
    for basic, forms in by_basic.items():
        accents_options = len(set(form for form, _ in forms))
        if accents_options == 1:
            value = accent_pos(forms[0][0])
        else:
            # TODO: compress multiple cases in a single record
            value = b''
            for form, tags in forms:
                pos = accent_pos(form)
                value += pos + b'^' + '|'.join(tags).encode() + b'$'
        trie.append((basic, value))
    return marisa_trie.BytesTrie(trie)


def _parse_dictionary(csv_path):
    by_basic = collections.defaultdict(list)  # TODO: change to set
    for row in tqdm.tqdm(csv.DictReader(open(csv_path))):
        form = row['form']
        basic = strip_accent(form)
        pos = parse_pos(row['type'])
        tags = parse_tags(row['tag'])
        tags.append(f'upos={pos}')
        by_basic[basic].append((form, tags))
    return by_basic


def strip_accent(s: str) -> str:
    return s.replace(ACCENT, "")


def parse_pos(s: str) -> str:
    mapping = {
        'іменник': "NOUN",
        'прикметник' : "ADJ",
        'вигук' : "INTJ",
        "сполучник": "CCONJ",
        "частка": "PART",
        "займенник": "PRON",
        "дієслово": "VERB",
        "прізвище": "PROPN",
        "власна назва": "PROPN",
        "прислівник": "ADV",
        "абревіатура": "NOUN",

        "сполука": "СПОЛУКА",
        "присудкове слово": "ПРИСУДКОВЕ СЛОВО",

        "числівник кількісний": "NumType=Card",

        "": "<None>",
    }

    for ukr, tag in mapping.items():
        if ukr in s:
            return tag

    raise ValueError(f"Can't parse POS string: {s}")


def parse_tags(s):
    mapping = {
        "однина": "Number=Sing",
        "множина": "Number=Plur",
        "називний": "Case=Nom",
        "родовий": "Case=Gen",
        "давальний": "Case=Dat",
        "знахідний": "Case=Acc",
        "орудний": "Case=Ins",
        "місцевий": "Case=Loc",
        "кличний": "Case=Voc",
        "чол. р.": "Gender=Masc",
        "жін. р.": "Gender=Fem",
        "сер. р.": "Gender=Neut",
        "Інфінітив": "VerbForm=Inf",
        "дієприслівник": "VerbForm=Conv",
        "пасивний дієприкметник": "",
        "активний дієприкметник": "",
        "безособова форма": "Person=0",
    }

    tags = []
    for ukr, tag in mapping.items():
        if ukr in s:
            tags.append(tag)

    if not tags and s:
        print(s)
        1/0
    return tags


def accent_pos(s: str) -> bytes:
    indexes = []
    pos = -1
    while True:
        pos = s.find(ACCENT, pos + 1)
        if pos == -1:
            break
        indexes.append(pos.to_bytes(1, 'little'))
    return b"".join(indexes)


if __name__ == "__main__":
    trie = compile("../ukrainian-word-stress-dictionary/ulif_accents.csv")
    trie.save("stress.trie")
