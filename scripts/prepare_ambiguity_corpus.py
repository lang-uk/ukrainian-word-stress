import json
import ukrainian_word_stress.stressify_
import marisa_trie
import fileinput


def decompress_tags(tags):
    result = tags.decode().split("|")
    return result


def on_ambiguity(matches, parse):
    matches_for_report = []
    for tags, stress in matches:
        comment = [t for t in tags if t.startswith("comment=")][0].removeprefix(
            "comment="
        )
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
