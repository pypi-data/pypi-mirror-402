class EnigmaMachine:
    def __init__(self, rotors, reflector, plugboard):
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = plugboard

    def step(self):
        """
        Step rotors.
        M3: rotors = [r, m, l]
        M4: rotors = [r, m, l, greek]  (greek does NOT rotate)
        Implements authentic Enigma stepping rules.
        """

        # Always extract only the first 3 rotors for stepping
        r, m, left = self.rotors[:3]

        right_at_notch = r.at_notch()
        middle_at_notch = m.at_notch()

        # Double-step: middle steps if it is at its own notch
        if middle_at_notch:
            m.step()
            left.step()

        # Normal turnover: middle steps if right is at its notch
        if right_at_notch:
            m.step()

        # Right rotor always steps
        r.step()

    def encode_letter(self, char: str) -> str:
        # 1. Step rotors before encoding
        self.step()

        c = char.upper()
        if not ("A" <= c <= "Z"):
            return c

        # 2. Plugboard IN
        c = self.plugboard.swap(c)

        # 3. Forward through rotors (right → middle → left)
        for rotor in self.rotors:
            c = rotor.encode_forward(c)

        # 4. Reflector
        c = self.reflector.reflect(c)

        # 5. Backward through rotors (left → middle → right)
        for rotor in reversed(self.rotors):
            c = rotor.encode_backward(c)

        # 6. Plugboard OUT
        c = self.plugboard.swap(c)

        return c
