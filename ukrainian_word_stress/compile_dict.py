import marisa_trie
import csv
import sys
import collections
import logging
import tqdm

from ukrainian_word_stress.tags import compress_tags


log = logging.getLogger(__name__)


ACCENT = '\u0301'
VOWELS = "уеіїаояиюєУЕІАОЯИЮЄЇ"

def compile(csv_path: str) -> marisa_trie.BytesTrie:
    trie = []
    by_basic = _parse_dictionary(csv_path)
    for basic, forms in by_basic.items():
        accents_options = len(set(form for form, _ in forms))
        if accents_options == 1:
            # no need to store tags if there's no ambiguity
            value = accent_pos(forms[0][0])
        else:
            value = b''
            for form, tags in forms:
                pos = accent_pos(form)
                value += pos + b'^' + compress_tags(tags) + b'$'
        trie.append((basic, value))
    return marisa_trie.BytesTrie(trie)


def _parse_dictionary(csv_path):
    by_basic = collections.defaultdict(list)  # TODO: change to set
    skipped = 0
    for row in tqdm.tqdm(csv.DictReader(open(csv_path))):
        form = row['form']
        if not validate_stress(form):
            log.debug("Skipping bad item: %s", form)
            skipped += 1
            continue

        basic = strip_accent(form)
        pos = parse_pos(row['type'])
        tags = parse_tags(row['tag'])
        tags.append(f'upos={pos}')
        by_basic[basic].append((form, tags))

    print(f"Skipped {skipped} bad word forms", file=sys.stderr)
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
    """Parse dictionary tags into a list of standard tags.

    Example::
        >>> parse_tags( "однина місцевий")
        ['Number=Sing', 'Case=Loc']
    """

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



def count_vowels(s):
    result = 0
    for x in VOWELS:
        result += s.count(x)
    return result


def validate_stress(word):
    good = True

    if count_vowels(word) < 2:
        return good

    pos = word.find(ACCENT)
    if pos <= 0:
        return not good

    elif word[pos - 1] not in VOWELS:
        return not good

    return good



if __name__ == "__main__":
    trie = compile("../ukrainian-word-stress-dictionary/ulif_accents.csv")
    trie.save("stress.trie")
