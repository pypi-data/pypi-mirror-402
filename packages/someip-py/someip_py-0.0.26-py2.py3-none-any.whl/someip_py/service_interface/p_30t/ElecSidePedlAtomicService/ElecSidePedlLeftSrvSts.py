from someip_py.codec import *


class IdtElecSidePedlSrvCondition(SomeIpPayload):

    IdtElecSidePedlSrvCondition: Uint8

    def __init__(self):

        self.IdtElecSidePedlSrvCondition = Uint8()
