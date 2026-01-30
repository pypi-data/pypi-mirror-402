from someip_py.codec import *


class IdtCbIndicatorLightKls(SomeIpPayload):

    _include_struct_len = True

    Function: Uint8

    PWM: Uint8

    def __init__(self):

        self.Function = Uint8()

        self.PWM = Uint8()


class IdtCbIndicatorLight(SomeIpPayload):

    IdtCbIndicatorLight: IdtCbIndicatorLightKls

    def __init__(self):

        self.IdtCbIndicatorLight = IdtCbIndicatorLightKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
