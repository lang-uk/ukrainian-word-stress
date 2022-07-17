import ua_gec
import time
from ukrainian_word_stress import Stressifier

"42306 parsed in 38.603643499998725 seconds (1095.9069187342743 tokens/sec)"


def benchmark():
    corpus = ua_gec.Corpus('test')
    text = '\n'.join([doc.target for doc in corpus])
    stressify = Stressifier()

    t0 = time.perf_counter()
    parsed = stressify.nlp(text)
    elapsed = time.perf_counter() - t0

    tokens = len(list(parsed.iter_tokens()))
    perf = tokens / elapsed
    print(f"{tokens} tokens parsed in {elapsed} seconds ({perf} tokens/sec)")

    t0 = time.perf_counter()
    stressify(text)
    elapsed = time.perf_counter() - t0
    perf = tokens / elapsed
    print(f"{tokens} tokens stressified in {elapsed} seconds ({perf} tokens/sec)")




if __name__ == "__main__":
    benchmark()
