from someip_py.codec import *


class IdtSingleTopPosnSetStruct(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    TopPosition: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.TopPosition = Uint8()


class IdtTopPosnSetAry(SomeIpPayload):

    IdtTopPosnSetAry: SomeIpDynamicSizeArray[IdtSingleTopPosnSetStruct]

    def __init__(self):

        self.IdtTopPosnSetAry = SomeIpDynamicSizeArray(IdtSingleTopPosnSetStruct)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
