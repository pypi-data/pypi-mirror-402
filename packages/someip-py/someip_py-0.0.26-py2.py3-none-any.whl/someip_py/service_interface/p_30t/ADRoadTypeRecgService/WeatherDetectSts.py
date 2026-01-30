from someip_py.codec import *


class IdtWthSts(SomeIpPayload):

    IdtWthSts: Uint8

    def __init__(self):

        self.IdtWthSts = Uint8()
