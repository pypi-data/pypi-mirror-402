from someip_py.codec import *


class IdtWiprWshrWorkReqKls(SomeIpPayload):

    _include_struct_len = True

    Category: Uint8

    Req: Uint8

    def __init__(self):

        self.Category = Uint8()

        self.Req = Uint8()


class IdtWiprWshrWorkReq(SomeIpPayload):

    IdtWiprWshrWorkReq: IdtWiprWshrWorkReqKls

    def __init__(self):

        self.IdtWiprWshrWorkReq = IdtWiprWshrWorkReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
