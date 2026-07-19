from __future__ import annotations


class MutableText:
    """Text that can be modified in-place."""

    def __init__(self, text: str) -> None:
        self._text = text
        self._edits: list[tuple[int, int, str]] = []

    def __str__(self) -> str:
        """Pretend to be a normal string. """
        return self.get_edited_text()

    def __repr__(self) -> str:
        return "<MutableText({})>".format(repr(str(self)))

    def replace(self, start: int, end: int, value: str) -> None:
        """Replace substring with a value.

        Example:
            >>> t = MutableText('the red fox')
            >>> t.replace(4, 7, 'brown')
            >>> t.get_edited_text()
            'the brown fox'
        """
        self._edits.append((start, end, value))  # TODO: keep _edits sorted?

    def apply_edits(self) -> None:
        """Applies all edits made so far. """

        self._text = self.get_edited_text()
        self._edits = []

    def get_source_text(self) -> str:
        """Return string without pending edits applied.

        Example:
            >>> t = MutableText('the red fox')
            >>> t.replace(4, 7, 'brown')
            >>> t.get_source_text()
            'the red fox'
        """
        return self._text

    def get_edited_text(self) -> str:
        """Return text with all corrections applied.

        Example::
            >>> t = MutableText('the red fox')
            >>> t.replace(4, 7, 'brown')
            >>> t.get_edited_text()
            'the brown fox'
        """

        result = []
        i = 0
        t = self._text
        for begin, end, val in sorted(self._edits, key=lambda x: (x[0], x[1])):
            result.append(t[i:begin])
            result.append(val)
            i = end
        result.append(t[i:])
        return "".join(result)
