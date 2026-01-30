from someip_py.codec import *


class IdtSwtRotateBtnForHWKls(SomeIpPayload):

    _include_struct_len = True

    RollDir: Uint8

    RollPos: Uint8

    def __init__(self):

        self.RollDir = Uint8()

        self.RollPos = Uint8()


class IdtSwtRotateBtnForHW(SomeIpPayload):

    IdtSwtRotateBtnForHW: IdtSwtRotateBtnForHWKls

    def __init__(self):

        self.IdtSwtRotateBtnForHW = IdtSwtRotateBtnForHWKls()
