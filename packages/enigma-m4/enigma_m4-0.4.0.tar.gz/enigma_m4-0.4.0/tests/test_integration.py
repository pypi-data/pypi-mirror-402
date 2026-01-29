from enigma.core.rotor import Rotor
from enigma.core.reflector import Reflector
from enigma.core.plugboard import Plugboard
from enigma.core.machine import EnigmaMachine

from enigma.data.rotors import ROTOR_I, ROTOR_II, ROTOR_III
from enigma.data.reflectors import REFLECTOR_B


def make_machine():
    # ROTOR_X = (wiring, notch)
    r_wiring, r_notch = ROTOR_III
    m_wiring, m_notch = ROTOR_II
    l_wiring, l_notch = ROTOR_I

    r = Rotor(r_wiring, notch=r_notch, ring_setting=0, position="A")
    m = Rotor(m_wiring, notch=m_notch, ring_setting=0, position="A")
    left = Rotor(l_wiring, notch=l_notch, ring_setting=0, position="A")

    reflector = Reflector(REFLECTOR_B)
    plugboard = Plugboard({})  # no swaps

    return EnigmaMachine([r, m, left], reflector, plugboard)


# ---------------------------------------------------------
# 1. Test: single letter passes full path without crashing
# ---------------------------------------------------------
def test_single_letter_full_path():
    machine = make_machine()
    out = machine.encode_letter("A")
    assert isinstance(out, str)
    assert len(out) == 1
    assert "A" <= out <= "Z"


# ---------------------------------------------------------
# 2. Test: reversibility (E(E(x)) == x)
# ---------------------------------------------------------
def test_reversibility_single_letter():
    machine1 = make_machine()
    machine2 = make_machine()

    c = machine1.encode_letter("A")  # encrypt
    p = machine2.encode_letter(c)  # decrypt = encrypt again

    assert p == "A"


# ---------------------------------------------------------
# 3. Test: historical known-value test (I-II-III, Reflector B)
# ---------------------------------------------------------
def test_historical_known_value():
    machine = make_machine()

    # With I-II-III, Reflector B, AAA, no plugboard:
    # The first encrypted letter of "A" is historically known to be "B".
    out = machine.encode_letter("A")

    assert out == "B"
