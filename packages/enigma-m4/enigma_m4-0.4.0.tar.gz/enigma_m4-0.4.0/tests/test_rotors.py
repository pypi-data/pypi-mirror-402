from enigma.core.rotor import Rotor
from enigma.data.rotors import (
    ROTOR_I,
    ROTOR_II,
    ROTOR_III,
    ROTOR_IV,
    ROTOR_V,
    ROTOR_VI,
    ROTOR_VII,
    ROTOR_VIII,
    ROTOR_BETA,
    ROTOR_GAMMA,
)

ALL_ROTORS = [
    ROTOR_I,
    ROTOR_II,
    ROTOR_III,
    ROTOR_IV,
    ROTOR_V,
    ROTOR_VI,
    ROTOR_VII,
    ROTOR_VIII,
    ROTOR_BETA,
    ROTOR_GAMMA,
]


def test_all_rotors_initialize():
    for wiring, notch in ALL_ROTORS:
        rotor = Rotor(
            wiring=wiring,
            notch=notch if notch is not None else "A",  # Greek rotors don't rotate
            ring_setting=0,
            position="A",
        )
        assert len(rotor.wiring) == 26
