#!/usr/bin/env python3
"""This script prepares a corpus of ambiguous words for manual stress correction.

The script reads a corpus of sentences from stdin and outputs a JSON file with
a list of ambiguous words and their possible stress patterns.

The script uses the stress-full.trie dictionary, which is a trie of all
possible stress patterns for all words in the Ukrainian dictionary.

Note, that we consider ambigous words only those that have more than one
possible stress pattern.

The script outputs a JSON-lines file with the following structure:

	{
	  "sentence": "Високий замок стояв на горі.",
	  "ambiguities": [
		{
		  "word": "замок",
		  "matches": [
			{
			  "comment": "будівля",
			  "tags": [
				"Number=Sing",
				"Case=Nom",
				"upos=NOUN",
				"Gender=Masc"
			  ],
			  "stress": [ 2 ]
			},
			{
			  "comment": "пристрій для замикання тощо",
			  "tags": [
				"Number=Sing",
				"Case=Nom",
				"upos=NOUN",
				"Gender=Masc"
			  ],
			  "stress": [ 4 ]
			}
		  ],
		  "parse": {
			"id": 2,
			"text": "замок",
			"upos": "NOUN",
			"xpos": "Ncmsnn",
			"feats": "Animacy=Inan|Case=Nom|Gender=Masc|Number=Sing",
			"start_char": 8,
			"end_char": 13
		  }
		}
	  ]
	}

"""



import json
import ukrainian_word_stress.stressify_
import marisa_trie
import fileinput


def decompress_tags(tags):
    result = tags.decode().split("|")
    return result


def on_ambiguity(matches, parse):
    unique_accents = len({repr(accents) for _, accents in matches})
    if unique_accents < 2:
        return matches[0][1]

    matches_for_report = []
    for tags, stress in matches:
        comment = [t for t in tags if t.startswith("comment=")]
        if comment:
            comment = comment[0].removeprefix("comment=")
        else:
            comment = ""
        excluded_tags = ("full=", "comment=")
        tags = [t for t in tags if not t.startswith(excluded_tags)]
        matches_for_report.append(
            {
                "comment": comment,
                "tags": tags,
                "stress": stress,
            }
        )
    report = {
        "word": parse["text"],
        "matches": matches_for_report,
        "parse": parse,
    }
    on_ambiguity.ambiguities.append(report)
    return matches[0][1]


def main():
    ukrainian_word_stress.stressify_.decompress_tags = decompress_tags
    stressifier = ukrainian_word_stress.stressify_.Stressifier(stress_symbol="+")
    stressifier.dict = marisa_trie.BytesTrie()
    stressifier.dict.load("./stress-full.trie")
    stressifier.on_ambiguity = on_ambiguity

    for line in fileinput.input():
        line = line.strip()
        if not line:
            continue

        stressifier.on_ambiguity.ambiguities = []
        stressifier(line)
        if stressifier.on_ambiguity.ambiguities:
            row = {
                    "sentence": line,
                    "ambiguities": stressifier.on_ambiguity.ambiguities,
                }
            print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    main()
