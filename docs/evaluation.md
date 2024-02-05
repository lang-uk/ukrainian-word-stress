# Evaluation and metrics

There are no evaluation datasets/metrics for measuring *correctness*.

We measure *coverage* (recall) by stressifying some large body of text and counting
missed tokens.

Specifically, we use the test split of [UA-GEC](https://github.com/grammarly/ua-gec)
as a source text. We compute

```
coverage = num_stressed_tokens / num_stressifiable_tokens
```

where

* `num_stressed_tokens` is the number of tokens for which we placed stress
  (not necessarily in the correct place)

* `num_stressifiable_tokens` is the number of tokens in the text for which it
  makes sense to put stress. This is different from the total number of tokens
  since we skip punctuation and single-syllable words.


## Results

| Version | Coverage |
|---------|----------|
|1.2.0    | 92.75%   |
|1.1.0    | 92.07%   |

See [./docs/stats.txt](./docs/stats.txt) and
[./scripts/compute_coverage.py](./scripts/compute_coverage.py) for more details.
