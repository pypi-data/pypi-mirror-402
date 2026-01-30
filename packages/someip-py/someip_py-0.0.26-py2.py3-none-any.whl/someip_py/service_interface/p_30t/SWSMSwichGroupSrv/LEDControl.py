from someip_py.codec import *


class IdtSWSMLEDReq(SomeIpPayload):

    IdtSWSMLEDReq: Uint8

    def __init__(self):

        self.IdtSWSMLEDReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
