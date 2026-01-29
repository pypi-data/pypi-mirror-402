from enigma.core.plugboard import Plugboard


def test_plugboard_swaps_configured_pairs():
    pb = Plugboard({"A": "V", "B": "S"})
    assert pb.swap("A") == "V"
    assert pb.swap("V") == "A"
    assert pb.swap("B") == "S"
    assert pb.swap("S") == "B"


def test_plugboard_leaves_unconnected_letters_unchanged():
    pb = Plugboard({"A": "V"})
    assert pb.swap("C") == "C"
    assert pb.swap("Z") == "Z"


def test_plugboard_is_case_insensitive():
    pb = Plugboard({"a": "v"})
    assert pb.swap("a") == "V"
    assert pb.swap("A") == "V"
    assert pb.swap("v") == "A"
    assert pb.swap("V") == "A"


def test_plugboard_rejects_self_connection():
    try:
        Plugboard({"A": "A"})
    except ValueError as exc:
        assert "Cannot connect letter" in str(exc)
    else:
        assert False, "Expected ValueError for A->A connection"


def test_plugboard_rejects_duplicate_usage_of_letter():
    try:
        Plugboard({"A": "V", "B": "V"})
    except ValueError as exc:
        assert "already used" in str(exc)
    else:
        assert False, "Expected ValueError for duplicate letter usage"


def test_plugboard_string_format_dash():
    pb = Plugboard("A-B C-D")
    assert pb.swap("A") == "B"
    assert pb.swap("C") == "D"


def test_plugboard_string_format_spaces():
    pb = Plugboard("PO ML IU")
    assert pb.swap("P") == "O"
    assert pb.swap("M") == "L"
    assert pb.swap("I") == "U"


def test_plugboard_invalid_token_length():
    try:
        Plugboard("POM")
    except ValueError as exc:
        assert "Invalid plugboard token" in str(exc)
    else:
        assert False, "Expected ValueError for invalid token"


def test_plugboard_max_pairs():
    pairs = {}
    for i in range(10):
        a = chr(ord("A") + i * 2)
        b = chr(ord("A") + i * 2 + 1)
        pairs[a] = b
    Plugboard(pairs)  # 10 pairs ok
    try:
        Plugboard(dict(pairs, **{"Y": "Z"}))  # 11th pair
    except ValueError as exc:
        assert "cannot have more than 10 pairs" in str(exc)
    else:
        assert False, "Expected ValueError for too many pairs"


def test_plugboard_invalid_character():
    try:
        Plugboard({"1": "A"})
    except ValueError as exc:
        assert "Invalid plugboard character" in str(exc)
    else:
        assert False, "Expected ValueError for invalid character"


def test_plugboard_swap_non_alpha():
    pb = Plugboard([])
    assert pb.swap("1") == "1"
    assert pb.swap("ab") == "ab"


def test_plugboard_repr():
    pb = Plugboard({"A": "B"})
    assert repr(pb) == "Plugboard({'A': 'B', 'B': 'A'})"


def test_plugboard_pairs():
    pb = Plugboard({"A": "B", "C": "D"})
    pairs = pb.pairs()
    assert ("A", "B") in pairs
    assert ("C", "D") in pairs
    assert len(pairs) == 2


def test_plugboard_invalid_type():
    try:
        Plugboard(123)
    except TypeError as exc:
        assert "must be dict, list, or string" in str(exc)
    else:
        assert False, "Expected TypeError for invalid type"
