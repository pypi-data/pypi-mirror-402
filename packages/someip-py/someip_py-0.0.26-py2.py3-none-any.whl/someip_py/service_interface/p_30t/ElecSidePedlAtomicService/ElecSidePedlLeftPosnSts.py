from someip_py.codec import *


class IdtElSPLeftPosnKls(SomeIpPayload):

    _include_struct_len = True

    ElSPLPosn: Uint8

    ElSPRDir: Uint8

    def __init__(self):

        self.ElSPLPosn = Uint8()

        self.ElSPRDir = Uint8()


class IdtElSPLeftPosn(SomeIpPayload):

    IdtElSPLeftPosn: IdtElSPLeftPosnKls

    def __init__(self):

        self.IdtElSPLeftPosn = IdtElSPLeftPosnKls()
