from __future__ import annotations


class Rotor:
    """Represents a single Enigma rotor."""

    def __init__(
        self, wiring: str, notch: str, ring_setting: int = 0, position: str = "A"
    ) -> None:
        if len(wiring) != 26:
            raise ValueError("Rotor wiring must be 26 characters long.")

        self.wiring = wiring.upper()
        self.notch = notch.upper() if notch is not None else None
        self.ring_setting = ring_setting
        self.position = position.upper()

    @staticmethod
    def _char_to_index(char: str) -> int:
        return ord(char) - ord("A")

    @staticmethod
    def _index_to_char(index: int) -> str:
        return chr(ord("A") + index)

    def encode_forward(self, char: str) -> str:
        """Encode a character from right to left through the rotor."""
        c = char.upper()
        if not ("A" <= c <= "Z"):
            return c

        i = self._char_to_index(c)
        pos = self._char_to_index(self.position)
        ring = self.ring_setting

        shifted_in = (i + pos - ring) % 26
        wired_char = self.wiring[shifted_in]
        j = self._char_to_index(wired_char)

        shifted_out = (j - pos + ring) % 26
        return self._index_to_char(shifted_out)

    def encode_backward(self, char: str) -> str:
        """Encode a character from left to right through the rotor."""
        c = char.upper()
        if not ("A" <= c <= "Z"):
            return c

        i = self._char_to_index(c)
        pos = self._char_to_index(self.position)
        ring = self.ring_setting

        shifted_in = (i + pos - ring) % 26
        wired_index = self.wiring.index(self._index_to_char(shifted_in))

        shifted_out = (wired_index - pos + ring) % 26
        return self._index_to_char(shifted_out)

    def step(self) -> bool:
        """Advance the rotor by one position and return True if it is now at its notch."""
        index = (self._char_to_index(self.position) + 1) % 26
        self.position = self._index_to_char(index)

        if self.notch is None:
            return False

        return self.position == self.notch

    def at_notch(self) -> bool:
        if self.notch is None:
            return False
        return self.position == self.notch
