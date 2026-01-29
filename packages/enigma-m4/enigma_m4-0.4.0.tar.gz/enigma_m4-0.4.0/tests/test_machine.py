from enigma.core.rotor import Rotor
from enigma.core.reflector import Reflector
from enigma.core.plugboard import Plugboard
from enigma.core.machine import EnigmaMachine
from enigma.data.rotors import ROTOR_I, ROTOR_II, ROTOR_III
from enigma.data.reflectors import REFLECTOR_B


def test_single_letter_encoding():
    plugboard = Plugboard([])

    rotor_r = Rotor(*ROTOR_I, ring_setting=0, position="A")
    rotor_m = Rotor(*ROTOR_II, ring_setting=0, position="A")
    rotor_l = Rotor(*ROTOR_III, ring_setting=0, position="A")

    reflector = Reflector(REFLECTOR_B)

    machine = EnigmaMachine([rotor_r, rotor_m, rotor_l], reflector, plugboard)
    result = machine.encode_letter("A")

    assert isinstance(result, str)
    assert len(result) == 1


def test_right_rotor_steps_on_each_keypress():
    plugboard = Plugboard([])
    rotor_r = Rotor(*ROTOR_I, ring_setting=0, position="A")
    rotor_m = Rotor(*ROTOR_II, ring_setting=0, position="A")
    rotor_l = Rotor(*ROTOR_III, ring_setting=0, position="A")
    reflector = Reflector(REFLECTOR_B)

    machine = EnigmaMachine([rotor_r, rotor_m, rotor_l], reflector, plugboard)

    machine.encode_letter("A")
    assert rotor_r.position == "B"


def test_enigma_stepping_rules():
    """
    Validates the authentic stepping rules of the Enigma M3 machine.

    Rules tested:
    1. The right rotor steps on every keypress.
    2. The middle rotor steps when the right rotor is at its notch (turnover).
    3. The middle rotor also steps when it is at its own notch (double‑stepping).
    4. The left rotor steps only when the middle rotor is at its notch.

    This test verifies stepping *logic*, not specific step numbers.
    """

    plugboard = Plugboard([])

    # Rotor I notch = Q
    # Rotor II notch = E
    # Rotor III notch = V
    rotor_r = Rotor(*ROTOR_I, ring_setting=0, position="A")
    rotor_m = Rotor(*ROTOR_II, ring_setting=0, position="A")
    rotor_l = Rotor(*ROTOR_III, ring_setting=0, position="A")

    reflector = Reflector(REFLECTOR_B)

    # Your machine uses rotor order: [RIGHT, MIDDLE, LEFT]
    machine = EnigmaMachine([rotor_r, rotor_m, rotor_l], reflector, plugboard)

    for _ in range(200):  # enough to observe turnover and double‑stepping
        prev_r = rotor_r.position
        prev_m = rotor_m.position
        prev_l = rotor_l.position

        # Check notch states BEFORE stepping
        right_at_notch_before = rotor_r.at_notch()
        middle_at_notch_before = rotor_m.at_notch()

        machine.encode_letter("A")

        # 1. Right rotor must always step
        assert rotor_r.position != prev_r

        # 2. If right rotor was at its notch → middle must step
        if right_at_notch_before:
            assert rotor_m.position != prev_m

        # 3. If middle rotor was at its notch → double‑step
        if middle_at_notch_before:
            assert rotor_m.position != prev_m
            # 4. Left rotor must also step in this case
            assert rotor_l.position != prev_l


def test_forced_double_step():
    """
    Forces a double‑step scenario by positioning the middle rotor on its own notch.

    According to real Enigma mechanics:
    - If the MIDDLE rotor is at its notch, it MUST step.
    - When the middle rotor steps due to its own notch, the LEFT rotor MUST also step.
    - The RIGHT rotor always steps regardless of notch states.

    This test does NOT require the right rotor to be at its notch.
    """

    plugboard = Plugboard([])

    # RIGHT rotor = Rotor I (notch Q)
    rotor_r = Rotor(*ROTOR_I, ring_setting=0, position="A")

    # MIDDLE rotor = Rotor II (notch E) → place it directly on its notch
    rotor_m = Rotor(*ROTOR_II, ring_setting=0, position="E")

    # LEFT rotor = Rotor III (notch V)
    rotor_l = Rotor(*ROTOR_III, ring_setting=0, position="A")

    reflector = Reflector(REFLECTOR_B)

    machine = EnigmaMachine([rotor_r, rotor_m, rotor_l], reflector, plugboard)

    # Save previous positions
    prev_r = rotor_r.position
    prev_m = rotor_m.position
    prev_l = rotor_l.position

    # Trigger stepping
    machine.encode_letter("A")

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # RIGHT rotor must step once
    assert rotor_r.position != prev_r

    # MIDDLE rotor must step once (because it was at its own notch)
    idx_m = alphabet.index(prev_m)
    expected_middle = alphabet[(idx_m + 1) % 26]
    assert rotor_m.position == expected_middle

    # LEFT rotor must also step once (because middle was at its notch)
    idx_l = alphabet.index(prev_l)
    expected_left = alphabet[(idx_l + 1) % 26]
    assert rotor_l.position == expected_left


def test_encode_non_letter():
    plugboard = Plugboard([])
    rotor_r = Rotor(*ROTOR_I, ring_setting=0, position="A")
    rotor_m = Rotor(*ROTOR_II, ring_setting=0, position="A")
    rotor_l = Rotor(*ROTOR_III, ring_setting=0, position="A")
    reflector = Reflector(REFLECTOR_B)
    machine = EnigmaMachine([rotor_r, rotor_m, rotor_l], reflector, plugboard)

    # Test with non-letter characters
    assert machine.encode_letter("1") == "1"
    assert machine.encode_letter(" ") == " "
    assert machine.encode_letter("@") == "@"
