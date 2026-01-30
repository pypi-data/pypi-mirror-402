from someip_py.codec import *


class IdtSoundTipSts(SomeIpPayload):

    IdtSoundTipSts: Uint8

    def __init__(self):

        self.IdtSoundTipSts = Uint8()
