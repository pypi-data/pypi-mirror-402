from someip_py.codec import *


class IdtARCSuspMod(SomeIpPayload):

    IdtARCSuspMod: Uint8

    def __init__(self):

        self.IdtARCSuspMod = Uint8()
