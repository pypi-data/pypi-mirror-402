from __future__ import annotations

from textwrap import dedent

from prettyerr import Error, Pointer, Span, SrcFile

print_src = "printl'Hello, World'"
print_sf = SrcFile.from_text(print_src, "path/to/file.dewy")

tight_src = "10x(y)"
tight_sf = SrcFile.from_text(tight_src, "path/to/file.dewy")

multi_src = "10x(y)\n* 42 + 3^x"
multi_sf = SrcFile.from_text(multi_src, "path/to/file.dewy")

triple_tight_src = "[a]5x(y)"
triple_tight_sf = SrcFile.from_text(triple_tight_src, "path/to/file.dewy")

tri_src = "alpha beta\ngamma + delta\nepsilon & zeta"
tri_sf = SrcFile.from_text(tri_src, "path/to/file.dewy")

multiline_block_src = "block start {\n  inner stuff\n} block end"
multiline_block_sf = SrcFile.from_text(multiline_block_src, "path/to/block.dewy")
full_span = Span(0, len(multiline_block_src))

long_src = dedent(
    """\
    step 01: fetch inputs
    step 02: decode config
    step 03: allocate buffers
    step 04: parse stream
    step 05: transform blocks
    step 06: stage outputs
    step 07: compute checksum
    step 08: sign payload
    step 09: finalize partial sum
    step 10: verify outputs
    step 11: cleanup temp files
    step 12: shutdown services
"""
)
long_sf = SrcFile.from_text(long_src, "path/to/long_example.dewy")


def span_cols(line_no: int, start: int, stop: int) -> Span:
    base = long_sf._line_starts[line_no - 1]
    return Span(base + start, base + stop)


def span_text(line_no: int, snippet: str) -> Span:
    row = line_no - 1
    line_text = long_sf.line_text(row)
    offset = line_text.index(snippet)
    return span_cols(line_no, offset, offset + len(snippet))


py_src = dedent(
    """\
    def repeat(message: str, times: int) -> str:
        return message * times

    result = repeat(\"hello\", \"3\")
    print(result)
"""
)
py_sf = SrcFile.from_text(py_src, "path/to/py_example.py")


def _error_unable_to_juxtapose(use_color: bool) -> Error:
    return Error(
        srcfile=print_sf,
        title="dewy.errors.E1234 (link)",
        message="Unable to juxtapose identifier and string",
        pointer_messages=[
            Pointer(
                span=Span(6, 6),
                message="tried to juxtapose printl (string:>void) and 'Hello, World' (string)\nexpected whitespace or operator between identifier and string",
            ),
        ],
        hint="insert a space or an operator",
        use_color=use_color,
    )


def _error_token_needs_context(use_color: bool) -> Error:
    return Error(
        srcfile=print_sf,
        title="dewy.errors.E2234 (link)",
        message="Token needs additional context",
        pointer_messages=[
            Pointer(
                span=Span(0, 6),
                message="<per token message>",
            ),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_highlight_multiple_tokens(use_color: bool) -> Error:
    return Error(
        srcfile=print_sf,
        title="dewy.errors.E2234 (link)",
        message="Highlight multiple adjacent tokens",
        pointer_messages=[
            Pointer(span=Span(0, 6), message="<message about the identifier token>"),
            Pointer(span=Span(6, 6), message="<message about the juxtapose token>"),
            Pointer(span=Span(6, len(print_src)), message="<message about the string token>"),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_dealing_with_tightly_packed(use_color: bool) -> Error:
    return Error(
        srcfile=tight_sf,
        title="dewy.errors.E3234 (link)",
        message="Dealing with tightly packed tokens",
        pointer_messages=[
            Pointer(span=Span(0, 2), message="<message about the `10` token>"),
            Pointer(span=Span(2, 3), message="<message about the `x` token>"),
            Pointer(span=Span(3, 4), message="<message about the `(` token>"),
            Pointer(span=Span(4, 5), message="<message about the `y` token>"),
            Pointer(span=Span(5, 6), message="<message about the `)` token>"),
            Pointer(span=Span(2, 2), message="<message about the 10x juxtaposition>"),
            Pointer(span=Span(3, 3), message="<message about the x(y) juxtaposition>"),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_flipping_pointer_directions(use_color: bool) -> Error:
    return Error(
        srcfile=tight_sf,
        title="dewy.errors.E3234 (link)",
        message="Flipping pointer directions",
        pointer_messages=[
            Pointer(span=Span(2, 2), message="<message about the 10x juxtaposition>"),
            Pointer(span=Span(3, 3), message="<message about the x(y) juxtaposition>"),
            Pointer(span=Span(0, 2), message="<message about the `10` token>"),
            Pointer(span=Span(2, 3), message="<message about the `x` token>"),
            Pointer(span=Span(3, 4), message="<message about the `(` token>"),
            Pointer(span=Span(4, 5), message="<message about the `y` token>"),
            Pointer(span=Span(5, 6), message="<message about the `)` token>"),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_multi_line_expression_pointers(use_color: bool) -> Error:
    pointer_messages = [
        Pointer(span=Span(2, 2), message="<message about the 10x juxtaposition>"),
        Pointer(span=Span(3, 3), message="<message about the x(y) juxtaposition>"),
        Pointer(span=Span(0, 2), message="<message about the `10` token>"),
        Pointer(span=Span(2, 3), message="<message about the `x` token>"),
        Pointer(span=Span(3, 4), message="<message about the `(` token>"),
        Pointer(span=Span(4, 5), message="<message about the `y` token>"),
        Pointer(span=Span(5, 6), message="<message about the `)` token>"),
        Pointer(span=Span(7, 8), message="<message about the `*` token>"),
        Pointer(span=Span(9, 11), message="<message about the `42` token>"),
        Pointer(span=Span(12, 13), message="<message about the `+` token>"),
        Pointer(span=Span(14, 15), message="<message about the `3` token>"),
        Pointer(span=Span(15, 16), message="<message about the `^` token>"),
        Pointer(span=Span(16, 17), message="<message about the `x` token>"),
    ]
    return Error(
        srcfile=multi_sf,
        title="dewy.errors.E3234 (link)",
        message="Multi-line expression pointers",
        pointer_messages=pointer_messages,
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_upper_above_lower_below(use_color: bool) -> Error:
    return Error(
        srcfile=multi_sf,
        title="dewy.errors.E3234 (link)",
        message="Upper line pointers above, lower line below",
        pointer_messages=[
            Pointer(span=Span(0, 2), message="<message about the `10` token>"),
            Pointer(span=Span(2, 3), message="<message about the `x` token>"),
            Pointer(span=Span(3, 4), message="<message about the `(` token>"),
            Pointer(span=Span(4, 5), message="<message about the `y` token>"),
            Pointer(span=Span(5, 6), message="<message about the `)` token>"),
            Pointer(span=Span(7, 8), message="<message about the `*` token>"),
            Pointer(span=Span(9, 11), message="<message about the `42` token>"),
            Pointer(span=Span(12, 13), message="<message about the `+` token>"),
            Pointer(span=Span(14, 15), message="<message about the `3` token>"),
            Pointer(span=Span(15, 16), message="<message about the `^` token>"),
            Pointer(span=Span(16, 17), message="<message about the `x` token>"),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_triple_tightly_packed(use_color: bool) -> Error:
    return Error(
        srcfile=triple_tight_sf,
        title="dewy.errors.E3234 (link)",
        message="Triple tightly packed tokens",
        pointer_messages=[
            Pointer(span=Span(0, 1), message="<message about the `[` token>"),
            Pointer(span=Span(1, 2), message="<message about the `a` token>"),
            Pointer(span=Span(2, 3), message="<message about the `]` token>"),
            Pointer(span=Span(3, 4), message="<message about the `5` token>"),
            Pointer(span=Span(4, 5), message="<message about the `x` token>"),
            Pointer(span=Span(5, 6), message="<message about the `(` token>"),
            Pointer(span=Span(6, 7), message="<message about the `y` token>"),
            Pointer(span=Span(7, 8), message="<message about the `)` token>"),
            Pointer(span=Span(3, 3), message="<message about the `[a]5` juxtaposition>"),
            Pointer(span=Span(4, 4), message="<message about the `5x` juxtaposition>"),
            Pointer(span=Span(5, 5), message="<message about the `x(y)` juxtaposition>"),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_unpositioned_triple_tightly_packed(use_color: bool) -> Error:
    return Error(
        srcfile=triple_tight_sf,
        title="dewy.errors.E3234 (link)",
        message="Unpositioned triple tightly packed tokens",
        pointer_messages=[
            Pointer(span=Span(0, 1), message="<message about the `[` token>"),
            Pointer(span=Span(1, 2), message="<message about the `a` token>"),
            Pointer(span=Span(2, 3), message="<message about the `]` token>"),
            Pointer(span=Span(3, 4), message="<message about the `5` token>"),
            Pointer(span=Span(4, 5), message="<message about the `x` token>"),
            Pointer(span=Span(5, 6), message="<message about the `(` token>"),
            Pointer(span=Span(6, 7), message="<message about the `y` token>"),
            Pointer(span=Span(7, 8), message="<message about the `)` token>"),
            Pointer(span=Span(3, 3), message="<message about the `[a]5` juxtaposition>"),
            Pointer(span=Span(4, 4), message="<message about the `5x` juxtaposition>"),
            Pointer(span=Span(5, 5), message="<message about the `x(y)` juxtaposition>"),
        ],
        hint="<some helpful hint>",
        use_color=use_color,
    )


def _error_three_line_spanning(use_color: bool) -> Error:
    tri_pointers = [
        Pointer(span=Span(0, 5), message="<message about alpha>"),
        Pointer(span=Span(6, 10), message="<message about beta>"),
        Pointer(span=Span(11, 16), message="<message about gamma>"),
        Pointer(span=Span(17, 18), message="<message about `+`>"),
        Pointer(span=Span(19, 24), message="<message about delta>"),
        Pointer(span=Span(25, 32), message="<message about epsilon>"),
        Pointer(span=Span(33, 34), message="<message about `&`>"),
        Pointer(span=Span(35, 39), message="<message about zeta>"),
    ]
    return Error(
        srcfile=tri_sf,
        title="dewy.errors.E4000 (link)",
        message="Three-line spanning diagnostic",
        pointer_messages=tri_pointers,
        hint="defaults to showing all markers below for 3+ lines",
        use_color=use_color,
    )


def _error_multiline_span_pointer(use_color: bool) -> Error:
    return Error(
        srcfile=multiline_block_sf,
        title="dewy.errors.E6000 (link)",
        message="Illustrate multi-line span pointer",
        pointer_messages=[
            Pointer(span=full_span, message="<message covering the entire block>"),
        ],
        hint="multi-line spans draw a single pointer after the block",
        use_color=use_color,
    )


def _error_multidigit_line_numbers(use_color: bool) -> Error:
    return Error(
        srcfile=long_sf,
        title="dewy.errors.E5000 (link)",
        message="Demonstrate multi-digit line numbers",
        pointer_messages=[
            Pointer(span=span_text(9, "finalize"), message="<message on line 9>"),
            Pointer(span=span_text(10, "verify outputs"), message="<message on line 10>"),
            Pointer(span=span_text(12, "shutdown services"), message="<message on line 12>"),
        ],
        hint="line numbers stay aligned even after 9",
        use_color=use_color,
    )


def _error_type_mismatch_times(use_color: bool) -> Error:
    return Error(
        srcfile=py_sf,
        title="type mismatch for argument `times`",
        pointer_messages=[
            Pointer(span=Span(82, 88), message="`repeat` function's second argument `times` expects an 'int'"),
            Pointer(span=Span(98, 101), message="argument given is type 'str'"),
        ],
        hint='Consider changing string literal "3" to integer 3',
        use_color=use_color,
    )


EXPECTED_PLAIN = {
  'DEALING_WITH_TIGHTLY_PACKED': '''Error: dewy.errors.E3234 (link)

  × Dealing with tightly packed tokens
    ╭─[path/to/file.dewy:1:1]
    ·  ╭─ <message about the 10x juxtaposition>
    ·  │╭─ <message about the x(y) juxtaposition>
    ·  ╲╳╱
  1 | 10x(y)
    · ┬─┬┬┬┬
    · │ │││╰─ <message about the `)` token>
    · │ ││╰─ <message about the `y` token>
    · │ │╰─ <message about the `(` token>
    · │ ╰─ <message about the `x` token>
    · ╰─ <message about the `10` token>
    ╰───
  help: <some helpful hint>''',
    'FLIPPING_POINTER_DIRECTIONS': '''Error: dewy.errors.E3234 (link)

  × Flipping pointer directions
    ╭─[path/to/file.dewy:1:1]
    ·  ╭─ <message about the 10x juxtaposition>
    ·  │╭─ <message about the x(y) juxtaposition>
    ·  ╲╳╱
  1 | 10x(y)
    · ┬─┬┬┬┬
    · │ │││╰─ <message about the `)` token>
    · │ ││╰─ <message about the `y` token>
    · │ │╰─ <message about the `(` token>
    · │ ╰─ <message about the `x` token>
    · ╰─ <message about the `10` token>
    ╰───
  help: <some helpful hint>''',
    'HIGHLIGHT_MULTIPLE_TOKENS': '''Error: dewy.errors.E2234 (link)

  × Highlight multiple adjacent tokens
    ╭─[path/to/file.dewy:1:1]
  1 | printl'Hello, World'
    · ──┬──╱╲─────┬───────
    ·   │  │      ╰─ <message about the string token>
    ·   │  ╰─ <message about the juxtapose token>
    ·   ╰─ <message about the identifier token>
    ╰───
  help: <some helpful hint>''',
    'MULTIDIGIT_LINE_NUMBERS': '''Error: dewy.errors.E5000 (link)

  × Demonstrate multi-digit line numbers
     ╭─[path/to/long_example.dewy:9:10]
     ·             ╭─ <message on line 9>
     ·          ───┴────
   9 | step 09: finalize partial sum
  10 | step 10: verify outputs
     ·          ──────┬───────
     ·                ╰─ <message on line 10>
  11 | step 11: cleanup temp files
  12 | step 12: shutdown services
     ·          ────────┬────────
     ·                  ╰─ <message on line 12>
     ╰───
  help: line numbers stay aligned even after 9''',
    'MULTILINE_SPAN_POINTER': '''Error: dewy.errors.E6000 (link)

  × Illustrate multi-line span pointer
    ╭─[path/to/block.dewy:1:1]
  1 | block start {
    · ─────────────
  2 |   inner stuff
    · ─────────────
  3 | } block end
    · ─────┬─────
    ·      ╰─ <message covering the entire block>
    ╰───
  help: multi-line spans draw a single pointer after the block''',
    'MULTI_LINE_EXPRESSION_POINTERS': '''Error: dewy.errors.E3234 (link)

  × Multi-line expression pointers
    ╭─[path/to/file.dewy:1:1]
    ·  ╭─ <message about the 10x juxtaposition>
    ·  │╭─ <message about the x(y) juxtaposition>
    ·  ╲╳╱
  1 | 10x(y)
    · ┬─┬┬┬┬
    · │ │││╰─ <message about the `)` token>
    · │ ││╰─ <message about the `y` token>
    · │ │╰─ <message about the `(` token>
    · │ ╰─ <message about the `x` token>
    · ╰─ <message about the `10` token>
  2 | * 42 + 3^x
    · ┬ ┬─ ┬ ┬┬┬
    · │ │  │ ││╰─ <message about the `x` token>
    · │ │  │ │╰─ <message about the `^` token>
    · │ │  │ ╰─ <message about the `3` token>
    · │ │  ╰─ <message about the `+` token>
    · │ ╰─ <message about the `42` token>
    · ╰─ <message about the `*` token>
    ╰───
  help: <some helpful hint>''',
    'THREE_LINE_SPANNING': '''Error: dewy.errors.E4000 (link)

  × Three-line spanning diagnostic
    ╭─[path/to/file.dewy:1:1]
    ·   ╭─ <message about alpha>
    ·   │    ╭─ <message about beta>
    · ──┴── ─┴──
  1 | alpha beta
  2 | gamma + delta
    · ──┬── ┬ ──┬──
    ·   │   │   ╰─ <message about delta>
    ·   │   ╰─ <message about `+`>
    ·   ╰─ <message about gamma>
  3 | epsilon & zeta
    · ───┬─── ┬ ─┬──
    ·    │    │  ╰─ <message about zeta>
    ·    │    ╰─ <message about `&`>
    ·    ╰─ <message about epsilon>
    ╰───
  help: defaults to showing all markers below for 3+ lines''',
    'TOKEN_NEEDS_CONTEXT': '''Error: dewy.errors.E2234 (link)

  × Token needs additional context
    ╭─[path/to/file.dewy:1:1]
  1 | printl'Hello, World'
    · ──┬───
    ·   ╰─ <per token message>
    ╰───
  help: <some helpful hint>''',
    'TRIPLE_TIGHTLY_PACKED': '''Error: dewy.errors.E3234 (link)

  × Triple tightly packed tokens
    ╭─[path/to/file.dewy:1:1]
    ·   ╭─ <message about the `[a]5` juxtaposition>
    ·   │╭─ <message about the `5x` juxtaposition>
    ·   ││╭─ <message about the `x(y)` juxtaposition>
    ·   ╲╳╳╱
  1 | [a]5x(y)
    · ┬┬┬┬┬┬┬┬
    · │││││││╰─ <message about the `)` token>
    · ││││││╰─ <message about the `y` token>
    · │││││╰─ <message about the `(` token>
    · ││││╰─ <message about the `x` token>
    · │││╰─ <message about the `5` token>
    · ││╰─ <message about the `]` token>
    · │╰─ <message about the `a` token>
    · ╰─ <message about the `[` token>
    ╰───
  help: <some helpful hint>''',
    'TYPE_MISMATCH_TIMES': '''Error: type mismatch for argument `times`

    ╭─[path/to/py_example.py:4:10]
  4 | result = repeat("hello", "3")
    ·          ──┬───          ─┬─
    ·            │              ╰─ argument given is type 'str'
    ·            ╰─ `repeat` function's second argument `times` expects an 'int'
    ╰───
  help: Consider changing string literal "3" to integer 3''',
    'UNABLE_TO_JUXTAPOSE': '''Error: dewy.errors.E1234 (link)

  × Unable to juxtapose identifier and string
    ╭─[path/to/file.dewy:1:7]
  1 | printl'Hello, World'
    ·      ╱╲
    ·      ╰─ tried to juxtapose printl (string:>void) and 'Hello, World' (string)
    ·         expected whitespace or operator between identifier and string
    ╰───
  help: insert a space or an operator''',
    'UNPOSITIONED_TRIPLE_TIGHTLY_PACKED': '''Error: dewy.errors.E3234 (link)

  × Unpositioned triple tightly packed tokens
    ╭─[path/to/file.dewy:1:1]
    ·   ╭─ <message about the `[a]5` juxtaposition>
    ·   │╭─ <message about the `5x` juxtaposition>
    ·   ││╭─ <message about the `x(y)` juxtaposition>
    ·   ╲╳╳╱
  1 | [a]5x(y)
    · ┬┬┬┬┬┬┬┬
    · │││││││╰─ <message about the `)` token>
    · ││││││╰─ <message about the `y` token>
    · │││││╰─ <message about the `(` token>
    · ││││╰─ <message about the `x` token>
    · │││╰─ <message about the `5` token>
    · ││╰─ <message about the `]` token>
    · │╰─ <message about the `a` token>
    · ╰─ <message about the `[` token>
    ╰───
  help: <some helpful hint>''',
    'UPPER_ABOVE_LOWER_BELOW': '''Error: dewy.errors.E3234 (link)

  × Upper line pointers above, lower line below
    ╭─[path/to/file.dewy:1:1]
    · ╭─ <message about the `10` token>
    · │ ╭─ <message about the `x` token>
    · │ │╭─ <message about the `(` token>
    · │ ││╭─ <message about the `y` token>
    · │ │││╭─ <message about the `)` token>
    · ┴─┴┴┴┴
  1 | 10x(y)
  2 | * 42 + 3^x
    · ┬ ┬─ ┬ ┬┬┬
    · │ │  │ ││╰─ <message about the `x` token>
    · │ │  │ │╰─ <message about the `^` token>
    · │ │  │ ╰─ <message about the `3` token>
    · │ │  ╰─ <message about the `+` token>
    · │ ╰─ <message about the `42` token>
    · ╰─ <message about the `*` token>
    ╰───
  help: <some helpful hint>''',
}


EXPECTED_COLOR = {
    'DEALING_WITH_TIGHTLY_PACKED': 'Error: \x1b[31mdewy.errors.E3234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Dealing with tightly packed tokens\n    ╭─[path/to/file.dewy:1:1]\n    ·  \x1b[38;5;211m╭\x1b[0m\x1b[38;5;211m─ <message about the 10x juxtaposition>\x1b[0m\n    ·  \x1b[38;5;211m│\x1b[0m\x1b[38;5;214m╭\x1b[0m\x1b[38;5;214m─ <message about the x(y) juxtaposition>\x1b[0m\n    ·  \x1b[38;5;211m╲\x1b[0m\x1b[38;5;214m╳\x1b[0m\x1b[38;5;214m╱\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | 10x(y)\n    · \x1b[96m┬\x1b[0m\x1b[96m─\x1b[0m\x1b[92m┬\x1b[0m\x1b[93m┬\x1b[0m\x1b[94m┬\x1b[0m\x1b[38;5;135m┬\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about the `)` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╰\x1b[0m\x1b[94m─ <message about the `y` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m╰\x1b[0m\x1b[93m─ <message about the `(` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m╰\x1b[0m\x1b[92m─ <message about the `x` token>\x1b[0m\n    · \x1b[96m╰\x1b[0m\x1b[96m─ <message about the `10` token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>',
    'FLIPPING_POINTER_DIRECTIONS': 'Error: \x1b[31mdewy.errors.E3234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Flipping pointer directions\n    ╭─[path/to/file.dewy:1:1]\n    ·  \x1b[96m╭\x1b[0m\x1b[96m─ <message about the 10x juxtaposition>\x1b[0m\n    ·  \x1b[96m│\x1b[0m\x1b[92m╭\x1b[0m\x1b[92m─ <message about the x(y) juxtaposition>\x1b[0m\n    ·  \x1b[96m╲\x1b[0m\x1b[92m╳\x1b[0m\x1b[92m╱\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | 10x(y)\n    · \x1b[93m┬\x1b[0m\x1b[93m─\x1b[0m\x1b[94m┬\x1b[0m\x1b[38;5;135m┬\x1b[0m\x1b[38;5;211m┬\x1b[0m\x1b[38;5;214m┬\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m│\x1b[0m\x1b[38;5;214m╰\x1b[0m\x1b[38;5;214m─ <message about the `)` token>\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about the `y` token>\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about the `(` token>\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m╰\x1b[0m\x1b[94m─ <message about the `x` token>\x1b[0m\n    · \x1b[93m╰\x1b[0m\x1b[93m─ <message about the `10` token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>',
    'HIGHLIGHT_MULTIPLE_TOKENS': "Error: \x1b[31mdewy.errors.E2234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Highlight multiple adjacent tokens\n    ╭─[path/to/file.dewy:1:1]\n  \x1b[38;5;245m1\x1b[0m | printl'Hello, World'\n    · \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m┬\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[92m╱\x1b[0m\x1b[92m╲\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m┬\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\n    ·   \x1b[96m│\x1b[0m  \x1b[92m│\x1b[0m      \x1b[93m╰\x1b[0m\x1b[93m─ <message about the string token>\x1b[0m\n    ·   \x1b[96m│\x1b[0m  \x1b[92m╰\x1b[0m\x1b[92m─ <message about the juxtapose token>\x1b[0m\n    ·   \x1b[96m╰\x1b[0m\x1b[96m─ <message about the identifier token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>",
    'MULTIDIGIT_LINE_NUMBERS': 'Error: \x1b[31mdewy.errors.E5000 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Demonstrate multi-digit line numbers\n     ╭─[path/to/long_example.dewy:9:10]\n     ·             \x1b[96m╭\x1b[0m\x1b[96m─ <message on line 9>\x1b[0m\n     ·          \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m┴\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\n  \x1b[38;5;245m 9\x1b[0m | step 09: finalize partial sum\n  \x1b[38;5;245m10\x1b[0m | step 10: verify outputs\n     ·          \x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m┬\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\n     ·                \x1b[92m╰\x1b[0m\x1b[92m─ <message on line 10>\x1b[0m\n  \x1b[38;5;245m11\x1b[0m | step 11: cleanup temp files\n  \x1b[38;5;245m12\x1b[0m | step 12: shutdown services\n     ·          \x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m┬\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\n     ·                  \x1b[93m╰\x1b[0m\x1b[93m─ <message on line 12>\x1b[0m\n     ╰───\n  \x1b[38;5;245mhelp:\x1b[0m line numbers stay aligned even after 9',
    'MULTILINE_SPAN_POINTER': 'Error: \x1b[31mdewy.errors.E6000 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Illustrate multi-line span pointer\n    ╭─[path/to/block.dewy:1:1]\n  \x1b[38;5;245m1\x1b[0m | block start {\n    · \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\n  \x1b[38;5;245m2\x1b[0m |   inner stuff\n    · \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\n  \x1b[38;5;245m3\x1b[0m | } block end\n    · \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m┬\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\n    ·      \x1b[96m╰\x1b[0m\x1b[96m─ <message covering the entire block>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m multi-line spans draw a single pointer after the block',
    'MULTI_LINE_EXPRESSION_POINTERS': 'Error: \x1b[31mdewy.errors.E3234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Multi-line expression pointers\n    ╭─[path/to/file.dewy:1:1]\n    ·  \x1b[96m╭\x1b[0m\x1b[96m─ <message about the 10x juxtaposition>\x1b[0m\n    ·  \x1b[96m│\x1b[0m\x1b[92m╭\x1b[0m\x1b[92m─ <message about the x(y) juxtaposition>\x1b[0m\n    ·  \x1b[96m╲\x1b[0m\x1b[92m╳\x1b[0m\x1b[92m╱\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | 10x(y)\n    · \x1b[93m┬\x1b[0m\x1b[93m─\x1b[0m\x1b[94m┬\x1b[0m\x1b[38;5;135m┬\x1b[0m\x1b[38;5;211m┬\x1b[0m\x1b[38;5;214m┬\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m│\x1b[0m\x1b[38;5;214m╰\x1b[0m\x1b[38;5;214m─ <message about the `)` token>\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about the `y` token>\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about the `(` token>\x1b[0m\n    · \x1b[93m│\x1b[0m \x1b[94m╰\x1b[0m\x1b[94m─ <message about the `x` token>\x1b[0m\n    · \x1b[93m╰\x1b[0m\x1b[93m─ <message about the `10` token>\x1b[0m\n  \x1b[38;5;245m2\x1b[0m | * 42 + 3^x\n    · \x1b[96m┬\x1b[0m \x1b[92m┬\x1b[0m\x1b[92m─\x1b[0m \x1b[93m┬\x1b[0m \x1b[94m┬\x1b[0m\x1b[38;5;135m┬\x1b[0m\x1b[38;5;211m┬\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m  \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about the `x` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m  \x1b[93m│\x1b[0m \x1b[94m│\x1b[0m\x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about the `^` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m  \x1b[93m│\x1b[0m \x1b[94m╰\x1b[0m\x1b[94m─ <message about the `3` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m  \x1b[93m╰\x1b[0m\x1b[93m─ <message about the `+` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m╰\x1b[0m\x1b[92m─ <message about the `42` token>\x1b[0m\n    · \x1b[96m╰\x1b[0m\x1b[96m─ <message about the `*` token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>',
    'THREE_LINE_SPANNING': 'Error: \x1b[31mdewy.errors.E4000 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Three-line spanning diagnostic\n    ╭─[path/to/file.dewy:1:1]\n    ·   \x1b[96m╭\x1b[0m\x1b[96m─ <message about alpha>\x1b[0m\n    ·   \x1b[96m│\x1b[0m    \x1b[92m╭\x1b[0m\x1b[92m─ <message about beta>\x1b[0m\n    · \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m┴\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m \x1b[92m─\x1b[0m\x1b[92m┴\x1b[0m\x1b[92m─\x1b[0m\x1b[92m─\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | alpha beta\n  \x1b[38;5;245m2\x1b[0m | gamma + delta\n    · \x1b[93m─\x1b[0m\x1b[93m─\x1b[0m\x1b[93m┬\x1b[0m\x1b[93m─\x1b[0m\x1b[93m─\x1b[0m \x1b[94m┬\x1b[0m \x1b[38;5;135m─\x1b[0m\x1b[38;5;135m─\x1b[0m\x1b[38;5;135m┬\x1b[0m\x1b[38;5;135m─\x1b[0m\x1b[38;5;135m─\x1b[0m\n    ·   \x1b[93m│\x1b[0m   \x1b[94m│\x1b[0m   \x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about delta>\x1b[0m\n    ·   \x1b[93m│\x1b[0m   \x1b[94m╰\x1b[0m\x1b[94m─ <message about `+`>\x1b[0m\n    ·   \x1b[93m╰\x1b[0m\x1b[93m─ <message about gamma>\x1b[0m\n  \x1b[38;5;245m3\x1b[0m | epsilon & zeta\n    · \x1b[38;5;211m─\x1b[0m\x1b[38;5;211m─\x1b[0m\x1b[38;5;211m─\x1b[0m\x1b[38;5;211m┬\x1b[0m\x1b[38;5;211m─\x1b[0m\x1b[38;5;211m─\x1b[0m\x1b[38;5;211m─\x1b[0m \x1b[38;5;214m┬\x1b[0m \x1b[96m─\x1b[0m\x1b[96m┬\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\n    ·    \x1b[38;5;211m│\x1b[0m    \x1b[38;5;214m│\x1b[0m  \x1b[96m╰\x1b[0m\x1b[96m─ <message about zeta>\x1b[0m\n    ·    \x1b[38;5;211m│\x1b[0m    \x1b[38;5;214m╰\x1b[0m\x1b[38;5;214m─ <message about `&`>\x1b[0m\n    ·    \x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about epsilon>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m defaults to showing all markers below for 3+ lines',
    'TOKEN_NEEDS_CONTEXT': "Error: \x1b[31mdewy.errors.E2234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Token needs additional context\n    ╭─[path/to/file.dewy:1:1]\n  \x1b[38;5;245m1\x1b[0m | printl'Hello, World'\n    · \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m┬\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\n    ·   \x1b[96m╰\x1b[0m\x1b[96m─ <per token message>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>",
    'TRIPLE_TIGHTLY_PACKED': 'Error: \x1b[31mdewy.errors.E3234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Triple tightly packed tokens\n    ╭─[path/to/file.dewy:1:1]\n    ·   \x1b[92m╭\x1b[0m\x1b[92m─ <message about the `[a]5` juxtaposition>\x1b[0m\n    ·   \x1b[92m│\x1b[0m\x1b[93m╭\x1b[0m\x1b[93m─ <message about the `5x` juxtaposition>\x1b[0m\n    ·   \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╭\x1b[0m\x1b[94m─ <message about the `x(y)` juxtaposition>\x1b[0m\n    ·   \x1b[92m╲\x1b[0m\x1b[93m╳\x1b[0m\x1b[94m╳\x1b[0m\x1b[94m╱\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | [a]5x(y)\n    · \x1b[96m┬\x1b[0m\x1b[92m┬\x1b[0m\x1b[93m┬\x1b[0m\x1b[94m┬\x1b[0m\x1b[38;5;135m┬\x1b[0m\x1b[38;5;211m┬\x1b[0m\x1b[38;5;214m┬\x1b[0m\x1b[96m┬\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m│\x1b[0m\x1b[38;5;214m│\x1b[0m\x1b[96m╰\x1b[0m\x1b[96m─ <message about the `)` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m│\x1b[0m\x1b[38;5;214m╰\x1b[0m\x1b[38;5;214m─ <message about the `y` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about the `(` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about the `x` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╰\x1b[0m\x1b[94m─ <message about the `5` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m╰\x1b[0m\x1b[93m─ <message about the `]` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m╰\x1b[0m\x1b[92m─ <message about the `a` token>\x1b[0m\n    · \x1b[96m╰\x1b[0m\x1b[96m─ <message about the `[` token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>',
    'TYPE_MISMATCH_TIMES': 'Error: \x1b[31mtype mismatch for argument `times`\x1b[0m\n\n    ╭─[path/to/py_example.py:4:10]\n  \x1b[38;5;245m4\x1b[0m | result = repeat("hello", "3")\n    ·          \x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m┬\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m\x1b[96m─\x1b[0m          \x1b[92m─\x1b[0m\x1b[92m┬\x1b[0m\x1b[92m─\x1b[0m\n    ·            \x1b[96m│\x1b[0m              \x1b[92m╰\x1b[0m\x1b[92m─ argument given is type \'str\'\x1b[0m\n    ·            \x1b[96m╰\x1b[0m\x1b[96m─ `repeat` function\'s second argument `times` expects an \'int\'\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m Consider changing string literal "3" to integer 3',
    'UNABLE_TO_JUXTAPOSE': "Error: \x1b[31mdewy.errors.E1234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Unable to juxtapose identifier and string\n    ╭─[path/to/file.dewy:1:7]\n  \x1b[38;5;245m1\x1b[0m | printl'Hello, World'\n    ·      \x1b[96m╱\x1b[0m\x1b[96m╲\x1b[0m\n    ·      \x1b[96m╰\x1b[0m\x1b[96m─ tried to juxtapose printl (string:>void) and 'Hello, World' (string)\x1b[0m\n    · \x1b[96m        expected whitespace or operator between identifier and string\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m insert a space or an operator",
    'UNPOSITIONED_TRIPLE_TIGHTLY_PACKED': 'Error: \x1b[31mdewy.errors.E3234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Unpositioned triple tightly packed tokens\n    ╭─[path/to/file.dewy:1:1]\n    ·   \x1b[92m╭\x1b[0m\x1b[92m─ <message about the `[a]5` juxtaposition>\x1b[0m\n    ·   \x1b[92m│\x1b[0m\x1b[93m╭\x1b[0m\x1b[93m─ <message about the `5x` juxtaposition>\x1b[0m\n    ·   \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╭\x1b[0m\x1b[94m─ <message about the `x(y)` juxtaposition>\x1b[0m\n    ·   \x1b[92m╲\x1b[0m\x1b[93m╳\x1b[0m\x1b[94m╳\x1b[0m\x1b[94m╱\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | [a]5x(y)\n    · \x1b[96m┬\x1b[0m\x1b[92m┬\x1b[0m\x1b[93m┬\x1b[0m\x1b[94m┬\x1b[0m\x1b[38;5;135m┬\x1b[0m\x1b[38;5;211m┬\x1b[0m\x1b[38;5;214m┬\x1b[0m\x1b[96m┬\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m│\x1b[0m\x1b[38;5;214m│\x1b[0m\x1b[96m╰\x1b[0m\x1b[96m─ <message about the `)` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m│\x1b[0m\x1b[38;5;214m╰\x1b[0m\x1b[38;5;214m─ <message about the `y` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m│\x1b[0m\x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about the `(` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m╰\x1b[0m\x1b[38;5;135m─ <message about the `x` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╰\x1b[0m\x1b[94m─ <message about the `5` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m│\x1b[0m\x1b[93m╰\x1b[0m\x1b[93m─ <message about the `]` token>\x1b[0m\n    · \x1b[96m│\x1b[0m\x1b[92m╰\x1b[0m\x1b[92m─ <message about the `a` token>\x1b[0m\n    · \x1b[96m╰\x1b[0m\x1b[96m─ <message about the `[` token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>',
    'UPPER_ABOVE_LOWER_BELOW': 'Error: \x1b[31mdewy.errors.E3234 (link)\x1b[0m\n\n  \x1b[31m×\x1b[0m Upper line pointers above, lower line below\n    ╭─[path/to/file.dewy:1:1]\n    · \x1b[96m╭\x1b[0m\x1b[96m─ <message about the `10` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m╭\x1b[0m\x1b[92m─ <message about the `x` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m╭\x1b[0m\x1b[93m─ <message about the `(` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╭\x1b[0m\x1b[94m─ <message about the `y` token>\x1b[0m\n    · \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m│\x1b[0m\x1b[38;5;135m╭\x1b[0m\x1b[38;5;135m─ <message about the `)` token>\x1b[0m\n    · \x1b[96m┴\x1b[0m\x1b[96m─\x1b[0m\x1b[92m┴\x1b[0m\x1b[93m┴\x1b[0m\x1b[94m┴\x1b[0m\x1b[38;5;135m┴\x1b[0m\n  \x1b[38;5;245m1\x1b[0m | 10x(y)\n  \x1b[38;5;245m2\x1b[0m | * 42 + 3^x\n    · \x1b[38;5;211m┬\x1b[0m \x1b[38;5;214m┬\x1b[0m\x1b[38;5;214m─\x1b[0m \x1b[96m┬\x1b[0m \x1b[92m┬\x1b[0m\x1b[93m┬\x1b[0m\x1b[94m┬\x1b[0m\n    · \x1b[38;5;211m│\x1b[0m \x1b[38;5;214m│\x1b[0m  \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m│\x1b[0m\x1b[94m╰\x1b[0m\x1b[94m─ <message about the `x` token>\x1b[0m\n    · \x1b[38;5;211m│\x1b[0m \x1b[38;5;214m│\x1b[0m  \x1b[96m│\x1b[0m \x1b[92m│\x1b[0m\x1b[93m╰\x1b[0m\x1b[93m─ <message about the `^` token>\x1b[0m\n    · \x1b[38;5;211m│\x1b[0m \x1b[38;5;214m│\x1b[0m  \x1b[96m│\x1b[0m \x1b[92m╰\x1b[0m\x1b[92m─ <message about the `3` token>\x1b[0m\n    · \x1b[38;5;211m│\x1b[0m \x1b[38;5;214m│\x1b[0m  \x1b[96m╰\x1b[0m\x1b[96m─ <message about the `+` token>\x1b[0m\n    · \x1b[38;5;211m│\x1b[0m \x1b[38;5;214m╰\x1b[0m\x1b[38;5;214m─ <message about the `42` token>\x1b[0m\n    · \x1b[38;5;211m╰\x1b[0m\x1b[38;5;211m─ <message about the `*` token>\x1b[0m\n    ╰───\n  \x1b[38;5;245mhelp:\x1b[0m <some helpful hint>',
}



def test_unable_to_juxtapose_plain() -> None:
    assert str(_error_unable_to_juxtapose(False)) == EXPECTED_PLAIN['UNABLE_TO_JUXTAPOSE']


def test_unable_to_juxtapose_color() -> None:
    assert str(_error_unable_to_juxtapose(True)) == EXPECTED_COLOR['UNABLE_TO_JUXTAPOSE']


def test_token_needs_context_plain() -> None:
    assert str(_error_token_needs_context(False)) == EXPECTED_PLAIN['TOKEN_NEEDS_CONTEXT']


def test_token_needs_context_color() -> None:
    assert str(_error_token_needs_context(True)) == EXPECTED_COLOR['TOKEN_NEEDS_CONTEXT']


def test_highlight_multiple_tokens_plain() -> None:
    assert str(_error_highlight_multiple_tokens(False)) == EXPECTED_PLAIN['HIGHLIGHT_MULTIPLE_TOKENS']


def test_highlight_multiple_tokens_color() -> None:
    assert str(_error_highlight_multiple_tokens(True)) == EXPECTED_COLOR['HIGHLIGHT_MULTIPLE_TOKENS']


def test_dealing_with_tightly_packed_plain() -> None:
    assert str(_error_dealing_with_tightly_packed(False)) == EXPECTED_PLAIN['DEALING_WITH_TIGHTLY_PACKED']


def test_dealing_with_tightly_packed_color() -> None:
    assert str(_error_dealing_with_tightly_packed(True)) == EXPECTED_COLOR['DEALING_WITH_TIGHTLY_PACKED']


def test_flipping_pointer_directions_plain() -> None:
    assert str(_error_flipping_pointer_directions(False)) == EXPECTED_PLAIN['FLIPPING_POINTER_DIRECTIONS']


def test_flipping_pointer_directions_color() -> None:
    assert str(_error_flipping_pointer_directions(True)) == EXPECTED_COLOR['FLIPPING_POINTER_DIRECTIONS']


def test_multi_line_expression_plain() -> None:
    assert str(_error_multi_line_expression_pointers(False)) == EXPECTED_PLAIN['MULTI_LINE_EXPRESSION_POINTERS']


def test_multi_line_expression_color() -> None:
    assert str(_error_multi_line_expression_pointers(True)) == EXPECTED_COLOR['MULTI_LINE_EXPRESSION_POINTERS']


def test_upper_above_lower_below_plain() -> None:
    assert str(_error_upper_above_lower_below(False)) == EXPECTED_PLAIN['UPPER_ABOVE_LOWER_BELOW']


def test_upper_above_lower_below_color() -> None:
    assert str(_error_upper_above_lower_below(True)) == EXPECTED_COLOR['UPPER_ABOVE_LOWER_BELOW']


def test_triple_tightly_packed_plain() -> None:
    assert str(_error_triple_tightly_packed(False)) == EXPECTED_PLAIN['TRIPLE_TIGHTLY_PACKED']


def test_triple_tightly_packed_color() -> None:
    assert str(_error_triple_tightly_packed(True)) == EXPECTED_COLOR['TRIPLE_TIGHTLY_PACKED']


def test_unpositioned_triple_tightly_packed_plain() -> None:
    assert str(_error_unpositioned_triple_tightly_packed(False)) == EXPECTED_PLAIN['UNPOSITIONED_TRIPLE_TIGHTLY_PACKED']


def test_unpositioned_triple_tightly_packed_color() -> None:
    assert str(_error_unpositioned_triple_tightly_packed(True)) == EXPECTED_COLOR['UNPOSITIONED_TRIPLE_TIGHTLY_PACKED']


def test_three_line_spanning_plain() -> None:
    assert str(_error_three_line_spanning(False)) == EXPECTED_PLAIN['THREE_LINE_SPANNING']


def test_three_line_spanning_color() -> None:
    assert str(_error_three_line_spanning(True)) == EXPECTED_COLOR['THREE_LINE_SPANNING']


def test_multiline_span_pointer_plain() -> None:
    assert str(_error_multiline_span_pointer(False)) == EXPECTED_PLAIN['MULTILINE_SPAN_POINTER']


def test_multiline_span_pointer_color() -> None:
    assert str(_error_multiline_span_pointer(True)) == EXPECTED_COLOR['MULTILINE_SPAN_POINTER']


def test_multidigit_line_numbers_plain() -> None:
    assert str(_error_multidigit_line_numbers(False)) == EXPECTED_PLAIN['MULTIDIGIT_LINE_NUMBERS']


def test_multidigit_line_numbers_color() -> None:
    assert str(_error_multidigit_line_numbers(True)) == EXPECTED_COLOR['MULTIDIGIT_LINE_NUMBERS']


def test_type_mismatch_plain() -> None:
    assert str(_error_type_mismatch_times(False)) == EXPECTED_PLAIN['TYPE_MISMATCH_TIMES']


def test_type_mismatch_color() -> None:
    assert str(_error_type_mismatch_times(True)) == EXPECTED_COLOR['TYPE_MISMATCH_TIMES']
