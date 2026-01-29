# Pretty Err

[![PyPI version](https://img.shields.io/pypi/v/prettyerr.svg)](https://pypi.org/project/prettyerr/)

A simple library for printing modern, source-annotated error messages.

## Features
- source span annotation
- color output
- multiple non-overlapping spans
- zero-width spans

## Install
```
pip install prettyerr
```

## Example

Say you have the following source code that contains an error
```python
def repeat(message: str, times: int) -> str:
    return message * times

result = repeat("hello", "3")
print(result)
```

A nice error message might look something like this
```
Error: type mismatch for argument `times`

    ╭─[path/to/py_example.py:4:10]
  4 | result = repeat("hello", "3")
    ·          ──┬───          ─┬─
    ·            │              ╰─ argument given is type 'str'
    ·            ╰─ `repeat` function's second argument `times` expects an 'int'
    ╰───
  help: Consider changing string literal "3" to integer 3
```

To render this error message:
```python
from prettyerr import Error, PointerMessage, Span, SrcFile

src = """\
def repeat(message: str, times: int) -> str:
    return message * times

result = repeat("hello", "3")
print(result)
"""

e = Error(
    SrcFile(py_src, "path/to/py_example.py"),
    title="type mismatch for argument `times`",
    pointer_messages=[
        PointerMessage(span=Span(82, 88), message="`repeat` function's second argument `times` expects an 'int'"),
        PointerMessage(span=Span(98, 101), message="argument given is type 'str'"),
    ],
    hint='Consider changing string literal "3" to integer 3',
)
print(e)
```




## Tasks
- [x] set up slaving to dewy-lang repo error.py
- [x] set up workflow to periodically check for changes to error.py (maybe once per week?)
    - [x] on change, create a PR using the newest version of the error.py
    - [x] run tests to make sure everything is still working
    - [x] if tests fail, note that in the PR (e.g. if I move error.py, the script would fail to pull it in, etc.)
    - [x] PR should assign me so that I know to deal with it
    - [ ] TBD if a previous PR hasn't been merged what to do, perhaps just let it make a new PR?
- [ ] improve README