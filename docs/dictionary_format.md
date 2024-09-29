# Dictionary format

Dictionary is a marisa_trie.BytesTrie. It maps words as they are written
(without stress marks) to one or more possible stress positions along
with morphological info that helps to resolve ambiguity.

Key is a word without any stress marks (let's call it base).

Value is a byte string in one of the following formats.

Value format #1: Base word has only one possible accent position.

In this case, each byte in the value is a character position of a stressed vowels.
Most often, there will be only one, but more is also possible.
Example: b'\x02' means that the accent placed on the character with index 2.


Value format #2: Base word has multiple possible accent positions.

The format in this case is

```
    b'{entry_1}{entry_2}...{entry_N}'
```

where each entry is


```
    b'{pos}\xFE{compressed_tags}\xFF'
```

`compressed_tags` is a sequence of bytes, where each byte corresponds to
a morphological or POS tag (see `ukrainian_word_stress.tags.TAGS`)

`0xFE` and `0xFF` are one byte separators.

