"""
Helper script to regenerate the test cases for color output (e.g. if we ever change the color scheme).
"""


def _default_key_from_error_fn_name(error_fn_name: str) -> str:
    if not error_fn_name.startswith("_error_"):
        raise ValueError(error_fn_name)
    return error_fn_name.removeprefix("_error_").upper()


def generate_expected_dicts() -> tuple[dict[str, str], dict[str, str]]:
    import test_examples

    error_fns = [
        (name, fn)
        for name, fn in vars(test_examples).items()
        if name.startswith("_error_") and callable(fn)
    ]

    color_out: dict[str, str] = {}
    plain_out: dict[str, str] = {}
    for fn_name, fn in sorted(error_fns, key=lambda t: t[0]):
        key = _default_key_from_error_fn_name(fn_name)
        color_out[key] = str(fn(True))
        plain_out[key] = str(fn(False))
    return color_out, plain_out




def generate_expected_color_code() -> str:
    expected, _ = generate_expected_dicts()
    lines: list[str] = ["EXPECTED_COLOR = {"]
    for key in sorted(expected):
        lines.append(f"    {key!r}: {expected[key]!r},")
    lines.append("}")
    return "\n".join(lines)


def generate_expected_plain_code() -> str:
    _, expected = generate_expected_dicts()
    lines: list[str] = ["EXPECTED_PLAIN = {"]
    for key in sorted(expected):
        lines.append(f"    {key!r}: '''{expected[key]}''',")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    print(generate_expected_plain_code())
    print()
    print(generate_expected_color_code())


if __name__ == "__main__":
    main()
