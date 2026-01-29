from contextlib import contextmanager

from .algorithm import Algorithm
from .util import bit_set_in_pos, clamp


class DrunkenBishop(Algorithm):
    """
    Drunken Bishop algorithm used in ssh-keygen.
    """

    def __init__(
        self,
        data: bytes | None = None,
        width: int = 17,
        height: int = 9,
        chars: str = ' .o+=*BOX@%&#/^SE',
    ) -> None:
        """
        Initializes a Drunken Bishop.

        Args:
            data: Input bytes.
            width: Width.
            height: Height.
            chars: Character set used to fill in the randomart.
        """
        self.width = width
        self.height = height
        self._start_x = width // 2
        self._start_y = height // 2
        self._chars = chars
        self._matrix = [[0 for _ in range(width)] for _ in range(height)]
        self._x = width // 2
        self._y = height // 2
        super().__init__(data)

    def __getitem__(self, key: tuple[int, int]) -> int:
        x, y = key
        return self._matrix[y][x]

    def __setitem__(self, key: tuple[int, int], value: int) -> None:
        x, y = key
        self._matrix[y][x] = value

    def update(self, data: bytes) -> None:
        for byte in data:
            for i in range(0, 8, 2):
                # * 2 - 1 converts 0 and 1 into -1 and 1
                x_off = bit_set_in_pos(byte, i) * 2 - 1
                y_off = bit_set_in_pos(byte, i + 1) * 2 - 1
                # not going off the edge of the matrix
                self._x = clamp(self._x + x_off, 0, self.width - 1)
                self._y = clamp(self._y + y_off, 0, self.height - 1)
                self[self._x, self._y] = clamp(
                    self[self._x, self._y] + 1, 0, len(self._chars) - 3
                )

    def _to_art(self) -> str:
        with self._temporary_override_start_and_end_values():
            art = '\n'.join(
                ''.join(
                    self._chars[clamp(x, 0, len(self._chars) - 1)] for x in row
                )
                for row in self._matrix
            )
            return art

    @contextmanager
    def _temporary_override_start_and_end_values(self):
        start_val = self[self._start_x, self._start_y]
        end_val = self[self._x, self._y]

        self[self._start_x, self._start_y] = len(self._chars) - 2
        self[self._x, self._y] = len(self._chars) - 1
        try:
            yield
        finally:
            self[self._start_x, self._start_y] = start_val
            self[self._x, self._y] = end_val
