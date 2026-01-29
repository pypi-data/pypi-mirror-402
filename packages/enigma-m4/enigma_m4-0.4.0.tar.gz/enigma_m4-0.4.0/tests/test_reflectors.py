from enigma.core.reflector import Reflector
from enigma.data.reflectors import (
    REFLECTOR_A,
    REFLECTOR_B,
    REFLECTOR_C,
    REFLECTOR_B_THIN,
    REFLECTOR_C_THIN,
)

ALL_REFLECTORS = [
    (REFLECTOR_A, True),
    (REFLECTOR_B, True),
    (REFLECTOR_C, True),
    (REFLECTOR_B_THIN, False),
    (REFLECTOR_C_THIN, False),
]


def test_all_reflectors_initialize():
    for wiring, involution in ALL_REFLECTORS:
        reflector = Reflector(wiring, involution=involution)
        assert len(reflector.wiring) == 26
        assert sorted(reflector.wiring) == sorted("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
