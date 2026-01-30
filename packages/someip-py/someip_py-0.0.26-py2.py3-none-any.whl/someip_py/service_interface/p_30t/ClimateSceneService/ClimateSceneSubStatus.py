from someip_py.codec import *


class IdtClimaSceneSubSts(SomeIpPayload):

    IdtClimaSceneSubSts: Uint8

    def __init__(self):

        self.IdtClimaSceneSubSts = Uint8()
