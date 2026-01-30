from someip_py.codec import *


class IdtElSPDrivSetting(SomeIpPayload):

    IdtElSPDrivSetting: Uint8

    def __init__(self):

        self.IdtElSPDrivSetting = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
