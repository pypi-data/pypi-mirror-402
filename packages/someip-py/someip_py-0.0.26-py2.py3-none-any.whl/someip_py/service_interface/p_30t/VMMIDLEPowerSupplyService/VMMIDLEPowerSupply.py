from someip_py.codec import *


class IdtIDLEPowerSupplyStatus(SomeIpPayload):

    IdtIDLEPowerSupplyStatus: Uint8

    def __init__(self):

        self.IdtIDLEPowerSupplyStatus = Uint8()
