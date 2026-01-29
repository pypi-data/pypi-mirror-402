import hashlib
import io
import os
from abc import ABC, abstractmethod

StrOrBytesPathOrBufferedReader = (
    os.PathLike[str] | os.PathLike[bytes] | str | bytes | io.BufferedReader
)


class Algorithm(ABC):
    """
    Base class for algorithms.
    """

    def __init__(self, data: bytes | None = None) -> None:
        """
        Initializes an algorithm.

        Args:
            data: Input bytes.
        """
        if data is not None:
            self.update(data)

    @abstractmethod
    def update(self, data: bytes) -> None:
        """
        Feeds bytes into the algorithm.

        Args:
            data: Input bytes.
        """
        pass

    def update_from_file_hash(
        self,
        file: StrOrBytesPathOrBufferedReader,
        hash_function: str = 'sha256',
    ) -> None:
        """
        Feeds a file digest into the algorithm.

        Args:
            file: File path or readable stream.
            hash_function: Hash function.
        """
        if not isinstance(file, io.BufferedReader):
            file = open(file, 'rb')
        with file:
            digest = hashlib.file_digest(file, hash_function).digest()
            self.update(digest)

    def to_art(
        self,
        framed: bool = True,
        top_text: str | None = None,
        bottom_text: str | None = None,
        brackets: tuple[str, str] = ('[', ']'),
        lines: tuple[str, str, str, str] = ('-', '|', '-', '|'),
        corners: tuple[str, str, str, str] = ('+', '+', '+', '+'),
    ) -> str:
        """
        Generates randomart.

        Args:
            framed: Whether randomart should be framed.
            top_text: Text on the top line.
            bottom_text: Text on the bottom line.
            brackets: Symbols surrounding text.
            lines: Frame side symbols in a clockwise order from the top.
            corners: Frame corner symbols in a clockwise order from the top-left.

        Returns:
            Randomart.
        """  # noqa: E501
        art = self._to_art()

        if not framed:
            return art

        art_lines = art.split('\n')
        width = len(art_lines[0])

        # unpacking the values from tuples
        frame_t, frame_r, frame_b, frame_l = lines
        corner_tl, corner_tr, corner_br, corner_bl = corners

        br_len = len(brackets[0]) + len(brackets[1])
        if top_text is None:
            top_text = ''
        else:
            top_len = len(top_text) + br_len
            if top_len > width:
                top_text = top_text[: width - top_len - 3] + '...'
            top_text = top_text.join(brackets)

        if bottom_text is None:
            bottom_text = ''
        else:
            bot_len = len(bottom_text) + br_len
            if bot_len > width:
                bottom_text = bottom_text[: width - bot_len - 3] + '...'
            bottom_text = bottom_text.join(brackets)

        top_line = top_text.center(width, frame_t).join((corner_tl, corner_tr))
        bot_line = bottom_text.center(width, frame_b).join(
            (corner_bl, corner_br)
        )
        content = '\n'.join(f'{frame_l}{line}{frame_r}' for line in art_lines)
        art = '\n'.join((top_line, content, bot_line))
        return art

    @abstractmethod
    def _to_art(self) -> str:
        pass
