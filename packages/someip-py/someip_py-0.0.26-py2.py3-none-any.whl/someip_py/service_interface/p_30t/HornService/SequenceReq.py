from someip_py.codec import *


class IdtHornSequenceReqKls(SomeIpPayload):

    _include_struct_len = True

    OnTime: Uint16

    OffTime: Uint16

    Cycle: Uint8

    Category: Uint8

    def __init__(self):

        self.OnTime = Uint16()

        self.OffTime = Uint16()

        self.Cycle = Uint8()

        self.Category = Uint8()


class IdtHornSequenceReq(SomeIpPayload):

    IdtHornSequenceReq: IdtHornSequenceReqKls

    def __init__(self):

        self.IdtHornSequenceReq = IdtHornSequenceReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
