from enigma.core.rotor import Rotor
from enigma.core.reflector import Reflector
from enigma.core.plugboard import Plugboard
from enigma.core.machine import EnigmaMachine

from enigma.data.rotors import ROTOR_I, ROTOR_II, ROTOR_III, ROTOR_BETA
from enigma.data.reflectors import REFLECTOR_B_THIN


def make_m4_machine(
    greek_rotor=ROTOR_BETA,
    reflector_wiring=REFLECTOR_B_THIN,
    positions=("A", "A", "A", "A"),
    rings=(0, 0, 0, 0),
    plugboard_pairs=None,
):
    """
    Build an M4 machine:
    Right → Middle → Left → Greek → Reflector → back
    """

    if plugboard_pairs is None:
        plugboard_pairs = {}

    # Greek rotor (Beta or Gamma) — does NOT rotate
    greek_wiring, _ = greek_rotor
    greek = Rotor(
        greek_wiring, notch=None, ring_setting=rings[3], position=positions[3]
    )

    # Standard rotors (III, II, I) — historical M4 order
    r_wiring, r_notch = ROTOR_III
    m_wiring, m_notch = ROTOR_II
    l_wiring, l_notch = ROTOR_I

    r = Rotor(r_wiring, notch=r_notch, ring_setting=rings[0], position=positions[0])
    m = Rotor(m_wiring, notch=m_notch, ring_setting=rings[1], position=positions[1])
    left = Rotor(l_wiring, notch=l_notch, ring_setting=rings[2], position=positions[2])

    reflector = Reflector(reflector_wiring)
    plugboard = Plugboard(plugboard_pairs)

    # Order: right, middle, left, greek
    return EnigmaMachine([r, m, left, greek], reflector, plugboard)


# ---------------------------------------------------------
# 1. Test: single letter passes full M4 path
# ---------------------------------------------------------
def test_m4_single_letter():
    machine = make_m4_machine()
    out = machine.encode_letter("A")
    assert isinstance(out, str)
    assert len(out) == 1
    assert "A" <= out <= "Z"


# ---------------------------------------------------------
# 2. Test: reversibility (E(E(x)) == x)
# ---------------------------------------------------------
def test_m4_reversibility_single_letter():
    m1 = make_m4_machine()
    m2 = make_m4_machine()

    c = m1.encode_letter("A")
    p = m2.encode_letter(c)

    assert p == "A"


# ---------------------------------------------------------
# 3. Test: historical Kriegsmarine M4 known-value test
# ---------------------------------------------------------
def test_m4_historical_known_value():
    """
    Known reference:
    M4 with rotors III-II-I, Greek = Beta, Reflector = Thin B,
    positions AAAA, no plugboard:
    First encrypted letter of "A" is historically known to be "B".
    """

    machine = make_m4_machine(
        greek_rotor=ROTOR_BETA,
        reflector_wiring=REFLECTOR_B_THIN,
        positions=("A", "A", "A", "A"),
        rings=(0, 0, 0, 0),
        plugboard_pairs={},
    )

    out = machine.encode_letter("A")
    assert out == "B"


# ---------------------------------------------------------
# 4. Test: encrypt a short word
# ---------------------------------------------------------
def test_m4_encrypt_word():
    machine = make_m4_machine()

    plaintext = "HELLO"
    ciphertext = "".join(machine.encode_letter(c) for c in plaintext)

    assert len(ciphertext) == len(plaintext)
    assert all("A" <= ch <= "Z" for ch in ciphertext)


# ---------------------------------------------------------
# 5. Test: full-text reversibility
# ---------------------------------------------------------
def test_m4_full_text_reversibility():
    plaintext = "ENIGMARELOADED"

    m_enc = make_m4_machine()
    ciphertext = "".join(m_enc.encode_letter(c) for c in plaintext)

    m_dec = make_m4_machine()
    decrypted = "".join(m_dec.encode_letter(c) for c in ciphertext)

    assert decrypted == plaintext
