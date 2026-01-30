from someip_py.codec import *


class IdtElSPMtnCmd(SomeIpPayload):

    IdtElSPMtnCmd: Uint8

    def __init__(self):

        self.IdtElSPMtnCmd = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
