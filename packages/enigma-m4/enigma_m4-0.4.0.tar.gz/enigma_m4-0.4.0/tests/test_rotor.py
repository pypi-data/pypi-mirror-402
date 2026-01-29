from enigma.core.rotor import Rotor


def test_rotor_initialization():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", ring_setting=0, position="A")
    assert rotor.position == "A"
    assert rotor.ring_setting == 0
    assert rotor.notch == "Q"
    assert len(rotor.wiring) == 26


def test_rotor_forward_basic_mapping_without_offset():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")

    # A (0) -> E
    assert rotor.encode_forward("A") == "E"
    # B (1) -> K
    assert rotor.encode_forward("B") == "K"
    # C (2) -> M
    assert rotor.encode_forward("C") == "M"


def test_rotor_forward_with_position_offset():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", position="B")

    # Position B means: input is shifted by +1 before wiring
    # A (0) -> shifted to 1 -> wiring[1] = K -> index 10 -> shifted back to 9 -> J
    assert rotor.encode_forward("A") == "J"


def test_rotor_forward_with_ring_setting():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", ring_setting=1, position="A")

    # Ring setting = 1 means: input is shifted by -1 before wiring
    # A (0) -> shifted to 25 -> wiring[25] = J -> index 9 -> shifted back to 10 -> K
    assert rotor.encode_forward("A") == "K"


def test_rotor_backward_basic_mapping_without_offset():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")

    # Forward: A -> E
    # Backward: E -> A
    assert rotor.encode_backward("E") == "A"

    # Forward: B -> K
    # Backward: K -> B
    assert rotor.encode_backward("K") == "B"


def test_rotor_backward_with_position_offset():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", position="B")

    # Position B shifts input by +1 before wiring
    # Let's test a known forward/backward pair:
    # Forward with pos=B: A -> J
    # So backward with pos=B: J -> A
    assert rotor.encode_backward("J") == "A"


def test_rotor_backward_with_ring_setting():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", ring_setting=1)

    # Forward with ring=1: A -> K
    # So backward with ring=1: K -> A
    assert rotor.encode_backward("K") == "A"


def test_rotor_step_basic_rotation():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", position="A")

    rotor.step()
    assert rotor.position == "B"

    rotor.step()
    assert rotor.position == "C"


def test_rotor_step_wraparound():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", position="Z")

    rotor.step()
    assert rotor.position == "A"


def test_rotor_step_notch_trigger():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q", position="P")

    # P -> Q, so notch should trigger
    assert rotor.step() is True
    assert rotor.position == "Q"


def test_rotor_wiring_length_validation():
    try:
        Rotor("ABC", "Q")
    except ValueError as exc:
        assert "26 characters" in str(exc)
    else:
        assert False, "Expected ValueError for wrong wiring length"


def test_rotor_encode_forward_non_letter():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")
    assert rotor.encode_forward("1") == "1"
    assert rotor.encode_forward(" ") == " "


def test_rotor_encode_backward_non_letter():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")
    assert rotor.encode_backward("1") == "1"
    assert rotor.encode_backward(" ") == " "


def test_rotor_step_no_notch():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", None, position="A")
    assert rotor.step() is False
    assert rotor.position == "B"


def test_rotor_at_notch_no_notch():
    rotor = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", None)
    assert rotor.at_notch() is False
