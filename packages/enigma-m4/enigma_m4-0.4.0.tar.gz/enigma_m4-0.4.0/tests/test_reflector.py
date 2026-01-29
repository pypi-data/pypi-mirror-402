from enigma.core.reflector import Reflector


def test_reflector_basic_mapping():
    reflector = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")

    assert reflector.reflect("A") == "Y"
    assert reflector.reflect("Y") == "A"
    assert reflector.reflect("B") == "R"
    assert reflector.reflect("R") == "B"


def test_reflector_involution_validation():
    # This wiring is NOT an involution, should raise error
    invalid = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    try:
        Reflector(invalid)
        assert False, "Expected ValueError for non-involutive reflector"
    except ValueError:
        pass


def test_reflector_length_validation():
    try:
        Reflector("ABC")
    except ValueError as exc:
        assert "26 characters" in str(exc)
    else:
        assert False, "Expected ValueError for wrong length"


def test_reflector_fixed_point_validation():
    # A maps to A
    invalid = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    try:
        Reflector(invalid)
    except ValueError as exc:
        assert "map a letter to itself" in str(exc)
    else:
        assert False, "Expected ValueError for fixed point"


def test_reflector_non_involution():
    # Create a wiring that's not symmetric
    # Swap A->B and B->A, but make C->D, D->E or something, wait hard.
    # Actually, to make not involution, make wiring[ wiring[i] ] != i for some i
    # For example, A->B, B->C, C->A, but then for D, etc.
    # Let's make a simple one: swap A and B, leave others.
    wiring = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    wiring[0] = "B"  # A->B
    wiring[1] = "C"  # B->C
    wiring[2] = "A"  # C->A
    # Now, wiring[wiring[0]] = wiring['B'-'A'=1] = 'C', but should be 'A' for involution.
    # Yes, wiring[wiring[0]] = wiring[1] = 'C' != 'A'
    invalid = "".join(wiring)
    try:
        Reflector(invalid)
    except ValueError as exc:
        assert "must be an involution" in str(exc)
    else:
        assert False, "Expected ValueError for non-involution"


def test_reflector_reflect_non_letter():
    reflector = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")
    assert reflector.reflect("1") == "1"
    assert reflector.reflect(" ") == " "


def test_reflector_index_to_char():
    assert Reflector._index_to_char(0) == "A"
    assert Reflector._index_to_char(25) == "Z"
