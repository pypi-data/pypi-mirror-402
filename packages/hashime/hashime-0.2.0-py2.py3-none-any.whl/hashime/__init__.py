"""
Hash visualization tool inspired by beautiful ssh-keygen randomart.

Typical usage as CLI::

    $ hashime LICENSE
    +----[LICENSE]----+
    |    ..o +        |
    |   o E.= o       |
    |  o +.. o        |
    | . o o.o         |
    |.   o =.S.       |
    |..   o.+..+      |
    |o.  o.oo+..=     |
    |. . *+=..+o o .  |
    |  .=+O.++  . o.. |
    +-----[SHA256]----+

Typical usage in code::

    >>> import hashime
    >>> bishop = hashime.DrunkenBishop()
    >>> bishop.update_from_file_hash('./LICENSE')
    >>> art = bishop.to_art(top_text='LICENSE', bottom_text='SHA256')
    >>> print(art)
    +----[LICENSE]----+
    |    ..o +        |
    |   o E.= o       |
    |  o +.. o        |
    | . o o.o         |
    |.   o =.S.       |
    |..   o.+..+      |
    |o.  o.oo+..=     |
    |. . *+=..+o o .  |
    |  .=+O.++  . o.. |
    +-----[SHA256]----+
"""

from .drunken_bishop import DrunkenBishop

__all__ = ['DrunkenBishop']
