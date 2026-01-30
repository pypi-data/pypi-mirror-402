from someip_py.codec import *


class IdtHangupCall(SomeIpPayload):

    IdtHangupCall: Uint8

    def __init__(self):

        self.IdtHangupCall = Uint8()


class IdtCallType(SomeIpPayload):

    IdtCallType: Uint8

    def __init__(self):

        self.IdtCallType = Uint8()


class IdtCallRetCode(SomeIpPayload):

    IdtCallRetCode: Uint8

    def __init__(self):

        self.IdtCallRetCode = Uint8()
