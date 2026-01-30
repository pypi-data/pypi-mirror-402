from someip_py.codec import *


class IdtSingleTopPosnSetStsStruct(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    SwtSts: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.SwtSts = Uint8()


class IdtTopPosnSetStsAry(SomeIpPayload):

    IdtTopPosnSetStsAry: SomeIpDynamicSizeArray[IdtSingleTopPosnSetStsStruct]

    def __init__(self):

        self.IdtTopPosnSetStsAry = SomeIpDynamicSizeArray(IdtSingleTopPosnSetStsStruct)
