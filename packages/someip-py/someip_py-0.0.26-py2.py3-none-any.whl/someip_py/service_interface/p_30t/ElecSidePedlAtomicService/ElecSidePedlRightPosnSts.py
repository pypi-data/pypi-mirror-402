from someip_py.codec import *


class IdtElSPRightPosnKls(SomeIpPayload):

    _include_struct_len = True

    ElSPRPosn: Uint8

    ElSPRDir: Uint8

    def __init__(self):

        self.ElSPRPosn = Uint8()

        self.ElSPRDir = Uint8()


class IdtElSPRightPosn(SomeIpPayload):

    IdtElSPRightPosn: IdtElSPRightPosnKls

    def __init__(self):

        self.IdtElSPRightPosn = IdtElSPRightPosnKls()
