#!/usr/bin/env python3
"""Count skipped words in a test corpus.

Words can be skipped for a variety of reasons, including:

1. Word sense disambiguation required to put a stress.
2. Word not in the dictionary.
3. Word is the dictionary but lacks accent information.
4. Bugs.

Note that this script doesn't measure the correctness (precision)
of the stress placement, only the coverage (recall).

The corpus used is UA-GEC. Nothing special about it, just that it's
easily accessible from Python and is versioned.
"""

from ukrainian_word_stress import Stressifier
from ukrainian_word_stress.compile_dict import count_vowels
from collections import Counter
import ua_gec
import tqdm

def main():
    corpus = ua_gec.Corpus("test")
    stressify= Stressifier(stress_symbol="+")
    num_total_tokens = 0
    num_stressed_tokens = 0
    missed_tokens = Counter()
    for doc in (pbar := tqdm.tqdm(corpus)):
        for sentence in doc.target_sentences_tokenized:
            stressed = stressify(sentence)
            tokens = get_word_tokens(sentence)
            stressed_tokens = [t for t in get_word_tokens(stressed) if "+" in t]
            num_total_tokens += len(tokens)
            num_stressed_tokens += len(stressed_tokens)

            coverage = num_stressed_tokens / num_total_tokens
            pbar.set_postfix(coverage=f"{coverage:.2%}")

            missed = set(tokens) - {t.replace("+", "") for t in stressed_tokens}
            missed_tokens.update(missed)

    print("Top 50 missed tokens:")
    for token, count in missed_tokens.most_common(100):
        print(f"{token:<30}: {count}")
    print()

    print(f"Stressable tokens: {num_total_tokens}")
    print(f"Stressed tokens:   {num_stressed_tokens}")
    print(f"Missed tokens:     {num_total_tokens - num_stressed_tokens}")
    print(f"Coverage:          {num_stressed_tokens / num_total_tokens:.2%}")


def get_word_tokens(text):
    # Skip punctuation
    tokens = [t for t in text.split() if any(c.isalpha() for c in t)]

    # Skip words that don't require stress
    tokens = [t for t in tokens if count_vowels(t) > 1]

    return tokens

if __name__ == "__main__":
    main()
