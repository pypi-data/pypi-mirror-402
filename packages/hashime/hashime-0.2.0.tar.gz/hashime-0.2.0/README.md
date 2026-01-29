# hashime

[![CI](https://github.com/sakhezech/hashime/actions/workflows/ci.yaml/badge.svg)](https://github.com/sakhezech/hashime/actions/workflows/ci.yaml)

Hash visualization tool inspired by beautiful ssh-keygen randomart.

How can something so soulless be so pretty?

## Installation

From PyPI:

```sh
pip install hashime
```

From git:

```sh
pip install git+https://github.com/sakhezech/hashime
```

## Usage as CLI

`hashime ...` or `python -m hashime ...`

```console
$ hashime -h
usage: hashime [-h] [-v] [-l] [-a ALGO] [-H HASH] [--frame FRAME | --no-frame]
               [--top-text TOP_TEXT] [--bottom-text BOTTOM_TEXT]
               [-d [DIGEST_FORM]] [-o OUT]
               [file]

hash visualization tool

positional arguments:
  file                  input file (defaults to stdin)

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -l, --list            show visualization algorithms, hashing functions,
                        digest forms and exit
  -a ALGO, --algorithm ALGO
                        visualization algorithm (defaults to drunken_bishop)
  -H HASH, --hash-function HASH
                        hashing function (defaults to sha256)
  --frame FRAME         comma-separated frame characters in order of
                        (top_line, right_line, bottom_line, left_line,
                        top_left_corner, top_right_corner,
                        bottom_right_corner, bottom_left_corner, left_bracket,
                        right_bracket)
  --no-frame            output visualization without a frame
  --top-text TOP_TEXT   text on the top frame line
  --bottom-text BOTTOM_TEXT
                        text on the bottom frame line
  -d [DIGEST_FORM], --digest [DIGEST_FORM]
                        show digest (defaults to base64)
  -o OUT, --output OUT  output file (defaults to stdout)

$ hashime -H md5 -d base64 LICENSE
+----[LICENSE]----+
|                 |
|         .       |
|  . .   o        |
| . = o +         |
|  * * + S        |
| o O +           |
|  * = +          |
| . + = .         |
|    E .          |
+------[MD5]------+
md5: lGqJe4ZYqSXluPYkZOH/oQ==
```

## Usage in code

```py
>>> import hashime
>>> bishop = hashime.DrunkenBishop()
>>> bishop.update_from_file_hash('./LICENSE')
>>> art = bishop.to_art(
...     top_text='LICENSE',
...     bottom_text='SHA256',
...     brackets=('<', '>'),
...     lines=('═', '│', '─', '║'),
...     corners=('╔', '╕', '┘', '╙'),
... )
>>> print(art)
╔════<LICENSE>════╕
║    ..o +        │
║   o E.= o       │
║  o +.. o        │
║ . o o.o         │
║.   o =.S.       │
║..   o.+..+      │
║o.  o.oo+..=     │
║. . *+=..+o o .  │
║  .=+O.++  . o.. │
╙─────<SHA256>────┘
```

## Development

Use `ruff check --fix .` and `ruff format .` to check and format your code.

To get started:

```sh
git clone https://github.com/sakhezech/hashime
cd hashime
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```
