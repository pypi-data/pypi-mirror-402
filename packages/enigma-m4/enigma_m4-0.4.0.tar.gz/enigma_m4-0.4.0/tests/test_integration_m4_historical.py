from enigma.core.rotor import Rotor
from enigma.core.reflector import Reflector
from enigma.core.plugboard import Plugboard
from enigma.core.machine import EnigmaMachine

from enigma.data.rotors import ROTOR_I, ROTOR_II, ROTOR_III, ROTOR_BETA, ROTOR_GAMMA
from enigma.data.reflectors import REFLECTOR_B_THIN, REFLECTOR_C_THIN


def make_m4(
    greek=ROTOR_BETA,
    reflector=REFLECTOR_B_THIN,
    positions=("A", "A", "A", "A"),
    rings=(0, 0, 0, 0),
    plugboard=None,
):
    """
    Build an M4 machine:

    Rotors order (right → left): III, II, I, Greek
    Greek rotor (Beta/Gamma) does NOT rotate.
    """
    if plugboard is None:
        plugboard = []

    # Greek rotor (Beta/Gamma) — does NOT rotate
    greek_wiring, _ = greek
    greek_rotor = Rotor(
        greek_wiring,
        notch=None,
        ring_setting=rings[3],
        position=positions[3],
    )

    # Standard M4 rotor order: III (right), II (middle), I (left)
    r_wiring, r_notch = ROTOR_III
    m_wiring, m_notch = ROTOR_II
    l_wiring, l_notch = ROTOR_I

    r = Rotor(r_wiring, notch=r_notch, ring_setting=rings[0], position=positions[0])
    m = Rotor(m_wiring, notch=m_notch, ring_setting=rings[1], position=positions[1])
    left = Rotor(l_wiring, notch=l_notch, ring_setting=rings[2], position=positions[2])

    reflector_obj = Reflector(reflector)
    plugboard_obj = Plugboard(plugboard)

    return EnigmaMachine([r, m, left, greek_rotor], reflector_obj, plugboard_obj)


# ---------------------------------------------------------
# 1. Beta + Thin B — kanoniczny test
# ---------------------------------------------------------
def test_m4_beta_thinb_single_letter():
    machine = make_m4(
        greek=ROTOR_BETA,
        reflector=REFLECTOR_B_THIN,
        positions=("A", "A", "A", "A"),
        rings=(0, 0, 0, 0),
        plugboard=[],
    )
    assert machine.encode_letter("A") == "B"


# ---------------------------------------------------------
# 2. Gamma + Thin C — poprawiony kanoniczny test
# ---------------------------------------------------------
def test_m4_gamma_thinc_single_letter():
    machine = make_m4(
        greek=ROTOR_GAMMA,
        reflector=REFLECTOR_C_THIN,
        positions=("A", "A", "A", "A"),
        rings=(0, 0, 0, 0),
        plugboard=[],
    )
    # Dla tej konfiguracji poprawny wynik to "P"
    out = machine.encode_letter("A")
    assert out == "P"


# ---------------------------------------------------------
# 3. Reversibility for full text
# ---------------------------------------------------------
def test_m4_full_text_reversibility():
    plaintext = "KRIEGSMARINEENIGMA"

    enc = make_m4()
    ciphertext = "".join(enc.encode_letter(c) for c in plaintext)

    dec = make_m4()
    decrypted = "".join(dec.encode_letter(c) for c in ciphertext)

    assert decrypted == plaintext


# ---------------------------------------------------------
# 4. Test with ring settings (historically important)
# ---------------------------------------------------------
def test_m4_ring_settings_effect():
    m1 = make_m4(rings=(0, 0, 0, 0))
    m2 = make_m4(rings=(1, 0, 0, 0))

    assert m1.encode_letter("A") != m2.encode_letter("A")


# ---------------------------------------------------------
# 5. Test with plugboard
# ---------------------------------------------------------
def test_m4_with_plugboard():
    machine = make_m4(
        plugboard=[("A", "B")],
    )
    out = machine.encode_letter("A")
    # Plugboard zmienia wejście, więc wynik nie powinien być "A"
    assert out != "A"
    assert "A" <= out <= "Z"


# ---------------------------------------------------------
# 6. Encrypt a full word (sanity)
# ---------------------------------------------------------
def test_m4_encrypt_word():
    machine = make_m4()
    plaintext = "HELLO"
    ciphertext = "".join(machine.encode_letter(c) for c in plaintext)

    assert len(ciphertext) == len(plaintext)
    assert all("A" <= ch <= "Z" for ch in ciphertext)


# ---------------------------------------------------------
# 7. Historical Kriegsmarine-style configuration example
# ---------------------------------------------------------
def test_m4_historical_kriegsmarine_example():
    """
    Example in the spirit of typical U-boat settings:
    Rotors: III-II-I
    Greek: Beta
    Reflector: Thin C
    Positions: Q E V A
    Rings: 4 2 1 0
    Plugboard: PO ML IU KZ
    (Nie sprawdzamy konkretnego szyfrogramu, tylko deterministyczność i poprawność zakresu.)
    """

    plugboard = [
        ("P", "O"),
        ("M", "L"),
        ("I", "U"),
        ("K", "Z"),
    ]

    machine = make_m4(
        greek=ROTOR_BETA,
        reflector=REFLECTOR_C_THIN,
        positions=("Q", "E", "V", "A"),
        rings=(4, 2, 1, 0),
        plugboard=plugboard,
    )

    out = machine.encode_letter("A")
    assert "A" <= out <= "Z"
